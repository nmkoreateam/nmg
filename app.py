"""
NMG SQLite3 Streamlit Search Application (v5.4)
--------------------------------------------------------------------
1. 불필요한 언어 선택 메뉴 제거 (en, ko 통합 자동 검색)
2. '대소문자 구분 (Case-Sensitive)' 옵션 추가
3. '단어 단위 일치 (Whole Words Only)' 옵션 추가
4. 암호 입력창 제거 (직접 메인 진입)
5. 우측 상단 점 세 개(⋮) 메뉴 유지, 불필요한 부가 아이콘 숨김
6. 엑셀/TSV 다운로드 버튼 비활성화
"""

import os
import re
import io
import time
import sqlite3
import html
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

# 분할 업로드된 DB 파일이 있으면 자동으로 하나로 합침
if not os.path.exists("./nmg.db") and os.path.exists("./nmg.db.part1"):
    with open("./nmg.db", "wb") as f_out:
        for part in ["./nmg.db.part1", "./nmg.db.part2"]:
            if os.path.exists(part):
                with open(part, "rb") as f_in:
                    f_out.write(f_in.read())

# =========================================================
# 1. Page Configuration
# =========================================================

st.set_page_config(
    page_title="NMG Search System (Streamlit)",
    page_icon="text-search.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. Custom CSS & Header Layout
# =========================================================

DB_DEFAULT_PATH = "./nmg.db"
if os.path.exists(DB_DEFAULT_PATH):
    mtime = os.path.getmtime(DB_DEFAULT_PATH)
    updated_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
else:
    updated_str = "DB Not Found"

header_html = """
<style>
/* 1. 글로벌 기본 다크 스타일 */
html, body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Helvetica Neue", Arial, "Noto Sans KR",
                 "Noto Sans", "Apple SD Gothic Neo", "Malgun Gothic",
                 sans-serif !important;
    color: #E5E7EB !important;
    background-color: #111827 !important;
}

div[data-testid="stStatusWidget"],
footer,
div[data-testid="InputInstructions"] {
    visibility: hidden !important;
    display: none !important;
}

/* 2. 헤더 바 및 불필요한 아이콘 숨김 (점 세 개 메뉴만 단독 보존) */
header[data-testid="stHeader"] {
    background-color: #111827 !important;
    z-index: 1000000 !important;
}

/* Share 버튼 및 Deploy 버튼 숨김 */
.stDeployButton,
header[data-testid="stHeader"] .stAppDeployButton {
    visibility: hidden !important;
    display: none !important;
}

/* 별, 연필, 깃허브 아이콘 컨테이너 강제 숨김 */
header[data-testid="stHeader"] [data-testid="stHeaderActionElements"],
header[data-testid="stHeader"] [data-testid="stToolbarActions"],
header[data-testid="stHeader"] .st-emotion-cache-15ecox0,
header[data-testid="stHeader"] .st-emotion-cache-zq5wmm,
header[data-testid="stHeader"] a:has(svg),
header[data-testid="stHeader"] div:has(> a[href*="github.com"]) {
    visibility: hidden !important;
    display: none !important;
}

/* 점 세 개(⋮) 메뉴 버튼만 명시적 표시 */
#MainMenu,
header[data-testid="stHeader"] button[data-testid="baseButton-headerNoPadding"],
div[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: inline-flex !important;
    color: #E5E7EB !important;
}

header[data-testid="stHeader"] button[data-testid="baseButton-headerNoPadding"] svg {
    fill: #E5E7EB !important;
    color: #E5E7EB !important;
}

/* 3. 사이드바 스타일 */
section[data-testid="stSidebar"] {
    background-color: #1F2937 !important;
    border-right: 1px solid #374151 !important;
    z-index: 1000005 !important;
}

section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #D1D5DB !important;
}

/* 4. 중앙 타이틀 및 우측 상단 Date Updated */
.custom-header-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3.5rem;
    background-color: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000001;
    pointer-events: none;
}

.custom-header-title-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: #E5E7EB;
    letter-spacing: -0.02em;
    pointer-events: auto;
}

.header-date-updated {
    position: fixed;
    top: 14px;
    right: 60px;
    font-size: 11px;
    color: #9CA3AF;
    z-index: 1000005;
    pointer-events: none;
    font-family: inherit;
}

.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 98% !important;
}

/* 5. 메인 검색 입력창 전폭 사용 */
.main div[data-testid="stTextInput"],
.main div[data-testid="stTextInput"] > div,
.main div[data-baseweb="input"],
.main div[data-baseweb="base-input"] {
    width: 100% !important;
    background-color: #374151 !important;
    border: 1px solid #4B5563 !important;
    border-radius: 0.375rem !important;
    height: 42px !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

.main div[data-baseweb="base-input"] {
    background-color: transparent !important;
    height: 100% !important;
}

.main .stTextInput input {
    background-color: transparent !important;
    color: #E5E7EB !important;
    -webkit-text-fill-color: #E5E7EB !important;
    caret-color: #E5E7EB !important;
    font-size: 14px !important;
    height: 100% !important;
    padding: 0 12px !important;
    border: none !important;
    box-shadow: none !important;
}

.main div[data-baseweb="input"]:focus-within {
    border-color: #60A5FA !important;
}

.main .stTextInput input::placeholder {
    color: #9CA3AF !important;
    -webkit-text-fill-color: #9CA3AF !important;
}

/* 6. 드롭다운 */
div[data-baseweb="select"],
div[data-baseweb="select"] > div {
    background-color: #374151 !important;
    border-color: #4B5563 !important;
    color: #E5E7EB !important;
    border-radius: 0.375rem !important;
}

div[data-baseweb="select"] * {
    color: #E5E7EB !important;
    -webkit-text-fill-color: #E5E7EB !important;
}

/* 7. 결과 테이블 스타일 */
.freq-info-box {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 6px 12px;
    color: #D1D5DB;
    font-size: 13px;
    display: inline-block;
}

.highlight-search {
    background-color: #FDE047;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: 600;
}

.highlight-keyword {
    background-color: #EAB308;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: 600;
}

.custom-table-container {
    width: 100%;
    overflow-x: auto;
    border-radius: 6px;
    border: 1px solid #374151;
    margin-top: 10px;
}

.custom-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    background-color: #1F2937;
    color: #D1D5DB;
    font-size: 12.5px;
    line-height: 1.4;
}

.custom-table th {
    background-color: #111827;
    color: #E5E7EB;
    font-weight: 600;
    border-bottom: 2px solid #374151;
    padding: 8px 10px;
    text-align: center;
    white-space: nowrap;
}

.custom-table td {
    border-bottom: 1px solid #374151;
    padding: 8px 10px;
    vertical-align: top;
    text-align: left;
    overflow-wrap: anywhere;
}

.custom-table tr:hover {
    background-color: #2D3748;
}

.col-vbcp {
    width: 7%;
    font-size: 11.5px;
    font-family: inherit !important;
    color: #9CA3AF;
    text-align: center !important;
    white-space: normal !important;
    word-break: break-all !important;
}

.col-main {
    width: 28%;
    min-width: 0;
    font-size: 13px;
    color: #E5E7EB;
}

.col-sub {
    width: 11%;
    font-size: 11.5px;
    color: #9CA3AF;
}

.col-link {
    width: 5%;
    font-size: 11.5px;
    text-align: center !important;
}

.col-link a {
    color: #60A5FA;
    text-decoration: underline;
    font-weight: 500;
}
</style>

<div class="custom-header-bar">
    <div class="custom-header-title-text">NMG Search System</div>
</div>
<div class="header-date-updated">
    Date Updated: <strong>__UPDATED_STR__</strong>
</div>
""".replace("__UPDATED_STR__", updated_str)

st.markdown(header_html, unsafe_allow_html=True)

# =========================================================
# 3. Session State
# =========================================================

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

if "highlight_query" not in st.session_state:
    st.session_state["highlight_query"] = ""


# =========================================================
# 4. General Helpers
# =========================================================

def escape_like(value: str) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def safe_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def clean_dataframe_nulls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["V.B.C.P", "Source", "번역문", "Book, Chapter", "책, 장", "Link"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


# =========================================================
# 5. V.B.C.P Parser & Regex Preprocessor
# =========================================================

def extract_vbc_conditions(query_str: str, prefix: str = "bt.") -> tuple[str, str, str]:
    query = (query_str or "").strip()
    if not query:
        return "", "", ""

    vbc_pattern = r'^(\d+\.\d+(?:\.[cC]?\d+){0,2})'
    
    pipe_match = re.match(rf'{vbc_pattern}\|(.*)$', query, re.DOTALL)
    if pipe_match:
        vbc_raw = pipe_match.group(1)
        clean_query = pipe_match.group(2).strip()
    else:
        space_match = re.match(rf'{vbc_pattern}(?:\s+(.*))?$', query, re.DOTALL)
        if not space_match:
            return "", query, ""
        vbc_raw = space_match.group(1)
        clean_query = (space_match.group(2) or "").strip()

    parts_clean = [re.sub(r'^[cC]', '', p) for p in vbc_raw.split(".")]
    fields = ["Volume", "BookNo", "ChapterNo_Old", "ParagraphNo"]
    conditions = [f"{prefix}{field} = '{val}'" for val, field in zip(parts_clean, fields)]

    return " AND ".join(conditions), clean_query, ".".join(parts_clean)


def sanitize_regex_pattern(pattern: str) -> str:
    pattern = (pattern or "").strip()
    while pattern.endswith("|"):
        pattern = pattern[:-1].strip()

    pattern = re.sub(r'(?<![\.\\])\*', r'.*', pattern)
    pattern = re.sub(r'(?<!\\)\.\*', r'[^.?!]*', pattern)
    pattern = re.sub(r'(?<!\\)\.\+', r'[^.?!]+', pattern)

    return pattern


# =========================================================
# 6. Database Connection
# =========================================================

def get_db_connection(db_path: str, case_sensitive: bool = False):
    conn = sqlite3.connect(db_path)
    
    # Simple LIKE 검색 시 대소문자 구분 설정 반영
    if case_sensitive:
        conn.execute("PRAGMA case_sensitive_like = ON;")
    else:
        conn.execute("PRAGMA case_sensitive_like = OFF;")

    flags = 0 if case_sensitive else re.IGNORECASE

    def regexp(expr, item):
        if item is None or expr is None or expr == "":
            return False
        try:
            return re.search(str(expr), str(item), flags) is not None
        except Exception:
            return False

    conn.create_function("REGEXP", 2, regexp)
    return conn


# =========================================================
# 7. Database Search
# =========================================================

def execute_search(
    db_path: str,
    query_str: str,
    search_type: str,
    case_sensitive: bool,
    whole_words: bool,
    limit_count
) -> tuple[pd.DataFrame, str, str]:

    range_cond, clean_query, _ = extract_vbc_conditions(query_str)

    conditions = []
    params = []
    effective_pattern = ""

    if range_cond:
        conditions.append(range_cond)

    if clean_query:
        # 단어 단위 일치(Whole Words Only) 옵션 처리
        if whole_words:
            base_pattern = re.escape(clean_query) if search_type == "simple" else sanitize_regex_pattern(clean_query)
            effective_pattern = rf"\b{base_pattern}\b"
            conditions.append("(bt.en REGEXP ? OR bt.ko REGEXP ?)")
            params.extend([effective_pattern, effective_pattern])
        else:
            if search_type == "simple":
                effective_pattern = re.escape(clean_query)
                conditions.append("(bt.en LIKE ? ESCAPE '\\' OR bt.ko LIKE ? ESCAPE '\\')")
                escaped = f"%{escape_like(clean_query)}%"
                params.extend([escaped, escaped])
            else:
                effective_pattern = sanitize_regex_pattern(clean_query)
                conditions.append("(bt.en REGEXP ? OR bt.ko REGEXP ?)")
                params.extend([effective_pattern, effective_pattern])

    if not conditions:
        return pd.DataFrame(), "", ""

    where_clause = " AND ".join(conditions)
    limit_sql = f"LIMIT {int(limit_count)}" if limit_count is not None else ""
    orderby_prefix = "A.recid, " if range_cond else ""

    sql = f"""
        SELECT
            A.vbcp AS "V.B.C.P",
            A.text_en AS "Source",
            A.text_ko AS "번역문",

            CASE
                WHEN A.BookTitle != '' AND A.Chapter != '' THEN A.BookTitle || ', ' || A.Chapter
                WHEN A.BookTitle != '' THEN A.BookTitle
                WHEN A.Chapter != '' THEN A.Chapter
                ELSE 'Volume ' || A.Volume || ' Book ' || A.BookNo
            END AS "Book, Chapter",

            CASE
                WHEN A.BookTitle_ko != '' AND A.Chapter_ko != '' THEN A.BookTitle_ko || ', ' || A.Chapter_ko
                WHEN A.BookTitle_ko != '' THEN A.BookTitle_ko
                WHEN A.Chapter_ko != '' THEN A.Chapter_ko
                ELSE A.Volume || '권 ' || A.BookNo || '책'
            END AS "책, 장",

            CASE 
                WHEN v.url IS NOT NULL OR v.url_ko IS NOT NULL THEN '[en]' || COALESCE(v.url, '') || char(10) || '[ko]' || COALESCE(v.url_ko, '')
                ELSE ''
            END AS "Link"

        FROM (
            SELECT
                bt.Volume || '.' || COALESCE(bt.BookNo, '') || '.' ||
                COALESCE(bt.ChapterNo_Old, '') || '.' || COALESCE(bt.ParagraphNo, '') AS vbcp,
                TRIM(COALESCE(bt.en, '')) AS text_en,
                TRIM(COALESCE(bt.ko, '')) AS text_ko,
                bt.Volume AS volume_int,
                bt.BookNo AS bookno_int,
                bt.ChapterNo_Old AS chapterno_int,
                bt.ParagraphNo AS paragraphno_int,
                bt.Volume,
                bt.BookNo,
                COALESCE(bk.BookTitleCorrected, 
                         CASE 
                             WHEN bt.Volume = 3 AND bt.BookNo = 1 THEN 'Steps to Knowledge'
                             WHEN bt.Volume = 3 AND bt.BookNo = 2 THEN 'Steps to Knowledge Continuation Training'
                             WHEN bt.Volume = 9 THEN 'The Allies of Humanity Book ' || bt.BookNo
                             ELSE '' 
                         END) AS BookTitle,
                COALESCE(bk.BookTitleCorrected, 
                         CASE 
                             WHEN bt.Volume = 3 AND bt.BookNo = 1 THEN '앎으로 가는 계단'
                             WHEN bt.Volume = 3 AND bt.BookNo = 2 THEN '앎으로 가는 계단 계속과정'
                             WHEN bt.Volume = 9 THEN '인류의 동행자, 제' || bt.BookNo || '권'
                             ELSE '' 
                         END) AS BookTitle_ko,
                COALESCE(bck.ChapterTitle, '') AS ChapterTitle,
                COALESCE(bck.en, 
                         CASE 
                             WHEN bt.Volume = 3 THEN 'Step ' || bt.ChapterNo_Old
                             WHEN bt.ChapterNo_Old = '0' THEN 'Foreword / Introduction'
                             ELSE 'Chapter ' || bt.ChapterNo_Old 
                         END) AS Chapter,
                COALESCE(bck.ko, 
                         CASE 
                             WHEN bt.Volume = 3 THEN '제' || bt.ChapterNo_Old || '계단'
                             WHEN bt.ChapterNo_Old = '0' THEN '서문'
                             ELSE '제' || bt.ChapterNo_Old || '장'
                         END) AS Chapter_ko,
                bt.recid,
                CASE WHEN bt.Volume = 9 THEN 0 ELSE bt.Volume END AS join_vol
            FROM book_translations AS bt
            LEFT JOIN books_ko AS bk 
                   ON bk.Volume = (CASE WHEN bt.Volume = 9 THEN 0 ELSE bt.Volume END) 
                  AND bk.BookNo = bt.BookNo
            LEFT JOIN book_contents_ko AS bck 
                   ON bck.Volume = (CASE WHEN bt.Volume = 9 THEN 0 ELSE bt.Volume END) 
                  AND bck.BookNo = bt.BookNo 
                  AND bck.ChapterNo = bt.ChapterNo_Old
            WHERE {where_clause}
        ) A
        LEFT JOIN v_b_c_u AS v 
               ON v.volume = A.join_vol 
              AND LOWER(v.book) = LOWER(A.BookTitle) 
              AND LOWER(v.chapter) = LOWER(A.ChapterTitle)
        ORDER BY
            {orderby_prefix}
            CAST(A.volume_int AS INTEGER),
            CAST(A.bookno_int AS INTEGER),
            CAST(A.chapterno_int AS INTEGER),
            CAST(A.paragraphno_int AS INTEGER)
        {limit_sql}
    """

    conn = get_db_connection(db_path, case_sensitive=case_sensitive)
    try:
        df = pd.read_sql_query(sql, conn, params=tuple(params))
    finally:
        conn.close()

    return clean_dataframe_nulls(df), clean_query, effective_pattern


# =========================================================
# 8. URL Formatter
# =========================================================

def safe_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() in ("http", "https"):
            return url
    except Exception:
        pass
    return ""


def parse_links_to_html(link_str: str) -> str:
    if not link_str or pd.isna(link_str):
        return ""

    html_links = []
    for line in str(link_str).split("\n"):
        line = line.strip()
        if line.startswith("[en]"):
            url = safe_url(line[4:].strip())
            html_links.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">en</a>' if url else "en")
        elif line.startswith("[ko]"):
            url = safe_url(line[4:].strip())
            html_links.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">ko</a>' if url else "ko")

    return "<br>".join(html_links)


# =========================================================
# 9. Regex Highlight Engine
# =========================================================

def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def find_regex_ranges(text: str, pattern: str, case_sensitive: bool = False) -> list[tuple[int, int]]:
    if not text or not pattern:
        return []
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error:
        return []

    ranges = [(m.start(), m.end()) for m in regex.finditer(text) if m.end() > m.start()]
    return merge_ranges(ranges)


def render_highlighted_text(
    text: str,
    search_ranges: list[tuple[int, int]],
    keyword_ranges: list[tuple[int, int]]
) -> str:
    if not text:
        return ""

    search_ranges = merge_ranges(search_ranges)
    keyword_ranges = merge_ranges(keyword_ranges)

    boundaries = {0, len(text)}
    for start, end in search_ranges + keyword_ranges:
        boundaries.add(start)
        boundaries.add(end)

    boundaries = sorted(boundaries)
    output = []

    for start, end in zip(boundaries[:-1], boundaries[1:]):
        if start == end:
            continue
        segment = text[start:end]
        is_search = any(s <= start and end <= e for s, e in search_ranges)
        is_keyword = any(s <= start and end <= e for s, e in keyword_ranges)
        escaped = html.escape(segment)

        if is_search:
            output.append(f'<span class="highlight-search">{escaped}</span>')
        elif is_keyword:
            output.append(f'<span class="highlight-keyword">{escaped}</span>')
        else:
            output.append(escaped)

    return "".join(output)


def get_keyword_ranges(text: str, keywords: list[str]) -> tuple[list[tuple[int, int]], dict]:
    ranges = []
    freq_map = {}
    if not text or not keywords:
        return ranges, freq_map

    for keyword in keywords:
        try:
            regex = re.compile(re.escape(keyword), re.IGNORECASE)
        except re.error:
            continue

        matches = list(regex.finditer(text))
        if matches:
            freq_map[keyword.lower()] = freq_map.get(keyword.lower(), 0) + len(matches)
        for m in matches:
            if m.end() > m.start():
                ranges.append((m.start(), m.end()))

    return merge_ranges(ranges), freq_map


def apply_highlights_and_format(
    df: pd.DataFrame,
    search_pattern: str,
    case_sensitive: bool,
    highlight_keywords_str: str
):
    df_display = clean_dataframe_nulls(df.copy())
    freq_map = {}

    keywords = [k.strip() for k in (highlight_keywords_str or "").split(",") if k.strip()]

    # 각 행마다 추가 키워드가 총 몇 번 나왔는지 세는 카운터 열 추가
    row_keyword_counts = [0] * len(df_display)

    for column in ["Source", "번역문"]:
        if column not in df_display.columns:
            continue

        formatted_values = []
        for idx, value in enumerate(df_display[column]):
            text = safe_text(value)
            if not text:
                formatted_values.append("")
                continue

            search_ranges = find_regex_ranges(text, search_pattern, case_sensitive) if search_pattern else []
            keyword_ranges, keyword_freq = get_keyword_ranges(text, keywords)

            # 행별 추가 키워드 매칭 개수 누적
            match_count = sum(keyword_freq.values())
            row_keyword_counts[idx] += match_count

            # 전체 키워드 빈도 합산
            for key, count in keyword_freq.items():
                freq_map[key] = freq_map.get(key, 0) + count

            formatted_values.append(render_highlighted_text(text, search_ranges, keyword_ranges))

        df_display[column] = formatted_values

    if "Link" in df_display.columns:
        df_display["Link"] = df_display["Link"].apply(parse_links_to_html)

    # 추가 하이라이트 키워드가 입력된 경우: 매칭 횟수가 많은 행을 맨 위로 정렬 (내림차순)
    if keywords:
        df_display["_kw_priority"] = row_keyword_counts
        # kind='stable'을 주어 등장 횟수가 같거나 0인 행들은 원래 책·장·절 순서 유지
        df_display = df_display.sort_values(by="_kw_priority", ascending=False, kind="stable").drop(columns=["_kw_priority"])

    sorted_freq = sorted(freq_map.items(), key=lambda x: x[1], reverse=True)
    freq_summary = ", ".join(f"{kw}({cnt})" for kw, cnt in sorted_freq)

    return df_display, freq_summary


# =========================================================
# 10. Custom Table Generator
# =========================================================

def generate_custom_table_html(df: pd.DataFrame) -> str:
    html_parts = [
        '<div class="custom-table-container">',
        '<table class="custom-table">',
        '<thead><tr>',
        '<th class="col-vbcp">V.B.C.P</th>',
        '<th class="col-main">Source</th>',
        '<th class="col-main">번역문</th>',
        '<th class="col-sub">Book, Chapter</th>',
        '<th class="col-sub">책, 장</th>',
        '<th class="col-link">Link</th>',
        '</tr></thead><tbody>'
    ]

    for _, row in df.iterrows():
        html_parts.append("<tr>")
        html_parts.append(f'<td class="col-vbcp">{html.escape(safe_text(row.get("V.B.C.P")))}</td>')
        html_parts.append(f'<td class="col-main">{safe_text(row.get("Source"))}</td>')
        html_parts.append(f'<td class="col-main">{safe_text(row.get("번역문"))}</td>')
        html_parts.append(f'<td class="col-sub">{html.escape(safe_text(row.get("Book, Chapter")))}</td>')
        html_parts.append(f'<td class="col-sub">{html.escape(safe_text(row.get("책, 장")))}</td>')
        html_parts.append(f'<td class="col-link">{safe_text(row.get("Link"))}</td>')
        html_parts.append("</tr>")

    html_parts.append("</tbody></table></div>")
    return "".join(html_parts)


# =========================================================
# 11. Main App
# =========================================================

def main():
    st.sidebar.header("⚙️ 검색 설정")

    db_path = DB_DEFAULT_PATH

    search_type = st.sidebar.radio(
        "검색 모드",
        options=["regex", "simple"],
        index=0,
        format_func=lambda x: "Regex (정규식)" if x == "regex" else "Simple (기본)"
    )

    # 검색 세부 옵션 체크박스
    case_sensitive = st.sidebar.checkbox("대소문자 구분 (Case-Sensitive)", value=False)
    whole_words = st.sidebar.checkbox("단어 단위 일치 (Whole Words Only)", value=False)

    limit_option = st.sidebar.selectbox(
        "최대 검색 제한",
        options=[1000, 2000, 3000, 5000, 10000, "무제한"],
        index=2
    )

    limit_count = None if limit_option == "무제한" else limit_option

    query_input = st.text_input(
        "검색어",
        key="search_query",
        placeholder="검색어를 입력하고 Enter를 누르세요 (예: 1.11.1 / 1.11.c1 / Step 1 / love*peace)",
        label_visibility="collapsed"
    )

    highlight_input = st.text_input(
        "추가 하이라이트 키워드",
        key="highlight_query",
        placeholder="추가 하이라이트 키워드 (쉼표 ',' 구분)",
        label_visibility="collapsed"
    )

    if not os.path.exists(db_path):
        st.error(f"DB 파일('{db_path}')을 찾을 수 없습니다. update_db.py를 먼저 실행해 주세요.")
        return

    if query_input:
        with st.spinner("DB 데이터 조회 중..."):
            try:
                raw_df, clean_query, search_pattern = execute_search(
                    db_path,
                    query_input,
                    search_type,
                    case_sensitive,
                    whole_words,
                    limit_count
                )
                display_df, freq_summary = apply_highlights_and_format(
                    raw_df,
                    search_pattern,
                    case_sensitive,
                    highlight_input
                )

                result_cnt = len(raw_df)
                cnt_text = f"📊 총 {result_cnt:,} 건 검색됨"
                if limit_count is not None and result_cnt >= limit_count:
                    cnt_text += f" <span style='color:#9CA3AF; font-size:11px;'>(최대 제한 {limit_count:,}건 적용됨)</span>"

                col_sum, col_freq = st.columns([1, 2])
                with col_sum:
                    st.markdown(f'<span style="font-size:13px; font-weight:600; color:#E5E7EB;">{cnt_text}</span>', unsafe_allow_html=True)

                with col_freq:
                    if freq_summary:
                        st.markdown(f'<div class="freq-info-box"><span style="color:#9CA3AF; font-weight:600;">키워드:</span> {html.escape(freq_summary)}</div>', unsafe_allow_html=True)

                table_html = generate_custom_table_html(display_df)
                st.write(table_html, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"검색 처리 중 오류 발생: {e}")


if __name__ == "__main__":
    main()