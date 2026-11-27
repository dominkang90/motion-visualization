# content.json 양식

AI가 직접 쓰는 것은 이 파일 하나다. 대부분의 문자열에는 짧은 HTML(`<b> <em> <br> <code> <a>`)을 쓸 수 있다.
**평문만 되는 칸**(HTML이 글자로 보임): `meta.brand`, `stats`의 값·단위, `callout.label`, `cover.stage`의 labels·chips, `code`, `prompt.text`, `words.copyLabel`. 코드·프롬프트 원문은 `code`/`prompt.text`에 그대로 넣는다(자동 이스케이프).

## 최상위

```json
{
  "meta": {"title": "브라우저 제목", "brand": "표지 큰 제목", "issue": "오른쪽 작은 줄<br>둘째 줄",
           "theme": "paper|calm|warm|night", "accent": "#hex(선택)", "level": "expert|beginner", "mode": "deck|scroll",
           "storageKey": "체크리스트 저장 이름", "labels": {"step": "단계", "more": "더 알아보기", "ok": "잘 됐나요?"},
           "goal": "누가 읽고 무엇을 정하나(한 문장)", "purpose": "decide|learn|do", "sides": ["왼쪽 대상", "오른쪽 대상"], "terms": ["반복 허용 고유명사"]},
  "images": {"logo": "brand:pickle/logo.svg", "shot": "assets/screen.png", "web": "https://..."},
  "cover": {"kicker": "", "title": "줄<br><em>강조</em>", "sub": "", "lines": [["굵은 말", "설명"]],
            "stage": {"left": "@a", "center": "@b", "right": "@c", "labels": ["", "", ""], "chips": ["", ""]}},
  "sections": [{"nav": "목차 이름", "kicker": "", "title": "", "lede": "", "dark": false, "blocks": []}],
  "footer": {"logos": ["@logo"], "html": "맨 아래 한 줄"}
}
```

- `goal`·`purpose`·`sides`·`terms`는 인지부하 점검용이다. 규칙은 `references/cognitive-load.md`.
- 본문 아무 문자열에서나 그 자리에 사실 상태를 붙인다: `<span class="unv">미확인</span>`(출처 못 찾음), `<span class="est">추정</span>`(계산·어림값), `<span class="sim">예시</span>`(지어낸 예·모의 화면). 표시가 없는 문장은 확인한 사실로 읽힌다.
- 이미지는 `images`에 한 번 등록하고 블록에서는 `"@이름"`으로 부른다. `brand:` = 로고 보관함, 상대경로 = content.json 기준.
- `stage`는 세 이미지(left/center/right) 또는 그림 하나(`"hero": "@x"`).
- `mode`: 기본 `deck`(한 섹션 = 한 장면, ‹ › 버튼·← → 키·스와이프·터치패드 좌우로 넘김, 3D 전환). `scroll`은 한 페이지로 길게. 보는 사람은 위쪽 버튼이나 주소 뒤 `?mode=scroll`로 바꿀 수 있다. 넘겨 보기에서는 한 장면에 블록 2~3개가 읽기 좋다.
- `stage.hero`가 있으면 left/center/right/chips는 무시된다(둘 중 하나만).
- `meta.series`(선택): 여러 편 묶음. `{"title": "묶음 이름", "items": [{"label": "1일차", "href": "day1.html"}, {"label": "2일차", "href": "day2.html", "current": true}]}`. 모든 편에 같은 목록을 넣고 `current`만 바꾼다. 표지 제목 아래와 맨 아래에 이동 링크가 나온다. href는 같은 폴더 상대 경로를 쓴다.
- verdict `stats`는 2·3·4·6개가 깔끔하다(4개는 한 줄 4칸, 휴대폰은 2칸). 5개는 3+2로 줄이 바뀐다.

## 넘겨 보기 한 장면 분량 (노트북 1280x800 기준)

넘으면 `build.py`가 경고하고, 실제로 장면이 넘치면 `check.py`가 "장면 안 스크롤 필요"를 알린다. 줄이기보다 섹션을 둘로 나누는 쪽이 낫다.

| 블록 | 권장 최대 |
|---|---|
| 한 장면의 블록 | 3개 |
| folders · rules | 6개 |
| diagram nodes | 6개 |
| dict · faq | 8개 |
| agenda · checklist | 10개 |
| steps | 4개 |
| cases (모든 그룹의 카드 합) | 4개. 원문 예와 새 아이디어가 많으면 두 장면으로 |
| compare rows | 8개 |
| decide items | 4개 |

diagram에서 `hub` 카드의 `chip`도 순번에 넣는다(예: `"3 · 핵심"`). "핵심"만 쓰면 1, 2, 핵심, 3처럼 번호가 어긋난다. `wires` 개수는 카드 수 빼기 1로 맞춘다.
- `labels` 키: prev, nextSlide, modeScroll, modeDeck, swipeHint, copy, copied, more, step, close, progress, done, doneTail, allDone, ok, okGood, okBad, sources, know, does, key, good, bad, next. 기본값은 전문가판 문구(STEP, 자세히, 성공 확인, 진행률 등).
- 섹션 번호는 자동(01, 02…). `no`로 번호를, `id`로 앵커를 직접 정할 수 있다. `"dark": true`는 검은 배경 섹션(강조할 한 곳에만).

## 필수 조건 (build.py가 "필수" 경고 + 종료코드 1)

- steps.items[].title, words.items[].say, diagram.nodes[].title는 꼭 채운다.
- faq·dict·checklist·cases는 항목이 1개 이상. timing은 start·end가 `[시각, 설명]`.
- checklist는 페이지당 1개만.

## 블록 (type별 필드)

| type | 필드 | 쓰는 곳 |
|---|---|---|
| decide | items[{q, yes, to, no, noTo, yesLabel, noLabel}], end | 결정용 첫 장면. 예/아니오는 버튼이라 누르면 그 길만 밝게 남고 나머지는 흐려짐('다시 고르기'). 처음에는 모두 보여 MP4·인쇄에도 내용이 남음. 질문마다 예→결과(to: "a"/"b"/대상 이름이면 그 색), 아니오→no(비우면 "다음 질문으로"). end는 끝까지 아니오일 때 |
| compare | cols[이름 또는 {name,logo}] (없으면 meta.sides), keyTitle, rows[[기준, 왼쪽html, 오른쪽html, 유리("a"/"b"/이름, 선택)]], note, winLabel | 두 대상 비교. 열 순서·색 고정, 유리한 칸만 그 대상 색 |
| verdict | quote, stats[[값,단위,설명]], fit{good[],bad[],goodTitle,badTitle}, next{label,html} | 첫 섹션 결론. 값이 정수면 숫자가 올라가는 모션 |
| scenes | items[{logo,alt,quote,text,dark}], bridge{icon,alt,html} | 문제 두 장면 비교 |
| diagram | nodes[{key,img,chip,title,sub,hub,detail}], wire 또는 wires[] | 눌러 보는 구조도. detail은 문자열 3개(아는 것/하는 것/열쇠) 또는 [[제목,내용]] |
| chips | items[html] | 숫자 강조 알약들 (`<b>0</b>`) |
| callout | label, html | 한 줄 경고·약속 |
| dict | items[[낱말, 풀이html]] | 용어 사전 (초보자판 필수) |
| folders | items[{name,tag,tone(a1/a2),text}] | 폴더·분류 카드 |
| rules | title, items[html], aside[[제목,내용]] | 번호 규칙 + 오른쪽 검은 상자 |
| steps | label, items[{no,where[],title,html,list[],code,media{img,alt,caption},note,ok,okLabel,prompt{text,why[[굵게,설명]]},detail[[항목,내용]]}] | 단계. detail이 있으면 "자세히" 팝업 |
| words | items[{when,say,who{img,text},copyLabel}] | 따라 말할 문장(복사 버튼). 보통 dark 섹션 |
| lanes | items[{icons[@a,@b],title,tone(b),steps[html 또는 {html,say}]}] | 두 방향 흐름 |
| timing | start[시각,설명], mid, end[시각,설명], note | 실제 기록 시간 |
| annotated | card{title,num,status,meta,branch,blocks[[머리,내용]]}, caption, notes[[제목,설명]], code, codeNote | 실제 문서에 번호 주석. 재구성 화면이면 caption에 밝힌다 |
| cases | groups[{title,label,verified,items[{title,flow[[누가,색(a1/a2/ink),내용]]}]}] | 활용 예. 원문 예시는 verified:true, 새 아이디어는 false |
| safety | neverTitle, never[], notes[[제목,내용]], oops{title,items[]}, extra{title,html} | 금지·실수 대처 |
| pull | quote, small | 강조 인용 |
| faq | items[[질문,답html]] | 접는 질문 |
| agenda | items[[시간,제목,설명,강조여부,폭]] | 진행표·단계 띠 |
| checklist | img, items[[할 일, 어느 단계]] | 진행률 체크리스트(브라우저 저장) |
| ledger | ok[], no[], okTitle, noTitle, sources[], sourcesTitle | 확인한 것/못 한 것 + 접는 출처. 마지막 섹션 권장 |
| figure | img, alt, caption | 큰 그림 |
| code | text, comments(false면 # 흐리게 안 함), style | 코드만 |
| text | html | 문단 |
| html | html | 예외용 원시 HTML (가능하면 쓰지 않기) |

## 권장 순서

**고르기(purpose=decide):** 결정(decide 또는 verdict) → 핵심 차이 1개(lanes) → 비교표(compare, 1~2장면) → 주의(safety) → 확인(ledger). 6섹션 이하.

**이해·따라 하기:** 결론(verdict) → 문제(scenes) → 구조(diagram) → [용어(dict)] → 본론(folders/rules/steps) → 요약 문장(words) → 흐름(lanes+timing) → 예시 해부(annotated) → 활용(cases) → 주의(safety+pull) → 질문(faq) → [진행표(agenda)] → 체크리스트 → 확인·출처(ledger).
내용에 없는 블록은 빼고, 짧은 문서는 5~7섹션이면 충분하다.

예시: `examples/pickle-beginner.json`(초보자판 14섹션), `examples/skill-guide.json`(전문가판 7섹션, calm 옷).
