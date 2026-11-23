# 로고·사진 모으기

## 순서
1. **보관함 먼저.** 공개판의 `assets/brands/`에는 상표 로고 파일이 없고 `sources.json`(받는 곳·규칙)만 있다. 필요한 로고는 그 주소에서 직접 받아 같은 폴더에 넣는다.
    `assets/brands/<브랜드>/`와 `sources.json`을 확인한다. 있으면 `brand:<브랜드>/<파일>`로 쓴다.
2. **없으면 공식 홍보 자료(프레스킷).** 사이트 아래쪽의 Press kit / Brand / Media assets / Logos 링크를 찾는다. 예: `pickle.com/press-kit`, `brand.github.com`, `anthropic.com/press-kit`. 검색 이미지 미리보기·비공식 아이콘 사이트는 쓰지 않는다.
3. **사용 규칙을 읽는다.** 변형 금지, 색 변경 금지, 다른 로고와 붙이기 금지, 보증처럼 보이게 하기 금지 등을 sources.json의 `rules`에 한 줄로 적는다.
4. **보관함에 넣는다.** SVG를 우선한다. 큰 PNG/JPG는 가로 1400px 이하 WebP로 줄인다(build.py가 Pillow가 있으면 자동). 흰 배경 캐릭터는 배경을 투명하게 만든 사본을 둔다(원본 모양은 바꾸지 않음).
5. **sources.json 형식:** `{"owner","source","zip","fetched":"YYYY-MM-DD","files":{"파일":"설명"},"rules"}`.
6. **본문 출처:** 마지막 ledger의 sources에 출처 주소·받은 날·상표 문구·"제휴 관계 없음"을 적는다.

## 구분해서 표시할 것
- 실제 화면 캡처 / 공식 홍보용 화면 / 다시 그린 화면(재구성) / AI 생성 그림. 재구성·생성 그림은 caption에 밝힌다.
- 공식 화면에 내가 설명하는 기능이 안 보이면 그 사실을 caption에 적는다.

## 하지 않을 것
- 로고를 늘리기·자르기·색 바꾸기(단색 심볼을 흰색으로 칠하는 정도만, 규칙이 허용할 때).
- 공개 저장소에 상표 로고 파일을 묶어 배포하기. 공개판에는 sources.json(받는 곳·규칙)만 둔다.
