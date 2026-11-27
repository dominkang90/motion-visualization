#!/usr/bin/env python3
"""모션시각화 capture: screenshot a web page (the site you are explaining) for figure/cover images.

usage: python capture.py URL -o shot.png [--size 1440x900] [--click "버튼 글자"]... [--wait 1.2] [--full]
       python capture.py URL -o shot.png --nav 3        -> click the 3rd button inside <nav> first (1-based)
       python capture.py URL -o shot.png --selector "main"   -> capture only that element
Clicks run in order. Text clicks match the visible text (first match). Saves PNG; build.py shrinks big images.
Use for real screens only and say "실제 화면 캡처(날짜)" in the caption. Do not capture logged-in private pages.
"""
import argparse, os, sys
from datetime import date

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--size", default="1440x900", help="WIDTHxHEIGHT")
    ap.add_argument("--click", action="append", default=[], help="visible text to click (repeatable)")
    ap.add_argument("--nav", type=int, help="click the Nth button inside <nav> (1-based)")
    ap.add_argument("--selector", help="capture only this CSS selector")
    ap.add_argument("--wait", type=float, default=1.2, help="seconds to wait after load and after each click")
    ap.add_argument("--full", action="store_true", help="full page")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("Playwright 없음: pip install playwright"); return 2
    w, h = (int(x) for x in a.size.lower().split("x"))
    with sync_playwright() as p:
        b = None
        for ch in (None, "chrome", "msedge"):
            try:
                b = p.chromium.launch(channel=ch) if ch else p.chromium.launch()
                break
            except Exception:
                continue
        if b is None:
            print("브라우저를 실행할 수 없음"); return 2
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(a.url, wait_until="domcontentloaded", timeout=45000)
        try:
            pg.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        pg.wait_for_timeout(int(a.wait * 1000))
        if a.nav:
            btns = pg.locator("nav button")
            if btns.count() < a.nav:
                print("nav 버튼이 %d개뿐입니다" % btns.count()); b.close(); return 1
            btns.nth(a.nav - 1).click(); pg.wait_for_timeout(int(a.wait * 1000))
        for t in a.click:
            loc = pg.get_by_text(t, exact=False).first
            try:
                loc.click(timeout=5000)
            except Exception as e:
                print("누르지 못함: %s (%s)" % (t, str(e).splitlines()[0][:80])); b.close(); return 1
            pg.wait_for_timeout(int(a.wait * 1000))
        pg.evaluate("window.scrollTo(0,0)")
        pg.wait_for_timeout(300)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        if a.selector:
            pg.locator(a.selector).first.screenshot(path=a.out)
        else:
            pg.screenshot(path=a.out, full_page=a.full)
        title = pg.title()
        b.close()
    print("캡처: %s (%s, %s, %s 기준)" % (a.out, title, a.url, date.today().isoformat()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
