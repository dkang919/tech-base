---
title: Journal
---

# 📓 Journal

Notion에 쓴 일기 · 잡글 · 아이디어 중 **Public으로 발행한 글만** 이곳에 올라옵니다.

!!! info "공개 범위"
    Private / Shared 로 표시된 글은 이 저장소(`dkang919/tech-base`)에 **포함되지 않습니다.**
    이 사이트에 존재한다는 것 자체가 "Public으로 발행했다"는 뜻입니다.

기본은 **하루 1개 글**이지만, 쓰지 않은 날은 그냥 비어 있습니다.
빈 날짜를 채우기 위한 글은 쓰지 않습니다.

---

## 월별 보기

<!-- sync:auto:start -->
### 2026

- [2026-08](2026/2026-08/index.md) — 2편
<!-- sync:auto:end -->

---

## 글 구성 규칙

두 언어로 쓴 글은 **한국어 / English 탭**으로 나뉩니다.
탭 제목에 `(원문)` 이 붙은 쪽이 먼저 쓴 글이고, 나머지는 번역본입니다.

- 한국어로 먼저 썼으면 → `한국어 (원문)` + `English (Translated)`
- 영어로 먼저 썼으면 → `English (Original)` + `한국어 (번역)`

한 언어로만 쓴 글은 탭 없이 본문만 나옵니다. 빈 탭은 만들지 않습니다.

---

## 경로 규칙

```text
docs/journal/
├── index.md                        ← 지금 이 페이지
├── _template.md                    ← 새 글 복사용 (사이트에는 빌드되지 않음)
└── 2026/
    └── 2026-08/
        ├── index.md                ← 월 인덱스
        └── 2026-08-09.md           ← 일자 글
```

새 글을 추가할 때 필요한 규칙은 하나뿐입니다.

- 파일 경로는 `docs/journal/YYYY/YYYY-MM/YYYY-MM-DD.md`

월 인덱스와 위 **월별 보기** 목록은 `tools/sync_journal.py` 가 자동으로 다시 씁니다.
`mkdocs.yml`은 건드릴 필요가 없습니다.

Notion에서 `Visibility=Public` 으로 발행한 글은 `tools/sync_journal.py` 가
위 경로로 자동 생성합니다. 자세한 실행 방법은 `tools/README.md` 를 보세요.
