# content.json 양식

AI가 직접 쓰는 것은 이 파일 하나다. 대부분의 문자열에는 짧은 HTML(`<b> <em> <br> <code> <a>`)을 쓸 수 있다.
**평문만 되는 칸**(HTML이 글자로 보임): `meta.brand`, `stats`의 값·단위, `callout.label`, `cover.stage`의 labels·chips, `code`, `prompt.text`, `words.copyLabel`. 코드·프롬프트 원문은 `code`/`prompt.text`에 그대로 넣는다(자동 이스케이프).

## 최상위

```json
{
  "meta": {"title": "브라우저 제목", "brand": "표지 큰 제목", "issue": "오른쪽 작은 줄<br>둘째 줄",
           "theme": "paper|calm|warm|night", "accent": "#hex(선택)", "level": "expert|beginner",
           "storageKey": "체크리스트 저장 이름", "labels": {"step": "단계", "more": "더 알아보기", "ok": "잘 됐나요?"}},
  "images": {"logo": "brand:pickle/logo.svg", "shot": "assets/screen.png", "web": "https://..."},
  "cover": {"kicker": "", "title": "줄<br><em>강조</em>", "sub": "", "lines": [["굵은 말", "설명"]],
            "stage": {"left": "@a", "center": "@b", "right": "@c", "labels": ["", "", ""], "chips": ["", ""]}},
  "sections": [{"nav": "목차 이름", "kicker": "", "title": "", "lede": "", "dark": false, "blocks": []}],
  "footer": {"logos": ["@logo"], "html": "맨 아래 한 줄"}
}
```

- 이미지는 `images`에 한 번 등록하고 블록에서는 `"@이름"`으로 부른다. `brand:` = 로고 보관함, 상대경로 = content.json 기준.
- `stage`는 세 이미지(left/center/right) 또는 그림 하나(`"hero": "@x"`).
- `stage.hero`가 있으면 left/center/right/chips는 무시된다(둘 중 하나만).
- `labels` 키: copy, copied, more, step, close, progress, done, doneTail, allDone, ok, okGood, okBad, sources, know, does, key, good, bad, next. 기본값은 전문가판 문구(STEP, 자세히, 성공 확인, 진행률 등).
- 섹션 번호는 자동(01, 02…). `no`로 번호를, `id`로 앵커를 직접 정할 수 있다. `"dark": true`는 검은 배경 섹션(강조할 한 곳에만).

## 필수 조건 (build.py가 "필수" 경고 + 종료코드 1)

- steps.items[].title, words.items[].say, diagram.nodes[].title는 꼭 채운다.
- faq·dict·checklist·cases는 항목이 1개 이상. timing은 start·end가 `[시각, 설명]`.
- checklist는 페이지당 1개만.

## 블록 (type별 필드)

| type | 필드 | 쓰는 곳 |
|---|---|---|
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

결론(verdict) → 문제(scenes) → 구조(diagram) → [용어(dict)] → 본론(folders/rules/steps) → 요약 문장(words) → 흐름(lanes+timing) → 예시 해부(annotated) → 활용(cases) → 주의(safety+pull) → 질문(faq) → [진행표(agenda)] → 체크리스트 → 확인·출처(ledger).
내용에 없는 블록은 빼고, 짧은 문서는 5~7섹션이면 충분하다.

예시: `examples/pickle-beginner.json`(초보자판 14섹션), `examples/skill-guide.json`(전문가판 7섹션, calm 옷).
