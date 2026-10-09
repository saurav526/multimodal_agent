# Groq Multimodal Agent

Streamlit app that routes text, code, image, audio, video, and document tasks to different Groq API models. Not a single native multimodal model: each modality calls its own endpoint.

## Layout

All code lives in the inner `multimodal_agent/` folder. Run every command from there.

```
multimodal_agent/            <- repo root
├── .claude/                 <- this folder
└── multimodal_agent/        <- project root (cd here)
    ├── app.py               Streamlit UI: sidebar + 5 tabs (Chat, Image, Audio, Video, Documents)
    ├── agent_core.py        MultiModalAgent: Planner -> Specialist -> Reviewer -> Finalizer
    ├── modalities.py        Stateless Groq helpers per modality + file text extraction
    ├── requirements.txt
    └── .gitignore
```

## Commands

```bash
cd multimodal_agent
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py                                 # http://localhost:8501
```

API key: `GROQ_API_KEY` in `.env` (loaded by python-dotenv) or the sidebar password field.
There is no test suite or linter configured yet.

## Architecture

- `app.py` imports `MultiModalAgent` and the functions in `modalities.py`. UI state lives in `st.session_state` (`messages`, `last_transcript`).
- `agent_core.py` has `complete()` (one chat call) and `run(prompt, use_reviewer)`, which returns `{plan, draft, review, answer}`. With the reviewer off it makes 2 calls; on, 4.
- `modalities.py` functions each create a fresh `Groq` client via `_client(api_key)`:
  - `analyze_image`, `analyze_video_frames` -> vision chat completion (images sent as base64 data URLs)
  - `transcribe_audio`, `transcribe_video_audio` -> `whisper-large-v3-turbo`
  - `text_to_speech` -> `canopylabs/orpheus-v1-english`, returns WAV bytes (input capped at 4000 chars)
  - `extract_video_frames` -> OpenCV, up to 6 evenly spaced frames, resized to max 1000px JPEG
  - `extract_text_from_file` -> txt/md/json/csv/pdf/docx
- Model IDs for chat and vision are chosen in the `app.py` sidebar; STT and TTS model IDs are hardcoded in `modalities.py`.

## Conventions

- Keep `modalities.py` functions stateless and UI-free (no `streamlit` imports). UI belongs in `app.py`.
- New modality = helper in `modalities.py` + a tab in `app.py` + a line in the README capability list.
- Wrap API calls in the UI with `try/except` and show `st.error(f"{type(e).__name__}: {e}")`, matching existing code.
- Truncation limits in use: documents 30000 chars to the agent, 12000 in the preview; video transcript 12000 chars.
- Never print, log, or commit the API key. `.env` must stay in `.gitignore`.

## Known gaps

- `README.md` references `.env.example`, which is not in the repo. Create it with `GROQ_API_KEY=your_key_here`.
- README project tree says `groq_multimodal_agent/`; the actual folder is `multimodal_agent/`.
- Model IDs in the sidebar (e.g. `qwen/qwen3.8-27b`) may become unavailable. Check Groq's current model list if a call returns "model not found".
- No video generation; video analysis is frame sampling only.
