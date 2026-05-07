# =========================================================
# 260506_naver_crawl_dashboard.py
# Streamlit 기반 네이버 검색 API 크롤링 대시보드
# =========================================================

import os
import importlib.util
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================================================
# 0. 기본 경로 설정
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRAWLER_PATH = os.path.join(
    BASE_DIR,
    "naver_api_crawler_H26장세현_260506.py"
)

# API 키 저장 파일명에도 날짜 접두어 260506_ 반영
API_KEY_FILE_PATH = os.path.join(BASE_DIR, "260506_naver_api_key_xor.dat")

# 과제용 XOR 키입니다.
XOR_KEY = "TextMining26_Naver_API_Key_260506"


# =========================================================
# 1. 숫자로 시작하는 파일명을 모듈로 불러오기 위한 함수
# =========================================================
def load_module_from_path(module_alias, file_path):
    """
    파일명이 숫자로 시작하는 Python 파일은 일반 import 문으로 불러올 수 없습니다.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"모듈 파일을 찾을 수 없습니다: {file_path}")

    spec = importlib.util.spec_from_file_location(module_alias, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# =========================================================
# 2. 크롤링 모듈 로딩
# =========================================================
naver_crawler = load_module_from_path(
    module_alias="naver_api_crawler_260506",
    file_path=CRAWLER_PATH
)

crawl_naver_search = naver_crawler.crawl_naver_search
save_api_key_xor = naver_crawler.save_api_key_xor
load_api_key_xor = naver_crawler.load_api_key_xor
check_api_key_file = naver_crawler.check_api_key_file


# =========================================================
# 3. Streamlit 기본 설정
# =========================================================
st.set_page_config(
    page_title="네이버 검색 API 크롤링 대시보드",
    page_icon="📰",
    layout="wide"
)


# =========================================================
# 4. 제목
# =========================================================
st.title("📰 네이버 검색 API 크롤링 대시보드")

st.write(
    """
    네이버 검색 API를 활용하여 뉴스 또는 블로그 검색 결과를 수집하고,  
    이후 형태소 분석 및 감성분석에 활용할 수 있는 데이터프레임을 생성합니다.
    """
)


# =========================================================
# 5. 사이드바: API 인증 정보
# =========================================================
st.sidebar.header("1. 네이버 API 인증 정보")

st.sidebar.write(
    """
    최초 사용시 Client ID와 Client Secret에 대하여 
    1회 등록하고 바랍니다.
    """
)

client_id = None
client_secret = None

api_key_exists = check_api_key_file(API_KEY_FILE_PATH)

if api_key_exists:
    try:
        client_id, client_secret = load_api_key_xor(
            load_path=API_KEY_FILE_PATH,
            xor_key=XOR_KEY
        )

        st.sidebar.success("저장된 API 키를 불러왔습니다.")

    except Exception as e:
        st.sidebar.error(f"API 키 파일을 불러오는 중 오류가 발생했습니다: {e}")
        client_id = None
        client_secret = None

else:
    st.sidebar.warning("저장된 API 키 파일이 없습니다.")


with st.sidebar.expander("API 키 최초 등록 / 재등록", expanded=not api_key_exists):
    input_client_id = st.text_input(
        "Client ID",
        type="password",
        help="네이버 개발자센터에서 발급받은 Client ID를 입력합니다."
    )

    input_client_secret = st.text_input(
        "Client Secret",
        type="password",
        help="네이버 개발자센터에서 발급받은 Client Secret을 입력합니다."
    )

    save_key_btn = st.button("API 키 저장")

    if save_key_btn:
        if not input_client_id or not input_client_secret:
            st.error("Client ID와 Client Secret을 모두 입력해주세요.")
        else:
            try:
                save_api_key_xor(
                    client_id=input_client_id,
                    client_secret=input_client_secret,
                    save_path=API_KEY_FILE_PATH,
                    xor_key=XOR_KEY
                )

                st.success("API 키가 저장되었습니다. 앱을 새로고침하면 자동으로 불러옵니다.")
                st.stop()

            except Exception as e:
                st.error(f"API 키 저장 중 오류가 발생했습니다: {e}")


with st.sidebar.expander("API 키 파일 관리"):
    st.write(f"저장 경로: `{API_KEY_FILE_PATH}`")

    delete_key_btn = st.button("저장된 API 키 삭제")

    if delete_key_btn:
        if os.path.exists(API_KEY_FILE_PATH):
            os.remove(API_KEY_FILE_PATH)
            st.success("저장된 API 키 파일을 삭제했습니다.")
            st.stop()
        else:
            st.info("삭제할 API 키 파일이 없습니다.")


# =========================================================
# 6. 사이드바: 기본 검색 조건
# =========================================================
st.sidebar.header("2. 기본 검색 조건")

keyword = st.sidebar.text_input(
    "검색어",
    value="인공지능",
    help='기존 코드의 urllib.parse.quote("인공지능")에 해당하는 원문 검색어입니다.'
)

search_type = st.sidebar.radio(
    "검색 대상",
    options=["news", "blog"],
    index=0,
    format_func=lambda x: "뉴스" if x == "news" else "블로그"
)

sort = st.sidebar.radio(
    "정렬 기준",
    options=["sim", "date"],
    index=0,
    format_func=lambda x: "정확도순" if x == "sim" else "날짜순"
)


# =========================================================
# 7. 사이드바: 분석 텍스트 기준 선택
# =========================================================
st.sidebar.header("3. 분석 텍스트 기준")

analysis_target_label = st.sidebar.radio(
    "형태소 분석 및 감성분석에 사용할 텍스트",
    options=["제목", "본문/요약문", "제목+본문/요약문"],
    index=2,
    help="네이버 검색 API는 실제 기사 전체 본문이 아니라 description 요약문을 제공합니다."
)

analysis_target_map = {
    "제목": "title",
    "본문/요약문": "description",
    "제목+본문/요약문": "title_description",
}

analysis_target = analysis_target_map[analysis_target_label]


# =========================================================
# 8. 사이드바: 수집 범위 설정
# =========================================================
st.sidebar.header("4. 수집 범위 설정")

start = st.sidebar.number_input(
    "검색 시작 위치 start",
    min_value=1,
    max_value=1000,
    value=1,
    step=1,
    help="기존 코드의 start = 1에 해당합니다. 보통 1부터 시작합니다."
)

display = st.sidebar.slider(
    "1회 요청 결과 수 display",
    min_value=10,
    max_value=100,
    value=10,
    step=10,
    help="기존 코드의 display = 10에 해당합니다. 1회 API 요청에서 가져올 결과 수입니다."
)

max_results = st.sidebar.slider(
    "최대 수집 개수",
    min_value=10,
    max_value=1000,
    value=100,
    step=10,
    help="반복 호출을 통해 최대 몇 건까지 수집할지 설정합니다."
)

sleep_sec = st.sidebar.slider(
    "요청 간 대기 시간",
    min_value=0.0,
    max_value=3.0,
    value=0.2,
    step=0.1,
    help="API를 반복 호출할 때 요청 사이에 쉬는 시간입니다."
)


# =========================================================
# 9. 사이드바: 저장 및 분석용 옵션
# =========================================================
st.sidebar.header("5. 분석 연계 옵션")

show_raw_columns = st.sidebar.checkbox(
    "원본 HTML 포함 열 표시",
    value=False,
    help="title_raw, description_raw 열까지 화면에 표시할지 선택합니다."
)

show_full_table = st.sidebar.checkbox(
    "전체 수집 결과 표시",
    value=False,
    help="체크하지 않으면 상위 30개만 미리보기로 표시합니다."
)


# =========================================================
# 10. 세션 상태 초기화
# =========================================================
if "crawled_df" not in st.session_state:
    st.session_state["crawled_df"] = None

if "crawl_config" not in st.session_state:
    st.session_state["crawl_config"] = None


# =========================================================
# 11. 크롤링 실행 영역
# =========================================================
st.subheader("1. 크롤링 실행")

btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
    crawl_btn = st.button("네이버 검색 결과 수집 실행", type="primary")

with btn_col2:
    reset_btn = st.button("수집 결과 초기화")


# =========================================================
# 12. 수집 결과 초기화
# =========================================================
if reset_btn:
    st.session_state["crawled_df"] = None
    st.session_state["crawl_config"] = None
    st.success("수집 결과가 초기화되었습니다.")
    st.stop()


# =========================================================
# 13. 현재 수집 조건 저장
# =========================================================
current_crawl_config = {
    "keyword": keyword,
    "search_type": search_type,
    "sort": sort,
    "analysis_target": analysis_target,
    "analysis_target_label": analysis_target_label,
    "start": start,
    "display": display,
    "max_results": max_results,
    "sleep_sec": sleep_sec,
}


# =========================================================
# 14. 크롤링 실행
# =========================================================
if crawl_btn:
    if not client_id or not client_secret:
        st.error("Client ID와 Client Secret이 필요합니다. 사이드바에서 API 키를 최초 등록해주세요.")
        st.stop()

    if not keyword.strip():
        st.error("검색어를 입력해주세요.")
        st.stop()

    try:
        with st.spinner("네이버 검색 API를 통해 데이터를 수집하고 있습니다."):
            df = crawl_naver_search(
                client_id=client_id,
                client_secret=client_secret,
                keyword=keyword.strip(),
                search_type=search_type,
                start=int(start),
                max_results=int(max_results),
                display=int(display),
                sort=sort,
                sleep_sec=float(sleep_sec),
                analysis_target=analysis_target,
            )

        st.session_state["crawled_df"] = df
        st.session_state["crawl_config"] = current_crawl_config

        st.success(f"수집 완료: {len(df):,}건")

    except Exception as e:
        st.error(f"수집 중 오류가 발생했습니다: {e}")
        st.stop()


# =========================================================
# 15. 수집 결과 확인
# =========================================================
df_result = st.session_state.get("crawled_df")

if df_result is None:
    st.info("검색 조건을 설정한 뒤 [네이버 검색 결과 수집 실행] 버튼을 눌러주세요.")
    st.stop()


# =========================================================
# 16. 검색 조건 변경 여부 안내
# =========================================================
saved_config = st.session_state.get("crawl_config")

if saved_config != current_crawl_config:
    st.warning(
        "검색 조건이 변경되었습니다. 변경된 조건을 반영하려면 [네이버 검색 결과 수집 실행] 버튼을 다시 눌러주세요."
    )


# =========================================================
# 17. 수집 요약
# =========================================================
st.subheader("2. 수집 요약")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("검색어", saved_config["keyword"])

with col2:
    st.metric("검색 대상", "뉴스" if saved_config["search_type"] == "news" else "블로그")

with col3:
    st.metric("분석 기준", saved_config["analysis_target_label"])

with col4:
    st.metric("수집 건수", f"{len(df_result):,}")

with col5:
    st.metric("시작 위치", saved_config["start"])

with col6:
    st.metric("정렬 기준", "정확도순" if saved_config["sort"] == "sim" else "날짜순")


# =========================================================
# 18. 수집 데이터 미리보기
# =========================================================
st.subheader("3. 수집 데이터 미리보기")

# 뉴스 데이터에는 pubDate, 블로그 데이터에는 postdate가 주로 존재합니다.
# 4번 영역과 동일하게 날짜 열이 가장 앞에 오도록 구성합니다.
preview_cols = [
    "pubDate",
    "postdate",
    "keyword",
    "search_type",
    "analysis_target",
    "rank",
    "title_clean",
    "description_clean",
    "text_for_analysis",
    "link",
]

# 원본 HTML 열 표시 옵션을 켠 경우 원본 열도 뒤쪽에 추가합니다.
if show_raw_columns:
    preview_cols += [
        "title_raw",
        "description_raw",
    ]

# 실제 df_result에 존재하는 열만 선택합니다.
available_preview_cols = [
    col for col in preview_cols
    if col in df_result.columns
]

if show_full_table:
    st.dataframe(
        df_result[available_preview_cols],
        use_container_width=True
    )
else:
    st.dataframe(
        df_result[available_preview_cols].head(30),
        use_container_width=True
    )


# =========================================================
# 19. 분석용 텍스트 열 확인
# =========================================================
st.subheader("4. 형태소 분석 및 감성분석용 텍스트")

st.write(
    f"""
    현재 분석 기준은 **{saved_config["analysis_target_label"]}** 입니다.  
    아래 `text_for_analysis` 열은 선택한 기준에 따라 생성된 분석용 텍스트입니다.
    """
)

# 18번 미리보기와 동일한 열 구조를 사용합니다.
# 단, 19번은 분석용 확인 목적이므로 원본 HTML 열은 제외합니다.
analysis_cols = [
    "pubDate",
    "postdate",
    "keyword",
    "search_type",
    "analysis_target",
    "rank",
    "title_clean",
    "description_clean",
    "text_for_analysis",
    "link",
]

# 실제 df_result에 존재하는 열만 선택합니다.
available_cols = [
    col for col in analysis_cols
    if col in df_result.columns
]

if show_full_table:
    st.dataframe(
        df_result[available_cols],
        use_container_width=True
    )
else:
    st.dataframe(
        df_result[available_cols].head(30),
        use_container_width=True
    )


# =========================================================
# 20. CSV 다운로드
# =========================================================
st.subheader("5. 수집 결과 다운로드")

today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_keyword = "".join(
    [ch for ch in saved_config["keyword"] if ch.isalnum() or ch in ["_", "-"]]
)

file_name = (
    f"naver_{saved_config['search_type']}_"
    f"{saved_config['analysis_target']}_"
    f"{safe_keyword}_{today_str}.csv"
)

csv_data = df_result.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="CSV 다운로드",
    data=csv_data,
    file_name=file_name,
    mime="text/csv"
)