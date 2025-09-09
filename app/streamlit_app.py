from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
from dotenv import load_dotenv


@dataclass(frozen=True)
class SearchParams:
    q: Optional[str]
    committee: Optional[str]
    speaker: Optional[str]
    date_from: Optional[date]
    date_to: Optional[date]
    order_by: str
    order: str
    limit: int
    offset: int


def get_api_base() -> str:
    load_dotenv(override=False)
    base = os.getenv("IM_API_BASE", "http://127.0.0.1:8000")
    return base.rstrip("/")


@st.cache_data(ttl=30)
def api_search(base: str, p: SearchParams) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "committee": p.committee or None,
        "order_by": p.order_by,
        "order": p.order,
        "limit": p.limit,
        "offset": p.offset,
    }
    if p.q:
        params["q"] = p.q
    if p.date_from:
        params["date_from"] = p.date_from.isoformat()
    if p.date_to:
        params["date_to"] = p.date_to.isoformat()

    url = f"{base}/search"
    r = requests.get(url, params=params, timeout=(3.0, 10.0))
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def api_document(base: str, doc_id: int) -> Dict[str, Any]:
    url = f"{base}/document/{doc_id}"
    r = requests.get(url, timeout=(3.0, 10.0))
    r.raise_for_status()
    return r.json()


def _init_state() -> None:
    defaults = {
        "q": "",
        "committee": "",
        "speaker": "",
        "order_by": "date",
        "order": "desc",
        "limit": 10,
        "offset": 0,
        "selected_id": None,
        "date_from": None,
        "date_to": None,
        "apply_speaker_filter": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _form_section() -> Tuple[bool, SearchParams, Optional[str]]:
    """Render search form. Return (submitted, params, warning)."""
    warning: Optional[str] = None
    with st.form("search-form", clear_on_submit=False):
        st.text_input("キーワード", key="q")
        st.text_input("委員会（完全一致）", key="committee")
        st.text_input("話者（ページ内オプションフィルタ）", key="speaker")

        c1, c2 = st.columns(2)
        with c1:
            st.date_input("開始日 (date_from)", key="date_from")
        with c2:
            st.date_input("終了日 (date_to)", key="date_to")

        c3, c4, c5 = st.columns(3)
        with c3:
            st.selectbox("並び替え", options=["date", "committee", "relevance"], key="order_by")
        with c4:
            st.selectbox("順序", options=["desc", "asc"], key="order")
        with c5:
            st.selectbox("件数", options=[5, 10, 20], key="limit")

        st.checkbox(
            "このページに話者フィルタを適用（limit<=10のときのみ）",
            key="apply_speaker_filter",
            help="選択時、表示中の各記録に対して詳細を取得し、話者で絞り込みます。",
        )

        submitted = st.form_submit_button("検索")

    # Normalize & validate
    q: Optional[str] = st.session_state.get("q") or None
    order_by: str = st.session_state.get("order_by") or "date"
    order: str = st.session_state.get("order") or "desc"
    limit: int = int(st.session_state.get("limit") or 10)
    offset: int = int(st.session_state.get("offset") or 0)
    committee: Optional[str] = st.session_state.get("committee") or None
    speaker: Optional[str] = st.session_state.get("speaker") or None
    date_from: Optional[date] = st.session_state.get("date_from")
    date_to: Optional[date] = st.session_state.get("date_to")

    # date range validation
    if date_from and date_to and date_from > date_to:
        warning = "開始日が終了日より後になっています。"

    # relevance fallback when q is empty
    if order_by == "relevance" and not q:
        order_by = "date"

    params = SearchParams(
        q=q,
        committee=committee,
        speaker=speaker,
        date_from=date_from,
        date_to=date_to,
        order_by=order_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return submitted, params, warning


def _pager_controls(total: int, limit: int, offset: int, has_next: bool) -> Tuple[int, bool]:
    left, mid, right = st.columns([1, 2, 1])
    new_offset = offset
    changed = False
    with left:
        if st.button("Prev", disabled=offset <= 0, use_container_width=True):
            new_offset = max(0, offset - limit)
            changed = True
    with right:
        if st.button("Next", disabled=not has_next, use_container_width=True):
            new_offset = offset + limit
            changed = True
    with mid:
        current_page = (offset // max(1, limit)) + 1
        st.write(f"ページ: {current_page} / 合計: {total}")
    return new_offset, changed


def _render_list(base: str, data: Dict[str, Any], speaker_filter: Optional[str]) -> Optional[int]:
    items: List[Dict[str, Any]] = data.get("items") or []
    if not items:
        st.info("結果なし")
        return None

    st.markdown("<style>em{font-weight:600}</style>", unsafe_allow_html=True)

    selected_id: Optional[int] = None
    for it in items:
        # Optional per-page speaker filter
        if speaker_filter and data.get("limit", 10) <= 10:
            try:
                doc = api_document(base, int(it["id"]))
                has_speaker = any(
                    any((sp.get("speaker") or "") == speaker_filter for sp in ai.get("speeches", []))
                    for ai in (doc.get("agenda_items") or [])
                )
                if not has_speaker:
                    continue
            except Exception as e:  # pragma: no cover - best-effort filter
                st.warning(f"話者フィルタ取得失敗: {e}")

        with st.container(border=True):
            top = st.columns([2, 2, 1])
            title = (it.get("title") or "(無題)")
            with top[0]:
                st.write(f"**{title}**")
            with top[1]:
                st.write(f"{it.get('meeting_date') or ''} / {it.get('committee') or ''}")
            with top[2]:
                if st.button("詳細", key=f"detail-{it['id']}"):
                    selected_id = int(it["id"])
            # snippet (with <em>)
            snippet = it.get("snippet") or ""
            if snippet:
                st.markdown(snippet, unsafe_allow_html=True)
    return selected_id


def main() -> None:  # pragma: no cover - UI entry
    st.set_page_config(page_title="Itabashi Minutes", layout="wide")
    _init_state()

    base = get_api_base()
    st.caption(f"API: {base}")

    # If user pressed Search, reset offset
    submitted, params, warn = _form_section()
    if submitted:
        st.session_state["offset"] = 0
        params = params.__class__(**{**params.__dict__, "offset": 0})

    if warn:
        st.warning(warn)
        return

    # Selected detail route
    selected_id: Optional[int] = st.session_state.get("selected_id")
    if selected_id:
        try:
            doc = api_document(base, selected_id)
        except Exception as e:
            st.error(f"API error: {e}")
            st.session_state["selected_id"] = None
            return

        st.header(doc.get("title") or "(無題)")
        st.write(f"{doc.get('meeting_date') or ''} / {doc.get('committee') or ''}")
        pdf_url = doc.get("pdf_url")
        if pdf_url:
            st.link_button("PDFを開く", pdf_url, use_container_width=False)

        for idx, ai in enumerate(doc.get("agenda_items") or [], start=1):
            with st.expander(f"{idx}. {ai.get('title')}"):
                for sp in ai.get("speeches") or []:
                    head = " ".join(filter(None, [sp.get("role"), sp.get("speaker")]))
                    if head:
                        st.write(f"**{head}**")
                    for para in sp.get("paragraphs") or []:
                        st.write(para)

        if st.button("一覧に戻る"):
            st.session_state["selected_id"] = None
        return

    # List route
    try:
        data = api_search(base, params)
    except Exception as e:  # pragma: no cover - API failure path
        st.error(f"API error: {e}")
        return

    # Pager
    new_offset, changed = _pager_controls(
        total=int(data.get("total") or 0),
        limit=int(data.get("limit") or params.limit),
        offset=int(data.get("offset") or params.offset),
        has_next=bool(data.get("has_next")),
    )
    if changed:
        st.session_state["offset"] = new_offset
        st.rerun()

    # List
    maybe_id = _render_list(
        base,
        data,
        speaker_filter=(params.speaker or None) if st.session_state.get("apply_speaker_filter") else None,
    )
    if maybe_id is not None:
        st.session_state["selected_id"] = int(maybe_id)
        st.rerun()


if __name__ == "__main__":  # pragma: no cover
    main()

