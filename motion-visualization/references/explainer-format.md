# 설명 영상형(explainer) 양식

글 대신 **장면 + 한 줄 자막 + 움직임**으로 설명한다. `meta.kind: "explainer"`면 build.py가 `assets/explainer.html`을 쓴다. 결과는 자동 재생 HTML(‹ ▶ › 버튼·← → 키·스와이프·화면 누르면 멈춤)이고, `record.py`로 무음 MP4를 만든다.

```json
{
  "meta": {"kind": "explainer", "title": "", "theme": "paper|calm|warm|night", "ratio": "16:9|9:16",
           "goal": "누가 보고 무엇을 정하나(한 문장)", "sides": ["왼쪽 대상", "오른쪽 대상"]},
  "images": {"logo": "brand:pickle/pieup.webp"},
  "scenes": [ {"type": "...", "say": "자막", "beats": [ {"say": "..."} ]} ]
}
```

- **비트(beat)** = 자막 한 줄이 바뀌는 순간. 장면 안에서 비트마다 하나씩 더 보여 준다. 비트가 없으면 장면 하나 = 비트 하나.
- **자막**: 한 줄 24자 안팎(34자 넘으면 경고). `**말**`은 노랑 강조. 길이로 재생 시간이 자동 계산된다(최소 2.3초). `dur`(ms)로 직접 지정 가능.
- 화면 글자는 자막 외 **장면당 3~4덩어리**까지. 설명 문장은 자막으로 보내고 화면에는 낱말·그림만.
- 아이콘: `"@이미지키"` 또는 내장 이름 `user phone laptop folder file mail calendar chat bot db cloud gear check x lock key search bolt note box clock star warn code home out`.

## 장면 종류

| type | 필드 | 쓰는 때 |
|---|---|---|
| title | kicker, title(줄바꿈 `\n`, `**강조**`), sub, icons[] | 첫 장면 질문·약속 |
| chapter | no, title | 큰 단락 시작. 위쪽 진행 막대와 동그라미 로드맵이 자동 |
| kinetic | text, hl(강조 낱말), sub | 핵심 한 문장을 낱말 단위로 튀어나오게 |
| build | nodes[{id,icon,label,sub,hub,at:[x,y]}], links[[from,to,라벨,"flow"?]], token, beats[{show[],link[],send,focus,mark{id:"ok"/"bad"}}] | 관계도를 하나씩 쌓기. send=링크 번호(쪽지가 선을 따라 날아감), focus=나머지 흐리게, mark=✓/✗ 배지 |
| compare | cols[{icon,title,tone:"good"/"bad",items[]}], beats[{show:열번호}] | 같은 예시 전후·두 대상 비교. 항목 앞 `*`는 차이 강조. tone 없이 title이 `meta.sides`와 같으면 왼쪽 청록·오른쪽 강조색으로 매거진과 같은 색 고정 |
| list | items[{icon,title,sub}], beats(항목 수만큼) | 단계·준비물 하나씩 |
| doc | title, meta, rows[[머리,내용]], caption, beats[{row,label,zoom}] | 실제 문서·쪽지 해부. row 하나만 밝히고 말풍선 |
| focus | img, caption, beats[{zoom:[x,y,w,h], box:[x,y,w,h], label}] | 실제 화면 확대·집중 조명·말풍선. 좌표는 이미지 비율(0~1) |
| map | rows[[질문/상황, 개념/답]] | 상황 → 답 짝 맞추기 |
| end | title, points[] | 요약 3개 + 다음 행동 |

## 좋은 순서 (연구한 인기 강의 공통)

1. title(질문) → chapter 01 → **문제 장면**(compare 또는 kinetic)
2. chapter 02 → **구조**(build로 하나씩 쌓기, 쪽지 send, 마지막에 focus+mark)
3. chapter 03 → **실제 증거**(doc 또는 focus로 실화면) — "말한 것을 화면으로 증명"
4. chapter 04 → **따라 하기**(list) → **두 마디/요약**(map) → end
- 장면은 같은 예시를 끝까지 유지한다(새 예시를 계속 만들지 않기).
- 한 번에 한 곳만 강조: focus·box·row 중 하나. 노랑=지금 볼 곳, 빨강=실패·주의, 초록=완료.
- **두 판을 골랐을 때는 같은 JSON으로** (만들기 전에 어느 판을 만들지 먼저 묻는다, SKILL.md 참고): PPT판(16:9, 발표·유튜브)과 숏폼판(9:16, 쇼츠·릴스). `build.py --ratio`, `record.py --both`. 숏폼판은 노드가 세로로, 비교 카드가 위아래로 자동 배치된다. 보는 사람은 주소 뒤 `?ratio=9:16`으로 바꿔 볼 수도 있다.

## 만들기

```
python scripts/build.py content.json -o out.html                     # PPT판(meta.ratio 기본 16:9)
python scripts/build.py content.json -o out-shorts.html --ratio 9:16 # 숏폼판 HTML
python scripts/check.py out.html --shots shots/                       # beats-1280.png = 모든 비트 모아보기
python scripts/record.py out.html -o out.mp4 --both                   # out-ppt.mp4 + out-shorts.mp4 (무음, 30fps)
```
예시: `examples/pickle-explainer.json`.

## 점검

- `build.py`: goal 없음, 같은 장면 종류 3연속, compare 열 순서·이름이 sides와 다름을 경고.
- `check.py`(390px): 모든 비트를 넘기며 재생 버튼·재생 막대의 누름 영역, 명암 대비, 키보드 접근을 본다. 화면이 통째로 줄어드는 영상이라 글자 크기는 보지 않는다(휴대폰은 9:16판).

## 알려진 한계 (다음 고도화 후보)

- 무음: 내레이션·효과음 없음(음성 합성 서비스가 필요).
- 숏폼판 doc 장면은 말풍선이 아래 줄을 가릴 수 있다. 숏폼판에서는 doc보다 focus·build를 우선한다.
- 녹화는 화면이 바뀔 때만 프레임을 받아 30fps로 맞춘다. 실시간 녹화라 PC가 바쁘면 움직임이 끊길 수 있다.
- 실제 화면 녹화 영상(동영상 클립) 삽입, 얼굴캠, 커서 클릭 효과는 아직 없다(이미지 확대만).
