from __future__ import annotations

import pytest


def test_mcp_fallback_import() -> None:
    """
    Ensure fallback server is importable.
    If optional deps are missing, skip via importorskip.
    """
    pytest.importorskip("jsonrpcserver")
    import mcp.server as srv  # type: ignore

    assert hasattr(srv, "main")
    assert isinstance(srv.SEARCH_SCHEMA, dict)
    assert isinstance(srv.GETDOC_SCHEMA, dict)

