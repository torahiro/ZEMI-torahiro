import streamlit as st
import sqlite3

# --- データベース準備 ---
def init_db():
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    # 1. NGワード保存用
    c.execute('''CREATE TABLE IF NOT EXISTS bad_words (word TEXT PRIMARY KEY)''')
    # 2. ユーザー統計用（ここを追加！）
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (username TEXT PRIMARY KEY, count INTEGER)''')
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
        pass
    conn.close()

# --- 統計用の新機能 ---
def increment_count(username):
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    # ユーザーがいなければ作成、いればカウントを+1
    c.execute('''INSERT INTO user_stats (username, count) VALUES (?, 1)
                 ON CONFLICT(username) DO UPDATE SET count = count + 1''', (username,))
    conn.commit()
    conn.close()

def get_count(username):
    conn = sqlite3.connect('ng_words.db')
    c = conn.cursor()
    c.execute("SELECT count FROM user_stats WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# 初期化
init_db()
username = "test_user" # 仮のユーザー名

# --- UI ---
st.title("🛡️ 誹謗中傷管理システム（DB版）")

# サイドバーで管理
with st.sidebar:
    st.header("管理設定")
    new_word = st.text_input("新しいNGワードを追加")
    if st.button("登録"):
        if new_word:
            add_bad_word(new_word)
            st.success(f"「{new_word}」を登録しました")
    
    st.write("---")
    st.write("現在のNGワード一覧:")
    st.write(get_bad_words())

# メインの投稿機能
st.subheader("投稿フォーム")
text = st.text_area("投稿内容を入力してください")

# 重複カウント防止用のフラグ管理
if "detected_flag" not in st.session_state:
    st.session_state.detected_flag = False

if text:
    bad_words_list = get_bad_words()
    detected = [w for w in bad_words_list if w in text]

    if detected:
        st.error(f"⚠️ 投稿できません。検知ワード: {', '.join(detected)}")
        
        # 初めて検知した場合のみカウントを増やす
        if not st.session_state.detected_flag:
            increment_count(username)
            st.session_state.detected_flag = True
            st.warning("不適切な表現が検知されたため、カウントが加算されました。")
            
        post_allowed = False
    else:
        st.success("✅ 問題ありません")
        st.session_state.detected_flag = False # クリーンになったらリセット
        post_allowed = True
else:
    post_allowed = False

# 投稿ボタン
if st.button("投稿する", disabled=not post_allowed):
    st.balloons()
    st.success("無事に投稿されました！")

# 最後に統計を表示
st.divider()
count = get_count(username)
st.metric("🚨 あなたの誹謗中傷検知回数", f"{count} 回")