# -*- coding: utf-8 -*-
"""
問題と苦しみの理解度テスト - Web版（Streamlit）
URLを知っている人がブラウザでアクセスして利用できます。
"""
import html
import os
import random

import pandas as pd
import streamlit as st

NUM_QUESTIONS = 10
# Excel列（0始まり）: 0=番号など, 1=出来事, 2=問題, 3=苦しみ, 4=回答
COL_DEKIGOTO = 1
COL_MONDAI = 2
COL_KURUSHIMI = 3
COL_KAITO = 4


def _find_col(df, names):
    """列名で列インデックスを返す。完全一致のあと、列名の先頭一致・含むで判定。"""
    for name in names:
        if name in df.columns:
            return df.columns.get_loc(name)
        for col in df.columns:
            c = str(col).strip()
            if c.startswith(name) or name in c:
                return df.columns.get_loc(col)
    return None


# タイトル・ボタン表示（「苦しみ」であって「意思」「考え方」「わたし」ではない）
APP_TITLE = "問題と苦しみの理解度テスト"
LABEL_MONDAI = "問題"
LABEL_KURUSHIMI = "苦しみ"
RIGHT_BUTTON_LABEL = "苦しみ"  # 右ボタンは必ず「苦しみ」
QUESTION_SENTENCE = "次の例文は「問題」と「苦しみ」のどちらに当たりますか？"
EXCEL_DISPLAY_NAME = "問題と苦しみ.xlsx"
FOOTER_CREDIT = "Produced by AI Fusion Service"  # 英語で表記
LEVEL_LABEL = "難易度を選んでください"
LEVEL_EASY = "簡単（結果のみ表示）"
LEVEL_HARD = "高難度（不正解時に正解・解説を表示）"

# Excelの表記ミスを表示時に置き換える（正しい文言はExcel側の修正が望ましい）
TEXT_CORRECTIONS = {
    "親切心に踏み出されました": "親切心が踏みにじられた",
}


def _apply_corrections(text):
    """TEXT_CORRECTIONS に含まれる文言を置き換える。"""
    if not text or not isinstance(text, str):
        return text
    t = text.strip()
    return TEXT_CORRECTIONS.get(t, text)


def load_data(excel_path):
    """Excelを読み込み、行リストを返す。1行目がヘッダーの場合は列名で判定。"""
    df = pd.read_excel(excel_path)
    idx_dekigoto = _find_col(df, ["出来事", "イベント"])
    idx_mondai = _find_col(df, ["問題"])
    idx_kurushimi = _find_col(df, ["苦しみ"])
    idx_kaito = _find_col(df, ["回答", "解説"])
    if idx_dekigoto is None:
        idx_dekigoto = COL_DEKIGOTO
    if idx_mondai is None:
        idx_mondai = COL_MONDAI
    if idx_kurushimi is None:
        idx_kurushimi = COL_KURUSHIMI
    if idx_kaito is None and len(df.columns) > COL_KAITO:
        idx_kaito = COL_KAITO
    rows = []
    for i in range(len(df)):
        dekigoto = str(df.iloc[i, idx_dekigoto]).strip() if pd.notna(df.iloc[i, idx_dekigoto]) else ""
        mondai = str(df.iloc[i, idx_mondai]).strip() if pd.notna(df.iloc[i, idx_mondai]) else ""
        kurushimi = str(df.iloc[i, idx_kurushimi]).strip() if pd.notna(df.iloc[i, idx_kurushimi]) else ""
        kaito = ""
        if idx_kaito is not None and len(df.columns) > idx_kaito and pd.notna(df.iloc[i, idx_kaito]):
            kaito = str(df.iloc[i, idx_kaito]).strip()
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
            example_text, correct_label = row["問題"], LABEL_MONDAI
        elif row["苦しみ"]:
            example_text, correct_label = row["苦しみ"], LABEL_KURUSHIMI
        else:
            example_text, correct_label = row["問題"], LABEL_MONDAI
        result.append({
            "出来事": _apply_corrections(row["出来事"]),
            "例文": _apply_corrections(example_text),
            "正解": correct_label,
            "解説": row.get("回答", ""),
            "level_difficult": level_difficult,
        })
    return result


# ページ設定
st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    .stButton > button { font-size: 1.1rem; padding: 0.5rem 1.5rem; min-width: 6em; background: #2196F3 !important; color: white !important; border: none !important; }
    .stButton > button:hover { background: #1976D2 !important; color: white !important; }
    div[data-testid="stSidebar"] .stButton > button { width: 100%; }
    .quiz-section { margin: 0.5em 0 0.2em 0; font-weight: bold; }
    .footer-credit { position: fixed; bottom: 8px; right: 12px; font-size: 0.75rem; color: #888; }
    .app-title-same { font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; }
    .quiz-content-min-height { min-height: 0; }
    p.caption { font-size: 0.88rem; color: #808495; margin-top: -0.5rem; }
    .load-success { padding: 0.75rem 1rem; border-radius: 0.25rem; background: #d4edda; color: #155724; margin: 0.5rem 0; }
    .quiz-info-box { padding: 1rem; border-radius: 0.25rem; background: #e8f4fd; border-left: 4px solid #1e88e5; margin: 0.5rem 0; }
</style>
<script>
(function(){
  function setNoTranslate() {
    document.querySelectorAll('.stButton button').forEach(function(btn) {
      btn.setAttribute('translate', 'no');
      btn.setAttribute('lang', 'en');
    });
  }
  setNoTranslate();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setNoTranslate);
  setTimeout(setNoTranslate, 300);
  setTimeout(setNoTranslate, 1000);
  setInterval(setNoTranslate, 2000);
})();
</script>
""", unsafe_allow_html=True)
st.markdown(f'<p class="footer-credit" lang="en" translate="no">{FOOTER_CREDIT}</p>', unsafe_allow_html=True)

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

# 正しいバージョン確認用（ボタンは「問題」と「苦しみ」です）
st.markdown('<p class="caption" lang="ja" translate="no">このテストでは、選択肢は「問題」と「苦しみ」の2つです。</p>', unsafe_allow_html=True)
# データ読み込み（同フォルダの Excel またはアップロード）
excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "問題と苦しみ.xlsx")
data = []
if os.path.isfile(excel_path):
    try:
        data = load_data(excel_path)
        actual_name = os.path.basename(excel_path)
        st.markdown(f'<div class="load-success" translate="no">{html.escape(actual_name)} から {len(data)} 件読み込みました。</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Excelの読み込みに失敗しました: {e}")
if not data:
    uploaded = st.file_uploader("問題データ（Excel）をアップロードしてください", type=["xlsx"])
    if uploaded:
        try:
            data = load_data(uploaded)
            actual_name = uploaded.name
            st.markdown(f'<div class="load-success" translate="no">{html.escape(actual_name)} として {len(data)} 件読み込みました。</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

if data:
    if not st.session_state.quiz_started:
        st.markdown(f'<p class="app-title-same" lang="ja" translate="no">{APP_TITLE}</p>', unsafe_allow_html=True)
        st.markdown(f'<p lang="ja" translate="no"><strong>難易度を選んでください</strong></p>', unsafe_allow_html=True)
        level = st.radio(" ", [LEVEL_EASY, LEVEL_HARD], horizontal=True)  # ラベルは上で「難易度を選んでください」を表示済み
        st.session_state.level_difficult = LEVEL_HARD in level
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
        st.markdown('<div class="quiz-content-min-height">', unsafe_allow_html=True)
        if st.session_state.answered_current and st.session_state.last_correct is not None:
            if st.session_state.last_correct:
                st.success("正解です。")
            else:
                st.warning("不正解です。")
                if st.session_state.level_difficult and st.session_state.last_wrong_detail:
                    d = st.session_state.last_wrong_detail
                    st.markdown(f'<p class="caption" translate="no"><strong>正解:</strong> 「{html.escape(d["正解"])}」</p>', unsafe_allow_html=True)
                    if d.get("解説"):
                        st.markdown(f'<p class="caption" translate="no"><strong>解説:</strong> {html.escape(d["解説"])}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("次の問題へ"):
                st.session_state.answered_current = False
                st.session_state.current_index += 1
                if st.session_state.current_index >= len(st.session_state.questions):
                    st.session_state.quiz_done = True
                st.rerun()
            st.markdown("---")
        else:
            idx = st.session_state.current_index
            st.markdown(f'<p lang="ja" translate="no">{QUESTION_SENTENCE}</p>', unsafe_allow_html=True)
            st.markdown("**【出来事】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["出来事"])}</div>', unsafe_allow_html=True)
            st.markdown("**【どのように感じたか】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["例文"])}</div>', unsafe_allow_html=True)
            st.caption("※以下のどちらかのボタンをクリックしてください")
            st.markdown('</div>', unsafe_allow_html=True)
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                st.markdown(f'<p lang="ja" translate="no" style="text-align:center; font-weight:600; margin-bottom:0.2rem;">{LABEL_MONDAI}</p>', unsafe_allow_html=True)
                if st.button("▶", key=f"mondai_{idx}", use_container_width=True):
                    is_correct = LABEL_MONDAI == q["正解"]
                    if is_correct:
                        st.session_state.correct_count += 1
                    else:
                        st.session_state.wrong_answers.append({
                            "出来事": q["出来事"], "例文": q["例文"], "正解": q["正解"],
                            "解説": q["解説"], "ユーザーの回答": LABEL_MONDAI,
                        })
                    st.session_state.answered_current = True
                    st.session_state.last_correct = is_correct
                    st.session_state.last_wrong_detail = q if not is_correct else None
                    st.rerun()
            with col2:
                st.markdown(f'<p lang="ja" translate="no" style="text-align:center; font-weight:600; margin-bottom:0.2rem;">{LABEL_KURUSHIMI}</p>', unsafe_allow_html=True)
                st.markdown('<p lang="en" translate="no" style="text-align:center; font-weight:600; margin-bottom:0.2rem;">PUSH</p>', unsafe_allow_html=True)
                if st.button("▶", key=f"kurushimi_{idx}", use_container_width=True):
                    is_correct = LABEL_KURUSHIMI == q["正解"]
                    if is_correct:
                        st.session_state.correct_count += 1
                    else:
                        st.session_state.wrong_answers.append({
                            "出来事": q["出来事"], "例文": q["例文"], "正解": q["正解"],
                            "解説": q["解説"], "ユーザーの回答": LABEL_KURUSHIMI,
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
                    st.markdown(f'<p translate="no"><strong>出来事:</strong> {html.escape(w["出来事"])}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p translate="no"><strong>どのように感じたか:</strong> {html.escape(w["例文"])}</p>', unsafe_allow_html=True)
                    st.markdown(
                        f'<p lang="ja" translate="no">'
                        f'<strong>あなたの答え:</strong> {html.escape(w["ユーザーの回答"])}<br><br>'
                        f'<strong>正解:</strong> {html.escape(w["正解"])}'
                        f'</p>',
                        unsafe_allow_html=True,
                    )
                    if w.get("解説"):
                        st.markdown(f'<p class="caption" translate="no"><strong>解説:</strong> {html.escape(w["解説"])}</p>', unsafe_allow_html=True)
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
