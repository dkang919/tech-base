---
title: "YYYY-MM-DD"
date: YYYY-MM-DD
lang_original: ko   # 먼저 쓴 언어: ko 또는 en
---

# YYYY-MM-DD — 글 제목

[← YYYY-MM](index.md)

/// tab | 한국어 (원문)
본문을 여기에 씁니다. 들여쓰기는 필요 없습니다.

- 리스트
- 코드 블록 모두 그대로 쓰면 됩니다

닫는 `///` 를 빠뜨리지 마세요.
///

/// tab | English (Translated)
Write the translation here.
///


<!--
================================================================
사용법
================================================================

1. 이 파일을 복사해서
   docs/journal/YYYY/YYYY-MM/YYYY-MM-DD.md 로 저장

2. front matter의 title / date / lang_original 을 채운다

3. 영어로 먼저 썼다면 탭 제목과 순서를 바꾼다
   lang_original: en
   /// tab | English (Original)
   /// tab | 한국어 (번역)

4. 한쪽 언어만 쓸 거라면 탭을 만들지 말고 본문만 쓴다
   (빈 탭은 만들지 않는다)

5. 목록은 손대지 않아도 된다. tools/sync_journal.py 가 파일을 보고 다시 쓴다.

주의
- 이 파일(_template.md)은 mkdocs.yml의 exclude_docs 에 등록되어 있어
  사이트에는 빌드되지 않습니다. 템플릿 위치를 옮기면 그 설정도 함께 고치세요.
- Private / Shared 글은 이 경로에 넣지 않습니다.
- Notion에서 동기화되는 글에는 frontmatter에 notion_id 가 붙습니다.
  그 파일은 tools/sync_journal.py 가 관리하므로 직접 고치지 마세요
  (다음 동기화 때 덮어써집니다). 이 템플릿으로 만든 수동 글에는
  notion_id 를 넣지 마세요 — 동기화가 건드리지 않습니다.
================================================================
-->
