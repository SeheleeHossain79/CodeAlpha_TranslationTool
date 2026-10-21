import io
import streamlit as st
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS

import time
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # makes detection consistent

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐")
st.title("🌐 Language Translation Tool")
st.caption("Type text, pick languages, and translate.")

# name -> code, e.g. {"bengali": "bn", "french": "fr", ...}
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)
names = sorted(LANGUAGES.keys())


def translate_text(text, source, target):
    """Try Google (with one retry); if it fails, fall back to MyMemory."""
    for attempt in range(2):
        try:
            result = GoogleTranslator(source=source, target=target).translate(text)
            return result, "Google Translate"
        except Exception:
            time.sleep(1)
    if source == "auto":
        raise ValueError(
            "Google is unavailable and the backup service can't auto-detect. "
            "Please choose the source language manually."
        )
    result = MyMemoryTranslator(source=source, target=target).translate(text)
    return result, "MyMemory (backup)"


def looks_like_target(result, target_code):
    """Check whether the output seems to be in the chosen language."""
    if len(result) < 10:
        return True  # too short to check reliably
    try:
        detected = detect(result).lower().split("-")[0]
    except Exception:
        return True
    return detected == target_code.lower().split("-")[0]


col1, col2 = st.columns(2)
with col1:
    source = st.selectbox("From", ["auto"] + names, index=0)
with col2:
    target = st.selectbox("To", names, index=names.index("bengali"))

text = st.text_area("Enter text to translate", height=150)

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text first.")
    elif source == target:
        st.warning("Source and target languages are the same.")
    else:
        with st.spinner("Translating..."):
            try:
                result, service = translate_text(text, source, target)
                st.session_state["result"] = result
                st.session_state["service"] = service
                st.session_state["target"] = target
                st.session_state["wrong_lang"] = not looks_like_target(result, LANGUAGES[target])
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"Translation failed: {e}")

if "result" in st.session_state:
    st.subheader("Translation")
    # st.code shows a small copy button in its top-right corner
    st.code(st.session_state["result"], language=None)
    st.caption(f"Translated using: {st.session_state['service']}")
    if st.session_state.get("wrong_lang"):
        st.warning(
            "This result may be in a different language than the one you chose. "
            "The backup service is less reliable, so try again later."
        )

    if st.button("🔊 Listen"):
        try:
            code = LANGUAGES[st.session_state["target"]]
            tts = gTTS(st.session_state["result"], lang=code)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            st.audio(buffer.getvalue(), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech isn't available for this language right now: {e}")