#!/usr/bin/env python3
"""모션시각화 자체 시험: 고친 경고·점검이 계속 작동하는지 확인한다.

usage: python scripts/selftest.py [--browser]
  기본: 조립·인지부하 경고 시험(파이썬 표준만).
  --browser: check.py 화면 시험까지(Playwright + Chrome/Edge/Chromium 필요, 없으면 NOT RUN).
결과는 PASS / FAIL / NOT RUN. 하나라도 FAIL이면 종료코드 1.
"""
import os, subprocess, sys, tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "tests", "fixtures")
OUT = tempfile.mkdtemp(prefix="mv-selftest-")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def build(src, name):
    out = os.path.join(OUT, name + ".html")
    p = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), src, "-o", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    return p.returncode, p.stdout + p.stderr, out


RESULTS = []


def rec(name, ok, note=""):
    RESULTS.append(("PASS" if ok is True else "FAIL" if ok is False else "NOT RUN", name, note))


# 1. 예제가 조립된다(그림 없음 경고는 괜찮음)
for ex in ("skill-guide", "pickle-beginner", "pickle-explainer"):
    src = os.path.join(ROOT, "examples", ex + ".json")
    if not os.path.isfile(src):
        rec("예제 조립: " + ex, None, "파일 없음")
        continue
    code, log, _ = build(src, ex)
    rec("예제 조립: " + ex, code == 0, "" if code == 0 else log[-200:])

# 2. 고치기 전 내용은 인지부하 문제를 모두 잡는다
code, log, _ = build(os.path.join(FX, "before.json"), "before")
want = {"결론 숫자 단위": "단위 섞인 결론 숫자", "한 칸에 두 대상": "한 칸 두 대상", "같은 말이 여러 장면": "반복",
        "마지막 장에만": "미확인 위치", "결정용 자료인데 섹션": "장면 수", "색이 다른 장면과 반대": "색 뒤집힘", "meta.goal 없음": "읽는 목적"}
for key, label in want.items():
    rec("고치기 전 → 경고: " + label, key in log)

# 3. 고친 뒤 내용은 인지부하 경고 0
code, log, after_html = build(os.path.join(FX, "after.json"), "after")
n = sum(1 for line in log.splitlines() if "인지부하" in line)
rec("고친 뒤 → 인지부하 경고 0", code == 0 and n == 0, "%d건" % n if n else "")

# 3-1. 설명 영상: 고친 뒤 경고 0, 비교 순서를 뒤집으면 경고
import json
exp_src = os.path.join(FX, "explainer.json")
code, log, exp_html = build(exp_src, "explainer")
rec("설명 영상 → 인지부하 경고 0", code == 0 and "인지부하" not in log)
with open(exp_src, encoding="utf-8") as f:
    ex = json.load(f)
for sc in ex["scenes"]:
    if sc.get("type") == "compare":
        sc["cols"] = list(reversed(sc["cols"]))
rev = os.path.join(OUT, "explainer-reversed.json")
with open(rev, "w", encoding="utf-8") as f:
    json.dump(ex, f, ensure_ascii=False)
code, log, _ = build(rev, "explainer-reversed")
rec("설명 영상 뒤집힌 비교 → 경고", "compare 순서" in log)

# 4. 화면 시험(선택)
if "--browser" in sys.argv:
    try:
        import playwright  # noqa: F401
        p = subprocess.run([sys.executable, os.path.join(HERE, "check.py"), after_html], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV)
        out = p.stdout
        if "[SKIP]" in out and "브라우저 실행 불가" in out:
            rec("화면 점검(check.py)", None, "브라우저 실행 불가")
        else:
            for key, label in (("장면 잘림 없음", "휴대폰 잘림"), ("누르는 영역 24px 미만 없음", "누르는 영역"),
                               ("12px 미만 글자 없음", "작은 글자"), ("명암 대비 부족(4.5:1, 큰 글자 3:1) 없음", "명암 대비"),
                               ("키보드 불가) 없음", "키보드"), ("넘겨 보기", "넘겨 보기 버튼·키·스와이프")):
                rec("화면: " + label, key in out and "[FAIL] " + key not in out)
            rec("화면: 실패 0", "결과: 실패 0" in out)
            p2 = subprocess.run([sys.executable, os.path.join(HERE, "check.py"), exp_html], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", env=ENV)
            o2 = p2.stdout
            rec("설명 영상 화면: 실패·경고 0(누름 영역·대비·키보드 포함)", "결과: 실패 0 / 경고 0" in o2 and "설명 영상 명암 대비" in o2)
    except ImportError:
        rec("화면 점검(check.py)", None, "Playwright 없음")
else:
    rec("화면 점검(check.py)", None, "--browser 없이 실행")

w = max(len(r[1]) for r in RESULTS)
for st, name, note in RESULTS:
    print("%-8s %s%s" % (st, name, ("  · " + note) if note else ""))
c = {k: sum(1 for r in RESULTS if r[0] == k) for k in ("PASS", "FAIL", "NOT RUN")}
print("결과: PASS %d / FAIL %d / NOT RUN %d" % (c["PASS"], c["FAIL"], c["NOT RUN"]))
sys.exit(1 if c["FAIL"] else 0)
