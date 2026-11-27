---
name: "motion-visualization"
description: "모션시각화. Turn an existing document, guide, lecture note or product explainer into a motion magazine (swipeable deck or scroll, single HTML) or an explainer video (auto-playing HTML + silent MP4, 16:9 / 9:16), Korean-first. Use when the user asks for a magazine-style manual, a motion visualization, an explainer video or shorts from a document, '매거진으로 만들어줘', '모션시각화', '쇼츠로', or an easy beginner edition. The agent writes only content.json; the bundled template, build.py, check.py and record.py handle design, motion, cognitive-load checks, screen checks and recording. Does not do new research or publish anything."
---

# 모션시각화 (motion-visualization)

원본 문서 → 공식 로고·사진 → 좌우로 넘겨 보는(기본) 또는 스크롤하는 움직이는 매거진형 HTML 한 파일. **AI가 쓰는 것은 `content.json` 하나**다. 디자인·동작·점검은 `assets/template.html`, `scripts/build.py`, `scripts/check.py`가 맡는다.

## 결과물 고르기

| 형식 | 언제 | 양식 |
|---|---|---|
| 매거진(넘겨 보기 기본·스크롤) | 읽고 따라 하는 안내서, 출처·체크리스트가 중요할 때 | `references/content-format.md` |
| **설명 영상 PPT판** (16:9) | 글을 줄이고 보여 주며 설명할 때, 발표·유튜브 | `references/explainer-format.md` |
| **설명 영상 숏폼판** (9:16) | 쇼츠·릴스·휴대폰 공유 | 같은 JSON, `--ratio 9:16` |

설명 영상의 장면 구성은 `references/visual-research.md`(인기 강의 연구)를 따른다.

## 시작 전에 먼저 묻기 (필수)

작업을 시작하기 전에 **무엇을 어떤 비율로 만들지** 한 번에 묻고, 답을 받은 뒤 시작한다. 여러 형식을 미리 다 만들지 않는다.

- 묻는 방법: 에이전트에 선택형 질문 도구가 있으면 그걸 쓰고, 없으면 채팅에 번호로 짧게 묻는다. 질문은 한 번에 모아서 한다.
- 질문은 **두 개**다. 형식과 비율을 한 질문으로 합쳐, 고르지 않은 형식에만 해당하는 질문이 나가지 않게 한다 (원본 내용·쓰임새에 맞는 선택지 하나에 '추천' 표시):
  1. **형식**: ① 매거진(넘겨 보는 안내서, HTML) ② 설명 영상 16:9 PPT판 ③ 설명 영상 9:16 숏폼판 ④ 설명 영상 둘 다
  2. **영상 파일**: ① HTML만 ② HTML + MP4 (매거진이면 장면을 하나씩 넘기는 MP4, 설명 영상이면 자동 재생 MP4)
- 요청에 이미 형식·비율이 적혀 있으면 그 부분은 다시 묻지 않는다. 예: "쇼츠로"는 설명 영상 9:16, "PPT로"는 16:9, "매거진으로"는 매거진. "영상은 빼고"면 2번도 묻지 않는다.
- 같은 작업의 다음 편(예: 1일차 다음 2·3일차)은 앞에서 고른 형식을 그대로 쓰고 다시 묻지 않는다.
- 답을 기다리는 동안 할 수 있는 준비(원본 읽기, 공식 로고 찾기)는 먼저 해 둬도 된다. 조립·녹화는 답을 받은 뒤 한다.
- 고른 것만 만든다. 둘 다 고르면 같은 JSON으로 두 판을 만든다.

## 진행 순서

1. **입력 확정.** 위 '시작 전에 먼저 묻기'로 형식·비율을 정한다. 원본 문서, 읽을 사람, 수준(전문가판 / 초보자판 / 둘 다). 요청에 없으면 전문가판 하나. "쉽게, 초보, 초등학생"이면 초보자판. 결과는 작업 폴더에 저장.
2. **핵심 뽑기(머릿속 메모, 채팅에 길게 쓰지 않기).** 결론 한 문장, 맞는/안 맞는 사람, 단계, 주의·금지, 실제 기록, 확인한 것/못 한 것, 원문 예시와 새 아이디어 구분.
2-1. **읽는 목적 정하기(묻지 않음).** 내용이 장면 3개가 안 되면 표 하나나 짧은 답이 더 나은지 먼저 따져 보고 보고에 적는다. `references/cognitive-load.md`를 읽고 `meta.goal`(누가 읽고 무엇을 정하나)·`purpose`(decide/learn/do)를 적는다. 두 대상 비교면 `sides`로 왼쪽·오른쪽과 색을 고정하고, 첫 장면은 `decide`, 비교는 `compare` 표로 쓴다.
3. **이미지.** `assets/brands/` 보관함 먼저(공개판에는 상표 파일 대신 받는 곳·규칙을 적은 `sources.json`만 있다). 없으면 `references/image-sourcing.md` 순서로 공식 자료를 받아 보관함에 넣고 `sources.json`을 쓴다. 설명하는 웹사이트 자체의 화면은 `scripts/capture.py`로 찍어 작업 폴더 `assets/`에 둔다(보관함에 넣지 않음).
4. **옷 고르기.** `paper`(잡지·따뜻한 종이), `calm`(회사·기술 남색), `warm`(생활·요리·교육), `night`(어두운 화면). 브랜드 색이 뚜렷하면 `meta.accent`로 강조색만 바꾼다.
5. **content.json 작성.** 양식은 `references/content-format.md`. 초보자판은 `references/beginner-rules.md`도 따른다. 둘 다 만들면 파일 두 개(같은 사실, 다른 말).
6. **조립.** `python <스킬>/scripts/build.py content.json -o <출력폴더>/<이름>.html` → 경고(이미지 없음, 긴 줄표, 모르는 블록, `인지부하:` 반복·단위 섞임·한 칸 두 대상·색 뒤집힘·미확인 위치·장면 수)를 고치고 다시 조립.
7. **점검.** `check.py <html> --shots <tmp>/shots --full` 한 번. 넘겨 보기 버튼·키·스와이프까지 눌러 본다. 실패 항목만 고친다. 볼 그림은 `slides-sheet.png`(모든 장면 한 장 모아보기)와 `cover-390.png` 두 장.
   `check.py`가 "장면 안 스크롤 필요" 경고를 내면 그 장면의 항목을 줄이거나 섹션을 나눈 뒤 다시 조립한다. `build.py`의 밀도 경고(블록 4개 이상, 항목 수 초과)도 같은 뜻이다.
7-1. **설명 영상이면** `check.py`의 `beats-1280.png`(모든 비트 모아보기) 한 장으로 확인한다. 숏폼판을 골랐으면 `build.py --ratio 9:16`으로 HTML을 따로 만든다. MP4를 골랐을 때만 `scripts/record.py`로 만든다(한 판만이면 `--ratio 16:9` 또는 `--ratio 9:16`, 둘 다면 `--both`). 만든 뒤 `ffprobe`로 길이·해상도를 확인한다. 영상은 무음이다.
7-2. **매거진 MP4를 골랐으면** 같은 `record.py`가 넘겨 보기 HTML을 알아보고 장면마다 `--hold`초(기본 5) 보여 주며 녹화한다. 장면 안에서 스크롤해야 보이는 부분은 영상에 나오지 않으므로, 넘침 경고를 먼저 없앤다. 만든 뒤 한 장면을 `ffmpeg -ss`로 뽑아 확인한다.
7-3. **여러 편 묶음(시리즈)이면** 각 편의 `meta.series`에 같은 목록을 넣고 자기 편에만 `"current": true`를 준다. 표지와 맨 아래에 편 사이 이동 링크가 생긴다. 파일 이름은 편 번호가 들어간 영문·숫자 위주로 짓는다.
7-4. **스킬 파일(템플릿·스크립트)을 고쳤으면** `scripts/selftest.py --browser`를 돌려 FAIL 0을 확인한다(`tests/TESTS.md`).
8. **보고.** 파일 위치, `goal` 한 줄, 품질 점수표와 PASS/FAIL/NOT RUN(`references/quality-gate.md`, 시험 안 한 항목은 만점 금지), 점검 결과(통과/미확인 구분, 남긴 인지부하 경고와 이유), 확인한 것·못 한 것, 그림 출처, 원문과 달라진 점. 대표 캡처 1장을 첨부한다.

## 실행 환경

- 조립(`build.py`): 파이썬 3 표준 라이브러리만 필요. Pillow가 있으면 큰 그림을 자동으로 줄인다. 출력은 UTF-8로 고정해 한국어 Windows 콘솔에서도 깨지지 않는다.
- 점검(`check.py`)·캡처(`capture.py`)·녹화(`record.py`): Playwright와 Chrome/Edge/Chromium이 필요하다. 녹화는 시스템 `ffmpeg`도 필요하다. 없으면 `check.py`는 정적 점검만 하고 SKIP을 출력한다. 이때는 "화면 점검 미확인"이라고 알린다.
- 캡처: `capture.py <주소> -o <작업폴더>/assets/site.png [--nav 2] [--click "버튼 글자"]`. 에이전트 브라우저 캡처가 시간 초과될 때도 쓴다.
- PowerShell에서 한글이 붙은 파일 이름을 변수로 만들 때 `"$n일차"`처럼 쓰지 않는다(변수 이름으로 읽혀 비어 버림). `"${n}일차"`를 쓴다.
- 여러 파이썬이 섞여 Playwright를 못 찾으면 Playwright가 설치된 파이썬으로 직접 실행하고, 필요하면 `PYTHONHOME`·`PYTHONPATH` 환경 변수를 비운다.

**파이썬을 실행할 수 없는 환경이면:** `assets/template.html`을 복사해 `__CONTENT_JSON__` 자리에 content.json을 넣고(`</`는 `<\/`로), `__TITLE__`을 제목으로 바꾼다. 이미지는 `https://` 주소나 data URI로 넣는다. 이 경우 인지부하 경고와 화면 점검은 받을 수 없다.
## 피드백을 받으면

`references/quality-gate.md`의 '피드백을 받았을 때' 5단계를 따른다. 사용자 말과 내 추측을 나누고, 고칠 곳 하나와 다음 실험 하나를 제안한다.

## 지키는 것

- 원문에 없는 사실·숫자·성공 경험을 만들지 않는다. 미확인은 초보자판에서도 지우지 않는다.
- `template.html`을 읽지 않는다. content.json을 채팅에 통째로 다시 쓰지 않는다(`references/pitfalls.md`).
- 로고는 공식 자료만, 변형 금지, 출처 표시. 재구성 화면·AI 그림은 그렇다고 밝힌다.
- 파일 만들기까지만 한다. 업로드·공유·게시는 사용자가 따로 요청할 때만.
- 새 블록이 정말 필요할 때만 템플릿에 추가하고 content-format.md 표를 갱신한다.
