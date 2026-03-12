# -*- coding: utf-8 -*-
"""
問題と苦しみの理解度テスト - Web版（Streamlit）
URLを知っている人がブラウザでアクセスして利用できます。
"""
import html
import io
import os
import random
import unicodedata

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
APP_TITLE = "「問題」と「苦しみ」の判別ゲーム"
LABEL_MONDAI = "問題"
LABEL_KURUSHIMI = "苦しみ"
RIGHT_BUTTON_LABEL = "苦しみ"  # 右ボタン表示
QUESTION_SENTENCE = "次の例文は「問題」と「苦しみ」のどちらに当たりますか？"
# 問題・回答の参照先（同梱ファイル名）
EXCEL_DEFAULT_FILENAME = "problem_answers_added.xlsx"
EXCEL_DISPLAY_NAME = "problem_answers_added.xlsx"
FOOTER_CREDIT = ""  # 表示しない（AI Fusion Service を削除）
LEVEL_LABEL = "難易度を選んでください"
# レベル1・レベル2（両方とも解説付きの処理）
LEVEL_EASY = "レベル1"
LEVEL_HARD = "レベル2"
# 目的・定義（初心者向け）
PURPOSE_MAIN = (
    "このゲームは、グルノートをうまく活用する上で必要な「問題」と「苦しみ」の違いを見分ける練習用ゲームです。"
    " ある出来事が「行動で解決すべき問題」なのか、それとも「考え方や視点を変えることで解決できる苦しみ」なのかを切り分ける力を身につけることが目的です。"
)
PURPOSE_MONDAI = "問題の場合 → 行動することで解決します"
PURPOSE_KURUSHIMI = "苦しみの場合 → その出来事への見方が変わることで解決します"
DEF_MONDAI = "問題とは：実際に起きた出来事や事実のこと。"
DEF_KURUSHIMI = "苦しみとは：その出来事に対して自分が感じた感情や解釈のこと。"
DEF_ACTION_VS_VIEW = "問題は「行動」でしか解決できません。苦しみは「視点の変化」で解決できます。"
# 初めての人向けの説明文（レベル1で慣れたらレベル2へ）
INTRO_STEPS = (
    '<span class="step-num">1</span> まず<strong>レベル1</strong>で10問のクイズに挑戦する<br>'
    '<span class="step-num">2</span> 各問で<strong>「問題」「苦しみ」</strong>のどちらかボタンを押す（選択するとすぐに次の問題へ進みます）<br>'
    '<span class="step-num">3</span> ゲーム終了後に<strong>結果</strong>と<strong>解説</strong>を確認できます → 慣れてきたら<strong>レベル2</strong>に挑戦'
)
INTRO_RANDOM = "問題は毎回ランダムで出題されます。"
GOAL_PHRASE = "ゲームを数回やった後、あなたの考え方や物事の見方が、少し変わっているかもしれません。何問正解できるか試してみましょう。"
INTUITION_PHRASE = "直感で答えてください。考えすぎなくて大丈夫です。"
BUTTON_HINT = "選択するとすぐに次の問題へ進みます。"
OUTCOME_FACT = "上が事実、下が感情です。<br>この感情が「問題」なのか「苦しみ」なのか判断しボタンを押してください。"
# テスト開始ボタン（行動イメージが湧く表現）
BTN_START_QUIZ = "10問に挑戦する"

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


def _df_to_rows(df):
    """DataFrame を行リストに変換。"""
    idx_dekigoto = _find_col(df, ["出来事", "イベント"])
    if idx_dekigoto is None:
        idx_dekigoto = COL_DEKIGOTO
    idx_mondai = _find_col(df, ["問題"])
    if idx_mondai is None:
        idx_mondai = COL_MONDAI
    idx_kurushimi = _find_col(df, ["苦しみ"])
    if idx_kurushimi is None:
        idx_kurushimi = COL_KURUSHIMI
    idx_kaito = _find_col(df, ["回答", "解説"])
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


def load_data(excel_path, sheet_name=None):
    """Excelを読み込み、行リストを返す。sheet_name を指定するとそのシートを読む。"""
    try:
        if sheet_name is None:
            df = pd.read_excel(excel_path)
            return _df_to_rows(df)
        # シート名指定時は ExcelFile で実際のシート名と照合して読む（先頭シートへはフォールバックしない）
        xl = pd.ExcelFile(excel_path)
        want = sheet_name.strip()
        chosen = None
        for s in xl.sheet_names:
            if s.strip() == want:
                chosen = s
                break
        if chosen is None:
            return []
        df = pd.read_excel(xl, sheet_name=chosen)
        return _df_to_rows(df)
    except Exception:
        return []


def _sheet_for_level(xl, level_num):
    """level_num が 1 ならレベル1用、2 ならレベル2用のシートを返す。「レベル1」「NO1」「ＮＯ１」等を認識。"""
    names = xl.sheet_names
    # 全角→半角に正規化（ＮＯ１→NO1、レベル１→レベル1 など。Excelで全角になっていても一致するように）
    def nfkc(t):
        return unicodedata.normalize("NFKC", str(t).strip())
    def norm(t):
        s = nfkc(t)
        return "".join(c for c in s.upper() if c not in " .・")
    if level_num == 1:
        for s in names:
            n = "".join(nfkc(s).split())
            n_asc = norm(s)
            if n == "レベル1" or n_asc == "NO1" or n_asc == "NO.1":
                return _df_to_rows(pd.read_excel(xl, sheet_name=s))
    else:
        for s in names:
            n = "".join(nfkc(s).split())
            n_asc = norm(s)
            if n == "レベル2" or n_asc == "NO2" or n_asc == "NO.2":
                return _df_to_rows(pd.read_excel(xl, sheet_name=s))
    return []


def load_data_level1_level2(excel_path):
    """Excel を1回だけ開き、シート「レベル1」or「NO1」、「レベル2」or「NO2」を探す。
    返り値: (data_level1, data_level2, シート名のリスト)
    """
    try:
        xl = pd.ExcelFile(excel_path)
        data_level1 = _sheet_for_level(xl, 1)
        data_level2 = _sheet_for_level(xl, 2)
        return data_level1, data_level2, list(xl.sheet_names)
    except Exception:
        return [], [], []


def load_one_sheet(excel_path, sheet_name):
    """指定したシート名で1シートだけ読み、行リストを返す。"""
    try:
        xl = pd.ExcelFile(excel_path)
        if sheet_name not in xl.sheet_names:
            return []
        df = pd.read_excel(xl, sheet_name=sheet_name)
        return _df_to_rows(df)
    except Exception:
        return []


def run_quiz(data, level_difficult, num=NUM_QUESTIONS):
    """問題データをすべて取り出し、その中からランダムに num 問（既定10問）を抽出して出題リストを返す。"""
    if not data:
        return []
    n = min(len(data), num)
    chosen = random.sample(data, n)
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
    .footer-credit { position: fixed !important; bottom: 8px !important; left: 50% !important; transform: translateX(-50%) !important; font-size: 0.75rem; color: #888; }
    .app-title-same { font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; }
    .quiz-content-min-height { min-height: 0; }
    p.caption { font-size: 0.88rem; color: #808495; margin-top: -0.5rem; }
    .load-success { padding: 0.75rem 1rem; border-radius: 0.25rem; background: #d4edda; color: #155724; margin: 0.5rem 0; }
    /* スマホ用：このラッパーごと非表示（.load-msg-mobile-hide は HTML 側で緑メッセージを囲む） */
    .load-msg-mobile-hide { }
    @media (max-width: 1024px), (max-width: 768px), (max-device-width: 1024px) {
        .load-msg-mobile-hide {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important; min-height: 0 !important;
            margin: 0 !important; padding: 0 !important;
            overflow: hidden !important;
            position: absolute !important;
            left: -9999px !important;
        }
        .load-success {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important; min-height: 0 !important;
            margin: 0 !important; padding: 0 !important;
            overflow: hidden !important;
        }
    }
    .quiz-info-box { padding: 1rem; border-radius: 0.25rem; background: #e8f4fd; border-left: 4px solid #1e88e5; margin: 0.5rem 0; }
    .intro-box { padding: 1rem 1.25rem; border-radius: 0.5rem; background: #f5f5f5; border: 1px solid #e0e0e0; margin: 0.75rem 0 1rem 0; font-size: 0.95rem; line-height: 1.6; color: #333; }
    .intro-box strong { color: #1a1a1a; }
    .step-num { display: inline-block; width: 1.5em; height: 1.5em; line-height: 1.4; text-align: center; background: #2196F3; color: white; border-radius: 50%; font-size: 0.85rem; font-weight: bold; margin-right: 0.35rem; }
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
if FOOTER_CREDIT:
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
if "level_choice" not in st.session_state:
    st.session_state["level_choice"] = LEVEL_EASY
# 解説表示：レベル1・レベル2とも True（両方とも解説付き）
if "show_explanations" not in st.session_state:
    st.session_state.show_explanations = True
# 文字の大きさ（小・中・大）
if "font_size" not in st.session_state:
    st.session_state.font_size = "中"

# 文字サイズ選択（常に表示・上段）※ラベルは翻訳防止でマークダウン表示
col_setting, _ = st.columns([1, 4])
with col_setting:
    st.markdown('<p lang="ja" translate="no" style="margin-bottom:0.25rem; font-weight:500;">文字の大きさ</p>', unsafe_allow_html=True)
    font_choice = st.radio(
        " ",  # ラベルは上で表示（翻訳で「文字め」等に変わらないように）
        options=["小", "中", "大"],
        index=["小", "中", "大"].index(st.session_state.font_size),
        horizontal=True,
        key="font_size_radio",
        label_visibility="collapsed",
    )
    if font_choice != st.session_state.font_size:
        st.session_state.font_size = font_choice
        st.rerun()

# 選択に応じたフォントサイズ用CSS（今の中を小にした：小＝旧中、中＝旧大、大＝さらに大）
_FONT_SIZES = {
    "小": {"title": "1.25rem", "caption": "1.05rem", "intro": "1.1rem", "quiz_box": "1.15rem", "button": "1.3rem"},
    "中": {"title": "1.5rem", "caption": "1.2rem", "intro": "1.3rem", "quiz_box": "1.35rem", "button": "1.5rem"},
    "大": {"title": "1.75rem", "caption": "1.35rem", "intro": "1.5rem", "quiz_box": "1.55rem", "button": "1.7rem"},
}
_fs = _FONT_SIZES.get(st.session_state.font_size, _FONT_SIZES["中"])
# メインエリア全体のベースもスケール
_base_scale = {"小": "115%", "中": "132%", "大": "150%"}.get(st.session_state.font_size, "115%")
st.markdown(f"""
<style>
    /* アプリ全体のベース（.main に依存しない） */
    [data-testid="stAppViewContainer"] {{ font-size: {_base_scale}; }}
    [data-testid="stAppViewContainer"] .block-container {{ font-size: inherit; }}
    [data-testid="stAppViewContainer"] .block-container * {{ font-size: inherit !important; }}
    .app-title-same {{ font-size: {_fs["title"]} !important; }}
    p.caption {{ font-size: {_fs["caption"]} !important; }}
    .intro-box {{ font-size: {_fs["intro"]} !important; }}
    .quiz-info-box {{ font-size: {_fs["quiz_box"]} !important; }}
    /* 全ボタン（フォーム送信含む）・複数セレクタで確実に */
    [data-testid="stAppViewContainer"] button {{ font-size: {_fs["button"]} !important; }}
    [data-testid="stAppViewContainer"] .stButton button {{ font-size: {_fs["button"]} !important; }}
    [data-testid="stAppViewContainer"] [data-testid="stFormSubmitButton"] {{ font-size: {_fs["button"]} !important; }}
    .stButton > button {{ font-size: {_fs["button"]} !important; }}
    .step-num {{ font-size: {_fs["caption"]} !important; }}
    /* キャプション */
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ font-size: {_fs["caption"]} !important; }}
    .main small, [data-testid="stAppViewContainer"] small {{ font-size: {_fs["caption"]} !important; }}
    /* ラジオ（レベル1・レベル2、文字の大きさ 小中大） */
    [data-testid="stAppViewContainer"] .stRadio label {{ font-size: {_fs["intro"]} !important; }}
    [data-testid="stAppViewContainer"] .stRadio span {{ font-size: {_fs["intro"]} !important; }}
    [data-testid="stAppViewContainer"] .stRadio div {{ font-size: {_fs["intro"]} !important; }}
    /* 文字の大きさラジオ（小・中・大）を常に1行表示 */
    .block-container .stRadio:first-of-type > div {{ flex-wrap: nowrap !important; white-space: nowrap !important; }}
    .block-container .stRadio:first-of-type label {{ white-space: nowrap !important; flex-shrink: 0 !important; }}
    /* アラート・エキスパンダー見出し（問1, 問2…）・ボタン風要素 */
    [data-testid="stAlert"], [data-testid="stAlert"] * {{ font-size: {_fs["quiz_box"]} !important; }}
    [data-testid="stExpander"] summary {{ font-size: {_fs["quiz_box"]} !important; }}
    [data-testid="stExpander"] details summary {{ font-size: {_fs["quiz_box"]} !important; }}
    [data-testid="stExpander"] .streamlit-expanderContent,
    [data-testid="stExpander"] .streamlit-expanderContent * {{ font-size: {_fs["intro"]} !important; }}
    /* マークダウン・一般テキスト */
    [data-testid="stVerticalBlock"] .stMarkdown,
    [data-testid="stVerticalBlock"] .stMarkdown p,
    [data-testid="stVerticalBlock"] .stMarkdown div,
    [data-testid="stVerticalBlock"] .stMarkdown label {{ font-size: {_fs["intro"]} !important; }}
</style>
""", unsafe_allow_html=True)

# 初めての人向け：このページの説明（クイズ開始前のみ表示）
# （「問題」と「苦しみ」の判別ゲームのキャプションはデータ読み込み後のタイトルで表示）

# データ読み込み（設定済みExcelを優先 → スマホではアップロード不要で利用可能）
excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_DEFAULT_FILENAME)
data = []
data_level1 = []
data_level2 = []
actual_name = ""
use_fallback = False
sheet_names_found = []
data_from_builtin = False

# 前回「シートを手動で選択」して読み込んだ結果があればそれを使う
if st.session_state.get("sheet_choice_done") and st.session_state.get("data_level1_override") is not None:
    data_level1 = st.session_state.data_level1_override
    data_level2 = st.session_state.data_level2_override
    actual_name = st.session_state.get("actual_name_override", "")
    data = data_level1 or data_level2
    use_fallback = False
else:
    # まず同梱の「problem_answers_added.xlsx」があれば読み込む（スマホではアップロード不要）
    if os.path.isfile(excel_path):
        try:
            data_level1, data_level2, sheet_names_found = load_data_level1_level2(excel_path)
            actual_name = os.path.basename(excel_path)
            data = data_level1 or data_level2
            if not data:
                data_fallback = load_data(excel_path, sheet_name=None)
                if data_fallback:
                    data_level1, data_level2 = data_fallback, data_fallback
                    data = data_fallback
                    use_fallback = True
            if data:
                st.session_state.excel_path_for_choice = excel_path
                st.session_state.uploaded_excel_bytes = None
                data_from_builtin = True
        except Exception:
            pass

    if data_from_builtin:
        pass
    else:
        if not data and os.path.isfile(excel_path):
            try:
                data_level1, data_level2, sheet_names_found = load_data_level1_level2(excel_path)
                actual_name = os.path.basename(excel_path)
                data = data_level1 or data_level2
                if not data:
                    data_fallback = load_data(excel_path, sheet_name=None)
                    if data_fallback:
                        data_level1, data_level2 = data_fallback, data_fallback
                        data = data_fallback
                        use_fallback = True
                st.session_state.excel_path_for_choice = excel_path
                st.session_state.uploaded_excel_bytes = None
            except Exception:
                pass
        if not data and st.session_state.get("uploaded_excel_bytes"):
            try:
                buf = io.BytesIO(st.session_state.uploaded_excel_bytes)
                data_level1, data_level2, sheet_names_found = load_data_level1_level2(buf)
                data = data_level1 or data_level2
                if not data:
                    buf.seek(0)
                    data_fallback = load_data(buf, sheet_name=None)
                    if data_fallback:
                        data_level1, data_level2 = data_fallback, data_fallback
                        data = data_fallback
            except Exception:
                pass

        if not data:
            uploaded = st.file_uploader("問題データ（Excel）をアップロードしてください", type=["xlsx"])
            if uploaded:
                st.session_state.sheet_choice_done = False
                try:
                    file_bytes = uploaded.read()
                    st.session_state.uploaded_excel_bytes = file_bytes
                    st.session_state.uploaded_name = uploaded.name
                    buf = io.BytesIO(file_bytes)
                    data_level1, data_level2, sheet_names_found = load_data_level1_level2(buf)
                    actual_name = uploaded.name
                    data = data_level1 or data_level2
                    if not data:
                        buf.seek(0)
                        data_fallback = load_data(buf, sheet_name=None)
                        if data_fallback:
                            data_level1, data_level2 = data_fallback, data_fallback
                            data = data_fallback
                            use_fallback = True
                    if data and not use_fallback:
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} を読み込みました。{INTRO_RANDOM}</div></div>', unsafe_allow_html=True)
                    elif data and use_fallback and len(sheet_names_found) < 2:
                        sheets_info = "このファイルのシート名: 「" + "」「".join(html.escape(s) for s in sheet_names_found) + "」。" if sheet_names_found else ""
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} の先頭シートから読み込みました。{INTRO_RANDOM}<br>{sheets_info}別々のデータにするにはシートを2枚以上用意し、下で「どのシートを使うか」を選んでください。</div></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"読み込みエラー: {e}")
            elif os.path.isfile(excel_path):
                try:
                    data_level1, data_level2, sheet_names_found = load_data_level1_level2(excel_path)
                    actual_name = os.path.basename(excel_path)
                    data = data_level1 or data_level2
                    if not data:
                        data_fallback = load_data(excel_path, sheet_name=None)
                        if data_fallback:
                            data_level1, data_level2 = data_fallback, data_fallback
                            data = data_fallback
                            use_fallback = True
                    st.session_state.excel_path_for_choice = excel_path
                    st.session_state.uploaded_excel_bytes = None
                    if data and not use_fallback:
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} を読み込みました。{INTRO_RANDOM}</div></div>', unsafe_allow_html=True)
                    elif data and use_fallback and len(sheet_names_found) < 2:
                        sheets_info = "このファイルのシート名: 「" + "」「".join(html.escape(s) for s in sheet_names_found) + "」。" if sheet_names_found else ""
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} の先頭シートから読み込みました。{INTRO_RANDOM}<br>{sheets_info}別々のデータにするにはシートを2枚以上用意し、下で選んでください。</div></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Excelの読み込みに失敗しました: {e}")

    if use_fallback and len(sheet_names_found) >= 2:
        st.markdown('<p lang="ja" translate="no"><strong>レベル1・レベル2に使うシートを選んでください。</strong><br>（番号はExcelのシートの並び順です。ブラウザの自動翻訳をオフにすると表示が安定します。）</p>', unsafe_allow_html=True)
        with st.form("sheet_choice_form"):
            idx1 = st.selectbox(
                "レベル1の出題に使うシート",
                range(len(sheet_names_found)),
                format_func=lambda i: f"{i+1}枚目",
                key="sheet1_choice",
            )
            idx2 = st.selectbox(
                "レベル2の出題に使うシート",
                range(len(sheet_names_found)),
                format_func=lambda i: f"{i+1}枚目",
                key="sheet2_choice",
            )
            if st.form_submit_button("このシートで出題する"):
                s1 = sheet_names_found[idx1]
                s2 = sheet_names_found[idx2]
                if st.session_state.get("uploaded_excel_bytes"):
                    buf = io.BytesIO(st.session_state.uploaded_excel_bytes)
                    d1 = load_one_sheet(buf, s1)
                    buf2 = io.BytesIO(st.session_state.uploaded_excel_bytes)
                    d2 = load_one_sheet(buf2, s2)
                    name = st.session_state.get("uploaded_name", "")
                else:
                    path = st.session_state.get("excel_path_for_choice", excel_path)
                    d1 = load_one_sheet(path, s1)
                    d2 = load_one_sheet(path, s2)
                    name = os.path.basename(path)
                if d1 or d2:
                    st.session_state.data_level1_override = d1
                    st.session_state.data_level2_override = d2
                    st.session_state.actual_name_override = name
                    st.session_state.sheet_choice_done = True
                    st.rerun()
                else:
                    st.error("選択したシートにデータがありません。列に「出来事」「問題」「苦しみ」があるか確認してください。")

if data:
    if not st.session_state.quiz_started:
        if st.session_state.get("sheet_choice_done"):
            st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">読み込みました。{INTRO_RANDOM}</div></div>', unsafe_allow_html=True)
            if st.button("別のExcelファイル・シートでやり直す"):
                for k in ("sheet_choice_done", "data_level1_override", "data_level2_override", "actual_name_override"):
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        st.markdown(f'<p class="app-title-same" lang="ja" translate="no">{APP_TITLE}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="caption" lang="ja" translate="no">{PURPOSE_MAIN}</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="intro-box" lang="ja" translate="no">このゲームの流れ<br>{INTRO_STEPS}</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="caption" lang="ja" translate="no">{DEF_MONDAI}<br>{DEF_KURUSHIMI}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="caption" lang="ja" translate="no">{INTRO_RANDOM}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="caption" lang="ja" translate="no">{GOAL_PHRASE}</p>', unsafe_allow_html=True)
        st.markdown(f'<p lang="ja" translate="no"><strong>レベルを選んでください</strong></p>', unsafe_allow_html=True)
        with st.form("quiz_start_form"):
            level = st.radio(
                " ",
                [LEVEL_EASY, LEVEL_HARD],
                index=0,
                horizontal=False,
            )
            st.markdown(
                '<p class="caption" lang="ja" translate="no">不正解の場合は、解説が表示されます。<br>レベル1に慣れたらレベル2に挑戦しましょう。</p>',
                unsafe_allow_html=True,
            )
            submitted = st.form_submit_button(BTN_START_QUIZ)
        if submitted:
            level_options = [LEVEL_EASY, LEVEL_HARD]
            selected_index = level_options.index(level) if level in level_options else 0
            is_level2 = (selected_index == 1)
            st.session_state.level_difficult = is_level2
            st.session_state.show_explanations = True
            data_to_use = data_level2 if is_level2 else data_level1
            if not data_to_use:
                st.error("選択したレベル（シート）にデータがありません。もう一方のシートか、先頭シートにデータがあるか確認してください。")
            else:
                st.session_state.questions = run_quiz(data_to_use, st.session_state.level_difficult)
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
                if st.session_state.get("show_explanations") is True:
                    d = st.session_state.last_wrong_detail
                    if d:
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
            if idx == 0:
                st.markdown(f'<p class="caption" lang="ja" translate="no">{INTUITION_PHRASE}</p>', unsafe_allow_html=True)
            st.markdown(f'<p lang="ja" translate="no">{QUESTION_SENTENCE}</p>', unsafe_allow_html=True)
            st.markdown("**【出来事】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["出来事"])}</div>', unsafe_allow_html=True)
            st.markdown("**【どのように感じたか】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["例文"])}</div>', unsafe_allow_html=True)
            if idx == 0:
                st.markdown(f'<p class="caption" lang="ja" translate="no">{OUTCOME_FACT}</p>', unsafe_allow_html=True)
                st.caption(BUTTON_HINT)
            st.markdown('</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
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
        balloon_count = min(score, 30)
        if balloon_count > 0:
            st.markdown("🎈 " * balloon_count)
            st.caption(f"正解 {score} 問おめでとうございます！")
        st.success(f"### テストが終了しました")
        st.markdown(f"**結果: {score} / {total} 問正解　得点: {pct} 点**")
        if st.session_state.wrong_answers and st.session_state.get("show_explanations") is True:
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
            st.session_state["level_choice"] = LEVEL_EASY
            if "show_explanations" in st.session_state:
                del st.session_state["show_explanations"]
            st.rerun()
