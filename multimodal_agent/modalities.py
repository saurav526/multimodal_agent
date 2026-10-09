import base64
import io
import json
import os
import tempfile
from pathlib import Path

from groq import Groq


def _client(api_key):
    return Groq(api_key=api_key, timeout=120.0, max_retries=2)


def _mime_to_data_url(image_bytes, mime_type):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type or 'image/jpeg'};base64,{encoded}"


def analyze_image(api_key, model, image_bytes, mime_type, question):
    client = _client(api_key)
    data_url = _mime_to_data_url(image_bytes, mime_type)
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        temperature=0.2,
        max_completion_tokens=3000,
    )
    return response.choices[0].message.content or ""


def transcribe_audio(api_key, filename, data, language=None):
    client = _client(api_key)
    kwargs = {
        "file": (filename, data),
        "model": "whisper-large-v3-turbo",
        "response_format": "text",
        "temperature": 0.0,
    }
    if language:
        kwargs["language"] = language
    result = client.audio.transcriptions.create(**kwargs)
    return result if isinstance(result, str) else getattr(result, "text", str(result))


def transcribe_video_audio(api_key, filename, data):
    # Groq accepts common audio/video container formats for transcription.
    return transcribe_audio(api_key, filename, data, None)


def text_to_speech(api_key, text, voice="austin"):
    client = _client(api_key)
    response = client.audio.speech.create(
        model="canopylabs/orpheus-v1-english",
        voice=voice,
        input=text[:4000],
        response_format="wav",
    )
    if hasattr(response, "read"):
        return response.read()
    if hasattr(response, "content"):
        return response.content
    if hasattr(response, "write_to_file"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            path = tmp.name
        try:
            response.write_to_file(path)
            with open(path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(path):
                os.remove(path)
    raise RuntimeError("Unexpected response format from Groq text-to-speech API.")


def extract_video_frames(video_path, max_frames=6):
    try:
        import cv2
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Video processing dependencies missing. Install opencv-python-headless and Pillow.") from exc

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    duration = frame_count / fps if fps > 0 else 0
    if frame_count <= 0:
        cap.release()
        return []

    # Sample evenly spaced timestamps, avoiding duplicate frames.
    if duration > 0:
        times = [duration * (i + 0.5) / max_frames for i in range(max_frames)]
    else:
        times = [0.0]
    frames = []
    seen = set()
    for seconds in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        marker = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if marker in seen:
            continue
        seen.add(marker)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((1000, 1000))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        frames.append((seconds, buffer.getvalue()))
    cap.release()
    return frames


def analyze_video_frames(api_key, model, frames, question, transcript=""):
    client = _client(api_key)
    content = [{
        "type": "text",
        "text": (
            f"Analyze this video using the sampled frames. User question: {question}\n"
            "Describe only what is supported by the frames/transcript. Mention that only sampled frames were inspected; do not claim continuous frame-by-frame review.\n"
            f"Audio transcript, if available:\n{transcript[:12000] or '[No transcript available]'}"
        ),
    }]
    for seconds, image_bytes in frames[:6]:
        data_url = _mime_to_data_url(image_bytes, "image/jpeg")
        content.append({"type": "text", "text": f"Sampled video frame at approximately {seconds:.1f} seconds:"})
        content.append({"type": "image_url", "image_url": {"url": data_url}})
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=0.2,
        max_completion_tokens=4000,
    )
    return response.choices[0].message.content or ""


def extract_text_from_file(filename, data):
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".json", ".csv"}:
        return data.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support missing. Install pypdf.") from exc
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support missing. Install python-docx.") from exc
        document = Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs)
    raise ValueError(f"Unsupported file type: {suffix}")
