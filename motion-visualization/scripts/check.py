#!/usr/bin/env python3
"""모션시각화 check: static checks, plus browser checks when Playwright is available.

usage: python check.py out.html [--shots DIR] [--no-browser]
Static : leftover placeholders, content JSON parse, em dash, empty images.
Browser: 1280px and 390px widths -> script errors, horizontal overflow, diagram card,
         step popup open/Esc close, copy toast, checklist, FAQ. Saves cover + one mobile shot.
If Playwright or its browser is missing, says so and reports the layout as unverified.
"""
import argparse, base64, json, os, re, sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Korean Windows consoles default to cp949
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SLIDE_OVER = """() => { const s = document.querySelector('.slide.cur'); if (!s) return 0;
  const sr = s.getBoundingClientRect(); let mb = 0;
  s.querySelectorAll('.blk,.sec-head,.cover-grid,.masthead').forEach(e => {
    const r = e.getBoundingClientRect(); if (r.height) mb = Math.max(mb, r.bottom - sr.top + s.scrollTop); });
  return Math.round(mb - s.clientHeight); }"""


def deck_overflow(b, url):
    """Open the deck at a common laptop size (1280x800) and measure how far real content goes below the visible area."""
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.goto(url, wait_until="domcontentloaded", timeout=30000)
    pg.wait_for_timeout(1200)
    n = pg.evaluate("(window.MV && MV.count) || 0")
    over = {}
    for k in range(n):
        pg.evaluate("i => MV.go(i)", k)
        pg.wait_for_timeout(900)
        px = pg.evaluate(SLIDE_OVER)
        if px > 16:
            over[k] = px
    pg.close()
    return over


SLIDE_HCLIP = """() => { const s = document.querySelector('.slide.cur') || document.querySelector('.slide'); if (!s) return 0;
  const W = innerWidth; let m = 0;
  s.querySelectorAll('.blk *, .cover-grid *').forEach(e => { const r = e.getBoundingClientRect();
    if (r.width && r.height) m = Math.max(m, r.right - W, -r.left); });
  return Math.round(m); }"""


def deck_hclip(b, url):
    """Phone width (390x844): content cut off at the right edge inside a slide. Page-level scrollWidth misses this
    because each slide clips its own overflow (found 2026-11-27 with a 3-column compare table)."""
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto(url, wait_until="domcontentloaded", timeout=30000)
    pg.wait_for_timeout(1200)
    n = pg.evaluate("(window.MV && MV.count) || 0")
    cut = {}
    for k in range(n):
        pg.evaluate("i => MV.go(i)", k)
        pg.wait_for_timeout(900)
        px = pg.evaluate(SLIDE_HCLIP)
        if px > 4:
            cut[k] = px
    pg.close()
    return cut


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
    n = len(c.get("sections") or c.get("scenes") or [])
    res.append(("OK" if n else "FAIL", "섹션 %d개" % n))
    return res


TO_EL = """(sel) => { const el = document.querySelector(sel); if (window.MV && MV.go && el) { const s = el.closest('.slide'); if (s) MV.go(+s.dataset.i); } }"""

JS_PROBE = """() => {
  const r = {};
  r.overflow = document.documentElement.scrollWidth > innerWidth + 1;
  r.sections = document.querySelectorAll('main section').length;
  r.missing = document.querySelectorAll('.missing').length;
  r.mode = window.MVX ? 'explainer' : ((window.MV && MV.mode) || 'scroll');
  r.beats = window.MVX ? MVX.count : 0;
  r.count = (window.MV && MV.count) || 0;
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
                if r["mode"] == "explainer":
                    res.append(("OK", tag + " 설명 영상 %d비트, 예상 길이 %.0f초" % (r["beats"], pg.evaluate("MVX.total()") / 1000)))
                    if w == 1280:
                        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(400)
                        pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(400)
                    if shots and (FULL or w == 1280):
                        imgs = []
                        for k in range(r["beats"]):
                            pg.evaluate("i => MVX.go(i)", k); pg.wait_for_timeout(1200)
                            imgs.append(base64.b64encode(pg.screenshot(type="jpeg", quality=68)).decode())
                        cols = 4 if w == 1280 else 6
                        sheet = b.new_page(viewport={"width": 1600, "height": 900})
                        sheet.set_content("<style>body{margin:0;padding:12px;background:#222;color:#ccc;font:600 13px sans-serif}div{display:grid;grid-template-columns:repeat(%d,1fr);gap:10px}img{width:100%%;display:block;border-radius:6px}</style><div>" % cols + "".join('<figure style="margin:0"><img src="data:image/jpeg;base64,%s">%d</figure>' % (x, n + 1) for n, x in enumerate(imgs)) + "</div>")
                        f2 = os.path.join(shots, "beats-%d.png" % w)
                        sheet.screenshot(path=f2, full_page=True); sheet.close()
                        res.append(("OK", "비트 모아보기 저장 " + f2))
                    errs2 = list(errs)
                    pg.close()
                    if errs2:
                        res.append(("FAIL", tag + " 재생 중 스크립트 오류 " + str(errs2[:2])))
                    continue
                over = {}
                if w == 1280 and r["mode"] == "deck":
                    over = deck_overflow(b, url)
                    if over:
                        res.append(("WARN", "장면 안 스크롤 필요(노트북 1280x800, 표지=1번): " + ", ".join("%d번 장면 +%dpx" % (k + 1, v) for k, v in over.items())
                                    + ". 항목을 줄이거나 섹션을 나누기. 매거진 MP4에도 넘친 부분은 안 보일 수 있음"))
                    else:
                        res.append(("OK", "장면 안 넘침 없음(노트북 1280x800)"))
                    cut = deck_hclip(b, url)
                    if cut:
                        res.append(("FAIL", "휴대폰(390px) 장면 오른쪽 잘림: " + ", ".join("%d번 장면 +%dpx" % (k + 1, v) for k, v in cut.items())
                                    + ". 표·긴 낱말·그림 폭 확인"))
                    else:
                        res.append(("OK", "휴대폰(390px) 장면 잘림 없음"))
                    i0 = pg.evaluate("MV.index()")
                    pg.locator("#nx").click(); pg.wait_for_timeout(700)
                    i1 = pg.evaluate("MV.index()")
                    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(700)
                    i2 = pg.evaluate("MV.index()")
                    pg.evaluate("""() => { const d = document.getElementById('deck'); const mk = (x) => new Touch({identifier: 1, target: d, clientX: x, clientY: 300});
                      d.dispatchEvent(new TouchEvent('touchstart', {touches: [mk(600)], changedTouches: [mk(600)], bubbles: true}));
                      d.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [mk(400)], bubbles: true})); }""")
                    pg.wait_for_timeout(700)
                    i3 = pg.evaluate("MV.index()")
                    pg.locator("#pv").click(); pg.wait_for_timeout(700)
                    i4 = pg.evaluate("MV.index()")
                    ok = (i0, i1, i2, i3, i4) == (0, 1, 2, 3, 2)
                    res.append(("OK" if ok else "FAIL", "넘겨 보기 %d장: 다음 버튼·→ 키·스와이프·이전 버튼 %s" % (r["count"], [i0, i1, i2, i3, i4])))
                if w == 1280:
                    if pg.locator(".node").count() > 1:
                        pg.evaluate(TO_EL, ".node"); pg.wait_for_timeout(700)
                        pg.locator(".node").nth(1).click()
                        ok = pg.locator(".node").nth(1).get_attribute("aria-pressed") == "true"
                        res.append(("OK" if ok else "FAIL", "구조도 카드 누르기"))
                    if pg.locator("[data-dlg]").count():
                        pg.evaluate(TO_EL, "[data-dlg]"); pg.wait_for_timeout(700)
                        pg.locator("[data-dlg]").first.click()
                        op = pg.evaluate("document.getElementById('dlg').open")
                        pg.keyboard.press("Escape")
                        cl = not pg.evaluate("document.getElementById('dlg').open")
                        res.append(("OK" if op and cl else "FAIL", "팝업 열기/Esc 닫기"))
                    if pg.locator("[data-copy]").count():
                        pg.evaluate(TO_EL, "[data-copy]"); pg.wait_for_timeout(700)
                        pg.locator("[data-copy]").first.click()
                        pg.wait_for_timeout(200)
                        t = pg.evaluate("document.getElementById('toast').classList.contains('on')")
                        res.append(("OK" if t else "WARN", "복사 버튼 알림"))
                    if pg.locator("#checks input").count():
                        pg.evaluate(TO_EL, "#checks"); pg.wait_for_timeout(700)
                        pg.locator("#checks input").first.check()
                        res.append(("OK", "체크리스트 " + pg.inner_text("#pct")))
                    if pg.locator("details.faq summary").count():
                        pg.evaluate(TO_EL, "details.faq"); pg.wait_for_timeout(700)
                        pg.locator("details.faq summary").first.click()
                        res.append(("OK" if pg.evaluate("document.querySelector('details.faq').open") else "FAIL", "질문 펼치기"))
                if errs:
                    res.append(("FAIL", tag + " 누른 뒤 스크립트 오류 " + str(errs[:2])))
                if shots:
                    os.makedirs(shots, exist_ok=True)
                    pg.evaluate("window.scrollTo(0,0);window.MV&&MV.go&&MV.go(0);document.getElementById('toast').classList.remove('on')")
                    pg.wait_for_timeout(800)
                    pg.wait_for_timeout(200)
                    f = os.path.join(shots, "cover-%d.png" % w)
                    pg.screenshot(path=f)
                    res.append(("OK", "캡처 저장 " + f))
                    if FULL and w == 1280 and r["mode"] == "deck":
                        imgs = []
                        for k in range(r["count"]):
                            pg.evaluate("i => MV.go(i)", k); pg.wait_for_timeout(1300)
                            imgs.append(base64.b64encode(pg.screenshot(type="jpeg", quality=70)).decode())
                        sheet = b.new_page(viewport={"width": 1600, "height": 900})
                        sheet.set_content("<style>body{margin:0;padding:16px;background:#ddd;font:600 14px sans-serif}div{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}img{width:100%;border-radius:8px;display:block}span{display:block;margin:4px 0 0}</style><div>" + "".join('<figure style="margin:0"><img src="data:image/jpeg;base64,%s"><span>%s</span></figure>' % (x, ("%d · 스크롤 필요 +%dpx(1280x800)" % (n + 1, over[n])) if n in over else str(n + 1)) for n, x in enumerate(imgs)) + "</div>")
                        f2 = os.path.join(shots, "slides-sheet.png")
                        sheet.screenshot(path=f2, full_page=True); sheet.close()
                        res.append(("OK", "장면 모아보기 저장 " + f2))
                    elif FULL and w == 1280:
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
