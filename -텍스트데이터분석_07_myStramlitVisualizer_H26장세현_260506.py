import io
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
from typing import Optional

class TextVisualizer:
    """
    텍스트 분석 결과 시각화를 전담하는 클래스
    (응집도는 높이고, 외부 환경에 대한 결합도는 낮춤)
    """
    def __init__(self, font_path: str):
        """
        초기화 시 폰트 경로를 외부에서 주입받습니다 (Dependency Injection).
        특정 OS나 파일 경로에 종속되지 않게 합니다.
        """
        self.font_path = font_path

    def draw_hbar(
        self, 
        freq_df: pd.DataFrame, 
        title: str = "형태소 빈도분석 결과", 
        top_n: int = 20, 
        figsize: tuple = (10, 7)
    ) -> plt.Figure:
        """
        형태소 빈도분석 결과를 수평 막대그래프로 시각화합니다.
        """
        if freq_df.empty:
            raise ValueError("시각화할 데이터가 없습니다 (빈 DataFrame).")

        plot_df = freq_df.head(top_n).copy()
        
        # 내부 상태에 의존하지 않고 전달받은 파라미터로만 그려냅니다.
        fig, ax = plt.subplots(figsize=figsize)

        ax.barh(
            plot_df["word"][::-1],
            plot_df["count"][::-1]
        )

        ax.set_title(title)
        ax.set_xlabel("빈도수")
        ax.set_ylabel("키워드")

        plt.tight_layout()
        return fig

    def draw_wordcloud(
        self,
        counter: Counter,
        width: int = 900,
        height: int = 600,
        max_words: int = 100,
        background_color: str = "ivory",
        figsize: tuple = (10, 7)
    ) -> plt.Figure:
        """
        Counter 객체를 기반으로 워드클라우드를 생성합니다.
        """
        if not counter:
            raise ValueError("워드클라우드를 생성할 데이터가 없습니다 (빈 Counter).")

        # 생성자에서 주입받은 폰트 경로(self.font_path)를 사용합니다.
        wc = WordCloud(
            font_path=self.font_path,
            width=width,
            height=height,
            max_words=max_words,
            background_color=background_color,
        )

        wc = wc.generate_from_frequencies(dict(counter))

        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        plt.tight_layout()
        return fig

    @staticmethod
    def fig_to_png_bytes(fig: plt.Figure) -> io.BytesIO:
        """
        matplotlib figure 객체를 PNG 이미지 bytes로 변환합니다.
        클래스의 상태(self)를 사용하지 않는 순수 유틸리티 기능이므로 
        정적 메서드(staticmethod)로 선언하여 결합도를 낮춥니다.
        """
        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        buffer.seek(0)
        
        # 메모리 누수 방지를 위해 figure를 명시적으로 닫아줍니다.
        plt.close(fig) 

        return buffer