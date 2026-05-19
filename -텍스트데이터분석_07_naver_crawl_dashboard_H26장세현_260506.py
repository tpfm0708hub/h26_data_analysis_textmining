import os
import importlib.util
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================================================
# 1. Configuration (설정 및 상수 관리)
# =========================================================
class AppConfig:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CRAWLER_PATH = os.path.join(BASE_DIR, "-텍스트데이터분석_07_naver_api_crawler_H26장세현_260506.py")
    API_KEY_FILE_PATH = os.path.join(BASE_DIR, "260506_naver_api_key_xor.dat")
    XOR_KEY = "TextMining26_Naver_API_Key_260506"
    
    ANALYSIS_TARGET_MAP = {
        "제목": "title",
        "본문/요약문": "description",
        "제목+본문/요약문": "title_description",
    }


# =========================================================
# 2. Core Services (비즈니스 및 도메인 로직)
# =========================================================
class ModuleLoader:
    """외부 파이썬 모듈을 동적으로 로드하는 유틸리티 클래스"""
    @staticmethod
    def load(module_alias: str, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"모듈 파일을 찾을 수 없습니다: {file_path}")
        spec = importlib.util.spec_from_file_location(module_alias, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class NaverAuthManager:
    """API 인증 키 관리를 전담하는 클래스"""
    def __init__(self, crawler_module):
        self.save_key = crawler_module.save_api_key_xor
        self.load_key = crawler_module.load_api_key_xor
        self.check_file = crawler_module.check_api_key_file

    def has_saved_key(self) -> bool:
        return self.check_file(AppConfig.API_KEY_FILE_PATH)

    def load_credentials(self) -> tuple:
        try:
            return self.load_key(load_path=AppConfig.API_KEY_FILE_PATH, xor_key=AppConfig.XOR_KEY)
        except Exception as e:
            st.sidebar.error(f"API 키 로드 오류: {e}")
            return None, None

    def save_credentials(self, client_id: str, client_secret: str):
        self.save_key(
            client_id=client_id,
            client_secret=client_secret,
            save_path=AppConfig.API_KEY_FILE_PATH,
            xor_key=AppConfig.XOR_KEY
        )

    def delete_credentials(self):
        if os.path.exists(AppConfig.API_KEY_FILE_PATH):
            os.remove(AppConfig.API_KEY_FILE_PATH)


class CrawlerService:
    """크롤링 실행을 전담하는 클래스"""
    def __init__(self, crawler_module):
        self.crawl_naver_search = crawler_module.crawl_naver_search

    def run_crawling(self, credentials: tuple, config: dict) -> pd.DataFrame:
        client_id, client_secret = credentials
        return self.crawl_naver_search(
            client_id=client_id,
            client_secret=client_secret,
            keyword=config["keyword"].strip(),
            search_type=config["search_type"],
            start=int(config["start"]),
            max_results=int(config["max_results"]),
            display=int(config["display"]),
            sort=config["sort"],
            sleep_sec=float(config["sleep_sec"]),
            analysis_target=config["analysis_target"],
        )


class SessionManager:
    """Streamlit 세션 상태를 캡슐화하여 관리하는 클래스"""
    @staticmethod
    def initialize():
        if "crawled_df" not in st.session_state:
            st.session_state["crawled_df"] = None
        if "crawl_config" not in st.session_state:
            st.session_state["crawl_config"] = None

    @staticmethod
    def clear():
        st.session_state["crawled_df"] = None
        st.session_state["crawl_config"] = None

    @staticmethod
    def update(df: pd.DataFrame, config: dict):
        st.session_state["crawled_df"] = df
        st.session_state["crawl_config"] = config

    @staticmethod
    def get_state() -> tuple:
        return st.session_state.get("crawled_df"), st.session_state.get("crawl_config")


# =========================================================
# 3. UI Layer (화면 렌더링 전담)
# =========================================================
class DashboardUI:
    @staticmethod
    def setup_page():
        st.set_page_config(page_title="네이버 검색 API 크롤링 대시보드", page_icon="📰", layout="wide")
        st.title("📰 네이버 검색 API 크롤링 대시보드")
        st.write("네이버 검색 API를 활용하여 뉴스 또는 블로그 검색 결과를 수집하고, 이후 분석에 활용할 수 있는 데이터프레임을 생성합니다.")

    @staticmethod
    def render_auth_sidebar(auth_manager: NaverAuthManager) -> tuple:
        st.sidebar.header("1. 네이버 API 인증 정보")
        client_id, client_secret = None, None
        key_exists = auth_manager.has_saved_key()

        if key_exists:
            client_id, client_secret = auth_manager.load_credentials()
            if client_id:
                st.sidebar.success("저장된 API 키를 불러왔습니다.")
        else:
            st.sidebar.warning("저장된 API 키 파일이 없습니다.")

        with st.sidebar.expander("API 키 최초 등록 / 재등록", expanded=not key_exists):
            input_id = st.text_input("Client ID", type="password")
            input_secret = st.text_input("Client Secret", type="password")
            if st.button("API 키 저장"):
                if input_id and input_secret:
                    try:
                        auth_manager.save_credentials(input_id, input_secret)
                        st.success("API 키가 저장되었습니다. 앱을 새로고침해주세요.")
                        st.stop()
                    except Exception as e:
                        st.error(f"저장 오류: {e}")
                else:
                    st.error("모두 입력해주세요.")

        with st.sidebar.expander("API 키 파일 관리"):
            st.write(f"저장 경로: `{AppConfig.API_KEY_FILE_PATH}`")
            if st.button("저장된 API 키 삭제"):
                auth_manager.delete_credentials()
                st.success("삭제 완료")
                st.stop()

        return client_id, client_secret

    @staticmethod
    def render_config_sidebar() -> dict:
        st.sidebar.header("2. 기본 검색 조건")
        keyword = st.sidebar.text_input("검색어", value="인공지능")
        search_type = st.sidebar.radio("검색 대상", options=["news", "blog"], format_func=lambda x: "뉴스" if x == "news" else "블로그")
        sort = st.sidebar.radio("정렬 기준", options=["sim", "date"], format_func=lambda x: "정확도순" if x == "sim" else "날짜순")

        st.sidebar.header("3. 분석 텍스트 기준")
        analysis_target_label = st.sidebar.radio("사용할 텍스트", options=list(AppConfig.ANALYSIS_TARGET_MAP.keys()), index=2)

        st.sidebar.header("4. 수집 범위 설정")
        start = st.sidebar.number_input("검색 시작 위치", min_value=1, max_value=1000, value=1, step=1)
        display = st.sidebar.slider("1회 요청 결과 수", min_value=10, max_value=100, value=10, step=10)
        max_results = st.sidebar.slider("최대 수집 개수", min_value=10, max_value=1000, value=100, step=10)
        sleep_sec = st.sidebar.slider("요청 간 대기 시간", min_value=0.0, max_value=3.0, value=0.2, step=0.1)

        st.sidebar.header("5. 분석 연계 옵션")
        show_raw_columns = st.sidebar.checkbox("원본 HTML 포함 열 표시", value=False)
        show_full_table = st.sidebar.checkbox("전체 수집 결과 표시", value=False)

        return {
            "keyword": keyword,
            "search_type": search_type,
            "sort": sort,
            "analysis_target_label": analysis_target_label,
            "analysis_target": AppConfig.ANALYSIS_TARGET_MAP[analysis_target_label],
            "start": start,
            "display": display,
            "max_results": max_results,
            "sleep_sec": sleep_sec,
            "show_raw_columns": show_raw_columns,
            "show_full_table": show_full_table
        }

    @staticmethod
    def render_results(df: pd.DataFrame, config: dict):
        st.subheader("2. 수집 요약")
        cols = st.columns(6)
        cols[0].metric("검색어", config["keyword"])
        cols[1].metric("검색 대상", "뉴스" if config["search_type"] == "news" else "블로그")
        cols[2].metric("분석 기준", config["analysis_target_label"])
        cols[3].metric("수집 건수", f"{len(df):,}")
        cols[4].metric("시작 위치", config["start"])
        cols[5].metric("정렬 기준", "정확도순" if config["sort"] == "sim" else "날짜순")

        preview_cols = ["pubDate", "postdate", "keyword", "search_type", "analysis_target", "rank", "title_clean", "description_clean", "text_for_analysis", "link"]
        if config["show_raw_columns"]:
            preview_cols += ["title_raw", "description_raw"]
        
        available_cols = [col for col in preview_cols if col in df.columns]

        st.subheader("3. 수집 데이터 미리보기")
        st.dataframe(df[available_cols] if config["show_full_table"] else df[available_cols].head(30), use_container_width=True)

        st.subheader("5. 수집 결과 다운로드")
        file_name = f"naver_{config['search_type']}_{config['analysis_target']}_{config['keyword']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        st.download_button("CSV 다운로드", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name=file_name, mime="text/csv")


# =========================================================
# 4. Main Application Flow (결합도 최소화된 제어부)
# =========================================================
def main():
    # 1. 초기 셋업
    DashboardUI.setup_page()
    SessionManager.initialize()

    try:
        crawler_module = ModuleLoader.load("naver_crawler", AppConfig.CRAWLER_PATH)
    except Exception as e:
        st.error(f"모듈 로드 실패: {e}")
        return

    # 2. 의존성 주입 (Dependency Injection)
    auth_manager = NaverAuthManager(crawler_module)
    crawler_service = CrawlerService(crawler_module)

    # 3. UI 렌더링 및 설정값 수집
    client_credentials = DashboardUI.render_auth_sidebar(auth_manager)
    current_config = DashboardUI.render_config_sidebar()

    # 4. 크롤링 액션 제어
    st.subheader("1. 크롤링 실행")
    col1, col2 = st.columns([1, 1])

    if col2.button("수집 결과 초기화"):
        SessionManager.clear()
        st.success("초기화되었습니다.")
        st.stop()

    if col1.button("네이버 검색 결과 수집 실행", type="primary"):
        if not all(client_credentials):
            st.error("API 키를 등록해주세요.")
            st.stop()
        if not current_config["keyword"].strip():
            st.error("검색어를 입력해주세요.")
            st.stop()

        try:
            with st.spinner("데이터를 수집하고 있습니다..."):
                df = crawler_service.run_crawling(client_credentials, current_config)
            SessionManager.update(df, current_config)
            st.success(f"수집 완료: {len(df):,}건")
        except Exception as e:
            st.error(f"수집 중 오류 발생: {e}")
            st.stop()

    # 5. 결과 렌더링
    df_result, saved_config = SessionManager.get_state()
    if df_result is not None:
        if saved_config != current_config:
            st.warning("조건이 변경되었습니다. 반영하려면 실행 버튼을 다시 눌러주세요.")
        DashboardUI.render_results(df_result, saved_config)
    else:
        st.info("검색 조건을 설정한 뒤 버튼을 눌러주세요.")

if __name__ == "__main__":
    main()