#!/usr/bin/env python3
"""
Notion -> MkDocs Journal 동기화 (최소 기능)

Visibility=Public 인 Notion 페이지만 골라서
docs/journal/YYYY/YYYY-MM/YYYY-MM-DD.md 로 생성/갱신하고,
Public에서 빠진 글은 삭제한다(reconcile).

실행 방법은 tools/README.md 참고.

의존성: requests, PyYAML (둘 다 requirements.txt에 이미 있음)
"""

import argparse
import mimetypes
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import yaml

# --- 설정 --------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
JOURNAL_DIR = REPO_ROOT / "docs" / "journal"

API = "https://api.notion.com/v1"

# Why: 2025-09-03에서 databases/query가 폐기되고 data_sources/query로 바뀌었다.
#      이 스크립트는 data source 기반 API를 쓴다.
DEFAULT_NOTION_VERSION = "2026-03-11"

# 이미지 저장 규칙
# Why: Notion이 주는 파일 URL은 한 시간쯤 뒤 만료되는 서명 링크라 그대로 쓸 수 없다.
#      받아서 레포에 넣고, 파일명은 블록 ID에서 만들어 실행할 때마다 같게 유지한다.
IMG_DIR_NAME = "images"
MAX_IMAGE_BYTES = 25 * 1024 * 1024
# 동기화가 만든 파일만 정리 대상으로 삼기 위한 패턴 (손으로 넣은 이미지는 보호)
SYNCED_IMG_RE = re.compile(r"^[0-9a-f]{12}\.[A-Za-z0-9]+$")


def load_dotenv():
    """
    레포 루트의 .env 를 환경변수로 읽어들인다(이미 설정된 값은 덮어쓰지 않음).

    Why: 토큰을 셸에 매번 export하지 않고 파일 하나로 관리하기 위함.
         .env 는 .gitignore에 등록되어 있어 커밋되지 않는다.
    How: 아래 속성 상수들이 이 값을 참조하므로 상수 정의보다 먼저 호출해야 한다.
    """
    path = REPO_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'\"")
        # Why: 값이 빈 줄(.env.example을 그대로 복사한 경우)은 건너뛴다.
        #      빈 문자열을 넣어버리면 "설정되어 있지만 비어 있음" 상태가 되어
        #      실제 설정을 가리고 원인을 찾기 어려운 오류가 난다.
        if key and val and key not in os.environ:
            os.environ[key] = val


load_dotenv()

# Notion DB 속성 이름. 노션에서 이름을 바꿨다면 환경변수로 덮어쓸 수 있다.
PROP_DATE = os.getenv("NOTION_PROP_DATE", "Date")
PROP_VISIBILITY = os.getenv("NOTION_PROP_VISIBILITY", "Visibility")
PROP_LANG = os.getenv("NOTION_PROP_LANG", "Lang original")
PUBLIC_VALUE = os.getenv("NOTION_PUBLIC_VALUE", "Public")

# 본문에서 언어 섹션을 찾을 때 쓰는 H2 제목 패턴
SECTION_KO = re.compile(r"^\s*(한국어|한글|korean|ko)\b", re.I)
SECTION_EN = re.compile(r"^\s*(english|영어|en)\b", re.I)

# 인덱스에서 스크립트가 관리하는 구간. 이 밖의 내용은 절대 건드리지 않는다.
MARK_START = "<!-- sync:auto:start -->"
MARK_END = "<!-- sync:auto:end -->"

ENTRY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")

TAB_LABEL = {
    ("ko", True): "한국어 (원문)",
    ("ko", False): "한국어 (번역)",
    ("en", True): "English (Original)",
    ("en", False): "English (Translated)",
}


class SyncError(Exception):
    pass


# --- Notion API --------------------------------------------------------


class Notion:
    """requests 기반 얇은 Notion 클라이언트. 토큰은 절대 로그에 남기지 않는다."""

    def __init__(self, token, version):
        self.s = requests.Session()
        self.s.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": version,
                "Content-Type": "application/json",
            }
        )

    def _request(self, method, path, **kw):
        url = f"{API}{path}"
        for attempt in range(5):
            r = self.s.request(method, url, timeout=30, **kw)
            # How: 429/5xx는 잠깐 쉬고 재시도. Retry-After가 오면 그걸 따른다.
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("Retry-After", 2 ** attempt))
                time.sleep(min(wait, 30))
                continue
            if not r.ok:
                # Why: 응답 본문에 토큰은 들어있지 않으므로 그대로 노출해도 안전하다.
                raise SyncError(f"{method} {path} -> {r.status_code} {r.text[:400]}")
            return r.json()
        raise SyncError(f"{method} {path}: 재시도 후에도 실패")

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, payload):
        return self._request("POST", path, json=payload)

    def paginate(self, path, payload=None):
        """Notion의 커서 페이지네이션을 걷어내고 결과만 흘려보낸다."""
        cursor = None
        while True:
            if payload is None:
                sep = "&" if "?" in path else "?"
                p = path + (f"{sep}start_cursor={cursor}" if cursor else "")
                data = self.get(p)
            else:
                body = dict(payload)
                if cursor:
                    body["start_cursor"] = cursor
                data = self.post(path, body)
            for item in data.get("results", []):
                yield item
            if not data.get("has_more"):
                return
            cursor = data.get("next_cursor")


def normalize_id(raw):
    """URL이든 대시 있든 없든 32자리 hex를 뽑아 UUID 형태로 만든다."""
    if not raw:
        return None
    m = re.findall(r"[0-9a-fA-F]{32}", raw.replace("-", ""))
    if not m:
        raise SyncError(f"Notion ID를 찾을 수 없음: {raw!r}")
    h = m[-1].lower()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def resolve_data_source_id(nc, database_id):
    """database_id -> data_source_id. 단일 소스 DB면 결과가 하나뿐이다."""
    db = nc.get(f"/databases/{database_id}")
    sources = db.get("data_sources") or []
    if not sources:
        raise SyncError(
            f"database {database_id} 에 data source가 없습니다. "
            "통합(integration)에 DB가 공유되어 있는지 확인하세요."
        )
    if len(sources) > 1:
        names = ", ".join(f"{s.get('name')}={s.get('id')}" for s in sources)
        print(f"  ! data source가 여러 개입니다. 첫 번째를 씁니다: {names}")
    return sources[0]["id"]


def build_visibility_filter(nc, data_source_id):
    """
    Visibility 속성의 실제 타입을 읽어서 맞는 필터를 만든다.

    Why: 노션에서 Select로 만들었는지 Status로 만들었는지에 따라
         필터 문법이 달라서, 하드코딩하면 조용히 0건이 나온다.
    """
    kind = "select"
    try:
        ds = nc.get(f"/data_sources/{data_source_id}")
        props = ds.get("properties", {})
        if PROP_VISIBILITY not in props:
            raise SyncError(
                f"'{PROP_VISIBILITY}' 속성이 DB에 없습니다. "
                f"있는 속성: {', '.join(sorted(props)) or '(없음)'}"
            )
        kind = props[PROP_VISIBILITY].get("type", "select")
    except SyncError:
        raise
    except Exception as e:  # 스키마 조회 실패해도 select로 시도는 해본다
        print(f"  ! 스키마 조회 실패({e}), select로 가정합니다.")

    if kind in ("select", "status"):
        return {"property": PROP_VISIBILITY, kind: {"equals": PUBLIC_VALUE}}
    if kind == "multi_select":
        return {"property": PROP_VISIBILITY, "multi_select": {"contains": PUBLIC_VALUE}}
    if kind == "checkbox":
        return {"property": PROP_VISIBILITY, "checkbox": {"equals": True}}
    raise SyncError(f"'{PROP_VISIBILITY}' 속성 타입({kind})은 아직 지원하지 않습니다.")


# --- rich text / block -> markdown -------------------------------------


def rich_text_to_md(rich):
    """Notion rich_text 배열을 마크다운 인라인으로 변환."""
    out = []
    for t in rich or []:
        if t.get("type") == "equation":
            out.append(f"${t['equation']['expression']}$")
            continue
        text = t.get("plain_text", "")
        if not text:
            continue
        a = t.get("annotations", {})
        # How: code를 가장 안쪽에 두고 링크를 가장 바깥에 둬야 마크다운이 깨지지 않는다.
        if a.get("code"):
            text = f"`{text}`"
        else:
            if a.get("bold"):
                text = f"**{text}**"
            if a.get("italic"):
                text = f"*{text}*"
            if a.get("strikethrough"):
                text = f"~~{text}~~"
        href = t.get("href")
        if href:
            text = f"[{text}]({href})"
        out.append(text)
    return "".join(out)


def block_file_url(data):
    """image/file 블록에서 실제 URL을 꺼낸다. Notion 호스팅과 외부 링크 둘 다 지원."""
    for key in ("file", "external", "file_upload"):
        v = data.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
    return None


def image_filename(block_id, url, content_type=""):
    """
    블록 ID로 파일명을 만든다.

    Why: Notion URL은 실행할 때마다 서명이 바뀌므로 이름의 근거로 쓸 수 없다.
         블록 ID는 고정이라 같은 이미지가 항상 같은 파일로 떨어지고,
         덕분에 재실행해도 diff가 생기지 않는다.
    """
    stem = block_id.replace("-", "")[:12].lower()
    ext = os.path.splitext(unquote(urlparse(url).path))[1].lower()
    if not re.fullmatch(r"\.[a-z0-9]{2,5}", ext):
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".png"
    if ext == ".jpe":
        ext = ".jpg"
    return f"{stem}{ext}"


class ImageContext:
    """한 글을 변환하는 동안의 이미지 저장 위치와 결과를 담는다."""

    def __init__(self, img_dir, dry_run):
        self.img_dir = img_dir
        self.dry_run = dry_run
        self.saved = set()      # 이 글이 실제로 참조하는 파일명
        self.written = []       # 실제로 새로 쓴 파일 (보고용)
        self.session = requests.Session()

    def fetch(self, block_id, url):
        """이미지를 내려받아 저장하고 파일명을 돌려준다. 실패하면 None."""
        try:
            r = self.session.get(url, timeout=60, stream=True)
            r.raise_for_status()
            size = int(r.headers.get("Content-Length") or 0)
            if size > MAX_IMAGE_BYTES:
                print(f"  ! 이미지가 너무 큼({size // 1024 // 1024}MB), 건너뜀: {block_id}")
                return None
            body = b""
            for chunk in r.iter_content(65536):
                body += chunk
                if len(body) > MAX_IMAGE_BYTES:
                    print(f"  ! 이미지가 너무 큼, 건너뜀: {block_id}")
                    return None
            name = image_filename(block_id, url, r.headers.get("Content-Type", ""))
        except requests.RequestException as e:
            print(f"  ! 이미지 내려받기 실패({block_id}): {e}")
            return None

        self.saved.add(name)
        dest = self.img_dir / name
        # How: 내용이 같으면 쓰지 않는다. 매번 새로 써서 불필요한 커밋이 생기는 것을 막는다.
        if dest.exists() and dest.read_bytes() == body:
            return name
        self.written.append(dest)
        if not self.dry_run:
            self.img_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
        return name


LIST_TYPES = ("bulleted_list_item", "numbered_list_item", "to_do")


def soft_breaks(text, pad="", inline=False):
    """
    문단 안의 줄바꿈(Shift+Enter)을 마크다운 줄바꿈으로 살린다.

    Why: 마크다운은 홑 줄바꿈을 공백으로 취급해서, 노션에서 줄이 나뉘어 보이던
         문장들이 사이트에서는 한 문단으로 쭉 이어져 버린다.
    How: <br> 을 명시적으로 넣는다. 줄 끝 공백 2칸 방식은 눈에 보이지 않아
         편집기가 지워버리기 쉬우므로 쓰지 않는다.
    """
    if "\n" not in text:
        return text
    parts = text.split("\n")
    if inline:
        # 리스트 항목은 한 줄로 유지해야 목록 구조가 깨지지 않는다
        return "<br>".join(parts)
    return f"<br>\n{pad}".join(parts)


def blocks_to_md(nc, block_id, depth=0, imgctx=None):
    """
    블록 트리를 재귀적으로 마크다운으로 변환한다.

    Why: 마크다운은 블록 사이의 빈 줄로 문단을 구분한다. Notion 블록을
         그냥 이어붙이면 별개 문단이 한 문단으로 합쳐지고, 문단 바로 뒤에
         온 리스트가 리스트로 인식되지 않는다.
    How: 리스트 항목끼리 연달아 나올 때만 빈 줄을 넣지 않고,
         그 외 블록 경계에는 항상 빈 줄을 하나 넣는다.
    """
    lines = []
    prev = None       # 직전 블록의 종류
    numbering = 0
    pad = "    " * depth

    for b in nc.paginate(f"/blocks/{block_id}/children?page_size=100"):
        t = b.get("type")
        data = b.get(t, {}) if t else {}
        text = rich_text_to_md(data.get("rich_text"))
        chunk = []
        kids = None

        if t == "paragraph":
            if text:
                chunk.append(pad + soft_breaks(text, pad))
        elif t in ("heading_1", "heading_2", "heading_3"):
            chunk.append(f"{'#' * int(t[-1])} {text.replace(chr(10), ' ')}")
        elif t == "bulleted_list_item":
            chunk.append(f"{pad}- {soft_breaks(text, inline=True)}")
            kids = depth + 1
        elif t == "numbered_list_item":
            numbering = numbering + 1 if prev == "numbered_list_item" else 1
            chunk.append(f"{pad}{numbering}. {soft_breaks(text, inline=True)}")
            kids = depth + 1
        elif t == "to_do":
            mark = "x" if data.get("checked") else " "
            chunk.append(f"{pad}- [{mark}] {soft_breaks(text, inline=True)}")
            kids = depth + 1
        elif t == "quote":
            chunk.extend(f"{pad}> {ln}" for ln in (text or "").split("\n"))
        elif t == "callout":
            icon = (data.get("icon") or {}).get("emoji", "")
            chunk.append(f"{pad}> {icon} {text}".rstrip())
        elif t == "code":
            lang = data.get("language", "")
            lang = "" if lang in ("plain text", "plain_text") else lang
            chunk.append(f"{pad}```{lang}")
            chunk.extend(pad + ln for ln in (text or "").split("\n"))
            chunk.append(f"{pad}```")
        elif t == "divider":
            chunk.append("---")
        elif t == "equation":
            chunk.append(f"$${data.get('expression','')}$$")
        elif t == "toggle":
            chunk.append(f'??? note "{text}"')
            kids = depth + 1
        elif t == "image":
            cap = rich_text_to_md(data.get("caption")).strip()
            url = block_file_url(data)
            name = imgctx.fetch(b["id"], url) if (imgctx and url) else None
            if name:
                # 캡션이 있으면 alt로 쓰고 그림 아래에도 보이게 남긴다
                chunk.append(f"{pad}![{cap}]({IMG_DIR_NAME}/{name})")
                if cap:
                    chunk.append(f"{pad}/// caption")
                    chunk.append(f"{pad}{cap}")
                    chunk.append(f"{pad}///")
            else:
                chunk.append(f"{pad}<!-- 이미지를 가져오지 못했습니다 ({cap or b['id']}) -->")
        elif t in ("video", "file", "pdf"):
            # 이미지 외 첨부는 아직 다루지 않는다. Notion URL이 만료되므로
            # 링크를 남겨도 곧 깨져서, 흔적만 주석으로 둔다.
            cap = rich_text_to_md(data.get("caption")) or t
            chunk.append(f"{pad}<!-- TODO: {t} 미동기화 ({cap}) -->")
        elif t in ("bookmark", "embed", "link_preview"):
            if data.get("url"):
                chunk.append(f"{pad}<{data['url']}>")
        elif t in ("child_page", "child_database", "table_of_contents",
                   "breadcrumb", "synced_block", "column_list", "column"):
            kids = depth  # 컨테이너는 자기 표현 없이 자식만 펼친다
        elif text:
            chunk.append(pad + text)

        if chunk:
            # How: 리스트가 연달아 이어지는 경우를 빼면 블록 사이에 빈 줄을 넣는다.
            both_list = t in LIST_TYPES and prev in LIST_TYPES
            if lines and not both_list:
                lines.append("")
            lines.extend(chunk)
            prev = t

        if b.get("has_children") and kids is not None:
            child = blocks_to_md(nc, b["id"], kids, imgctx)
            if child:
                # 리스트 항목의 하위 블록은 부모에 바로 붙여야 중첩이 유지된다
                if t not in LIST_TYPES and lines:
                    lines.append("")
                lines.extend(child)
                prev = None

    return lines


def split_sections(lines):
    """
    '## 한국어' / '## English' H2를 기준으로 본문을 나눈다.
    해당 H2가 없으면 전체를 한 덩어리로 본다.
    """
    ko, en, head = [], [], []
    cur = head
    for ln in lines:
        m = re.match(r"^##\s+(.*)$", ln)
        if m:
            label = m.group(1).strip()
            if SECTION_KO.match(label):
                cur = ko
                continue
            if SECTION_EN.match(label):
                cur = en
                continue
        cur.append(ln)

    def clean(xs):
        return "\n".join(xs).strip("\n")

    if not ko and not en:
        return clean(head), ""
    # H2 앞에 있던 도입부는 한국어 쪽에 붙인다
    if head and ko:
        ko = head + [""] + ko
    elif head and not ko:
        ko = head
    return clean(ko), clean(en)


# --- 파일 렌더링 -------------------------------------------------------


def render_markdown(meta, ko, en):
    """frontmatter + 본문(탭 또는 단일)을 최종 마크다운 문자열로."""
    fm = {
        "title": meta["title"],
        "date": meta["date"],
        "lang_original": meta["lang_original"],
        "notion_id": meta["notion_id"],
    }
    front = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()

    body = [f"---\n{front}\n---", "", f"# {meta['title']}", ""]

    orig = meta["lang_original"]
    if ko and en:
        # 원문을 항상 첫 탭으로
        order = [("en", en), ("ko", ko)] if orig == "en" else [("ko", ko), ("en", en)]
        for lang, content in order:
            body.append(f"/// tab | {TAB_LABEL[(lang, lang == orig)]}")
            body.append(content)
            body.append("///")
            body.append("")
    else:
        # Why: 한쪽만 있으면 빈 탭이 생기지 않게 탭 위젯 자체를 만들지 않는다.
        body.append(ko or en)
        body.append("")

    return "\n".join(body).rstrip() + "\n"


def read_frontmatter(path):
    """파일 앞의 YAML frontmatter만 파싱. 실패하면 빈 dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end])
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def target_path(date_str):
    y = date_str[:4]
    ym = date_str[:7]
    return JOURNAL_DIR / y / ym / f"{date_str}.md"


# --- 메인 흐름 ---------------------------------------------------------


def extract_meta(page):
    props = page.get("properties", {})

    title = ""
    for _, p in props.items():
        if p.get("type") == "title":
            title = rich_text_to_md(p.get("title")).strip()
            break

    date_str = ""
    dp = props.get(PROP_DATE, {})
    if dp.get("type") == "date" and dp.get("date"):
        date_str = (dp["date"].get("start") or "")[:10]
    if not date_str:
        date_str = page.get("created_time", "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        raise SyncError(f"날짜를 정할 수 없음 (page {page.get('id')})")

    lang = "ko"
    lp = props.get(PROP_LANG, {})
    if lp.get("type") == "select" and lp.get("select"):
        lang = (lp["select"].get("name") or "ko").strip().lower()
    if lang not in ("ko", "en", "mixed"):
        lang = "ko"

    return {
        "title": title or date_str,
        "date": date_str,
        "lang_original": lang,
        "notion_id": page["id"],
    }


def replace_marked_region(path, body_lines, template, dry_run):
    """
    파일의 MARK_START~MARK_END 사이만 갈아끼운다.

    Why: 월 인덱스에는 사람이 쓴 회고나 메모가 들어갈 수 있다. 파일 전체를
         덮어쓰면 그게 매번 날아가므로, 자동 관리 구간을 마커로 격리한다.
    """
    block = [MARK_START] + body_lines + [MARK_END]

    if path.exists():
        text = path.read_text(encoding="utf-8")
        if MARK_START not in text or MARK_END not in text:
            # 마커가 없는 파일은 사람이 통째로 관리하는 것으로 보고 손대지 않는다
            print(f"  ! {path.relative_to(REPO_ROOT).as_posix()} 에 마커가 없어 건너뜁니다.")
            return None
        head = text.split(MARK_START)[0]
        tail = text.split(MARK_END, 1)[1]
        new = head + "\n".join(block) + tail
    else:
        new = template.replace("__AUTO__", "\n".join(block))

    if path.exists() and path.read_text(encoding="utf-8") == new:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8", newline="\n")
    return True


def entry_title(path):
    """일자 글의 제목. frontmatter title이 없으면 날짜를 쓴다."""
    return str(read_frontmatter(path).get("title") or path.stem)


def month_label(ym):
    """'2026-08' -> '2026년 8월'"""
    y, m = ym.split("-")
    return f"{y}년 {int(m)}월"


def entry_line(path, href):
    """
    목록 한 줄. 날짜와 제목을 통째로 링크에 넣는다.

    Why: 일기 목록은 훑어보는 게 전부라, 줄 전체가 눌리는 편이 편하다.
         연도는 월 제목에 이미 있으므로 날짜는 MM-DD 만 남긴다.
    """
    return f"- [**{path.stem[5:]}** · {entry_title(path)}]({href})"


MONTH_TEMPLATE = """---
title: "__YM__"
---

# __LABEL__

__AUTO__

[← 전체 목록](../../index.md)
"""

OVERVIEW_MARKER_HINT = (
    "docs/journal/index.md 에 마커가 없습니다. "
    f"월 목록을 자동 관리하려면 그 자리에 {MARK_START} / {MARK_END} 를 넣으세요."
)


def rebuild_indexes(dry_run=False):
    """
    디스크에 있는 일자 글을 기준으로 월 인덱스와 Overview의 월 목록을 다시 만든다.

    Why: Notion에서 온 글과 손으로 쓴 글이 섞여도 목록이 빠지지 않게 하려면
         Notion 응답이 아니라 실제 파일을 기준으로 삼아야 한다.
    """
    changed = []
    months = {}   # "2026-08" -> [Path, ...]

    for entry in JOURNAL_DIR.rglob("*.md"):
        if not ENTRY_RE.match(entry.name):
            continue
        months.setdefault(entry.stem[:7], []).append(entry)

    for ym in sorted(months):
        entries = sorted(months[ym], key=lambda p: p.stem, reverse=True)
        lines = [entry_line(p, p.name) for p in entries]
        path = JOURNAL_DIR / ym[:4] / ym / "index.md"
        template = (MONTH_TEMPLATE
                    .replace("__YM__", ym)
                    .replace("__LABEL__", month_label(ym)))
        r = replace_marked_region(path, lines, template, dry_run)
        if r:
            changed.append(path.relative_to(REPO_ROOT).as_posix())

    # Overview에는 월별로 묶은 글 목록 전체를 편다.
    # Why: 일기가 목적이라 Overview -> 월 -> 글 로 두 번 타는 것보다
    #      첫 화면에서 바로 고르는 편이 빠르다.
    overview = JOURNAL_DIR / "index.md"
    if overview.exists():
        lines = []
        for ym in sorted(months, reverse=True):
            lines.append(f"## {month_label(ym)}")
            lines.append("")
            entries = sorted(months[ym], key=lambda p: p.stem, reverse=True)
            lines += [entry_line(p, f"{ym[:4]}/{ym}/{p.name}") for p in entries]
            lines.append("")
        r = replace_marked_region(overview, lines[:-1] if lines else [], "", dry_run)
        if r is None:
            print(f"  ! {OVERVIEW_MARKER_HINT}")
        elif r:
            changed.append(overview.relative_to(REPO_ROOT).as_posix())

    return changed


def managed_files():
    """
    docs/journal 아래에서 notion_id를 가진 파일만 관리 대상으로 본다.

    Why: 같은 notion_id가 두 경로에 있을 수 있어(노션에서 Date를 바꾼 경우)
         dict가 아니라 목록으로 돌려준다. dict로 만들면 한쪽이 조용히 사라져
         고아 파일을 못 지운다.
    """
    found = []
    if not JOURNAL_DIR.exists():
        return found
    for p in JOURNAL_DIR.rglob("*.md"):
        nid = read_frontmatter(p).get("notion_id")
        if nid:
            found.append((normalize_id(str(nid)), p))
    return found


def sync(dry_run=False):
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise SyncError("환경변수 NOTION_TOKEN 이 설정되지 않았습니다.")

    version = os.getenv("NOTION_VERSION", DEFAULT_NOTION_VERSION)
    nc = Notion(token, version)

    ds_id = os.getenv("NOTION_DATA_SOURCE_ID")
    if ds_id:
        ds_id = normalize_id(ds_id)
    else:
        db_id = os.getenv("NOTION_DATABASE_ID")
        if not db_id:
            raise SyncError(
                "NOTION_DATABASE_ID 또는 NOTION_DATA_SOURCE_ID 중 하나가 필요합니다."
            )
        ds_id = resolve_data_source_id(nc, normalize_id(db_id))
    print(f"  data source: {ds_id}")

    flt = build_visibility_filter(nc, ds_id)
    pages = list(nc.paginate(f"/data_sources/{ds_id}/query", {"filter": flt}))
    print(f"  {PROP_VISIBILITY}={PUBLIC_VALUE} 페이지: {len(pages)}건")

    seen, created, updated, unchanged = set(), [], [], []
    expected = {}       # notion_id -> 이 글이 있어야 할 경로
    used_images = {}    # 이미지 폴더 -> 지금도 쓰이는 파일명 집합
    images = []         # 새로 받았거나 내용이 바뀐 이미지
    for page in pages:
        meta = extract_meta(page)
        nid = normalize_id(meta["notion_id"])
        seen.add(nid)
        expected[nid] = target_path(meta["date"])

        path = target_path(meta["date"])
        imgctx = ImageContext(path.parent / IMG_DIR_NAME, dry_run)
        ko, en = split_sections(blocks_to_md(nc, page["id"], imgctx=imgctx))
        content = render_markdown(meta, ko, en)
        for name in imgctx.saved:
            used_images.setdefault(imgctx.img_dir, set()).add(name)
        images += [p.relative_to(REPO_ROOT).as_posix() for p in imgctx.written]

        rel = path.relative_to(REPO_ROOT).as_posix()
        old = path.read_text(encoding="utf-8") if path.exists() else None

        if old is None:
            created.append(rel)
        elif old != content:
            prev = read_frontmatter(path).get("notion_id")
            if prev and normalize_id(str(prev)) != normalize_id(meta["notion_id"]):
                raise SyncError(
                    f"{rel} 는 다른 notion_id({prev})가 이미 차지하고 있습니다. "
                    "같은 날짜에 Public 글이 2개인지 확인하세요."
                )
            if not prev:
                print(f"  ! {rel} 는 수동 작성 파일이었습니다. 덮어씁니다.")
            updated.append(rel)
        else:
            unchanged.append(rel)
            continue

        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")

    # reconcile: Public에서 빠졌거나, 날짜가 바뀌어 경로가 옮겨간 파일 삭제
    removed = []
    for nid, path in managed_files():
        if nid in seen and path == expected.get(nid):
            continue
        why = "Public 해제" if nid not in seen else "날짜 변경으로 이동"
        rel = path.relative_to(REPO_ROOT).as_posix()
        removed.append(f"{rel}  ({why})")
        if not dry_run:
            path.unlink()

    # 더 이상 쓰이지 않는 이미지 정리
    # Why: 글에서 사진을 빼거나 글이 Private으로 바뀌면 파일만 레포에 남는다.
    # How: 동기화가 만든 이름 규칙에 맞는 파일만 지운다. 손으로 넣은 이미지는 건드리지 않는다.
    img_dirs = set(used_images) | {d for d in JOURNAL_DIR.rglob(IMG_DIR_NAME) if d.is_dir()}
    for img_dir in sorted(img_dirs):
        if not img_dir.exists():
            continue
        keep = used_images.get(img_dir, set())
        for f in sorted(img_dir.iterdir()):
            if not f.is_file() or f.name in keep:
                continue
            if not SYNCED_IMG_RE.match(f.name):
                continue    # 사람이 넣은 파일
            removed.append(f"{f.relative_to(REPO_ROOT).as_posix()}  (미사용 이미지)")
            if not dry_run:
                f.unlink()
        if not dry_run and not any(img_dir.iterdir()):
            img_dir.rmdir()

    # 글이 확정된 뒤에 인덱스를 다시 만든다(삭제분까지 반영되도록)
    indexes = rebuild_indexes(dry_run)

    tag = "[dry-run] " if dry_run else ""
    for label, items in (
        ("created", created), ("updated", updated),
        ("removed", removed), ("image 저장", images),
        ("index 갱신", indexes), ("unchanged", unchanged),
    ):
        if items:
            print(f"  {tag}{label} {len(items)}건")
            for i in items:
                print(f"    - {i}")
    if not (created or updated or removed or images or indexes):
        print(f"  {tag}변경 없음")
    return 0


def discover(ref):
    """페이지 URL/ID만 알 때 부모 database/data source ID를 찾아준다."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise SyncError("환경변수 NOTION_TOKEN 이 설정되지 않았습니다.")
    nc = Notion(token, os.getenv("NOTION_VERSION", DEFAULT_NOTION_VERSION))
    page = nc.get(f"/pages/{normalize_id(ref)}")
    parent = page.get("parent", {})
    print(f"  page id        : {page.get('id')}")
    print(f"  parent type    : {parent.get('type')}")
    for key in ("data_source_id", "database_id"):
        if parent.get(key):
            print(f"  {key:<15}: {parent[key]}")
    print(f"  properties     : {', '.join(sorted(page.get('properties', {})))}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Notion -> MkDocs Journal 동기화")
    ap.add_argument("--dry-run", action="store_true",
                    help="파일을 쓰지 않고 무엇이 바뀔지만 출력")
    ap.add_argument("--discover-from-page", metavar="URL_OR_ID",
                    help="페이지의 부모 database/data source ID를 조회")
    args = ap.parse_args()

    try:
        if args.discover_from_page:
            return discover(args.discover_from_page)
        return sync(dry_run=args.dry_run)
    except SyncError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
