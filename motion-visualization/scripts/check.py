#!/usr/bin/env python3
"""모션시각화 check: static checks, plus browser checks when Playwright is available.

usage: python check.py out.html [--shots DIR] [--no-browser]
Static : leftover placeholders, content JSON parse, em dash, empty images.
Browser: 1280px and 390px widths -> script errors, horizontal overflow, diagram card,
         step popup open/Esc close, copy toast, checklist, FAQ. Saves cover + one mobile shot.
If Playwright or its browser is missing, says so and reports the layout as unverified.
"""
import argparse, json, os, re, sys
from pathlib import Path


def static(html):
    res = []
    for ph in ("__CONTENT_JSON__", "__TITLE__", "/*__THEME_OVERRIDE__*/"):
        if ph in html and ph != "/*__THEME_OVERRIDE__*/":
            res.append(("FAIL", "자리표시 남음: " + ph))
    m = re.search(r'<script type="application/json" id="content">(.*?)</script>', html, re.S)
    if not m:
        return res + [("FAIL", "content JSON 없음")]
    try:
        c = json.loads(m.group(1))
    except Exception as e:
        return res + [("FAIL", "content JSON 오류: %s" % e)]
    empty = [k for k, v in (c.get("images") or {}).items() if not v]
    res.append(("OK" if not empty else "WARN", "이미지 %d개, 비어 있는 것 %s" % (len(c.get("images") or {}), empty or "없음")))
    res.append(("OK" if "\u2014" not in m.group(1) else "WARN", "긴 줄표(—) " + ("없음" if "\u2014" not in m.group(1) else "있음")))
    n = len(c.get("sections") or [])
    res.append(("OK" if n else "FAIL", "섹션 %d개" % n))
    return res


JS_PROBE = """() => {
  const r = {};
  r.overflow = document.documentElement.scrollWidth > innerWidth + 1;
  r.sections = document.querySelectorAll('main section').length;
  r.missing = document.querySelectorAll('.missing').length;
  return r;
}"""


FULL = False


def browser(path, shots):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return [("SKIP", "Playwright 없음: 화면 점검 미확인 (pip install playwright && playwright install chromium)")]
    res = []
    url = Path(path).resolve().as_uri()
    try:
        with sync_playwright() as p:
            b, why = None, []
            for ch in (None, "chrome", "msedge"):  # bundled Chromium first, then installed Chrome/Edge
                try:
                    b = p.chromium.launch(channel=ch) if ch else p.chromium.launch()
                    break
                except Exception as e:
                    why.append(str(e).splitlines()[0][:80])
            if b is None:
                return [("SKIP", "브라우저 실행 불가: %s (화면 점검 미확인)" % "; ".join(why)[:200])]
            for w in (1280, 390):
                pg = b.new_page(viewport={"width": w, "height": 900})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(url, wait_until="domcontentloaded", timeout=30000)
                pg.add_style_tag(content="html{scroll-behavior:auto!important}")
                pg.wait_for_timeout(1200)
                pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
                pg.wait_for_timeout(900)
                r = pg.evaluate(JS_PROBE)
                tag = "%dpx" % w
                res.append(("FAIL" if errs else "OK", tag + " 스크립트 오류 " + (str(errs[:2]) if errs else "없음")))
                res.append(("FAIL" if r["overflow"] else "OK", tag + " 가로 넘침 " + ("있음" if r["overflow"] else "없음")))
                if r["missing"]:
                    res.append(("WARN", tag + " 빈 이미지 자리 %d개" % r["missing"]))
                if w == 1280:
                    if pg.locator(".node").count() > 1:
                        pg.locator(".node").nth(1).click()
                        ok = pg.locator(".node").nth(1).get_attribute("aria-pressed") == "true"
                        res.append(("OK" if ok else "FAIL", "구조도 카드 누르기"))
                    if pg.locator("[data-dlg]").count():
                        pg.locator("[data-dlg]").first.click()
                        op = pg.evaluate("document.getElementById('dlg').open")
                        pg.keyboard.press("Escape")
                        cl = not pg.evaluate("document.getElementById('dlg').open")
                        res.append(("OK" if op and cl else "FAIL", "팝업 열기/Esc 닫기"))
                    if pg.locator("[data-copy]").count():
                        pg.locator("[data-copy]").first.click()
                        pg.wait_for_timeout(200)
                        t = pg.evaluate("document.getElementById('toast').classList.contains('on')")
                        res.append(("OK" if t else "WARN", "복사 버튼 알림"))
                    if pg.locator("#checks input").count():
                        pg.locator("#checks input").first.check()
                        res.append(("OK", "체크리스트 " + pg.inner_text("#pct")))
                    if pg.locator("details.faq summary").count():
                        pg.locator("details.faq summary").first.click()
                        res.append(("OK" if pg.evaluate("document.querySelector('details.faq').open") else "FAIL", "질문 펼치기"))
                if errs:
                    res.append(("FAIL", tag + " 누른 뒤 스크립트 오류 " + str(errs[:2])))
                if shots:
                    os.makedirs(shots, exist_ok=True)
                    pg.evaluate("window.scrollTo(0,0);document.getElementById('toast').classList.remove('on')")
                    pg.wait_for_timeout(200)
                    f = os.path.join(shots, "cover-%d.png" % w)
                    pg.screenshot(path=f)
                    res.append(("OK", "캡처 저장 " + f))
                    if FULL and w == 1280:
                        f2 = os.path.join(shots, "full-%d.png" % w)
                        pg.screenshot(path=f2, full_page=True)
                        res.append(("OK", "전체 캡처 저장 " + f2))
                pg.close()
            b.close()
    except Exception as e:
        res.append(("FAIL", "화면 점검 중 오류: %s" % str(e).splitlines()[0][:160]))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--shots")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--full", action="store_true", help="also save a full-page shot (with --shots)")
    a = ap.parse_args()
    global FULL
    FULL = a.full
    with open(a.html, encoding="utf-8") as f:
        html = f.read()
    res = static(html)
    if not a.no_browser:
        res += browser(a.html, a.shots)
    for s, m in res:
        print("[%s] %s" % (s, m))
    fails = sum(1 for s, _ in res if s == "FAIL")
    print("결과: 실패 %d / 경고 %d / 미확인 %d" % (fails, sum(1 for s, _ in res if s == "WARN"), sum(1 for s, _ in res if s == "SKIP")))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
