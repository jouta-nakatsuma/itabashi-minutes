from __future__ import annotations

from pathlib import Path


def main() -> None:
    """Launch Streamlit app via official bootstrap API.

    This keeps Ctrl+C behavior sane and avoids subprocess juggling.
    """
    try:
        # Streamlit import only when invoked (optional dependency group "app").
        from streamlit.web.bootstrap import run  # type: ignore
    except Exception:  # pragma: no cover - UI optional
        raise SystemExit(
            "Streamlit is not installed. Run: poetry install --with app"
        )

    target = str(Path(__file__).parent / "streamlit_app.py")
    # args: command_line, args, flag_options are intentionally minimal.
    run(target, "", [], flag_options={})

