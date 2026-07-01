import streamlit as st
import streamlit.components.v1 as components
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
# テキスト入力欄に対応する内部状態
if "answer_input" not in st.session_state:
    st.session_state.answer_input = ""

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1m5xs669Gkt2BTTeF9p47hfl_RqLkF5Hv7bOgO8NU5I4/edit"
)


def generate_question():
    if random.choice(["mul", "div"]) == "mul":
        # 掛け算：2桁 × 1桁
        a = random.randint(10, 99)  # 2桁
        b = random.randint(2, 9)    # 1桁（1は簡単すぎるため除外）
        return f"{a} × {b}", a * b
    else:
        # 割り算：2桁 ÷ 1桁（必ず割り切れる）
        # 割られる数は2桁（10〜99）、答えは1桁（1〜9）
        divisor = random.randint(2, 9)  # 割る数：1桁（1は簡単すぎるため除外）

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
    st.session_state.answer_input = ""
    st.session_state.feedback = ""
    st.session_state.ranking_saved = False
    q, a = generate_question()
    st.session_state.question = q
    st.session_state.answer = a


def next_question():
    st.session_state.question_index += 1
    st.session_state.answer_input = ""
    st.session_state.feedback = ""
    if st.session_state.question_index < 10:
        q, a = generate_question()
        st.session_state.question = q
        st.session_state.answer = a


def check_answer():
    raw = st.session_state.get("answer_input", "").strip()
    if raw == "":
        return

    try:
        user = int(raw)
    except ValueError:
        st.session_state.feedback = "数字を入力してください"
        st.session_state.answer_input = ""
        return

    if user == st.session_state.answer:
        st.session_state.correct_count += 1
        st.session_state.feedback = "Correct!"
        st.session_state.answer_input = ""
        next_question()
    else:
        st.session_state.feedback = "Try again"
        st.session_state.answer_input = ""


if not st.session_state.started:
    st.button("START", on_click=start_game, use_container_width=True)
else:
    if st.session_state.question_index < 10:
        st.subheader(f"Question {st.session_state.question_index + 1}/10")
        st.markdown(f"## {st.session_state.question}")

        # 入力欄（PCでキーボード派はここに直接入力してEnterでもOK）
        st.text_input(
            "Answer",
            key="answer_input",
            on_change=check_answer,
        )

        # 電卓風キーパッド（iPad/スマホ用）
        # タップはブラウザ内だけで処理し、OKを押した時だけ実際の入力欄に
        # Enterキー入力として送信する（サーバーとの往復は1回だけなのでラグが出ない）。
        components.html(
            """
            <style>
                .nj-keypad {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                    max-width: 300px;
                    margin: 12px auto 0 auto;
                }
                .nj-key {
                    font-size: 28px;
                    font-weight: bold;
                    padding: 18px 0;
                    border: none;
                    border-radius: 14px;
                    color: white;
                    background: #4A90D9;
                    touch-action: manipulation;
                    user-select: none;
                    -webkit-tap-highlight-color: transparent;
                }
                .nj-key:active {
                    transform: scale(0.95);
                    opacity: 0.85;
                }
                .nj-key.clear { background: #E05353; }
                .nj-key.ok { background: #3CB371; }
            </style>
            <div class="nj-keypad">
                <button class="nj-key" data-digit="1">1</button>
                <button class="nj-key" data-digit="2">2</button>
                <button class="nj-key" data-digit="3">3</button>
                <button class="nj-key" data-digit="4">4</button>
                <button class="nj-key" data-digit="5">5</button>
                <button class="nj-key" data-digit="6">6</button>
                <button class="nj-key" data-digit="7">7</button>
                <button class="nj-key" data-digit="8">8</button>
                <button class="nj-key" data-digit="9">9</button>
                <button class="nj-key clear" id="nj-clear">C</button>
                <button class="nj-key" data-digit="0">0</button>
                <button class="nj-key ok" id="nj-ok">OK</button>
            </div>
            <script>
            (function() {
                var doc = window.parent.document;

                function getInput() {
                    return doc.querySelector('input[aria-label="Answer"]');
                }

                function setNativeValue(el, value) {
                    var setter = Object.getOwnPropertyDescriptor(
                        window.parent.HTMLInputElement.prototype, 'value'
                    ).set;
                    setter.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }

                function appendDigit(digit) {
                    var input = getInput();
                    if (!input) return;
                    setNativeValue(input, (input.value || '') + digit);
                }

                function clearValue() {
                    var input = getInput();
                    if (!input) return;
                    setNativeValue(input, '');
                }

                function submit() {
                    var input = getInput();
                    if (!input) return;
                    input.focus();
                    ['keydown', 'keypress', 'keyup'].forEach(function(type) {
                        input.dispatchEvent(new KeyboardEvent(type, {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                        }));
                    });
                    // フォーカスを残すとiPadでキーボードが再表示されたままになるため、
                    // 送信直後（再描画が始まる前）にフォーカスを外す。
                    setTimeout(function() {
                        input.blur();
                    }, 30);
                }

                document.querySelectorAll('.nj-key[data-digit]').forEach(function(btn) {
                    btn.addEventListener('click', function() {
                        appendDigit(btn.getAttribute('data-digit'));
                    });
                });
                document.getElementById('nj-clear').addEventListener('click', clearValue);
                document.getElementById('nj-ok').addEventListener('click', submit);

                // 物理キーボード利用時の保険：数字専用キーパッド＋自動スクロール
                var input = getInput();
                if (input) {
                    input.setAttribute('inputmode', 'numeric');
                    input.setAttribute('pattern', '[0-9]*');
                    input.setAttribute('autocomplete', 'off');
                    input.addEventListener('focus', function() {
                        setTimeout(function() {
                            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }, 300);
                    });
                }
            })();
            </script>
            """,
            height=340,
        )

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
