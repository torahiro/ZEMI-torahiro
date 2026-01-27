import streamlit as st   # ← これが必要！

import system3
import screan
import voice_upload

st.title("誹謗中傷対策ツール")

tabs = st.tabs(["言語変換", "画像認識", "音声認識"])

with tabs[0]:
    system3.run()

with tabs[1]:
    screan.run()

with tabs[2]:
    voice_upload.run()