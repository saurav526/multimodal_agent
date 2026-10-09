Groq Multimodal Agent

A Streamlit assistant that combines sequential agent roles with multimodal input/output workflows using the Groq API.

Capabilities
Text chat: ask questions and continue a session in the chat tab.
Code generation and debugging: request code, explain errors, and ask for implementation plans.
Multi-agent workflow: Planner → Specialist → Reviewer → Finalizer (review can be disabled).
Image understanding: upload images, screenshots, charts, diagrams, or OCR-style image content for vision analysis.
Audio input: upload audio for speech-to-text transcription using Whisper.
Audio output: generate spoken audio from text using Groq text-to-speech.
Video understanding: sample up to six frames from a video and combine visual analysis with an audio transcript when the API accepts the uploaded video format.
Documents and data: extract text from TXT, Markdown, PDF, DOCX, CSV, and JSON, then ask the agent to summarize or analyze it.
Touch interaction: responsive Streamlit controls work on touch-enabled devices. This does not mean raw touch sensor data is an AI input modality.
Important modality limits
This is not a single model that natively handles every modality. The app routes each task to a suitable API endpoint/model:

Text/code: chat-completion models.
Images: Qwen vision-capable model.
Audio transcription: whisper-large-v3-turbo.
Speech generation: canopylabs/orpheus-v1-english.
Video: selected still frames are sent to a vision model, and the video file is separately sent to transcription where supported.
Video generation is not included because this project uses Groq endpoints for understanding and speech output, not a video-generation service. Video analysis is approximate because only a small number of frames are sampled. Audio transcription can fail for unsupported/oversized files; check current Groq limits. TTS voice/language support depends on the selected API model. Models and account access can change, so use the current Groq model documentation if an ID is unavailable.

Requirements
Python 3.11 recommended
Groq API key: https://console.groq.com/keys
Internet connection for API calls
Windows, macOS, or Linux
Windows / VS Code setup
Download and extract the ZIP.

Open the extracted groq_multimodal_agent folder in VS Code.

Open Terminal → New Terminal.

Create and activate a virtual environment:

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
If py -3.11 is unavailable, use py -m venv .venv with a compatible installed Python version.

Install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt
Create your environment file:

Copy-Item .env.example .env
Open .env and replace the placeholder with your key:

GROQ_API_KEY=your_actual_groq_api_key
Start the application:

streamlit run app.py
Open the URL printed in the terminal, usually http://localhost:8501.

You may instead paste the key into the password field in the sidebar.

How to use
Chat & Code: type your request and press Enter.
Image: upload an image, enter a question, and click Analyze image.
Audio & Voice: upload a recording and transcribe it, or enter text to generate speech.
Video: upload a short video and ask about its events. The app samples up to six frames and attempts to transcribe the video audio.
Documents: upload a supported document or data file and enter a task.
Change the model selectors in the sidebar to compare supported models.
Turn off multi-agent review to reduce the number of chat-completion calls.
Troubleshooting
API key / 401: create a new key in Groq Console and update .env.
Model not found or not allowed: choose a model currently available in your account. Model IDs and availability change.
Rate limits / quota: check the Groq Console usage and limits.
Video cannot open: try MP4 (H.264) or a smaller/shorter clip. OpenCV codec support varies.
Video transcription fails: some video files or sizes may not be accepted by the audio endpoint. The visual analysis can still proceed.
Speech output fails: verify TTS access and model/voice availability in Groq docs.
PowerShell activation blocked: run Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass in that terminal, then activate again.
Missing dependency: confirm .venv is active and rerun pip install -r requirements.txt.
Security
Never share your API key or commit .env to GitHub. API calls may incur usage and are subject to Groq account limits.

Project structure
groq_multimodal_agent/
├── app.py
├── agent_core.py
├── modalities.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
