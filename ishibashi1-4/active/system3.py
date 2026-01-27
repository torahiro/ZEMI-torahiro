import MeCab
import json
import ollama
import os
import sys
import streamlit as st
import stats_db
stats_db.init_db()

username = "test_user"   # 今は仮（後でGoogleログイン）

try:
    import unidic_lite
except Exception:
    unidic_lite = None

# --- 1. 判定・変換ロジック ---

def analyze_level2(text, dictionary):
    """MeCabで辞書（JSON）と照らし合わせ、キーワードを抽出する"""
    tagger = None
    mecabrc_path = os.environ.get("MECABRC")

    try:
        if mecabrc_path and os.path.exists(mecabrc_path):
            tagger = MeCab.Tagger()
        elif unidic_lite is not None:
            tagger = MeCab.Tagger(f"-d {unidic_lite.DICDIR}")
        else:
            tagger = MeCab.Tagger()
        node = tagger.parseToNode(text)
    except Exception:
        # MeCab が初期化できない場合は、簡易トークナイズで続行
        tokens = list(text)
        found_targets = [w for w in dictionary.get("targets", []) if w in text]
        found_insults = [w for w in dictionary.get("insult_words", {}) if w in text]
        return found_targets, found_insults

    found_targets, found_insults = [], []
    while node:
        word = node.surface
        if word in dictionary["targets"]: found_targets.append(word)
        if word in dictionary["insult_words"]: found_insults.append(word)
        node = node.next
    return found_targets, found_insults

def check_toxicity_with_ai(text):
    """AIに、その文章が攻撃的・ネガティブかどうかを判定させる"""
    # このプロンプトにより、辞書にない嫌味なども検知可能になります
    prompt = (
        f"以下の文章が、他人を不快にさせる表現、攻撃的な意図、またはネガティブな感情を含んでいるか判定してください。"
        f"判定結果は、含んでいるなら 'YES'、含まない（クリーン）なら 'NO' とだけ回答してください。\n\n"
        f"文章: {text}"
    )
    try:
        response = ollama.chat(model='llama3.2:3b', messages=[{'role': 'user', 'content': prompt}])
        return "YES" in response['message']['content'].upper()
    except:
        return False # エラー時は安全のためFalse（または辞書判定に頼る）

def call_ai_cleaner(text, targets, insults, dictionary):
    target_info = f"（対象：{', '.join(targets)}）" if targets else "その方"
    
    system_instruction = (
        "あなたは世界一優しい、ポジティブ変換の専門家です。"
        "入力された攻撃的な言葉から『不快感』を一切排除し、"
        "100%温かい『純粋な応援メッセージ』のみを日本語1文で出力してください。"
    )
    
    user_prompt = (
        f"以下の文章は、{target_info}に対するネガティブな表現です。"
        "この文章にある『嫌悪感』や『攻撃性』を完全に消し去ってください。"
        "その代わりに、その人が『活躍している事実』や『存在』を、"
        "純粋に喜び、応援し、称賛する非常に自然な日本語に変換してください。\n"
        "※『残念』『違和感』などの否定的な言葉は一切使わないでください。\n\n"
        f"文章: {text}"
    )

    response = ollama.chat(model='llama3.2:3b', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': user_prompt},
    ])
    return response['message']['content']

# --- 2. CLI の定義 ---

def load_dictionary():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dic_path = os.path.join(base_dir, "dictionary.json")
    try:
        with open(dic_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"targets": [], "insult_words": {}}

def read_multiline_input():
    print("解析したい文章を入力してください（空行で確定）")
    print("例：今日もスタメンなの気持ち悪い")
    lines = []
    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            return None
        if line is None or line == "":
            break
        line = line.rstrip("\n")
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    return text if text else None

def run_cli():
    print("誹謗中傷を優しさに変える AI")
    print("特定のキーワードだけでなく、AIが文脈から悪意を検知して浄化します。")
    print("終了するには Ctrl+C を押してください。\n")

    dic = load_dictionary()

    while True:
        input_text = read_multiline_input()
        if input_text is None:
            print("\n入力が空のため終了します。")
            return

        print("\nAIが文脈を読み取っています...")

        targets, insults = analyze_level2(input_text, dic)

        is_aggressive_dict = len(insults) > 0
        is_aggressive_ai = check_toxicity_with_ai(input_text)

        if is_aggressive_dict or is_aggressive_ai:
            try:
                converted_text = call_ai_cleaner(input_text, targets, insults, dic)
                print("\n【AI浄化結果】\n")
                print(converted_text)
            except Exception as ex:
                print(f"\nエラーが発生しました: {ex}")
        else:
            print("\nこの文章はクリーンです。変換の必要はありません。")

        print("\n---\n")


def run():
    st.title("誹謗中傷を優しさに変える AI")
    st.caption("辞書 + AI で文脈を判定し、ポジティブに変換します。")

    dic = load_dictionary()

    if "last_event" not in st.session_state:
        st.session_state.last_event = None

    text = st.text_area("解析したい文章を入力してください", height=150)

    if st.button("判定・変換"):

        if not text.strip():
            st.warning("文章を入力してください。")
            return

        targets, insults = analyze_level2(text, dic)

        is_aggressive_dict = len(insults) > 0
        is_aggressive_ai = check_toxicity_with_ai(text)

        is_aggressive = is_aggressive_dict or is_aggressive_ai

        event_key = f"{username}_{hash(text)}"

        # ✅ 誹謗中傷だった場合のみ
        if is_aggressive:

            # DBは1投稿1回だけ
            if event_key != st.session_state.last_event:
                stats_db.add_count(username)
                st.session_state.last_event = event_key

            try:
                converted_text = call_ai_cleaner(text, targets, insults, dic)
                st.success("AIがポジティブに変換しました 🌱")
                st.write(converted_text)

            except Exception as ex:
                st.error(f"変換中にエラーが発生しました: {ex}")

        # ✅ クリーン文章は変換しない
        else:
            st.info("この文章はすでにクリーンです。変換の必要はありません ✨")

        # ✅ 表示は常にDBから
        st.metric("誹謗中傷試行回数", stats_db.get_count(username))

    if __name__ == "__main__":
        run_cli()