---
description: Add a new modality (helper + UI tab + docs)
argument-hint: <modality name and what it should do>
---

Add this modality: $ARGUMENTS

Follow the project conventions in CLAUDE.md:

1. Add a stateless helper to `modalities.py` using `_client(api_key)`. No Streamlit imports.
2. Add a tab in `app.py` with a `try/except` that shows `st.error(...)`, plus an `ensure_key()` check.
3. Add the dependency to `requirements.txt` if needed.
4. Update the capability list and limits in `README.md`.
5. Run `python -m py_compile app.py agent_core.py modalities.py` to confirm it imports cleanly.
