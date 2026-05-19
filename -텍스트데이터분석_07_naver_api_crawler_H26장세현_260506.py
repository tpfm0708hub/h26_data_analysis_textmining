import urllib.request
import urllib.parse
import json
import re
import html
import time
import base64
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pandas as pd


# =========================================================
# 1. Security & Auth (고응집도: 암호화 및 키 관리)
# =========================================================
class CryptoManager:
    """XOR 기반 데이터 암/복호화 및 API 키 파일 입출력을 담당합니다."""
    
    @staticmethod
    def _xor_bytes(data_bytes: bytes, key_bytes: bytes) -> bytes:
        result = bytearray()
        for i, b in enumerate(data_bytes):
            result.append(b ^ key_bytes[i % len(key_bytes)])
        return bytes(result)

    @classmethod
    def save_api_key(cls, client_id: str, client_secret: str, save_path: str, xor_key: str) -> str:
        if not client_id or not client_secret:
            raise ValueError("Client ID와 Client Secret을 모두 입력해야 합니다.")
        if not xor_key:
            raise ValueError("XOR key가 비어 있습니다.")

        key_data = {"client_id": client_id, "client_secret": client_secret}
        json_str = json.dumps(key_data, ensure_ascii=False)
        
        encrypted_bytes = cls._xor_bytes(json_str.encode("utf-8"), xor_key.encode("utf-8"))
        encrypted_text = base64.b64encode(encrypted_bytes).decode("utf-8")

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(encrypted_text)
        return save_path

    @classmethod
    def load_api_key(cls, load_path: str, xor_key: str) -> Tuple[str, str]:
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"API 키 파일을 찾을 수 없습니다: {load_path}")
        if not xor_key:
            raise ValueError("XOR key가 비어 있습니다.")

        with open(load_path, "r", encoding="utf-8") as f:
            encrypted_text = f.read().strip()

        encrypted_bytes = base64.b64decode(encrypted_text.encode("utf-8"))
        decrypted_bytes = cls._xor_bytes(encrypted_bytes, xor_key.encode("utf-8"))
        
        key_data = json.loads(decrypted_bytes.decode("utf-8"))
        return key_data["client_id"], key_data["client_secret"]

    @staticmethod
    def check_file(key_file_path: str) -> bool:
        return os.path.exists(key_file_path)


# =========================================================
# 2. Text Processing (고응집도: 텍스트 정제 전담)
# =========================================================
class TextProcessor:
    """HTML 태그 제거 및 텍스트 정제 로직을 제공하는 유틸리티 클래스입니다."""
    
    @staticmethod
    def clean_html(text: Optional[str]) -> str:
        if not text:
            return ""
        text = str(text)
        text = re.sub(r"<.*?>", "", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def make_analysis_text(cls, title_clean: str, description_clean: str, analysis_target: str) -> str:
        if analysis_target == "title":
            text = title_clean
        elif analysis_target == "description":
            text = description_clean
        else:
            text = f"{title_clean} {description_clean}"
            
        return re.sub(r"\s+", " ", text).strip()


# =========================================================
# 3. Network Client (고응집도: API 통신 전담)
# =========================================================
class NaverAPIClient:
    """네이버 검색 API와의 HTTP 통신만을 책임집니다. (크롤링 로직 모름)"""
    
    def __init__(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            raise ValueError("Client ID와 Client Secret이 필요합니다.")
        self.client_id = client_id
        self.client_secret = client_secret

    def search(self, keyword: str, search_type: str, start: int, display: int, sort: str) -> dict:
        enc_keyword = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/{search_type}.json?query={enc_keyword}&start={start}&display={display}&sort={sort}"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.client_id)
        request.add_header("X-Naver-Client-Secret", self.client_secret)

        try:
            response = urllib.request.urlopen(request)
            if response.getcode() != 200:
                raise RuntimeError(f"네이버 API 요청 실패: HTTP {response.getcode()}")
            return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"API 호출 중 오류 발생: {e}")


# =========================================================
# 4. Data Normalizer (고응집도: 데이터 구조 변환)
# =========================================================
class ItemNormalizer:
    """API 응답 Item(dict)을 DataFrame 규격에 맞는 Row(dict)로 변환합니다."""
    
    @staticmethod
    def normalize(items: List[dict], keyword: str, search_type: str, start_rank: int, analysis_target: str) -> List[dict]:
        normalized_rows = []
        for idx, item in enumerate(items):
            title_raw = item.get("title", "")
            description_raw = item.get("description", "")

            title_clean = TextProcessor.clean_html(title_raw)
            description_clean = TextProcessor.clean_html(description_raw)
            text_for_analysis = TextProcessor.make_analysis_text(title_clean, description_clean, analysis_target)

            row = {
                "keyword": keyword,
                "search_type": search_type,
                "analysis_target": analysis_target,
                "rank": start_rank + idx,
                "title_raw": title_raw,
                "title_clean": title_clean,
                "description_raw": description_raw,
                "description_clean": description_clean,
                "text_for_analysis": text_for_analysis,
                "link": item.get("link", ""),
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            if search_type == "news":
                row["originallink"] = item.get("originallink", "")
                row["pubDate"] = item.get("pubDate", "")
            elif search_type == "blog":
                row["bloggername"] = TextProcessor.clean_html(item.get("bloggername", ""))
                row["bloggerlink"] = item.get("bloggerlink", "")
                row["postdate"] = item.get("postdate", "")

            normalized_rows.append(row)
        return normalized_rows


# =========================================================
# 5. Crawler / Pipeline (고응집도: 흐름 제어, 저결합도: 의존성 주입)
# =========================================================
class NaverSearchCrawler:
    """수집 로직(반복문, 딜레이, 제한 등)을 오케스트레이션합니다."""
    
    def __init__(self, api_client: NaverAPIClient, normalizer=ItemNormalizer):
        # 의존성을 외부에서 주입받습니다 (Dependency Injection)
        self.api_client = api_client
        self.normalizer = normalizer

    def crawl(
        self, 
        keyword: str, 
        search_type: str = "news", 
        start: int = 1, 
        max_results: int = 100, 
        display: int = 10, 
        sort: str = "sim", 
        sleep_sec: float = 0.2, 
        max_start_limit: int = 1000, 
        analysis_target: str = "title_description"
    ) -> pd.DataFrame:
        
        self._validate_params(keyword, search_type, start, display, max_results, analysis_target)

        all_rows = []
        current_start = start
        collected_count = 0

        while collected_count < max_results:
            if current_start > max_start_limit:
                break

            remain_count = max_results - collected_count
            current_display = min(display, remain_count)

            # 1. API 호출 (Network 계층에 위임)
            py_data = self.api_client.search(keyword, search_type, current_start, current_display, sort)
            items = py_data.get("items", [])
            if not items:
                break

            # 2. 데이터 정규화 (Normalizer 계층에 위임)
            normalized_rows = self.normalizer.normalize(
                items, keyword, search_type, current_start, analysis_target
            )
            all_rows.extend(normalized_rows)

            item_count = len(items)
            collected_count += item_count
            current_start += item_count

            if item_count < current_display:
                break

            time.sleep(sleep_sec)

        return pd.DataFrame(all_rows)

    def _validate_params(self, keyword, search_type, start, display, max_results, analysis_target):
        if not keyword or not str(keyword).strip():
            raise ValueError("검색어를 입력해야 합니다.")
        if search_type not in ["news", "blog"]:
            raise ValueError("검색 대상은 news 또는 blog만 가능합니다.")
        if analysis_target not in ["title", "description", "title_description"]:
            raise ValueError("analysis_target은 title, description, title_description 중 하나여야 합니다.")
        if start < 1 or display < 1 or max_results < 1:
            raise ValueError("start, display, max_results는 1 이상이어야 합니다.")


# =========================================================
# 6. Data Exporter (고응집도: 저장 전담)
# =========================================================
class DataExporter:
    @staticmethod
    def save_to_csv(df: pd.DataFrame, save_path: str) -> str:
        if df is None or df.empty:
            raise ValueError("저장할 데이터가 없습니다.")
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        return save_path


# =========================================================
# [기존 하위 호환성을 위한 Facade 함수 (필요시 사용)]
# =========================================================
def crawl_naver_search(client_id, client_secret, keyword, **kwargs):
    client = NaverAPIClient(client_id, client_secret)
    crawler = NaverSearchCrawler(api_client=client)
    return crawler.crawl(keyword=keyword, **kwargs)

save_api_key_xor = CryptoManager.save_api_key
load_api_key_xor = CryptoManager.load_api_key
check_api_key_file = CryptoManager.check_file