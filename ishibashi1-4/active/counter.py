import streamlit as st
import stats_db

stats_db.init_db()

def register_hate_event(username, text, is_aggressive):
    if "last_event" not in st.session_state:
        st.session_state.last_event = None

    if not text.strip():
        return

    event_key = f"{username}_{hash(text)}"

    if is_aggressive and event_key != st.session_state.last_event:
        stats_db.add_count(username)
        st.session_state.last_event = event_key


def show_hate_count(username):
    st.metric(
        "誹謗中傷試行回数",
        stats_db.get_count(username)
    )