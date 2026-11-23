#!/usr/bin/env python3
"""모션시각화 build: content.json + template.html -> single self-contained HTML.

usage: python build.py content.json -o out.html [--theme paper|calm|warm|night] [--accent #hex] [--lib DIR]
Image refs in content["images"]:
  brand:<brand>/<file>   -> <lib>/<brand>/<file>  (lib default: ../assets/brands)
  relative/path.png      -> relative to the content.json folder
  https://... or data:   -> kept as is
Standard library only. Pillow is used to shrink big PNG/JPG if it happens to be installed.
"""
import argparse, base64, io, json, mimetypes, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")
DEFAULT_LIB = os.path.join(HERE, "..", "assets", "brands")
BLOCKS = {"verdict", "scenes", "diagram", "chips", "callout", "dict", "folders", "rules", "steps", "words",
          "lanes", "timing", "annotated", "cases", "safety", "pull", "faq", "agenda", "checklist", "ledger",
          "figure", "code", "text", "html"}
THEMES = {"paper", "calm", "warm", "night"}


def shrink(raw, mime, max_w=1400):
    try:
        from PIL import Image  # optional
    except Exception:
        return raw, mime
    try:
        im = Image.open(io.BytesIO(raw))
        if im.width <= max_w and len(raw) < 400_000:
            return raw, mime
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)))
        out = io.BytesIO()
        im.save(out, "WEBP", quality=82)
        return out.getvalue(), "image/webp"
    except Exception:
        return raw, mime


def to_data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if path.lower().endswith(".svg"):
        mime = "image/svg+xml"
    if path.lower().endswith(".webp"):
        mime = "image/webp"
    with open(path, "rb") as f:
        raw = f.read()
    if mime in ("image/png", "image/jpeg"):
        raw, mime = shrink(raw, mime)
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())


def resolve(ref, base, lib, warn):
    if not isinstance(ref, str) or not ref:
        return ""
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    path = os.path.join(lib, ref[6:]) if ref.startswith("brand:") else os.path.join(base, ref)
    if not os.path.isfile(path):
        warn.append("이미지 없음: %s (%s)" % (ref, path))
        return ""
    return to_data_uri(path)


def walk_strings(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for x in node:
            walk_strings(x, out)
    elif isinstance(node, dict):
        for v in node.values():
            walk_strings(v, out)


def lint(c, warn):
    secs = c.get("sections") or []
    if not secs:
        warn.append("sections가 비어 있음")
    for i, s in enumerate(secs):
        for b in s.get("blocks") or []:
            if b.get("type") not in BLOCKS:
                warn.append("섹션 %d: 모르는 블록 '%s'" % (i + 1, b.get("type")))
    REQ = {"words": ("items", "say"), "steps": ("items", "title"), "faq": ("items", None), "checklist": ("items", None),
           "diagram": ("nodes", "title"), "dict": ("items", None), "cases": ("groups", "items")}
    nck = 0
    for i, s in enumerate(secs):
        for b in s.get("blocks") or []:
            t = b.get("type")
            if t == "checklist":
                nck += 1
            if t == "timing" and not (isinstance(b.get("start"), list) and isinstance(b.get("end"), list)):
                warn.append("필수: 섹션 %d timing에 start/end [시각, 설명] 필요" % (i + 1))
            if t in REQ:
                key, sub = REQ[t]
                items = b.get(key)
                if not isinstance(items, list) or not items:
                    warn.append("필수: 섹션 %d %s에 %s 목록 필요" % (i + 1, t, key))
                elif sub and any(not isinstance(x, dict) or not x.get(sub) for x in items):
                    warn.append("필수: 섹션 %d %s.%s[].%s 누락" % (i + 1, t, key, sub))
    if nck > 1:
        warn.append("필수: checklist는 페이지당 1개만")
    texts = []
    walk_strings(c, texts)
    dash = [t[:40] for t in texts if "\u2014" in t]
    if dash:
        warn.append("긴 줄표(—) %d곳: %s" % (len(dash), dash[:3]))
    refs = set(re.findall(r"@([A-Za-z0-9_\-]+)", json.dumps(c, ensure_ascii=False)))
    missing = sorted(r for r in refs if r not in (c.get("images") or {}))
    if missing:
        warn.append("images에 없는 참조: %s" % missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--theme")
    ap.add_argument("--accent")
    ap.add_argument("--lib", default=DEFAULT_LIB)
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any warning")
    a = ap.parse_args()

    with open(a.content, encoding="utf-8") as f:
        raw_content = f.read()
    c = json.loads(raw_content)
    meta = c.setdefault("meta", {})
    if a.theme:
        meta["theme"] = a.theme
    if meta.get("theme", "paper") not in THEMES:
        print("경고: 모르는 theme '%s' -> paper" % meta.get("theme"))
        meta["theme"] = "paper"
    warn = []
    lint(c, warn)
    base = os.path.dirname(os.path.abspath(a.content))
    c["images"] = {k: resolve(v, base, a.lib, warn) for k, v in (c.get("images") or {}).items()}

    with open(a.template, encoding="utf-8") as f:
        html = f.read()
    override = ""
    accent = a.accent or meta.get("accent")
    if accent and not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", str(accent)):
        warn.append("accent는 #hex 형식이어야 함: %s (무시)" % accent)
        accent = None
    if accent:
        override = ":root[data-theme]{--accent:%s}" % accent
    payload = json.dumps(c, ensure_ascii=False).replace("<", "\\u003c")
    title = meta.get("title") or "모션시각화"
    html = (html.replace("/*__THEME_OVERRIDE__*/", override)
                .replace("__TITLE__", title.replace("<", "&lt;"))
                .replace("__CONTENT_JSON__", payload))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)

    print("완성: %s" % a.out)
    print("  내용 %d자 / 결과 %dKB / 섹션 %d개 / 이미지 %d개 / 옷 %s"
          % (len(raw_content), os.path.getsize(a.out) // 1024, len(c.get("sections") or []),
             len(c["images"]), meta.get("theme", "paper")))
    for w in warn:
        print("  경고: " + w)
    return 1 if (warn and a.strict) or any(w.startswith("필수") for w in warn) else 0


if __name__ == "__main__":
    sys.exit(main())
