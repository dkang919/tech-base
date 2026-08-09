# tools

```text
tools/
├── sync_journal.py   ← 실제 동작하는 코드 (커밋됨)
├── README.md
└── debug/            ← 임시 확인/디버깅 스크립트 (gitignore, 커밋 안 됨)
```

**`tools/debug/` 규칙**: 일회성 진단·확인 스크립트는 전부 여기에만 만든다.
핵심 코드와 섞지 않기 위한 격리 폴더이고 `.gitignore`에 등록되어 있어
커밋되지 않는다. 자유롭게 만들고 지워도 된다.

---

## sync_journal.py — Notion → MkDocs Journal 동기화

Notion Journal DB에서 **`Visibility=Public`** 인 글만 가져와
`docs/journal/YYYY/YYYY-MM/YYYY-MM-DD.md` 로 생성/갱신하고,
Public에서 빠진 글은 삭제한다.

의존성은 `requests`, `PyYAML` 뿐이고 둘 다 `requirements.txt`에 이미 있다.

---

### 1. Notion 준비 (최초 1회)

1. <https://www.notion.so/my-integrations> 에서 **New integration** 생성
   → Internal integration secret(`ntn_...`) 발급
2. Journal DB 페이지 → 우측 상단 `...` → **Connections** → 만든 integration 추가
   - 이걸 안 하면 API가 DB를 못 본다 (404 또는 결과 0건)
3. DB에 아래 속성이 있어야 한다

   | 속성 | 타입 | 비고 |
   | --- | --- | --- |
   | (제목) | title | 이름은 아무거나. 타입이 title이면 자동 인식 |
   | `Date` | date | 파일 경로와 `date` frontmatter |
   | `Visibility` | select | `Private` / `Shared` / `Public` — **기본값 Private 권장** |
   | `Lang original` | select | `ko` / `en` / `mixed` |

   속성 이름이 다르면 아래 환경변수로 덮어쓸 수 있다.

---

### 2. 환경변수

**토큰은 절대 레포에 커밋하지 않는다.** 셸 세션에만 넣는다.

| 변수 | 필수 | 설명 |
| --- | --- | --- |
| `NOTION_TOKEN` | ✅ | Internal integration secret |
| `NOTION_DATABASE_ID` | ✅* | Journal DB ID |
| `NOTION_DATA_SOURCE_ID` | — | DB ID 대신 직접 지정할 때 |
| `NOTION_VERSION` | — | 기본 `2026-03-11` |
| `NOTION_PROP_DATE` | — | 기본 `Date` |
| `NOTION_PROP_VISIBILITY` | — | 기본 `Visibility` |
| `NOTION_PROP_LANG` | — | 기본 `Lang original` |
| `NOTION_PUBLIC_VALUE` | — | 기본 `Public` |

\* `NOTION_DATABASE_ID` 와 `NOTION_DATA_SOURCE_ID` 중 하나만 있으면 된다.

**권장: 레포 루트에 `.env` 파일**

```bash
cp .env.example .env
```

그 다음 `.env` 를 열어 값을 채운다. 스크립트가 자동으로 읽는다.
`.env` 는 `.gitignore`에 등록되어 있어 커밋되지 않는다.

셸에 직접 넣어도 된다(이미 설정된 환경변수가 `.env`보다 우선한다).

```powershell
$env:NOTION_TOKEN = "ntn_..."
```

```bash
export NOTION_TOKEN="ntn_..."
```

---

### 3. 실행

DB ID를 모를 때 — 글 URL만 있으면 부모 DB를 찾아준다:

```bash
python tools/sync_journal.py --discover-from-page https://app.notion.com/p/<page-id>
```

무엇이 바뀔지만 확인 (파일을 쓰지 않음):

```bash
python tools/sync_journal.py --dry-run
```

실제 동기화:

```bash
python tools/sync_journal.py
```

빌드 확인:

```bash
python -m mkdocs build --strict
```

---

### 4. 동작 규칙

- **대상**: `Visibility=Public` 인 페이지 **전체**가 정답 집합
- **본문**: 페이지 본문의 `## 한국어` / `## English` H2로 언어를 나눈다
  - 둘 다 있으면 `pymdownx.blocks.tab` 탭으로, 원문 언어가 첫 탭
  - 한쪽만 있으면 **탭 없이 본문만** (빈 탭을 만들지 않는다)
- **frontmatter**: `title`, `date`, `lang_original`, `notion_id`
- **reconcile**: `docs/journal/` 아래에서 frontmatter에 `notion_id` 가 있는
  파일만 관리 대상이다.
  - Public 집합에 없는 관리 대상 파일은 **삭제**한다
  - `notion_id` 가 없는 파일(월 인덱스, 수동 작성 글, `_template.md`)은
    **절대 건드리지 않는다**

즉 Notion에서 글을 Public → Private으로 되돌리면 다음 실행 때 사이트에서도 사라진다.

#### 인덱스 자동 갱신

동기화가 끝나면 아래 두 곳의 목록을 다시 만든다.

- `docs/journal/YYYY/YYYY-MM/index.md` 의 글 목록 (없으면 새로 만든다)
- `docs/journal/index.md` 의 월별 보기 목록

**Notion 응답이 아니라 디스크의 파일을 기준으로** 만들기 때문에,
손으로 쓴 글도 목록에 함께 들어간다.

갱신되는 것은 아래 마커 사이 구간뿐이다.

```markdown
<!-- sync:auto:start -->
- [2026-08-09](2026-08-09.md) — 글 제목
<!-- sync:auto:end -->
```

마커 **밖**에 쓴 내용(그 달의 회고, 메모, 이전/다음 달 링크 등)은 보존된다.
마커가 아예 없는 인덱스 파일은 사람이 통째로 관리하는 것으로 보고 건너뛴다.

---

### 5. 아직 안 되는 것

- **이미지/첨부 미지원.** Notion이 주는 파일 URL은 서명된 임시 링크라
  그대로 넣으면 한 시간쯤 뒤에 깨진다. 지금은 본문에서 빼고
  `<!-- TODO: image 미동기화 -->` 주석만 남긴다.
  나중에 파일을 내려받아 레포에 저장하는 단계를 추가해야 한다.
- **GitHub Actions 미연동.** 지금은 로컬에서 수동 실행한다.
  자동화하려면 `NOTION_TOKEN` 을 repo secret으로 넣고 워크플로를 추가하면 된다.
