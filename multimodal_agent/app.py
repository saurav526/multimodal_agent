import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent_core import MultiModalAgent
from modalities import (
    analyze_image, extract_text_from_file, extract_video_frames,
    transcribe_audio, transcribe_video_audio, text_to_speech, analyze_video_frames
)

load_dotenv()
st.set_page_config(page_title="Multimodal Agent", page_icon="✦", layout="wide")

st.title("✦ Multimodal Agent")
st.caption("One workspace for text, code, images, audio, video understanding, and voice output.")

with st.sidebar:
    st.subheader("Connection")
    api_key = st.text_input("Groq API key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    st.caption("Create a key at console.groq.com/keys")
    st.divider()
    st.subheader("Model routing")
    vision_model = st.selectbox("Text + image model", ["qwen/qwen3.8-27b", "qwen/qwen3.6-27b"], index=0)
    text_model = st.selectbox("Text / code / agent model", ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"], index=0)
    reviewer_model = st.selectbox("Reviewer model", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"], index=0)
    use_review = st.checkbox("Use multi-agent review", value=True)
    st.divider()
    st.markdown("**Supported workflows**")
    st.markdown("- Text chat and coding\n- Image understanding\n- Audio transcription\n- Text-to-speech audio output\n- Video frame + audio analysis\n- Text extraction from common documents")

if "messages" not in st.session_state:
    st.session_state.messages = []

agent = MultiModalAgent(api_key, text_model, reviewer_model) if api_key else None

tab_chat, tab_image, tab_audio, tab_video, tab_files = st.tabs(
    ["Chat & Code", "Image", "Audio & Voice", "Video", "Documents"]
)

def ensure_key():
    if not api_key:
        st.error("Enter your Groq API key in the sidebar, or set GROQ_API_KEY in your .env file.")
        return False
    return True

with tab_chat:
    st.subheader("Chat, reasoning, and code")
    st.caption("Ask questions, request code, debug errors, or ask the agents to plan and review a solution.")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask a question or request code...", key="chat_prompt")
    if prompt:
        if ensure_key():
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Planner, specialist, and reviewer are working..."):
                    try:
                        result = agent.run(prompt, use_reviewer=use_review)
                        st.markdown(result["answer"])
                        with st.expander("Agent workflow details"):
                            st.markdown("**Plan**")
                            st.markdown(result["plan"])
                            st.markdown("**Specialist draft**")
                            st.markdown(result["draft"])
                            if result["review"]:
                                st.markdown("**Review notes**")
                                st.markdown(result["review"])
                        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
                    except Exception as e:
                        st.error(f"{type(e).__name__}: {e}")
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.rerun()

with tab_image:
    st.subheader("Image understanding")
    st.write("Upload a photo, screenshot, chart, diagram, or image containing text.")
    image_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "webp"], key="image_upload")
    image_question = st.text_area("What should the agent inspect?", value="Describe this image and explain the important details.", key="image_question")
    if image_file:
        st.image(image_file, caption=image_file.name, use_container_width=True)
    if st.button("Analyze image", key="analyze_image_btn"):
        if ensure_key() and image_file:
            with st.spinner("Vision model is analyzing the image..."):
                try:
                    answer = analyze_image(api_key, vision_model, image_file.getvalue(), image_file.type, image_question)
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
        elif not image_file:
            st.warning("Upload an image first.")

with tab_audio:
    st.subheader("Audio input and voice generation")
    audio_file = st.file_uploader("Upload audio to transcribe", type=["wav", "mp3", "m4a", "ogg", "flac", "webm", "mp4", "mpeg"], key="audio_upload")
    language = st.selectbox("Audio language (optional)", ["Auto-detect", "English", "Hindi", "Spanish", "French", "German"], key="audio_language")
    if st.button("Transcribe audio", key="transcribe_btn"):
        if ensure_key() and audio_file:
            with st.spinner("Transcribing audio..."):
                try:
                    lang_map = {"English": "en", "Hindi": "hi", "Spanish": "es", "French": "fr", "German": "de"}
                    transcript = transcribe_audio(api_key, audio_file.name, audio_file.getvalue(), lang_map.get(language))
                    st.session_state.last_transcript = transcript
                    st.markdown("**Transcript**")
                    st.text_area("Transcript result", value=transcript, height=180, key="transcript_result")
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
        elif not audio_file:
            st.warning("Upload an audio file first.")
    if "last_transcript" in st.session_state:
        st.markdown("**Ask about the transcript**")
        transcript_question = st.text_input("Question", value="Summarize the main points.", key="transcript_question")
        if st.button("Analyze transcript", key="transcript_analyze_btn") and ensure_key():
            with st.spinner("Agents are analyzing the transcript..."):
                try:
                    st.markdown(agent.run(f"Analyze this audio transcript.\n\nTranscript:\n{st.session_state.last_transcript}\n\nTask: {transcript_question}", use_reviewer=use_review)["answer"])
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
    st.divider()
    st.markdown("**Text-to-speech**")
    tts_text = st.text_area("Text to speak", placeholder="Enter the text you want to turn into spoken audio...", key="tts_text")
    tts_voice = st.selectbox("Voice", ["austin", "daniel", "hannah", "troy"], index=0, key="tts_voice")
    if st.button("Generate speech", key="tts_btn"):
        if ensure_key() and tts_text.strip():
            with st.spinner("Generating audio..."):
                try:
                    audio_bytes = text_to_speech(api_key, tts_text.strip(), tts_voice)
                    st.audio(audio_bytes, format="audio/wav")
                    st.download_button("Download generated audio", data=audio_bytes, file_name="generated_speech.wav", mime="audio/wav")
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
        elif not tts_text.strip():
            st.warning("Enter text to speak first.")

with tab_video:
    st.subheader("Video understanding")
    st.write("Upload a short video. The app samples frames and, where possible, transcribes its audio track.")
    st.info("This provides video understanding, not video generation. The Groq workflow analyzes sampled frames plus the spoken audio transcript.")
    video_file = st.file_uploader("Choose a video", type=["mp4", "mov", "avi", "webm", "mkv"], key="video_upload")
    video_question = st.text_area("What do you want to know about the video?", value="Summarize the video, the sequence of events, and important visual details.", key="video_question")
    if st.button("Analyze video", key="analyze_video_btn"):
        if ensure_key() and video_file:
            suffix = Path(video_file.name).suffix or ".mp4"
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(video_file.getvalue())
                    tmp_path = tmp.name
                with st.spinner("Extracting video frames..."):
                    frames = extract_video_frames(tmp_path, max_frames=6)
                    if not frames:
                        st.error("Could not extract frames. Check that OpenCV can read this video format.")
                    else:
                        st.image([f[1] for f in frames], caption=[f"Frame at {f[0]:.1f}s" for f in frames], width=220)
                        transcript = ""
                        try:
                            transcript = transcribe_video_audio(api_key, video_file.name, video_file.getvalue())
                        except Exception as audio_error:
                            st.warning(f"Audio transcription was unavailable; continuing with visual frames only. Details: {audio_error}")
                        with st.spinner("Analyzing frames and transcript..."):
                            answer = analyze_video_frames(api_key, vision_model, frames, video_question, transcript)
                            st.markdown(answer)
                            if transcript:
                                with st.expander("Video audio transcript"):
                                    st.write(transcript)
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
        elif not video_file:
            st.warning("Upload a video first.")

with tab_files:
    st.subheader("Document and data analysis")
    st.write("Extract text from TXT, Markdown, PDF, DOCX, CSV, and JSON files, then ask the agent to summarize or analyze it.")
    doc_file = st.file_uploader("Upload a document or data file", type=["txt", "md", "pdf", "docx", "csv", "json"], key="doc_upload")
    doc_question = st.text_area("Task for this file", value="Summarize the file and identify its most important information.", key="doc_question")
    if st.button("Analyze document", key="doc_analyze_btn"):
        if ensure_key() and doc_file:
            try:
                extracted = extract_text_from_file(doc_file.name, doc_file.getvalue())
                if not extracted.strip():
                    st.warning("No readable text was extracted from this file.")
                else:
                    with st.expander("Preview extracted text"):
                        st.text(extracted[:12000])
                    with st.spinner("Analyzing document..."):
                        answer = agent.run(f"File name: {doc_file.name}\n\nFile content:\n{extracted[:30000]}\n\nTask: {doc_question}", use_reviewer=use_review)["answer"]
                        st.markdown(answer)
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")
        elif not doc_file:
            st.warning("Upload a file first.")

st.divider()
st.caption("Touch: the responsive interface supports touch interaction on phones/tablets. Raw touch-sensor interpretation is not provided. API model availability, limits, and costs depend on your Groq account.")
