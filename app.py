# -*- coding: utf-8 -*-
"""
問題と苦しみの理解度テスト - Web版（Streamlit）
URLを知っている人がブラウザでアクセスして利用できます。
"""
import os
import random
import urllib.parse

import pandas as pd
import streamlit as st

CONTACT_EMAIL = "ai.fusion.service@gmail.com"
NUM_QUESTIONS = 10
COL_DEKIGOTO = 1
COL_MONDAI = 2
COL_KURUSHIMI = 3
COL_KAITO = 4


def load_data(excel_path):
    """Excelを読み込み、行リストを返す。"""
    df = pd.read_excel(excel_path)
    rows = []
    for i in range(len(df)):
        dekigoto = str(df.iloc[i, COL_DEKIGOTO]).strip() if pd.notna(df.iloc[i, COL_DEKIGOTO]) else ""
        mondai = str(df.iloc[i, COL_MONDAI]).strip() if pd.notna(df.iloc[i, COL_MONDAI]) else ""
        kurushimi = str(df.iloc[i, COL_KURUSHIMI]).strip() if pd.notna(df.iloc[i, COL_KURUSHIMI]) else ""
        kaito = str(df.iloc[i, COL_KAITO]).strip() if len(df.columns) > COL_KAITO and pd.notna(df.iloc[i, COL_KAITO]) else ""
        if dekigoto and (mondai or kurushimi):
            rows.append({"出来事": dekigoto, "問題": mondai, "苦しみ": kurushimi, "回答": kaito})
    return rows


def run_quiz(data, level_difficult, num=NUM_QUESTIONS):
    """ランダムに num 問選び、リストで返す。"""
    if len(data) < num:
        num = len(data)
    chosen = random.sample(data, num)
    result = []
    for row in chosen:
        show_mondai = random.choice([True, False])
        if show_mondai and row["問題"]:
            example_text, correct_label = row["問題"], "問題"
        elif row["苦しみ"]:
            example_text, correct_label = row["苦しみ"], "苦しみ"
        else:
            example_text, correct_label = row["問題"], "問題"
        result.append({
            "出来事": row["出来事"],
            "例文": example_text,
            "正解": correct_label,
            "解説": row.get("回答", ""),
            "level_difficult": level_difficult,
        })
    return result


# ページ設定
st.set_page_config(page_title="問題と苦しみの理解度テスト", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    .stButton > button { font-size: 1.1rem; padding: 0.5rem 1.5rem; min-width: 6em; }
    div[data-testid="stSidebar"] .stButton > button { width: 100%; }
    .quiz-section { margin: 0.5em 0 0.2em 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_done" not in st.session_state:
    st.session_state.quiz_done = False
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "wrong_answers" not in st.session_state:
    st.session_state.wrong_answers = []
if "level_difficult" not in st.session_state:
    st.session_state.level_difficult = False
if "answered_current" not in st.session_state:
    st.session_state.answered_current = False
if "last_correct" not in st.session_state:
    st.session_state.last_correct = None
if "last_wrong_detail" not in st.session_state:
    st.session_state.last_wrong_detail = None

# ナビゲーション
tab_quiz, tab_contact = st.tabs(["📝 テスト", "✉️ お問い合わせ"])

with tab_quiz:
    # データ読み込み（同フォルダの Excel またはアップロード）
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "問題と苦しみ.xlsx")
    data = []
    if os.path.isfile(excel_path):
        try:
            data = load_data(excel_path)
        except Exception as e:
            st.error(f"Excelの読み込みに失敗しました: {e}")
    if not data:
        uploaded = st.file_uploader("問題データ（Excel）をアップロードしてください", type=["xlsx"])
        if uploaded:
            try:
                data = load_data(uploaded)
                st.success(f"{len(data)} 件読み込みました。")
            except Exception as e:
                st.error(f"読み込みエラー: {e}")

    if data:
        if not st.session_state.quiz_started:
            st.title("問題と苦しみの理解度テスト")
            level = st.radio("レベル", ["かんたん（結果のみ表示）", "むずかしい（不正解時に正解・解説を表示）"], horizontal=True)
            st.session_state.level_difficult = "むずかしい" in level
            if st.button("テスト開始（10問）"):
                st.session_state.questions = run_quiz(data, st.session_state.level_difficult)
                st.session_state.quiz_started = True
                st.session_state.quiz_done = False
                st.session_state.current_index = 0
                st.session_state.correct_count = 0
                st.session_state.wrong_answers = []
                st.session_state.answered_current = False
                st.session_state.last_correct = None
                st.session_state.last_wrong_detail = None
                st.rerun()

        elif not st.session_state.quiz_done:
            q = st.session_state.questions[st.session_state.current_index]
            # 直前の回答結果を表示（あれば）
            if st.session_state.answered_current and st.session_state.last_correct is not None:
                if st.session_state.last_correct:
                    st.success("正解です。")
                else:
                    st.warning("不正解です。")
                    if st.session_state.level_difficult and st.session_state.last_wrong_detail:
                        d = st.session_state.last_wrong_detail
                        st.caption(f"正解: 「{d['正解']}」")
                        if d.get("解説"):
                            st.caption("解説: " + d["解説"])
                if st.button("次の問題へ"):
                    st.session_state.answered_current = False
                    st.session_state.current_index += 1
                    if st.session_state.current_index >= len(st.session_state.questions):
                        st.session_state.quiz_done = True
                    st.rerun()
                st.markdown("---")
            else:
                idx = st.session_state.current_index
                st.markdown("### 次の例文は「問題」と「苦しみ」のどちらに当たりますか？")
                st.markdown("**【出来事】**")
                st.write(q["出来事"])
                st.markdown("**【どのように感じたか】**")
                st.info(q["例文"])
                col1, col2, _ = st.columns([1, 1, 2])
                with col1:
                    if st.button("　問題　", key=f"mondai_{idx}", use_container_width=True):
                        is_correct = "問題" == q["正解"]
                        if is_correct:
                            st.session_state.correct_count += 1
                        else:
                            st.session_state.wrong_answers.append({
                                "出来事": q["出来事"], "例文": q["例文"], "正解": q["正解"],
                                "解説": q["解説"], "ユーザーの回答": "問題",
                            })
                        st.session_state.answered_current = True
                        st.session_state.last_correct = is_correct
                        st.session_state.last_wrong_detail = q if not is_correct else None
                        st.rerun()
                with col2:
                    if st.button("　苦しみ　", key=f"kurushimi_{idx}", use_container_width=True):
                        is_correct = "苦しみ" == q["正解"]
                        if is_correct:
                            st.session_state.correct_count += 1
                        else:
                            st.session_state.wrong_answers.append({
                                "出来事": q["出来事"], "例文": q["例文"], "正解": q["正解"],
                                "解説": q["解説"], "ユーザーの回答": "苦しみ",
                            })
                        st.session_state.answered_current = True
                        st.session_state.last_correct = is_correct
                        st.session_state.last_wrong_detail = q if not is_correct else None
                        st.rerun()

        else:
            total = len(st.session_state.questions)
            score = st.session_state.correct_count
            pct = (100 * score // total) if total else 0
            st.balloons()
            st.success(f"### テストが終了しました")
            st.markdown(f"**結果: {score} / {total} 問正解　得点: {pct} 点**")
            if st.session_state.wrong_answers:
                st.markdown("---")
                st.markdown("**【間違えた問題の正解・解説】**")
                for i, w in enumerate(st.session_state.wrong_answers, 1):
                    with st.expander(f"問{i}"):
                        st.write("出来事:", w["出来事"])
                        st.write("どのように感じたか:", w["例文"])
                        st.write("あなたの回答:", w["ユーザーの回答"], "→ 正解:", w["正解"])
                        if w.get("解説"):
                            st.caption("解説: " + w["解説"])
            if st.button("もう一度テストを始める"):
                st.session_state.quiz_started = False
                st.session_state.quiz_done = False
                st.session_state.questions = []
                st.session_state.current_index = 0
                st.session_state.correct_count = 0
                st.session_state.wrong_answers = []
                st.session_state.answered_current = False
                st.session_state.last_correct = None
                st.session_state.last_wrong_detail = None
                st.rerun()

with tab_contact:
    st.markdown("### お仕事のご依頼やご質問はこちらからご連絡ください。")
    with st.form("contact_form"):
        name = st.text_input("お名前 *")
        company = st.text_input("会社名・団体名")
        email = st.text_input("メールアドレス *")
        postal = st.text_input("郵便番号")
        address = st.text_input("住所")
        message = st.text_area("ご依頼内容 *", height=150)
        submitted = st.form_submit_button("送信する")
        if submitted:
            if not name.strip():
                st.warning("お名前を入力してください。")
            elif not email.strip():
                st.warning("メールアドレスを入力してください。")
            elif not message.strip():
                st.warning("ご依頼内容を入力してください。")
            else:
                body = f"お名前: {name}\n会社名・団体名: {company}\nメールアドレス: {email}\n郵便番号: {postal}\n住所: {address}\n\nご依頼内容:\n{message}"
                subject = "お仕事のご依頼"
                url = f"mailto:{CONTACT_EMAIL}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                st.markdown(f"[メールソフトで送信する（クリックで開く）]({url})")
                st.info("メールソフトが起動します。内容を確認のうえ送信してください。")
