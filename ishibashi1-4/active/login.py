import streamlit as st
import streamlit_authenticator as stauth
import bcrypt

# --- 設定部分 ---
GOOGLE_CLIENT_ID = "あなたのGoogleクライアントIDをここに貼り付け"
GOOGLE_CLIENT_SECRET = "あなたのGoogleクライアントシークレットをここに貼り付け"
REDIRECT_URI = "http://localhost:8501"

# 1. Credentials（認証情報）の初期化と保持
# session_state に保存することで、画面リロード後も登録情報を維持します
if 'credentials' not in st.session_state:
    # 初回実行時のみ初期設定を行う
    password = "password123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    st.session_state.credentials = {
        "usernames": {
            "user1": {
                "name": "User One",
                "password": hashed_password,
                "email": "user1@example.com"
            }
        },
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

# 3. ログインウィジェットの表示
try:
    authenticator.login(location='main')
except Exception as e:
    st.error(f"ログインウィジェットエラー: {e}")

# 4. セッションステートから認証情報を取得して判定
if st.session_state.get("authentication_status"):
    # --- ログイン成功時 ---
    authenticator.logout(location='main')
    
    name = st.session_state.get("name")
    st.success(f"ログイン成功！ようこそ {name} さん")
    st.write("---")
    st.write("誹謗中傷対策ツールのアクティブなコンテンツがここに表示されます。")
    
elif st.session_state.get("authentication_status") is False:
    # --- ログイン失敗時 ---
    st.error("ユーザー名またはパスワードが違います")
    
elif st.session_state.get("authentication_status") is None:
    # --- 未ログイン時 ---
    st.warning("ログインしてください")

    # === 新規登録画面の追加 ===
    st.write("---")
    st.subheader("新規登録")
    try:
        try:
            # 多くのバージョンで動作する呼び出し方
            email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(location='main')
        except TypeError:
             # 引数なしの場合（古いバージョンの対応）
             email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user()

        if email_of_registered_user:
            st.success('登録が完了しました。上のフォームからログインしてください。')
            # 重要: register_user は st.session_state.credentials を更新してくれます。
            # ブラウザを閉じた後も維持したい場合は、ここで YAML ファイルなどへの保存処理が必要です。
    except Exception as e:
        st.error(f"登録エラー: {e}")