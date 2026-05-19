import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import List, Dict, Any, Tuple

import pandas as pd


# =========================================================
# 1. 입력 규칙 파싱 (Rule Parser)
# =========================================================
class RuleParser:
    """사용자 입력 문자열을 파이썬 객체(불용어 리스트, 변환어 딕셔너리)로 변환하는 클래스"""
    
    @staticmethod
    def parse_stopwords(stopword_text: str, max_words: int = 50) -> List[str]:
        if not stopword_text:
            return []
            
        raw_words = re.split(r"[,\n\r\t ]+", str(stopword_text))
        stop_words = []

        for word in raw_words:
            word = word.strip()
            if word and word not in stop_words:
                stop_words.append(word)
            if len(stop_words) >= max_words:
                break

        return stop_words

    @staticmethod
    def parse_replace_rules(replace_rule_text: str, max_rules: int = 100) -> Dict[str, str]:
        if not replace_rule_text or not str(replace_rule_text).strip():
            return {}

        raw_rules = re.split(r"[,\n\r]+", str(replace_rule_text).strip())
        replace_dict = {}

        for rule in raw_rules:
            rule = rule.strip()
            if not rule or "=" not in rule:
                continue

            before, after = map(str.strip, rule.split("=", 1))
            if before and after:
                replace_dict[before] = after
            if len(replace_dict) >= max_rules:
                break

        return replace_dict


# =========================================================
# 2. 텍스트 후처리 (Text Preprocessor)
# =========================================================
class TextPreprocessor:
    """형태소 분석 전후의 텍스트 정제 및 필터링을 담당하는 클래스"""
    
    @staticmethod
    def clean_korean_text(text: Any) -> str:
        if pd.isna(text):
            return ""
        text = re.sub(r"[^ㅏ-ㅣㄱ-ㅎ가-힣]+", " ", str(text))
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def process_tokens(tokens: List[str], replace_dict: Dict[str, str], stop_words: List[str], min_len: int) -> List[str]:
        """추출된 토큰에 대해 치환, 불용어 제거, 길이 제한을 적용합니다."""
        processed = []
        for token in tokens:
            # 1. 변환어 적용
            token = replace_dict.get(token, token)
            # 2. 불용어 및 길이 체크
            if token not in stop_words and len(token) >= min_len:
                processed.append(token)
        return processed


# =========================================================
# 3. 형태소 분석기 추상화 및 구현 (Strategy Pattern)
# =========================================================
class BaseAnalyzer(ABC):
    """모든 형태소 분석기가 구현해야 하는 공통 인터페이스"""
    
    @abstractmethod
    def extract_tokens(self, text: str, selected_pos_kor: List[str]) -> List[str]:
        """주어진 텍스트에서 조건에 맞는 형태소 리스트를 추출하여 반환합니다."""
        pass


class OktAnalyzer(BaseAnalyzer):
    def __init__(self):
        from konlpy.tag import Okt
        self.tokenizer = Okt()
        self.pos_map = {
            "명사": ["Noun"],
            "동사": ["Verb"],
            "형용사": ["Adjective"],
        }

    def _get_tags(self, selected_pos_kor: List[str]) -> List[str]:
        tags = []
        for pos in selected_pos_kor:
            tags.extend(self.pos_map.get(pos, []))
        return tags

    def extract_tokens(self, text: str, selected_pos_kor: List[str]) -> List[str]:
        clean_text = TextPreprocessor.clean_korean_text(text)
        if not clean_text:
            return []

        target_tags = self._get_tags(selected_pos_kor)
        tagged_tokens = self.tokenizer.pos(clean_text, stem=True)
        
        return [word for word, tag in tagged_tokens if tag in target_tags]


class KiwiAnalyzer(BaseAnalyzer):
    def __init__(self):
        from kiwipiepy import Kiwi
        self.tokenizer = Kiwi()
        self.pos_map = {
            "명사": ["NNG", "NNP", "NP"],
            "동사": ["VV"],
            "형용사": ["VA"],
        }

    def _get_tags(self, selected_pos_kor: List[str]) -> List[str]:
        tags = []
        for pos in selected_pos_kor:
            tags.extend(self.pos_map.get(pos, []))
        return tags

    def extract_tokens(self, text: str, selected_pos_kor: List[str]) -> List[str]:
        clean_text = TextPreprocessor.clean_korean_text(text)
        if not clean_text:
            return []

        target_tags = self._get_tags(selected_pos_kor)
        tagged_tokens = self.tokenizer.tokenize(clean_text)
        
        return [token.form for token in tagged_tokens if token.tag in target_tags]


class AnalyzerFactory:
    """이름에 따라 적절한 분석기 인스턴스를 생성하여 반환합니다."""
    @staticmethod
    def create(analyzer_name: str) -> BaseAnalyzer:
        if analyzer_name == "konlpy-Okt":
            return OktAnalyzer()
        elif analyzer_name == "kiwipiepy":
            return KiwiAnalyzer()
        else:
            raise ValueError(f"지원하지 않는 형태소 분석기입니다: {analyzer_name}")


# =========================================================
# 4. 분석 파이프라인 (Coordinator / Pipeline)
# =========================================================
class TextAnalysisPipeline:
    """데이터프레임 입력부터 최종 분석 결과 생성까지의 흐름을 제어합니다."""
    
    def __init__(self, analyzer_name: str):
        self.analyzer = AnalyzerFactory.create(analyzer_name)

    def _make_text_series(self, df: pd.DataFrame, selected_columns: List[str]) -> pd.Series:
        if not selected_columns:
            return pd.Series([], dtype=str)
        text_df = df[selected_columns].fillna("").astype(str)
        return text_df.apply(lambda row: " ".join(row.values), axis=1)

    def run(
        self,
        df: pd.DataFrame,
        selected_columns: List[str],
        selected_pos_kor: List[str] = None,
        stop_words: List[str] = None,
        replace_dict: Dict[str, str] = None,
        min_len: int = 2,
        top_n: int = 50
    ) -> Dict[str, Any]:
        
        selected_pos_kor = selected_pos_kor or ["명사"]
        stop_words = stop_words or []
        replace_dict = replace_dict or {}

        texts = self._make_text_series(df, selected_columns)
        
        all_tokens = []
        row_tokens_list = []

        # 각 행(row)별로 파이프라인 실행
        for text in texts:
            # 1. 형태소 추출 (내부적으로 텍스트 정제 포함)
            raw_tokens = self.analyzer.extract_tokens(text, selected_pos_kor)
            
            # 2. 토큰 후처리 (치환, 불용어, 길이 제한)
            processed_tokens = TextPreprocessor.process_tokens(
                raw_tokens, replace_dict, stop_words, min_len
            )
            
            row_tokens_list.append(processed_tokens)
            all_tokens.extend(processed_tokens)

        # 결과 집계
        counter = Counter(all_tokens)
        freq_df = pd.DataFrame(counter.most_common(top_n), columns=["word", "count"])

        result_df = df.copy()
        result_df["분석대상텍스트"] = texts
        result_df["tokens"] = row_tokens_list

        return {
            "freq_df": freq_df,
            "counter": counter,
            "result_df": result_df,
            "total_token_count": len(all_tokens),
            "unique_token_count": len(counter),
        }

# =========================================================
# (기존 호환성을 위한 래퍼 함수)
# =========================================================
def run_text_analysis(df, selected_columns, analyzer_name="kiwipiepy", **kwargs):
    """
    기존 코드 인터페이스를 유지하기 위한 래퍼(Wrapper) 함수입니다.
    외부 모듈에서는 이 함수만 호출하면 됩니다.
    """
    pipeline = TextAnalysisPipeline(analyzer_name=analyzer_name)
    return pipeline.run(df, selected_columns, **kwargs)