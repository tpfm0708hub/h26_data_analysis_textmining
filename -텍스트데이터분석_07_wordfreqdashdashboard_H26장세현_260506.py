import os
import importlib.util
from io import BytesIO

import pandas as pd
import streamlit as st
from matplotlib import font_manager, rc

# =========================================================
# 1. System Setup (고응집도: 시스템 및 환경 설정)
# =========================================================
class SystemSetup:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MYLIB_DIR = os.path.join(BASE_DIR, "mylib")
    DEFAULT_DATA_PATH = r"D:\Lecture\TextMining26\data\daum_movie_review.csv"
    FONT_PATH = "c:/Windows/Fonts/malgun.ttf"

    @staticmethod
    def load_module_from_path(module_alias, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"모듈 파일을 찾을 수 없습니다: {file_path}")
        spec = importlib.util.spec_from_file_location(module_alias, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @classmethod
    def initialize_modules(cls):
        analyzer_path = os.path.join(cls.MYLIB_DIR, "-텍스트데이터분석_07_myTextAnalyzer_H26장세현_260506.py")
        visualizer_path = os.path.join(cls.MYLIB_DIR, "-텍스트데이터분석_07_myStramlitVisualizer_H26장세현_260506.py")
        
        myTextAnalyzer = cls.load_module_from_path("myTextAnalyzer", analyzer_path)
        myVisualizer = cls.load_module_from_path("myVisualizer", visualizer_path)
        
        return myTextAnalyzer, myVisualizer

    @classmethod
    def setup_font(cls):
        if os.path.exists(cls.FONT_PATH):
            font_name = font_manager.FontProperties(fname=cls.FONT_PATH).get_name()
            rc("font", family=font_name)


# =========================================================
# 2. Data Management (고응집도: 데이터 로딩 및 전처리)
# =========================================================
class DataManager:
    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_default(file_path):
        try:
            return pd.read_csv(file_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="cp949")

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_uploaded(file_name, file_bytes):
        file_ext = file_name.lower().split(".")[-1]
        file_buffer = BytesIO(file_bytes)

        if file_ext == "csv":
            try:
                return pd.read_csv(file_buffer, encoding="utf-8-sig")
            except UnicodeDecodeError:
                file_buffer.seek(0)
                return pd.read_csv(file_buffer, encoding="cp949")
        elif file_ext in ["xlsx", "xls"]:
            return pd.read_excel(file_buffer)
        else:
            raise ValueError("csv, xlsx, xls 파일만 업로드할 수 있습니다.")


# =========================================================
# 3. Analysis Service (고응집도: 분석 비즈니스 로직)
# =========================================================
class TextAnalyzerService:
    def __init__(self, analyzer_module):
        # 모듈 레벨의 래퍼(Wrapper) 함수
        self.run_text_analysis = analyzer_module.run_text_analysis
        
        # RuleParser 클래스를 명시적으로 참조하여 함수 연결
        self.parse_stopwords = analyzer_module.RuleParser.parse_stopwords
        self.parse_replace_rules = analyzer_module.RuleParser.parse_replace_rules

    @st.cache_data(show_spinner=True)
    def analyze(_self, df, config):
        """딕셔너리 형태의 config를 받아 독립적으로 분석 수행 (결합도 최소화)"""
        return _self.run_text_analysis(
            df=df,
            selected_columns=config["selected_columns"],
            analyzer_name=config["analyzer_name"],
            selected_pos_kor=config["selected_pos_kor"],
            stop_words=config["stop_words"],
            replace_dict=config["replace_dict"],
            min_len=config["min_len"],
            top_n=config["top_n"],
        )


# =========================================================
# 4. UI Manager (고응집도: 화면 렌더링)
# =========================================================
class UIManager:
    def __init__(self, visualizer_module):
        # 의존성 주입: 폰트 경로를 넘겨주어 TextVisualizer 인스턴스 생성
        self.visualizer = visualizer_module.TextVisualizer(font_path=SystemSetup.FONT_PATH)
        
        # 인스턴스 메서드 연결
        self.draw_hbar = self.visualizer.draw_hbar
        self.draw_wordcloud = self.visualizer.draw_wordcloud
        
        # 정적(static) 메서드 연결
        self.fig_to_png_bytes = visualizer_module.TextVisualizer.fig_to_png_bytes

    @staticmethod
    def render_header():
        st.set_page_config(page_title="형태소 빈도분석 대시보드", page_icon="📊", layout="wide")
        st.title("📊 한국어 형태소 빈도분석 대시보드")
        st.write("기본 데이터 또는 사용자가 업로드한 CSV·Excel 파일을 대상으로 한국어 형태소 빈도분석, 수평 막대그래프, 워드클라우드 생성을 수행합니다.")

    @staticmethod
    def render_sidebar_data_selection():
        st.sidebar.header("1. 데이터 선택")
        data_source = st.sidebar.radio("분석 데이터 선택", options=["기본 데이터 사용", "직접 파일 업로드"], index=0)
        uploaded_file = None
        if data_source == "직접 파일 업로드":
            uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 파일 업로드", type=["csv", "xlsx", "xls"])
        return data_source, uploaded_file

    @staticmethod
    def render_sidebar_analysis_config(df):
        st.sidebar.header("2. 분석 열 선택")
        all_columns = df.columns.tolist()
        default_columns = ["review"] if "review" in all_columns else []
        selected_columns = st.sidebar.multiselect("형태소 분석을 진행할 열 선택", options=all_columns, default=default_columns)

        st.sidebar.header("3. 분석 조건")
        analyzer_name = st.sidebar.radio("형태소 분석 도구 선택", options=["kiwipiepy", "konlpy-Okt"], index=0)
        top_n = st.sidebar.slider("빈도표 출력 단어 수", min_value=5, max_value=200, value=50, step=5)
        bar_top_n = st.sidebar.slider("막대그래프 표시 단어 수", min_value=5, max_value=50, value=20, step=5)
        min_len = st.sidebar.slider("최소 글자 수", min_value=1, max_value=10, value=2, step=1)

        return {
            "selected_columns": selected_columns,
            "analyzer_name": analyzer_name,
            "top_n": top_n,
            "bar_top_n": bar_top_n,
            "min_len": min_len
        }

    @staticmethod
    def render_main_configs(text_analyzer_service):
        st.subheader("2. 분석 품사 선택")
        pos_col1, pos_col2, pos_col3 = st.columns(3)
        with pos_col1: use_noun = st.toggle("명사", value=True)
        with pos_col2: use_verb = st.toggle("동사", value=False)
        with pos_col3: use_adjective = st.toggle("형용사", value=False)
        
        selected_pos_kor = []
        if use_noun: selected_pos_kor.append("명사")
        if use_verb: selected_pos_kor.append("동사")
        if use_adjective: selected_pos_kor.append("형용사")

        st.subheader("3. 불용어 입력")
        default_stopwords = "정말, 진짜, 하는, 입니다, 정도, 그냥, 있는, 봤어요"
        stopword_text = st.text_area("제외할 단어를 입력해주세요. (최대 50개)", value=default_stopwords, height=120)
        stop_words = text_analyzer_service.parse_stopwords(stopword_text, max_words=50)

        st.subheader("4. 변환어 규칙 입력")
        default_replace_rules = "재밌다=재미있다\n재미있다=재미있다\n봤다=보다\n봤어요=보다\n영화관=극장"
        replace_rule_text = st.text_area("변환어 규칙을 입력해주세요.", value=default_replace_rules, height=140)
        replace_dict = text_analyzer_service.parse_replace_rules(replace_rule_text, max_rules=100)

        return selected_pos_kor, stop_words, replace_dict

    def render_results(self, analysis_result, config):
        freq_df = analysis_result["freq_df"]
        counter = analysis_result["counter"]
        
        st.subheader("6. 분석 요약")
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        sum_col1.metric("분석기", config["analyzer_name"])
        sum_col2.metric("전체 토큰 수", f"{analysis_result['total_token_count']:,}")
        sum_col3.metric("고유 토큰 수", f"{analysis_result['unique_token_count']:,}")
        sum_col4.metric("선택 품사", ", ".join(config["selected_pos_kor"]))

        st.subheader("7. 형태소 빈도분석 결과")
        if freq_df.empty:
            st.warning("분석 결과가 비어 있습니다. 조건을 조정해주세요.")
            return

        st.dataframe(freq_df, use_container_width=True)
        st.download_button("결과 CSV 다운로드", data=freq_df.to_csv(index=False, encoding="utf-8-sig"), file_name="word_frequency_result.csv", mime="text/csv")

        st.subheader("8. 시각화 결과")
        tab1, tab2 = st.tabs(["수평 막대그래프", "워드클라우드"])
        with tab1:
            fig_bar = self.draw_hbar(freq_df=freq_df, title="형태소 빈도분석 수평 막대그래프", top_n=config["bar_top_n"])
            st.pyplot(fig_bar)
            st.download_button("막대그래프 다운로드", data=self.fig_to_png_bytes(fig_bar), file_name="bargraph.png", mime="image/png")
        with tab2:
            fig_wc = self.draw_wordcloud(counter=counter, max_words=config["top_n"], background_color="ivory")
            st.pyplot(fig_wc)
            st.download_button("워드클라우드 다운로드", data=self.fig_to_png_bytes(fig_wc), file_name="wordcloud.png", mime="image/png")


# =========================================================
# 5. Main Application Flow (결합도 최소화된 파이프라인)
# =========================================================
def main():
    # 1. 환경 및 모듈 초기화
    UIManager.render_header()
    SystemSetup.setup_font()
    
    try:
        analyzer_mod, visualizer_mod = SystemSetup.initialize_modules()
    except Exception as e:
        st.error(f"모듈 로드 실패: {e}")
        return

    text_service = TextAnalyzerService(analyzer_mod)
    ui_manager = UIManager(visualizer_mod)

    # 2. 데이터 로드
    data_source, uploaded_file = UIManager.render_sidebar_data_selection()
    
    try:
        if data_source == "기본 데이터 사용":
            df = DataManager.load_default(SystemSetup.DEFAULT_DATA_PATH)
            file_name = os.path.basename(SystemSetup.DEFAULT_DATA_PATH)
        else:
            if uploaded_file is None:
                st.info("파일을 업로드해주세요.")
                return
            df = DataManager.load_uploaded(uploaded_file.name, uploaded_file.getvalue())
            file_name = uploaded_file.name
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return

    # 3. 설정 값 취합 (Config Object)
    sidebar_config = UIManager.render_sidebar_analysis_config(df)
    if not sidebar_config["selected_columns"]:
        st.warning("분석할 열을 최소 1개 이상 선택해주세요.")
        return

    st.subheader("1. 데이터 미리보기")
    st.dataframe(df.head(10), use_container_width=True)

    pos_kor, stopwords, replace_rules = UIManager.render_main_configs(text_service)
    
    if not pos_kor:
        st.warning("분석 품사를 최소 1개 이상 선택해주세요.")
        return

    # 단일 Config 딕셔너리로 결합 (의존성 주입용)
    current_config = {
        **sidebar_config,
        "selected_pos_kor": pos_kor,
        "stop_words": stopwords,
        "replace_dict": replace_rules,
        "file_name": file_name
    }

    # 4. 실행 및 상태 관리
    st.subheader("5. 형태소 분석 실행")
    btn_col1, btn_col2 = st.columns([1, 1])
    
    if btn_col2.button("분석 결과 초기화"):
        st.session_state.clear()
        st.success("초기화되었습니다.")
        st.stop()

    if btn_col1.button("형태소 분석 실행", type="primary"):
        try:
            result = text_service.analyze(df, current_config)
            st.session_state["analysis_result"] = result
            st.session_state["analysis_config"] = current_config
            st.success("분석이 완료되었습니다.")
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
            return

    # 5. 결과 렌더링
    if "analysis_result" in st.session_state:
        if st.session_state["analysis_config"] != current_config:
            st.warning("분석 조건이 변경되었습니다. 변경된 조건을 반영하려면 실행 버튼을 다시 눌러주세요.")
        
        ui_manager.render_results(
            analysis_result=st.session_state["analysis_result"], 
            config=st.session_state["analysis_config"]
        )

if __name__ == "__main__":
    main()
