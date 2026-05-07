# =========================================================
# 260506_naver_api_crawler.py
# 네이버 검색 API 기반 뉴스/블로그 검색 결과 수집 모듈
# =========================================================

import urllib.request
import urllib.parse
import json
import re
import html
import time
import base64
import os
from datetime import datetime

import pandas as pd


# =========================================================
# 0. XOR 기반 API 키 저장/불러오기 함수
# =========================================================
def xor_bytes(data_bytes, key_bytes):
    """
    XOR 방식으로 bytes 데이터를 변환합니다.

    XOR은 같은 key로 다시 한 번 적용하면 원래 값으로 돌아옵니다.
    즉, 암호화와 복호화에 같은 함수가 사용됩니다.
    """
    result = bytearray()

    for i, b in enumerate(data_bytes):
        result.append(b ^ key_bytes[i % len(key_bytes)])

    return bytes(result)


def save_api_key_xor(client_id, client_secret, save_path, xor_key):
    """
    Client ID와 Client Secret을 XOR 방식으로 암호화하여 파일에 저장합니다.
    """
    if not client_id or not client_secret:
        raise ValueError("Client ID와 Client Secret을 모두 입력해야 합니다.")

    if not xor_key:
        raise ValueError("XOR key가 비어 있습니다.")

    key_data = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    json_str = json.dumps(key_data, ensure_ascii=False)

    data_bytes = json_str.encode("utf-8")
    key_bytes = xor_key.encode("utf-8")

    encrypted_bytes = xor_bytes(data_bytes, key_bytes)

    encrypted_text = base64.b64encode(encrypted_bytes).decode("utf-8")

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(encrypted_text)

    return save_path


def load_api_key_xor(load_path, xor_key):
    """
    XOR 방식으로 암호화 저장된 API 키 파일을 복호화하여 불러옵니다.
    """
    if not os.path.exists(load_path):
        raise FileNotFoundError(f"API 키 파일을 찾을 수 없습니다: {load_path}")

    if not xor_key:
        raise ValueError("XOR key가 비어 있습니다.")

    with open(load_path, "r", encoding="utf-8") as f:
        encrypted_text = f.read().strip()

    encrypted_bytes = base64.b64decode(encrypted_text.encode("utf-8"))
    key_bytes = xor_key.encode("utf-8")

    decrypted_bytes = xor_bytes(encrypted_bytes, key_bytes)
    json_str = decrypted_bytes.decode("utf-8")

    key_data = json.loads(json_str)

    return key_data["client_id"], key_data["client_secret"]


def check_api_key_file(key_file_path):
    """
    API 키 파일 존재 여부를 확인합니다.
    """
    return os.path.exists(key_file_path)


# =========================================================
# 1. HTML 태그 및 특수문자 정리 함수
# =========================================================
def clean_html_text(text):
    """
    네이버 검색 API 결과의 title, description에는
    <b>검색어</b> 같은 HTML 태그가 포함될 수 있습니다.

    이 함수는 HTML 태그를 제거하고,
    &quot; 같은 HTML 특수문자를 일반 문자로 변환합니다.
    """
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"<.*?>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# 2. 분석용 텍스트 정리 함수
# =========================================================
def clean_text_for_analysis(text):
    """
    형태소 분석 및 감성분석용 텍스트를 정리합니다.
    """
    text = clean_html_text(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# 3. 분석 대상 텍스트 생성 함수
# =========================================================
def make_text_for_analysis(title_clean, description_clean, analysis_target="title_description"):
    """
    사용자가 선택한 분석 기준에 따라 text_for_analysis 열을 생성합니다.

    analysis_target
    ----------------
    title               : 제목만 분석
    description         : 본문/요약문만 분석
    title_description   : 제목 + 본문/요약문 함께 분석
    """
    if analysis_target == "title":
        text = title_clean

    elif analysis_target == "description":
        text = description_clean

    elif analysis_target == "title_description":
        text = f"{title_clean} {description_clean}"

    else:
        text = f"{title_clean} {description_clean}"

    return clean_text_for_analysis(text)


# =========================================================
# 4. 네이버 검색 API 단일 페이지 호출 함수
# =========================================================
def request_naver_search_api(
    client_id,
    client_secret,
    keyword,
    search_type="news",
    start=1,
    display=10,
    sort="sim",
):
    """
    네이버 검색 API를 한 번 호출합니다.
    """
    if search_type not in ["news", "blog"]:
        raise ValueError("search_type은 'news' 또는 'blog'만 가능합니다.")

    if start < 1:
        raise ValueError("start는 1 이상이어야 합니다.")

    if display < 1:
        raise ValueError("display는 1 이상이어야 합니다.")

    enc_keyword = urllib.parse.quote(keyword)

    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    url += f"?query={enc_keyword}&start={start}&display={display}&sort={sort}"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    response = urllib.request.urlopen(request)
    rescode = response.getcode()

    if rescode != 200:
        raise RuntimeError(f"네이버 API 요청 실패: HTTP {rescode}")

    response_body = response.read()
    json_str = response_body.decode("utf-8")
    py_data = json.loads(json_str)

    return py_data


# =========================================================
# 5. 검색 결과 item 정규화 함수
# =========================================================
def normalize_items(
    items,
    keyword,
    search_type,
    start_rank,
    analysis_target="title_description",
):
    """
    네이버 API items 리스트를 분석용 DataFrame 구조로 정리합니다.

    analysis_target에 따라 text_for_analysis 열을 다르게 생성합니다.
    """
    normalized_rows = []

    for idx, item in enumerate(items):
        rank = start_rank + idx

        title_raw = item.get("title", "")
        description_raw = item.get("description", "")

        title_clean = clean_html_text(title_raw)
        description_clean = clean_html_text(description_raw)

        text_for_analysis = make_text_for_analysis(
            title_clean=title_clean,
            description_clean=description_clean,
            analysis_target=analysis_target,
        )

        row = {
            "keyword": keyword,
            "search_type": search_type,
            "analysis_target": analysis_target,
            "rank": rank,

            "title_raw": title_raw,
            "title_clean": title_clean,

            "description_raw": description_raw,
            "description_clean": description_clean,

            # 이후 형태소 분석·감성분석 입력 열
            "text_for_analysis": text_for_analysis,

            "link": item.get("link", ""),
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if search_type == "news":
            row["originallink"] = item.get("originallink", "")
            row["pubDate"] = item.get("pubDate", "")

        if search_type == "blog":
            row["bloggername"] = clean_html_text(item.get("bloggername", ""))
            row["bloggerlink"] = item.get("bloggerlink", "")
            row["postdate"] = item.get("postdate", "")

        normalized_rows.append(row)

    return normalized_rows


# =========================================================
# 6. 네이버 검색 결과 전체 수집 함수
# =========================================================
def crawl_naver_search(
    client_id,
    client_secret,
    keyword,
    search_type="news",
    start=1,
    max_results=100,
    display=10,
    sort="sim",
    sleep_sec=0.2,
    max_start_limit=1000,
    analysis_target="title_description",
):
    """
    네이버 검색 API를 반복 호출하여 검색 결과를 DataFrame으로 반환합니다.

    Parameters
    ----------
    analysis_target : str
        text_for_analysis 열 생성 기준입니다.
        - title
        - description
        - title_description
    """
    if not client_id or not client_secret:
        raise ValueError("Client ID와 Client Secret을 입력해야 합니다.")

    if not keyword or not str(keyword).strip():
        raise ValueError("검색어를 입력해야 합니다.")

    if search_type not in ["news", "blog"]:
        raise ValueError("검색 대상은 news 또는 blog만 가능합니다.")

    if analysis_target not in ["title", "description", "title_description"]:
        raise ValueError("analysis_target은 title, description, title_description 중 하나여야 합니다.")

    if start < 1:
        raise ValueError("start는 1 이상이어야 합니다.")

    if display < 1:
        raise ValueError("display는 1 이상이어야 합니다.")

    if max_results < 1:
        raise ValueError("max_results는 1 이상이어야 합니다.")

    all_rows = []

    current_start = start
    collected_count = 0

    while collected_count < max_results:
        if current_start > max_start_limit:
            break

        remain_count = max_results - collected_count
        current_display = min(display, remain_count)

        py_data = request_naver_search_api(
            client_id=client_id,
            client_secret=client_secret,
            keyword=keyword,
            search_type=search_type,
            start=current_start,
            display=current_display,
            sort=sort,
        )

        items = py_data.get("items", [])

        if not items:
            break

        normalized_rows = normalize_items(
            items=items,
            keyword=keyword,
            search_type=search_type,
            start_rank=current_start,
            analysis_target=analysis_target,
        )

        all_rows.extend(normalized_rows)

        item_count = len(items)
        collected_count += item_count
        current_start += item_count

        if item_count < current_display:
            break

        time.sleep(sleep_sec)

    df = pd.DataFrame(all_rows)

    return df


# =========================================================
# 7. 수집 결과 저장 함수
# =========================================================
def save_crawled_data(df, save_path):
    """
    수집된 DataFrame을 CSV 파일로 저장합니다.
    """
    if df is None or df.empty:
        raise ValueError("저장할 데이터가 없습니다.")

    df.to_csv(save_path, index=False, encoding="utf-8-sig")

    return save_path