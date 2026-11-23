---
name: "motion-visualization"
description: "모션시각화. Turn an existing document, guide, lecture note or product explainer into a motion magazine-style single HTML page (Korean-first), optionally with an expert and a beginner (easy-words) edition. Use when the user asks for a magazine-style manual, a 'motion visualization', '매거진으로 만들어줘', '모션시각화', or an easy version for beginners/children. The agent writes only content.json; the bundled template, build.py and check.py handle design, motion and checks to save tokens. Does not do new research or publish anything."
---

# 모션시각화 (motion-visualization)

원본 문서 → 움직이는 매거진형 HTML 한 파일. **AI가 쓰는 것은 `content.json` 하나**다. 디자인·모션·점검은 `assets/template.html`, `scripts/build.py`, `scripts/check.py`가 맡는다. 사용자 언어로 쓰되 기본 예시는 한국어다.

## 진행 순서

1. **입력 확정.** 원본 문서, 읽을 사람, 수준(전문가판 / 초보자판 / 둘 다). 말이 없으면 전문가판 하나. "쉽게·초보·아이도"라는 말이 있으면 초보자판.
2. **핵심 뽑기(짧게, 채팅에 길게 쓰지 않기).** 결론 한 문장, 맞는/안 맞는 사람, 단계, 주의·금지, 실제 기록, 확인한 것/못 한 것, 원문 예시와 새 아이디어 구분.
3. **이미지.** `assets/brands/<브랜드>/`를 먼저 본다. 공개판에는 상표 파일 대신 `sources.json`(받는 곳·규칙)만 있다. 필요하면 `references/image-sourcing.md` 순서로 공식 자료를 받는다. 받을 수 없는 환경이면 이미지 없이 만든다(빈 자리는 점선 상자로 보임).
4. **옷 고르기.** `paper`(잡지), `calm`(회사·기술), `warm`(생활·교육), `night`(어두운 화면). 브랜드 색은 `meta.accent`로.
5. **content.json 작성.** `references/content-format.md` 양식. 초보자판은 `references/beginner-rules.md`도 따른다.
6. **조립.** `python scripts/build.py content.json -o out.html` (파이썬 3 표준 라이브러리만 필요). 경고를 고치고 다시 조립.
7. **점검.** `python scripts/check.py out.html --shots shots/`. Playwright와 Chrome/Edge/Chromium이 있으면 1280px·390px로 열어 오류·가로 넘침·팝업·복사·체크리스트를 눌러 보고 캡처 2장을 남긴다. 없으면 정적 점검만 하고 SKIP을 출력한다. 이때는 "화면 점검 미확인"이라고 알린다.
8. **보고.** 파일 위치, 점검 결과(통과/미확인 구분), 확인한 것·못 한 것, 그림 출처, 원문과 달라진 점.

**파이썬을 실행할 수 없는 환경이면:** `assets/template.html`을 복사해 `__CONTENT_JSON__` 자리에 content.json을 넣고(`</`는 `<\/`로), `__TITLE__`을 제목으로 바꾼다. 이미지는 `https://` 주소나 data URI로 넣는다.

## 지키는 것

- 원문에 없는 사실·숫자·성공 경험을 만들지 않는다. 미확인은 초보자판에서도 지우지 않는다.
- `template.html` 전체를 읽지 않는다. content.json을 채팅에 통째로 다시 쓰지 않는다(`references/pitfalls.md`).
- 로고는 공식 자료만, 변형 금지, 출처 표시. 재구성 화면·AI 그림은 그렇다고 밝힌다.
- 파일 만들기까지만 한다. 업로드·공유·게시는 사용자가 따로 요청할 때만.
