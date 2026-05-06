import io
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# =========================================================
# 1. 수평 막대그래프 생성 함수
# =========================================================
def draw_hbar(freq_df, title="형태소 빈도분석 결과", top_n=20):
    """
    형태소 빈도분석 결과를 수평 막대그래프로 시각화합니다.
    """
    plot_df = freq_df.head(top_n).copy()

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.barh(
        plot_df["word"][::-1],
        plot_df["count"][::-1]
    )

    ax.set_title(title)
    ax.set_xlabel("빈도수")
    ax.set_ylabel("키워드")

    plt.tight_layout()

    return fig


# =========================================================
# 2. 워드클라우드 생성 함수
# =========================================================
def draw_wordcloud(
    counter,
    font_path="c:/Windows/Fonts/malgun.ttf",
    width=900,
    height=600,
    max_words=100,
    background_color="ivory",
):
    """
    Counter 객체를 기반으로 워드클라우드를 생성합니다.
    """
    wc = WordCloud(
        font_path=font_path,
        width=width,
        height=height,
        max_words=max_words,
        background_color=background_color,
    )

    wc = wc.generate_from_frequencies(dict(counter))

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(wc)
    ax.axis("off")

    plt.tight_layout()

    return fig


# =========================================================
# 3. matplotlib figure를 PNG bytes로 변환
# =========================================================
def fig_to_png_bytes(fig):
    """
    Streamlit 다운로드 버튼에서 사용할 수 있도록
    matplotlib figure 객체를 PNG 이미지 bytes로 변환합니다.
    """
    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=300,
        bbox_inches="tight"
    )

    buffer.seek(0)

    return buffer
