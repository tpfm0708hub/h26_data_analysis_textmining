import os
import importlib.util

import pandas as pd
import streamlit as st
from matplotlib import font_manager, rc


# =========================================================
# 0. 기본 경로 설정
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MYLIB_DIR = os.path.join(BASE_DIR, "mylib")


# =========================================================
# 1. 숫자로 시작하는 파일명을 모듈로 불러오기 위한 함수
# =========================================================
def load_module_from_path(module_alias, file_path):
    """
    파일명이 숫자로 시작하는 Python 파일은 일반 import 문으로 불러올 수 없습니다.

    예:
    from 260506_myTextAnalyzer import ...

    위 문법은 불가능하므로 importlib.util을 사용하여
    파일 경로 기준으로 모듈을 불러옵니다.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"모듈 파일을 찾을 수 없습니다: {file_path}")

    spec = importlib.util.spec_from_file_location(module_alias, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# =========================================================
# 2. 사용자 정의 모듈 로딩
# =========================================================
TEXT_ANALYZER_PATH = os.path.join(MYLIB_DIR, "260506_myTextAnalyzer.py")
VISUALIZER_PATH = os.path.join(MYLIB_DIR, "260506_myStramlitVisualizer.py")

myTextAnalyzer = load_module_from_path(
    module_alias="myTextAnalyzer_260506",
    file_path=TEXT_ANALYZER_PATH
)

myVisualizer = load_module_from_path(
    module_alias="myStramlitVisualizer_260506",
    file_path=VISUALIZER_PATH
)


# =========================================================
# 3. 모듈 내 함수 연결
# =========================================================
parse_stopwords = myTextAnalyzer.parse_stopwords
parse_replace_rules = myTextAnalyzer.parse_replace_rules
run_text_analysis = myTextAnalyzer.run_text_analysis

draw_hbar = myVisualizer.draw_hbar
draw_wordcloud = myVisualizer.draw_wordcloud
fig_to_png_bytes = myVisualizer.fig_to_png_bytes


# =========================================================
# 4. Streamlit 기본 설정
# =========================================================
st.set_page_config(
    page_title="형태소 빈도분석 대시보드",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# 5. 기본 데이터 경로 설정
# =========================================================
DEFAULT_DATA_PATH = r"D:\Lecture\TextMining26\data\daum_movie_review.csv"


# =========================================================
# 6. 한글 폰트 설정
# =========================================================
FONT_PATH = "c:/Windows/Fonts/malgun.ttf"

if os.path.exists(FONT_PATH):
    font_name = font_manager.FontProperties(fname=FONT_PATH).get_name()
    rc("font", family=font_name)


# =========================================================
# 7. 캐시 적용: 기본 CSV 파일 읽기
# =========================================================
@st.cache_data(show_spinner=False)
def load_default_file(file_path):
    """
    기본 데이터 파일을 불러옵니다.
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="cp949")

    return df


# =========================================================
# 8. 캐시 적용: 업로드 파일 읽기
# =========================================================
@st.cache_data(show_spinner=False)
def load_uploaded_file(uploaded_file_name, uploaded_file_bytes):
    """
    업로드한 CSV 또는 Excel 파일을 데이터프레임으로 불러옵니다.
    """
    from io import BytesIO

    file_ext = uploaded_file_name.lower().split(".")[-1]
    file_buffer = BytesIO(uploaded_file_bytes)

    if file_ext == "csv":
        try:
            df = pd.read_csv(file_buffer, encoding="utf-8-sig")
        except UnicodeDecodeError:
            file_buffer.seek(0)
            df = pd.read_csv(file_buffer, encoding="cp949")

    elif file_ext in ["xlsx", "xls"]:
        df = pd.read_excel(file_buffer)

    else:
        raise ValueError("csv, xlsx, xls 파일만 업로드할 수 있습니다.")

    return df


# =========================================================
# 9. 캐시 적용: 형태소 분석 실행
# =========================================================
@st.cache_data(show_spinner=True)
def cached_text_analysis(
    df,
    selected_columns,
    analyzer_name,
    selected_pos_kor,
    stop_words,
    replace_dict,
    min_len,
    top_n,
):
    """
    동일한 조건의 형태소 분석 결과를 캐시에 저장합니다.
    """
    return run_text_analysis(
        df=df,
        selected_columns=selected_columns,
        analyzer_name=analyzer_name,
        selected_pos_kor=selected_pos_kor,
        stop_words=stop_words,
        replace_dict=replace_dict,
        min_len=min_len,
        top_n=top_n,
    )


# =========================================================
# 10. 제목 영역
# =========================================================
st.title("📊 한국어 형태소 빈도분석 대시보드")

st.write(
    """
    기본 데이터 또는 사용자가 업로드한 CSV·Excel 파일을 대상으로  
    한국어 형태소 빈도분석, 수평 막대그래프, 워드클라우드 생성을 수행합니다.
    """
)


# =========================================================
# 11. 사이드바: 데이터 선택 방식
# =========================================================
st.sidebar.header("1. 데이터 선택")

data_source = st.sidebar.radio(
    "분석 데이터 선택",
    options=[
        "기본 데이터 사용",
        "직접 파일 업로드"
    ],
    index=0
)


# =========================================================
# 12. 기본 데이터 또는 업로드 데이터 불러오기
# =========================================================
if data_source == "기본 데이터 사용":

    if not os.path.exists(DEFAULT_DATA_PATH):
        st.error(f"기본 데이터 파일을 찾을 수 없습니다: {DEFAULT_DATA_PATH}")
        st.stop()

    try:
        df = load_default_file(DEFAULT_DATA_PATH)
        current_file_name = os.path.basename(DEFAULT_DATA_PATH)
        st.sidebar.success(f"기본 데이터 로딩 완료: {current_file_name}")

    except Exception as e:
        st.error(f"기본 데이터 파일을 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()

else:
    uploaded_file = st.sidebar.file_uploader(
        "CSV 또는 Excel 파일 업로드",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is None:
        st.info("왼쪽 사이드바에서 분석할 CSV 또는 Excel 파일을 업로드해주세요.")
        st.stop()

    try:
        df = load_uploaded_file(
            uploaded_file_name=uploaded_file.name,
            uploaded_file_bytes=uploaded_file.getvalue()
        )
        current_file_name = uploaded_file.name
        st.sidebar.success(f"업로드 완료: {current_file_name}")

    except Exception as e:
        st.error(f"파일을 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()


# =========================================================
# 13. 사이드바: 분석 열 선택
# =========================================================
st.sidebar.header("2. 분석 열 선택")

all_columns = df.columns.tolist()

default_columns = ["review"] if "review" in all_columns else []

selected_columns = st.sidebar.multiselect(
    "형태소 분석을 진행할 열 선택",
    options=all_columns,
    default=default_columns,
    help="복수 열을 선택하면 선택한 열의 텍스트를 합쳐서 분석합니다."
)

if not selected_columns:
    st.warning("분석할 열을 최소 1개 이상 선택해주세요.")
    st.dataframe(df.head(10), use_container_width=True)
    st.stop()


# =========================================================
# 14. 사이드바: 형태소 분석기 및 분석 조건
# =========================================================
st.sidebar.header("3. 분석 조건")

analyzer_name = st.sidebar.radio(
    "형태소 분석 도구 선택",
    options=["kiwipiepy", "konlpy-Okt"],
    index=0,
    help="konlpy-Okt가 실행되지 않는 환경에서는 kiwipiepy 사용을 권장합니다."
)

top_n = st.sidebar.slider(
    "빈도표 출력 단어 수",
    min_value=5,
    max_value=200,
    value=50,
    step=5
)

bar_top_n = st.sidebar.slider(
    "막대그래프 표시 단어 수",
    min_value=5,
    max_value=50,
    value=20,
    step=5
)

min_len = st.sidebar.slider(
    "최소 글자 수",
    min_value=1,
    max_value=10,
    value=2,
    step=1,
    help="예: 2로 설정하면 한 글자 단어는 제외됩니다."
)


# =========================================================
# 15. 메인 화면: 데이터 미리보기
# =========================================================
st.subheader("1. 데이터 미리보기")

col_info_1, col_info_2, col_info_3, col_info_4 = st.columns(4)

with col_info_1:
    st.metric("현재 데이터", current_file_name)

with col_info_2:
    st.metric("행 수", f"{df.shape[0]:,}")

with col_info_3:
    st.metric("열 수", f"{df.shape[1]:,}")

with col_info_4:
    st.metric("선택 열 수", f"{len(selected_columns):,}")

st.dataframe(df.head(10), use_container_width=True)


# =========================================================
# 16. 메인 화면: 품사 선택
# =========================================================
st.subheader("2. 분석 품사 선택")

st.write("분석에 포함할 품사를 선택해주세요.")

pos_col1, pos_col2, pos_col3 = st.columns(3)

with pos_col1:
    use_noun = st.toggle("명사", value=True)

with pos_col2:
    use_verb = st.toggle("동사", value=False)

with pos_col3:
    use_adjective = st.toggle("형용사", value=False)

selected_pos_kor = []

if use_noun:
    selected_pos_kor.append("명사")

if use_verb:
    selected_pos_kor.append("동사")

if use_adjective:
    selected_pos_kor.append("형용사")

if not selected_pos_kor:
    st.warning("분석 품사를 최소 1개 이상 선택해주세요.")
    st.stop()


# =========================================================
# 17. 메인 화면: 불용어 입력
# =========================================================
st.subheader("3. 불용어 입력")

default_stopwords = "정말, 진짜, 하는, 입니다, 정도, 그냥, 있는, 봤어요"

stopword_text = st.text_area(
    "제외할 단어를 입력해주세요. 쉼표 또는 줄바꿈으로 구분할 수 있습니다. 최대 50개까지 반영됩니다.",
    value=default_stopwords,
    height=120
)

stop_words = parse_stopwords(stopword_text, max_words=50)

st.caption(f"현재 반영된 불용어 수: {len(stop_words)}개")
st.write(stop_words)


# =========================================================
# 18. 메인 화면: 변환어 규칙 입력
# =========================================================
st.subheader("4. 변환어 규칙 입력")

default_replace_rules = """재밌다=재미있다
재미있다=재미있다
봤다=보다
봤어요=보다
영화관=극장"""

replace_rule_text = st.text_area(
    "변환어 규칙을 입력해주세요. 예: 재밌다=재미있다 / 봤다=보다 / 영화관=극장",
    value=default_replace_rules,
    height=140
)

replace_dict = parse_replace_rules(replace_rule_text, max_rules=100)

st.caption(f"현재 반영된 변환어 규칙 수: {len(replace_dict)}개")

replace_rule_df = pd.DataFrame(
    list(replace_dict.items()),
    columns=["변환 전", "변환 후"]
)

st.dataframe(replace_rule_df, use_container_width=True)


# =========================================================
# 19. 형태소 분석 실행 버튼
# =========================================================
st.subheader("5. 형태소 분석 실행")

btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
    run_btn = st.button("형태소 분석 실행", type="primary")

with btn_col2:
    reset_btn = st.button("분석 결과 초기화")


# =========================================================
# 20. 분석 결과 초기화
# =========================================================
if reset_btn:
    if "analysis_result" in st.session_state:
        del st.session_state["analysis_result"]

    if "analysis_config" in st.session_state:
        del st.session_state["analysis_config"]

    st.success("저장된 분석 결과가 초기화되었습니다.")
    st.stop()


# =========================================================
# 21. 현재 분석 조건 저장
# =========================================================
current_analysis_config = {
    "current_file_name": current_file_name,
    "selected_columns": selected_columns,
    "analyzer_name": analyzer_name,
    "selected_pos_kor": selected_pos_kor,
    "stop_words": stop_words,
    "replace_dict": replace_dict,
    "min_len": min_len,
    "top_n": top_n,
}


# =========================================================
# 22. 형태소 분석 실행
# =========================================================
if run_btn:
    try:
        with st.spinner("형태소 분석을 진행하고 있습니다."):
            analysis_result = cached_text_analysis(
                df=df,
                selected_columns=selected_columns,
                analyzer_name=analyzer_name,
                selected_pos_kor=selected_pos_kor,
                stop_words=stop_words,
                replace_dict=replace_dict,
                min_len=min_len,
                top_n=top_n,
            )

        st.session_state["analysis_result"] = analysis_result
        st.session_state["analysis_config"] = current_analysis_config

        st.success("형태소 분석이 완료되었습니다.")

    except Exception as e:
        st.error(f"형태소 분석 중 오류가 발생했습니다: {e}")
        st.stop()


# =========================================================
# 23. 저장된 분석 결과 확인
# =========================================================
if "analysis_result" not in st.session_state:
    st.info("설정을 완료한 뒤 [형태소 분석 실행] 버튼을 눌러주세요.")
    st.stop()


# =========================================================
# 24. 분석 조건 변경 여부 확인
# =========================================================
saved_analysis_config = st.session_state.get("analysis_config")

if saved_analysis_config != current_analysis_config:
    st.warning(
        "분석 조건이 변경되었습니다. 변경된 조건을 반영하려면 [형태소 분석 실행] 버튼을 다시 눌러주세요."
    )


# =========================================================
# 25. 저장된 분석 결과 불러오기
# =========================================================
analysis_result = st.session_state["analysis_result"]


# =========================================================
# 26. 분석 결과 객체 분리
# =========================================================
freq_df = analysis_result["freq_df"]
counter = analysis_result["counter"]
result_df = analysis_result["result_df"]
total_token_count = analysis_result["total_token_count"]
unique_token_count = analysis_result["unique_token_count"]


# =========================================================
# 27. 분석 요약
# =========================================================
st.subheader("6. 분석 요약")

sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)

with sum_col1:
    st.metric("분석기", analyzer_name)

with sum_col2:
    st.metric("전체 토큰 수", f"{total_token_count:,}")

with sum_col3:
    st.metric("고유 토큰 수", f"{unique_token_count:,}")

with sum_col4:
    st.metric("선택 품사", ", ".join(selected_pos_kor))


# =========================================================
# 28. 빈도분석 결과표
# =========================================================
st.subheader("7. 형태소 빈도분석 결과")

if freq_df.empty:
    st.warning("분석 결과가 비어 있습니다. 불용어, 품사, 최소 글자 수 조건을 조정해주세요.")
    st.stop()

st.dataframe(freq_df, use_container_width=True)

csv_data = freq_df.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="빈도분석 결과 CSV 다운로드",
    data=csv_data,
    file_name="word_frequency_result.csv",
    mime="text/csv"
)


# =========================================================
# 29. 시각화 출력 및 이미지 다운로드
# =========================================================
st.subheader("8. 시각화 결과")

tab1, tab2 = st.tabs(["수평 막대그래프", "워드클라우드"])


with tab1:
    fig_bar = draw_hbar(
        freq_df=freq_df,
        title="형태소 빈도분석 수평 막대그래프",
        top_n=bar_top_n
    )

    st.pyplot(fig_bar)

    bar_img = fig_to_png_bytes(fig_bar)

    st.download_button(
        label="이미지 다운로드",
        data=bar_img,
        file_name="word_frequency_bargraph.png",
        mime="image/png"
    )


with tab2:
    if not os.path.exists(FONT_PATH):
        st.error("한글 폰트 파일을 찾을 수 없습니다. FONT_PATH를 확인해주세요.")
    else:
        fig_wc = draw_wordcloud(
            counter=counter,
            font_path=FONT_PATH,
            max_words=top_n,
            background_color="ivory"
        )

        st.pyplot(fig_wc)

        wc_img = fig_to_png_bytes(fig_wc)

        st.download_button(
            label="이미지 다운로드",
            data=wc_img,
            file_name="wordcloud_result.png",
            mime="image/png"
        )


# =========================================================
# 30. 토큰화 결과 데이터 확인
# =========================================================
st.subheader("9. 토큰화 결과 데이터")

show_cols = selected_columns + ["분석대상텍스트", "tokens"]

st.dataframe(
    result_df[show_cols].head(100),
    use_container_width=True
)

token_csv = result_df.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="CSV 다운로드",
    data=token_csv,
    file_name="tokenized_result.csv",
    mime="text/csv"
)
