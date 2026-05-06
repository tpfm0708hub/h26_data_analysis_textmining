import re
from collections import Counter

import pandas as pd


# =========================================================
# 1. 텍스트 정제 함수
# =========================================================
def clean_korean_text(text):
    """
    입력된 텍스트에서 한글만 남기고 나머지는 공백으로 변환합니다.
    """
    if pd.isna(text):
        return ""

    text = str(text)
    text = re.sub(r"[^ㅏ-ㅣㄱ-ㅎ가-힣]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# 2. 불용어 문자열 처리 함수
# =========================================================
def parse_stopwords(stopword_text, max_words=50):
    """
    사용자가 입력한 불용어 문자열을 리스트로 변환합니다.

    입력 예시:
    정말, 진짜, 그냥
    또는
    정말
    진짜
    그냥
    """
    if stopword_text is None:
        return []

    stopword_text = str(stopword_text)

    raw_words = re.split(r"[,\n\r\t ]+", stopword_text)
    stop_words = []

    for word in raw_words:
        word = word.strip()
        if word and word not in stop_words:
            stop_words.append(word)

    return stop_words[:max_words]


# =========================================================
# 3. 품사 선택값 변환
# =========================================================
def get_okt_pos_list(selected_pos_kor):
    """
    화면에서 선택한 한국어 품사명을 Okt 품사명으로 변환합니다.
    """
    pos_map = {
        "명사": "Noun",
        "동사": "Verb",
        "형용사": "Adjective",
    }

    return [pos_map[pos] for pos in selected_pos_kor if pos in pos_map]


def get_kiwi_pos_list(selected_pos_kor):
    """
    화면에서 선택한 한국어 품사명을 Kiwi 품사 태그로 변환합니다.

    Kiwi 주요 품사:
    - 일반명사: NNG
    - 고유명사: NNP
    - 대명사: NP
    - 동사: VV
    - 형용사: VA
    """
    pos_map = {
        "명사": ["NNG", "NNP", "NP"],
        "동사": ["VV"],
        "형용사": ["VA"],
    }

    result = []
    for pos in selected_pos_kor:
        result.extend(pos_map.get(pos, []))

    return result


# =========================================================
# 4. Okt 형태소 분석
# =========================================================
def analyze_with_okt(texts, selected_pos_kor, stop_words=None, min_len=2, stem=True):
    """
    Okt를 이용해 형태소 분석을 수행합니다.
    """
    from konlpy.tag import Okt

    stop_words = stop_words or []
    okt_pos_list = get_okt_pos_list(selected_pos_kor)

    tokenizer = Okt()
    all_tokens = []
    row_tokens = []

    for text in texts:
        clean_text = clean_korean_text(text)

        tagged_tokens = tokenizer.pos(clean_text, stem=stem)

        tokens = [
            word
            for word, tag in tagged_tokens
            if tag in okt_pos_list
            and word not in stop_words
            and len(word) >= min_len
        ]

        row_tokens.append(tokens)
        all_tokens.extend(tokens)

    return all_tokens, row_tokens


# =========================================================
# 5. Kiwi 형태소 분석
# =========================================================
def analyze_with_kiwi(texts, selected_pos_kor, stop_words=None, min_len=2):
    """
    kiwipiepy를 이용해 형태소 분석을 수행합니다.
    """
    from kiwipiepy import Kiwi

    stop_words = stop_words or []
    kiwi_pos_list = get_kiwi_pos_list(selected_pos_kor)

    kiwi = Kiwi()
    all_tokens = []
    row_tokens = []

    for text in texts:
        clean_text = clean_korean_text(text)

        tagged_tokens = kiwi.tokenize(clean_text)

        tokens = [
            token.form
            for token in tagged_tokens
            if token.tag in kiwi_pos_list
            and token.form not in stop_words
            and len(token.form) >= min_len
        ]

        row_tokens.append(tokens)
        all_tokens.extend(tokens)

    return all_tokens, row_tokens


# =========================================================
# 6. 선택 열 결합
# =========================================================
def make_text_series(df, selected_columns):
    """
    사용자가 선택한 여러 열을 하나의 분석 대상 텍스트로 결합합니다.
    """
    if not selected_columns:
        return pd.Series([], dtype=str)

    text_df = df[selected_columns].fillna("").astype(str)

    combined_text = text_df.apply(
        lambda row: " ".join(row.values),
        axis=1
    )

    return combined_text


# =========================================================
# 7. 형태소 분석 통합 실행 함수
# =========================================================
def run_text_analysis(
    df,
    selected_columns,
    analyzer_name="kiwipiepy",
    selected_pos_kor=None,
    stop_words=None,
    min_len=2,
    top_n=50,
):
    """
    데이터프레임의 선택 열에 대해 형태소 분석을 수행하고
    빈도분석 결과 데이터프레임을 반환합니다.
    """
    selected_pos_kor = selected_pos_kor or ["명사"]
    stop_words = stop_words or []

    texts = make_text_series(df, selected_columns)

    if analyzer_name == "konlpy-Okt":
        all_tokens, row_tokens = analyze_with_okt(
            texts=texts,
            selected_pos_kor=selected_pos_kor,
            stop_words=stop_words,
            min_len=min_len,
            stem=True,
        )

    elif analyzer_name == "kiwipiepy":
        all_tokens, row_tokens = analyze_with_kiwi(
            texts=texts,
            selected_pos_kor=selected_pos_kor,
            stop_words=stop_words,
            min_len=min_len,
        )

    else:
        raise ValueError("지원하지 않는 형태소 분석기입니다.")

    counter = Counter(all_tokens)

    freq_df = pd.DataFrame(
        counter.most_common(top_n),
        columns=["word", "count"]
    )

    result_df = df.copy()
    result_df["분석대상텍스트"] = texts
    result_df["tokens"] = row_tokens

    return {
        "freq_df": freq_df,
        "counter": counter,
        "result_df": result_df,
        "total_token_count": len(all_tokens),
        "unique_token_count": len(counter),
    }