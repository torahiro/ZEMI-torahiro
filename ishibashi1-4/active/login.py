import streamlit as st
import streamlit_authenticator as stauth
import bcrypt
from streamlit_authenticator.utilities.exceptions import LoginError
import app
import stats_db

stats_db.init_db()

# --- 設定部分 ---
GOOGLE_CLIENT_ID = "あなたのGoogleクライアントIDをここに貼り付け"
GOOGLE_CLIENT_SECRET = "あなたのGoogleクライアントシークレットをここに貼り付け"
REDIRECT_URI = "http://localhost:8501"

# 1. Credentials（認証情報）の初期化と保持
# session_state に保存することで、画面リロード後も登録情報を維持します
if 'credentials' not in st.session_state:
    users = stats_db.get_all_users()
    if not users:
        # 初回実行時のみ初期設定を行う
        password = "password123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users = {
            "user1": {
                "name": "User One",
                "password": hashed_password,
                "email": "user1@example.com",
            }
        }
        stats_db.save_user("user1", users["user1"])

    st.session_state.credentials = {
        "usernames": users,
        "oauth": {
            "google": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI
            }
        }
    }

# 2. Authenticatorの初期化
# session_state 内の credentials を使用します
authenticator = stauth.Authenticate(
    st.session_state.credentials,
    "cookie_name",
    "signature_key",
    cookie_expiry_days=1
)

st.title("ログイン / 新規登録")

login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

with login_tab:
    try:
        authenticator.login(location='main')
    except LoginError:
        authenticator.cookie_controller.delete_cookie()
        st.session_state["authentication_status"] = None
        st.session_state["username"] = None
        st.warning("セッション情報をリセットしました。もう一度ログインしてください。")
    except Exception as e:
        st.error(f"ログインウィジェットエラー: {e}")

    if st.session_state.get("authentication_status"):
        authenticator.logout(location='main')
        name = st.session_state.get("name")
        st.success(f"ログイン成功！ようこそ {name} さん")
        st.write("---")
        st.write("誹謗中傷対策ツールのアクティブなコンテンツがここに表示されます。")
    elif st.session_state.get("authentication_status") is False:
        st.error("ユーザー名またはパスワードが違います")
    else:
        st.info("ログインしてください")

with register_tab:
    st.subheader("新規登録")
    try:
        try:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(location='main')
        except TypeError:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user()

        if email_of_registered_user:
            new_user = authenticator.credentials["usernames"].get(username_of_registered_user, {})
            if new_user:
                stats_db.save_user(username_of_registered_user, new_user)
            st.success('登録が完了しました。ログインタブからログインしてください。')
    except Exception as e:
        st.error(f"登録エラー: {e}")
# --- ここまで認証部分 ---

# 認証成功時にのみ app.py を実行
if st.session_state.get("authentication_status"):
    app.run()
else:
    st.info("ログインまたは新規登録を行ってください。")