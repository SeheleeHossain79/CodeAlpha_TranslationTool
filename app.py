import io
import time
import streamlit as st
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐")

st.markdown(
    """
    <style>
    .block-container {max-width: 800px; padding-top: 2rem;}
    div.stButton > button {width: 100%; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)
names = sorted(LANGUAGES.keys())
MAX_CHARS = 1000

# Default selections (only set on the first run)
st.session_state.setdefault("src_lang", "english")
st.session_state.setdefault("tgt_lang", "bengali")
st.session_state.setdefault("history", [])


def translate_text(text, source, target):
    """Try Google (with one retry); if it fails, fall back to MyMemory."""
    for _ in range(2):
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
        return True
    try:
        detected = detect(result).lower().split("-")[0]
    except Exception:
        return True
    return detected == target_code.lower().split("-")[0]


def swap_languages():
    src, tgt = st.session_state["src_lang"], st.session_state["tgt_lang"]
    if src != "auto":
        st.session_state["src_lang"] = tgt
        st.session_state["tgt_lang"] = src


def clear_all():
    st.session_state["input_text"] = ""
    for key in ("result", "service", "result_lang", "wrong_lang"):
        st.session_state.pop(key, None)


# ---------- Page ----------
st.title("🌐 Language Translation Tool")
st.caption("Type text, pick languages, and translate.")

col1, col_mid, col2 = st.columns([5, 1.2, 5])
with col1:
    st.selectbox("From", ["auto"] + names, key="src_lang")
with col_mid:
    st.write("")  # spacer so the button lines up with the dropdowns
    st.button("⇄", on_click=swap_languages, help="Swap languages")
with col2:
    st.selectbox("To", names, key="tgt_lang")

text = st.text_area(
    "Enter text to translate",
    height=150,
    max_chars=MAX_CHARS,
    key="input_text",
    placeholder="Type or paste your text here...",
)

b1, b2 = st.columns(2)
translate_clicked = b1.button("Translate", type="primary")
b2.button("Clear", on_click=clear_all)

if translate_clicked:
    source, target = st.session_state["src_lang"], st.session_state["tgt_lang"]
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
                st.session_state["result_lang"] = target
                st.session_state["wrong_lang"] = not looks_like_target(
                    result, LANGUAGES[target]
                )
                st.session_state["history"].insert(
                    0, (source, target, text[:60], result[:60])
                )
                st.session_state["history"] = st.session_state["history"][:5]
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"Translation failed: {e}")

if "result" in st.session_state:
    st.subheader("Translation")
    st.code(st.session_state["result"], language=None)  # has a built-in copy icon
    st.caption(f"Translated using: {st.session_state['service']}")

    if st.session_state.get("wrong_lang"):
        st.warning(
            "This result may be in a different language than the one you chose. "
            "The backup service is less reliable, so try again later."
        )

    if st.button("🔊 Listen"):
        try:
            code = LANGUAGES[st.session_state["result_lang"]]
            buffer = io.BytesIO()
            gTTS(st.session_state["result"], lang=code).write_to_fp(buffer)
            st.audio(buffer.getvalue(), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech isn't available right now: {e}")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Recent translations")
    if not st.session_state["history"]:
        st.caption("Nothing yet.")
    for src, tgt, original, translated in st.session_state["history"]:
        st.markdown(f"**{src} → {tgt}**")
        st.caption(f"{original}")
        st.write(translated)
        st.divider()