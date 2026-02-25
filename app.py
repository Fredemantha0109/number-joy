import streamlit as st
import random
import time
import json
import gspread

st.set_page_config(page_title="Number Joy", layout="centered")
st.title("Number Joy")

# 状態の初期化
if "started" not in st.session_state:
    st.session_state.started = False
if "question" not in st.session_state:
    st.session_state.question = ""
if "answer" not in st.session_state:
    st.session_state.answer = 0
if "input" not in st.session_state:
    st.session_state.input = ""
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "ranking_saved" not in st.session_state:
    st.session_state.ranking_saved = False

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1m5xs669Gkt2BTTeF9p47hfl_RqLkF5Hv7bOgO8NU5I4/edit"
)


def generate_question():
    if random.choice(["mul", "div"]) == "mul":
        # 掛け算：2桁 × 1桁
        a = random.randint(10, 99)  # 2桁
        b = random.randint(1, 9)    # 1桁
        return f"{a} × {b}", a * b
    else:
        # 割り算：2桁 ÷ 1桁（必ず割り切れる）
        # 割られる数は2桁（10〜99）、答えは1桁（1〜9）
        divisor = random.randint(1, 9)  # 割る数：1桁

        # 答えの範囲を計算（割られる数が10〜99、答えが1〜9になるように）
        min_quotient = (10 + divisor - 1) // divisor  # 切り上げ：10以上
        max_quotient = min(9, 99 // divisor)          # 切り捨て：99以下、かつ9以下

        if min_quotient <= max_quotient:
            quotient = random.randint(min_quotient, max_quotient)
        else:
            # 理論的には発生しないが、念のため
            quotient = 9

        dividend = divisor * quotient  # 割られる数：必ず10〜99

        return f"{dividend} ÷ {divisor}", quotient


def get_sheet():
    """Googleスプレッドシートの1枚目を取得（失敗時はNoneを返す）"""
    try:
        creds_json = st.secrets["google_credentials"]
    except Exception:
        # ローカルなどでsecretsが無い場合は静かにスキップ
        st.info("Google連携設定が見つからないため、ランキング保存はスキップします。")
        return None

    try:
        creds_dict = json.loads(creds_json)
        client = gspread.service_account_from_dict(creds_dict)
        sh = client.open_by_url(SPREADSHEET_URL)
        return sh.get_worksheet(0)
    except Exception:
        st.info("Googleスプレッドシートに接続できなかったため、ランキング保存はスキップします。")
        return None


def update_ranking(score: int, elapsed_seconds: int):
    """スプレッドシートに結果を追記し、ランキング上位5件を表示する"""
    sheet = get_sheet()
    if sheet is None:
        return

    # 既存データ取得
    values = sheet.get_all_values()

    # ヘッダー行がなければ追加
    if not values:
        sheet.append_row(["Name", "Score", "Time", "Date"])
        values = sheet.get_all_values()

    # 今回の結果を一度だけ追記
    if not st.session_state.ranking_saved:
        date_str = time.strftime("%Y-%m-%d")
        sheet.append_row(["Player", score, elapsed_seconds, date_str])
        st.session_state.ranking_saved = True

    # 全データを取得してランキングを計算
    records = sheet.get_all_records()
    if not records:
        return

    try:
        sorted_records = sorted(
            records,
            key=lambda r: (-int(r.get("Score", 0)), int(r.get("Time", 0))),
        )
    except Exception:
        return

    top5 = sorted_records[:5]

    st.subheader("Ranking (Top 5)")
    for i, r in enumerate(top5, start=1):
        st.write(
            f"{i}. {r.get('Name', '')} - "
            f"Score: {r.get('Score', '')}/10, "
            f"Time: {r.get('Time', '')}s "
            f"({r.get('Date', '')})"
        )


def start_game():
    st.session_state.started = True
    st.session_state.correct_count = 0
    st.session_state.question_index = 0
    st.session_state.start_time = time.time()
    st.session_state.input = ""
    st.session_state.feedback = ""
    st.session_state.ranking_saved = False
    q, a = generate_question()
    st.session_state.question = q
    st.session_state.answer = a


def next_question():
    st.session_state.question_index += 1
    st.session_state.input = ""
    st.session_state.feedback = ""
    if st.session_state.question_index < 10:
        q, a = generate_question()
        st.session_state.question = q
        st.session_state.answer = a


def check_answer():
    raw = st.session_state.input.strip()
    if raw == "":
        return

    try:
        user = int(raw)
    except ValueError:
        st.session_state.feedback = "数字を入力してください"
        st.session_state.input = ""
        return

    if user == st.session_state.answer:
        st.session_state.correct_count += 1
        st.session_state.feedback = "Correct!"
        next_question()
    else:
        st.session_state.feedback = "Try again"
        st.session_state.input = ""


def keypad_append(digit: str):
    """テンキーで数字を追加"""
    st.session_state.input = (st.session_state.input or "") + digit


def keypad_clear():
    """テンキー入力をクリア"""
    st.session_state.input = ""


def keypad_ok():
    """テンキーのOKで送信"""
    check_answer()


if not st.session_state.started:
    st.button("START", on_click=start_game, use_container_width=True)
else:
    if st.session_state.question_index < 10:
        st.subheader(f"Question {st.session_state.question_index + 1}/10")
        st.markdown(f"## {st.session_state.question}")

        # テキスト入力：Enterキーで送信
        st.text_input(
            "Answer",
            key="input",
            on_change=check_answer,
        )

        # テンキーUI（タブレット・スマホ向け）
        st.markdown("### Keypad")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("1", use_container_width=True):
                keypad_append("1")
            if st.button("4", use_container_width=True):
                keypad_append("4")
            if st.button("7", use_container_width=True):
                keypad_append("7")
            if st.button("C", use_container_width=True):
                keypad_clear()

        with col2:
            if st.button("2", use_container_width=True):
                keypad_append("2")
            if st.button("5", use_container_width=True):
                keypad_append("5")
            if st.button("8", use_container_width=True):
                keypad_append("8")
            if st.button("0", use_container_width=True):
                keypad_append("0")

        with col3:
            if st.button("3", use_container_width=True):
                keypad_append("3")
            if st.button("6", use_container_width=True):
                keypad_append("6")
            if st.button("9", use_container_width=True):
                keypad_append("9")
            if st.button("OK", use_container_width=True):
                keypad_ok()

        if st.session_state.feedback:
            st.write(st.session_state.feedback)

    else:
        elapsed = int(time.time() - st.session_state.start_time)

        # ランキング更新（追記と上位5件表示）
        update_ranking(st.session_state.correct_count, elapsed)

        st.success(
            f"Finished! Score: {st.session_state.correct_count}/10 | Time: {elapsed}s"
        )
        if st.button("Play Again", on_click=start_game, use_container_width=True):
            pass
