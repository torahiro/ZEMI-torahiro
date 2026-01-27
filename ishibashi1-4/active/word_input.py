import streamlit as st
import sqlite3

# --- データベース準備 ---
def init_db():
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    # NGワードを保存するテーブルを作成
    c.execute('''CREATE TABLE IF NOT EXISTS bad_words (word TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def get_bad_words():
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    c.execute("SELECT word FROM bad_words")
    words = [row[0] for row in c.fetchall()]
    conn.close()
    return words

def add_bad_word(word):
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bad_words (word) VALUES (?)", (word,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # 既にある場合は無視
    conn.close()

# 初期化
init_db()

# --- UI ---
st.title("🛡️ 誹謗中傷管理システム（DB版）")

# サイドバーでNGワードを管理（上書き・追加）
with st.sidebar:
    st.header("管理設定")
    new_word = st.text_input("新しいNGワードを追加")
    if st.button("登録"):
        if new_word:
            add_bad_word(new_word)
            st.success(f"「{new_word}」を登録しました")
    
    st.write("---")
    st.write("現在のNGワード一覧:")
    current_words = get_bad_words()
    st.write(current_words)

# メインの投稿機能
st.subheader("投稿フォーム")
text = st.text_area("投稿内容を入力してください")

# DBから最新のリストを取得して判定
bad_words_list = get_bad_words()
detected = [w for w in bad_words_list if w in text]

if text:
    if detected:
        st.error(f"⚠️ 投稿できません。検知ワード: {', '.join(detected)}")
        post_allowed = False
    else:
        st.success("✅ 問題ありません")
        post_allowed = True
else:
    post_allowed = False

if st.button("投稿する", disabled=not post_allowed):
    st.balloons()