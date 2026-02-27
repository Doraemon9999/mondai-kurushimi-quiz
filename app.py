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
APP_TITLE = "問題と苦しみの理解度テスト"
LABEL_MONDAI = "問題"
LABEL_KURUSHIMI = "苦しみ"
RIGHT_BUTTON_LABEL = "苦しみ"  # 右ボタンは必ず「苦しみ」
QUESTION_SENTENCE = "次の例文は「問題」と「苦しみ」のどちらに当たりますか？"
EXCEL_DISPLAY_NAME = "問題と苦しみ.xlsx"
FOOTER_CREDIT = "Produced by AI Fusion Service"  # 英語で表記
LEVEL_LABEL = "難易度を選んでください"
LEVEL_EASY = "レベル1（結果のみ表示）"
LEVEL_HARD = "レベル2（不正解時に正解・解説を表示）"

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
    """level_num が 1 ならレベル1用、2 ならレベル2用。「レベル1」「NO1」「ＮＯ１」等を認識。"""
    names = xl.sheet_names
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
    """Excel を1回だけ開き、(data_level1, data_level2, シート名のリスト) を返す。"""
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
    .footer-credit { position: fixed !important; bottom: 8px !important; left: 50% !important; transform: translateX(-50%) !important; font-size: 0.75rem; color: #888; }
    .app-title-same { font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; }
    .quiz-content-min-height { min-height: 0; }
    p.caption { font-size: 0.88rem; color: #808495; margin-top: -0.5rem; }
    .load-success { padding: 0.75rem 1rem; border-radius: 0.25rem; background: #d4edda; color: #155724; margin: 0.5rem 0; }
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
if "level_choice" not in st.session_state:
    st.session_state["level_choice"] = LEVEL_EASY
if "show_explanations" not in st.session_state:
    st.session_state.show_explanations = False

# 正しいバージョン確認用（ボタンは「問題」と「苦しみ」です）
st.markdown('<p class="caption" lang="ja" translate="no">このテストでは、選択肢は「問題」と「苦しみ」の2つです。</p>', unsafe_allow_html=True)
# データ読み込み（設定済みExcelを優先 → スマホではアップロード不要で利用可能）
excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "問題と苦しみ.xlsx")
data = []
data_level1 = []
data_level2 = []
actual_name = ""
use_fallback = False
sheet_names_found = []
data_from_builtin = False  # 同梱の問題と苦しみ.xlsx で読み込んだか

if st.session_state.get("sheet_choice_done") and st.session_state.get("data_level1_override") is not None:
    data_level1 = st.session_state.data_level1_override
    data_level2 = st.session_state.data_level2_override
    actual_name = st.session_state.get("actual_name_override", "")
    data = data_level1 or data_level2
    use_fallback = False
else:
    # まず同梱の「問題と苦しみ.xlsx」があれば読み込む（スマホではアップロード不要）
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
        # データは既にあるのでアップロード案内は一切出さない（「問題データをアップロードしてください」「Drag and drop」非表示）
        # 別のExcelを使う場合は下の「別のExcelファイル・シートでやり直す」ボタンで対応
        pass
    else:
        # 同梱ファイルがない場合：まずセッションまたは同梱パスから復元を試みる（URL再表示でもアップロード欄を出さないため）
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

        # データがまだ無いときだけ「問題データをアップロードしてください」と Drag and drop を表示
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
                    if data:
                        st.rerun()  # 再実行してアップロード欄を消し、GOOD表示（クイズのみ）にする
                    if data and not use_fallback:
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} から レベル1: {len(data_level1)}件、レベル2: {len(data_level2)}件読み込みました。</div></div>', unsafe_allow_html=True)
                    elif data and use_fallback and len(sheet_names_found) < 2:
                        sheets_info = "このファイルのシート名: 「" + "」「".join(html.escape(s) for s in sheet_names_found) + "」。" if sheet_names_found else ""
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} の先頭シートから {len(data)} 件読み込みました。<br>{sheets_info}別々のデータにするには下でシートを選んでください。</div></div>', unsafe_allow_html=True)
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
                    if data:
                        st.rerun()  # 再実行してアップロード欄を消し、GOOD表示にする
                    if data and not use_fallback:
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} から レベル1: {len(data_level1)}件、レベル2: {len(data_level2)}件読み込みました。</div></div>', unsafe_allow_html=True)
                    elif data and use_fallback and len(sheet_names_found) < 2:
                        sheets_info = "このファイルのシート名: 「" + "」「".join(html.escape(s) for s in sheet_names_found) + "」。" if sheet_names_found else ""
                        st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">{html.escape(actual_name)} の先頭シートから {len(data)} 件読み込みました。<br>{sheets_info}別々のデータにするには下でシートを選んでください。</div></div>', unsafe_allow_html=True)
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
                    st.error("選択したシートにデータがありません。")

if data:
    if not st.session_state.quiz_started:
        if st.session_state.get("sheet_choice_done"):
            st.markdown(f'<div class="load-msg-mobile-hide"><div class="load-success" translate="no">選択したシートで読み込みました。レベル1: {len(data_level1)}件、レベル2: {len(data_level2)}件。</div></div>', unsafe_allow_html=True)
            if st.button("別のExcelファイル・シートでやり直す"):
                for k in ("sheet_choice_done", "data_level1_override", "data_level2_override", "actual_name_override"):
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        st.markdown(f'<p class="app-title-same" lang="ja" translate="no">{APP_TITLE}</p>', unsafe_allow_html=True)
        st.markdown(f'<p lang="ja" translate="no"><strong>難易度を選んでください</strong></p>', unsafe_allow_html=True)
        # フォーム内にすると「送信」時に選ばれたレベルが確実に渡る
        with st.form("quiz_start_form"):
            level = st.radio(
                " ",
                [LEVEL_EASY, LEVEL_HARD],
                index=0,
                horizontal=True,
            )
            submitted = st.form_submit_button("テスト開始（10問）")
        if submitted:
            level_options = [LEVEL_EASY, LEVEL_HARD]
            selected_index = level_options.index(level) if level in level_options else 0
            is_level2 = (selected_index == 1)
            st.session_state.level_difficult = is_level2
            st.session_state.show_explanations = is_level2
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
                # レベル2のときだけ正解・解説を表示
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
            st.markdown(f'<p lang="ja" translate="no">{QUESTION_SENTENCE}</p>', unsafe_allow_html=True)
            st.markdown("**【出来事】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["出来事"])}</div>', unsafe_allow_html=True)
            st.markdown("**【どのように感じたか】**")
            st.markdown(f'<div class="quiz-info-box" translate="no">{html.escape(q["例文"])}</div>', unsafe_allow_html=True)
            st.caption("※以下のどちらかのボタンをクリックしてください")
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
        st.success(f"### テストが終了しました")
        st.markdown(f"**結果: {score} / {total} 問正解　得点: {pct} 点**")
        # レベル2のときだけ間違えた問題の正解・解説を表示
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
            st.session_state["level_choice"] = LEVEL_EASY  # レベル選択をリセット（次回はレベル1）
            if "show_explanations" in st.session_state:
                del st.session_state["show_explanations"]
            st.rerun()
