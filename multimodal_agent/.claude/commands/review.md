---
description: Review the code for bugs, security, and API-usage problems
---

Review `app.py`, `agent_core.py`, and `modalities.py`. Check for:

- Secrets: API key exposure, `.env` not ignored.
- Error handling around every Groq call and file read.
- Large-file handling (video, audio, PDFs) and temp-file cleanup.
- Hardcoded model IDs that may be unavailable.
- Streamlit state bugs (reruns resetting results, missing keys in `st.session_state`).

Return findings grouped by severity with file and line references. Do not edit files unless I ask.
