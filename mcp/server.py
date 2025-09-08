from __future__ import annotations

import asyncio
import os
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter

try:
    # urllib3 Retry is optional; if missing, fall back to no retry
    from urllib3.util.retry import Retry  # type: ignore
except Exception:  # pragma: no cover
    Retry = None  # type: ignore


def get_api_base() -> str:
    load_dotenv(override=False)
    base = os.getenv("IM_API_BASE", "http://127.0.0.1:8000")
    return base.rstrip("/")


def build_session() -> requests.Session:
    s = requests.Session()
    if Retry is not None:
        retry = Retry(total=2, backoff_factor=0.2, status_forcelist=[429, 500, 502, 503, 504])
        s.mount("http://", HTTPAdapter(max_retries=retry))
        s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


SEARCH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "q": {"type": ["string", "null"]},
        "committee": {"type": ["string", "null"]},
        "date_from": {"type": ["string", "null"], "format": "date"},
        "date_to": {"type": ["string", "null"], "format": "date"},
        "order_by": {"type": "string", "enum": ["date", "committee", "relevance"], "default": "date"},
        "order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
        "offset": {"type": "integer", "minimum": 0, "default": 0},
    },
    "additionalProperties": False,
}

GETDOC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "minimum": 1},
    },
    "required": ["id"],
    "additionalProperties": False,
}


def _validate_params(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    # Minimal inline validation to avoid adding extra deps here.
    try:
        if schema is SEARCH_SCHEMA:
            if "order_by" in data and data["order_by"] not in ["date", "committee", "relevance"]:
                return False, "order_by must be one of: date, committee, relevance"
            if "order" in data and data["order"] not in ["asc", "desc"]:
                return False, "order must be one of: asc, desc"
            if "limit" in data and not (1 <= int(data["limit"]) <= 100):
                return False, "limit must be within [1, 100]"
            if "offset" in data and int(data["offset"]) < 0:
                return False, "offset must be >= 0"
        elif schema is GETDOC_SCHEMA:
            if "id" not in data:
                return False, "id is required"
            if int(data["id"]) < 1:
                return False, "id must be >= 1"
    except Exception as e:
        return False, f"parameter validation error: {e}"
    return True, None


def _map_http_error(resp: Optional[requests.Response], exc: Optional[Exception]) -> Dict[str, Any]:
    request_id = str(uuid.uuid4())[:8]
    if resp is not None:
        status = resp.status_code
        try:
            text = resp.text[:200]
        except Exception:
            text = ""
        if status == 404:
            return {"code": "NotFound", "message": f"upstream 404: resource not found ({text})", "request_id": request_id}
        if status in (400, 422):
            return {"code": "BadRequest", "message": f"upstream {status}: invalid request ({text})", "request_id": request_id}
        return {"code": "UpstreamError", "message": f"upstream {status}: {text}", "request_id": request_id}
    return {"code": "UpstreamError", "message": f"upstream error: {exc}", "request_id": request_id}


@dataclass
class ApiClient:
    base: str
    timeout: Tuple[float, float] = (3.0, 15.0)
    session: requests.Session = field(default_factory=build_session)

    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # qが空で order_by=relevance の場合はdateへフォールバック
        if (not params.get("q")) and params.get("order_by") == "relevance":
            params = dict(params)
            params["order_by"] = "date"
        url = f"{self.base}/search"
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            if r.status_code >= 400:
                raise requests.HTTPError(response=r)
            return r.json()
        except requests.HTTPError as he:
            raise ToolError(**_map_http_error(he.response, None))
        except Exception as e:
            raise ToolError(**_map_http_error(None, e))

    def get_document(self, doc_id: int) -> Dict[str, Any]:
        url = f"{self.base}/document/{doc_id}"
        try:
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code >= 400:
                raise requests.HTTPError(response=r)
            return r.json()
        except requests.HTTPError as he:
            raise ToolError(**_map_http_error(he.response, None))
        except Exception as e:
            raise ToolError(**_map_http_error(None, e))


class ToolError(Exception):
    def __init__(self, code: str, message: str, request_id: str) -> None:
        super().__init__(message)
        self.code = code
        self.request_id = request_id
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "request_id": self.request_id}


def _stdio_jsonrpc_server() -> None:
    """
    Fallback stdio JSON-RPC server (requires jsonrpcserver).
    Exposes methods: search_minutes(params), get_document(id)
    """
    try:
        from jsonrpcserver import method, serve  # type: ignore
        from jsonrpcserver import Error as JrpcError  # type: ignore
    except Exception:
        print("jsonrpcserver is not installed. Run: poetry install --with mcp", file=sys.stderr)
        sys.exit(1)

    api = ApiClient(get_api_base())

    @method
    def search_minutes(**kwargs: Any) -> Any:  # type: ignore
        ok, msg = _validate_params(kwargs, SEARCH_SCHEMA)
        if not ok:
            te = ToolError("BadRequest", msg or "invalid params", request_id=str(uuid.uuid4())[:8])
            raise JrpcError(code=-32000, message=te.message, data=te.to_dict())
        try:
            return api.search(kwargs)
        except ToolError as te:
            raise JrpcError(code=-32000, message=te.message, data=te.to_dict())

    @method
    def get_document(id: int) -> Any:  # type: ignore
        ok, msg = _validate_params({"id": id}, GETDOC_SCHEMA)
        if not ok:
            te = ToolError("BadRequest", msg or "invalid params", request_id=str(uuid.uuid4())[:8])
            raise JrpcError(code=-32000, message=te.message, data=te.to_dict())
        try:
            return api.get_document(int(id))
        except ToolError as te:
            raise JrpcError(code=-32000, message=te.message, data=te.to_dict())

    print(f"[MCP] itabashi-minutes ready (base={api.base})", file=sys.stderr)
    # Block and serve on stdio
    serve()


async def _mcp_sdk_server() -> None:
    """
    Native MCP (stdio) server if `mcp` package is available.
    Exposes tools: search_minutes, get_document
    """
    try:
        from mcp.server import Server  # type: ignore
        from mcp.server.stdio import stdio_server  # type: ignore
    except Exception:
        raise

    server = Server("itabashi-minutes")
    api = ApiClient(get_api_base())

    @server.tool(
        "search_minutes",
        SEARCH_SCHEMA,
        description="全文検索で会議録を探し、<em>強調</em>付きスニペットとメタ情報を返す。",
    )
    async def _search_minutes(**kwargs: Any) -> Dict[str, Any]:  # type: ignore
        ok, msg = _validate_params(kwargs, SEARCH_SCHEMA)
        if not ok:
            raise ToolError("BadRequest", msg or "invalid params", request_id=str(uuid.uuid4())[:8])
        result = api.search(kwargs)
        return {"content": [{"type": "json", "json": result}]}

    @server.tool(
        "get_document",
        GETDOC_SCHEMA,
        description="会議録1件の詳細（メタ・議題・発言・PDF URL）を返す。",
    )
    async def _get_document(id: int) -> Dict[str, Any]:  # type: ignore
        ok, msg = _validate_params({"id": id}, GETDOC_SCHEMA)
        if not ok:
            raise ToolError("BadRequest", msg or "invalid params", request_id=str(uuid.uuid4())[:8])
        result = api.get_document(int(id))
        return {"content": [{"type": "json", "json": result}]}

    # stdio で待ち受け
    with stdio_server() as (read, write):  # type: ignore
        print(f"[MCP] itabashi-minutes ready (base={api.base})", file=sys.stderr)
        await server.run(read, write)  # type: ignore


def main(argv: Optional[list[str]] = None) -> None:
    # まず MCP SDK を試し、無ければ JSON-RPC にフォールバック
    try:
        asyncio.run(_mcp_sdk_server())
    except Exception:
        _stdio_jsonrpc_server()


if __name__ == "__main__":  # pragma: no cover
    main()

