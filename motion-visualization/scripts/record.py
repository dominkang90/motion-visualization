#!/usr/bin/env python3
"""모션시각화 record: explainer HTML or magazine deck HTML -> MP4 (silent), by capturing browser frames.

usage: python record.py out.html -o video.mp4 [--ratio 16:9|9:16] [--size 1280]
       magazine (deck) HTML is detected automatically: each scene is shown for --hold seconds (default 5).
       python record.py out.html -o video.mp4 --both   -> video-ppt.mp4 (16:9) + video-shorts.mp4 (9:16)
Needs Playwright (python) + Chrome/Edge/Chromium, and ffmpeg on PATH.
Frames come from the browser's screencast in real time; the MP4 is re-timed to 30 fps.
"""
import argparse, base64, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Korean Windows consoles default to cp949
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    if "--both" in sys.argv:
        argv = [x for x in sys.argv[1:] if x != "--both"]
        i = argv.index("-o") if "-o" in argv else argv.index("--out")
        base, ext = os.path.splitext(argv[i + 1])
        rc = 0
        for r, tag in (("16:9", "ppt"), ("9:16", "shorts")):
            a2 = list(argv); a2[i + 1] = "%s-%s%s" % (base, tag, ext or ".mp4")
            rc |= subprocess.call([sys.executable, os.path.abspath(__file__)] + a2 + ["--ratio", r])
        return rc
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--ratio", default=None, help="override meta.ratio")
    ap.add_argument("--size", type=int, default=1280, help="long edge in px")
    ap.add_argument("--hold", type=float, default=5.0, help="magazine deck: seconds per scene")
    a = ap.parse_args()
    tail = None
    from playwright.sync_api import sync_playwright
    ratio = a.ratio
    url = Path(a.html).resolve().as_uri()
    work = tempfile.mkdtemp(prefix="mvrec-")
    frames = []
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
        probe = b.new_page(); probe.goto(url + "?rec=1"); probe.wait_for_timeout(800)
        r = ratio or probe.evaluate("(JSON.parse(document.getElementById('content').textContent).meta||{}).ratio||'16:9'")
        is_exp = probe.evaluate("!!window.MVX")
        probe.close()
        w, h = (a.size, round(a.size * 9 / 16)) if r == "16:9" else (round(a.size * 9 / 16), a.size)
        w -= w % 2; h -= h % 2
        vw, vh = (w, h) if is_exp or r != "16:9" else (1920, 1080)  # deck: lay out on a roomy 1080p screen, then scale down
        pg = b.new_page(viewport={"width": vw, "height": vh})
        pg.goto(url + ("?rec=1&ratio=" + r if is_exp else "?mode=deck")); pg.wait_for_timeout(1500)
        total = pg.evaluate("MVX.total()") if is_exp else 0
        n_deck = 0 if is_exp else pg.evaluate("(window.MV && MV.count) || 0")
        if not is_exp and not n_deck:
            print("설명 영상도 넘겨 보기 매거진도 아님: 녹화할 장면을 찾지 못함"); b.close(); return 1
        cdp = pg.context.new_cdp_session(pg)
        def on_frame(ev):
            frames.append((ev["metadata"]["timestamp"], ev["data"]))
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": vw, "maxHeight": vh, "everyNthFrame": 1})
        pg.wait_for_timeout(300)
        if is_exp:
            pg.evaluate("MVX.play()")
            end = time.time() + total / 1000 + 1.5
            while time.time() < end and not pg.evaluate("window.__done===true"):
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(1200)
        else:
            for k in range(n_deck):
                pg.evaluate("i => MV.go(i)", k)
                pg.wait_for_timeout(int(a.hold * 1000))
            tail = time.time()
        cdp.send("Page.stopScreencast")
        b.close()
    if not frames:
        print("프레임 없음"); return 1
    lines = []
    for i, (ts, data) in enumerate(frames):
        f = os.path.join(work, "f%05d.jpg" % i)
        open(f, "wb").write(base64.b64decode(data))
        d = (frames[i + 1][0] - ts) if i + 1 < len(frames) else (max(tail - ts, 1.0) if tail else 1.0)
        lines.append("file '%s'\nduration %.4f" % (f.replace("\\", "/"), max(d, 0.001)))
    lines.append("file '%s'" % os.path.join(work, "f%05d.jpg" % (len(frames) - 1)).replace("\\", "/"))
    lst = os.path.join(work, "list.txt"); open(lst, "w", encoding="utf-8").write("\n".join(lines))
    tmp = os.path.join(work, "out.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-vf", "scale=%d:%d,fps=30,format=yuv420p" % (w, h), "-c:v", "libx264", "-crf", "20",
                    "-movflags", "+faststart", tmp], check=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    shutil.copyfile(tmp, a.out)
    span = frames[-1][0] - frames[0][0]
    print("영상: %s (%dx%d, 약 %.1f초, 캡처 %d장, 평균 %.0f fps)" % (a.out, w, h, span, len(frames), len(frames) / span if span else 0))
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
