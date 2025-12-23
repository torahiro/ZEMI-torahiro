import streamlit as st

# 誹謗中傷ワード辞書（最低限）
BAD_WORDS = [
    "無能",
    "バカ",
    "死ね",
    "消えろ",
    "きもい",
]

def detect_bad_words(text):
    detected = [w for w in BAD_WORDS if w in text]
    return detected

# ===== UI =====
st.set_page_config(page_title="誹謗中傷防止システム", layout="centered")
st.title("投稿前誹謗中傷チェック")

st.write("投稿内容に誹謗中傷が含まれる場合、投稿はできません。")

text = st.text_area("投稿内容を入力してください", height=150)

detected_words = detect_bad_words(text)

if detected_words:
    st.error("⚠️ 攻撃的な表現が検出されました")
    st.write("検出された語句：", ", ".join(detected_words))
    st.write("修正しない限り投稿できません。")
    post_allowed = False
else:
    if text.strip() != "":
        st.success("問題のある表現は検出されませんでした")
    post_allowed = True

# ===== 投稿ボタン =====
st.button(
    "投稿する",
    disabled=not post_allowed
)