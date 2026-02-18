import streamlit as st
import random
import time

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


def generate_question():
    if random.choice(["mul", "div"]) == "mul":
        a = random.randint(1, 99)
        b = random.randint(1, 99)
        return f"{a} × {b}", a * b
    else:
        b = random.randint(1, 99)
        ans = random.randint(1, 99)
        a = b * ans
        return f"{a} ÷ {b}", ans


def start_game():
    st.session_state.started = True
    st.session_state.correct_count = 0
    st.session_state.question_index = 0
    st.session_state.start_time = time.time()
    st.session_state.input = ""
    st.session_state.feedback = ""
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
        # time.sleep はUIが固まるので基本不要（残したいなら短めに）
        # time.sleep(0.3)
        next_question()
    else:
        st.session_state.feedback = "Try again"
        st.session_state.input = ""


if not st.session_state.started:
    st.button("START", on_click=start_game)
else:
    if st.session_state.question_index < 10:
        st.subheader(f"Question {st.session_state.question_index + 1}/10")
        st.markdown(f"## {st.session_state.question}")

        st.text_input("Answer", key="input")

        # ここが重要：ボタンの on_click で処理する
        st.button("OK", on_click=check_answer)

        if st.session_state.feedback:
            st.write(st.session_state.feedback)

    else:
        elapsed = int(time.time() - st.session_state.start_time)
        st.success(
            f"Finished! Score: {st.session_state.correct_count}/10 | Time: {elapsed}s"
        )
        if st.button("Play Again", on_click=start_game):
            pass
