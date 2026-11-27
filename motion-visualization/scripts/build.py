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

for _s in (sys.stdout, sys.stderr):  # Korean Windows consoles default to cp949
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")
EXPLAINER = os.path.join(HERE, "..", "assets", "explainer.html")
SCENES = {"title", "chapter", "kinetic", "build", "compare", "list", "focus", "doc", "map", "end"}
DEFAULT_LIB = os.path.join(HERE, "..", "assets", "brands")
BLOCKS = {"verdict", "scenes", "diagram", "chips", "callout", "dict", "folders", "rules", "steps", "words",
          "lanes", "timing", "annotated", "cases", "safety", "pull", "faq", "agenda", "checklist", "ledger",
          "figure", "code", "text", "html", "compare", "decide"}
THEMES = {"paper", "calm", "warm", "night"}
# deck mode: more items than this in one block usually makes the scene scroll inside (laptop 1280x800)
DENSITY = {"folders": ("items", 6), "agenda": ("items", 10), "dict": ("items", 8), "faq": ("items", 8),
           "steps": ("items", 4), "diagram": ("nodes", 6), "rules": ("items", 6), "checklist": ("items", 10),
           "compare": ("rows", 8), "decide": ("items", 4)}
TAG_RE = re.compile(r"<[^>]+>")
TOKEN_RE = re.compile(r"[0-9A-Za-z\uac00-\ud7a3]+")


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


def lint_explainer(c, warn):
    sc = c.get("scenes") or []
    if not sc:
        warn.append("필수: scenes가 비어 있음")
    for i, s in enumerate(sc):
        t = s.get("type")
        if t not in SCENES:
            warn.append("필수: 장면 %d 모르는 type '%s'" % (i + 1, t))
        if t == "build" and not s.get("nodes"):
            warn.append("필수: 장면 %d build에 nodes 필요" % (i + 1))
        if t in ("focus",) and not s.get("img"):
            warn.append("필수: 장면 %d focus에 img 필요" % (i + 1))
        for b in s.get("beats") or []:
            say = str(b.get("say") or "").replace("**", "")
            if len(say) > 34:
                warn.append("장면 %d 자막이 깁니다(%d자): %s" % (i + 1, len(say), say[:20]))
        say0 = str(s.get("say") or "").replace("**", "")
        if len(say0) > 34:
            warn.append("장면 %d 자막이 깁니다(%d자)" % (i + 1, len(say0)))
    texts = []
    walk_strings(c, texts)
    if any("\u2014" in t for t in texts):
        warn.append("긴 줄표(—) 있음")
    if not (c.get("meta") or {}).get("goal"):
        warn.append("인지부하: meta.goal 없음. '누가 보고 무엇을 정하거나 하는가'를 한 문장으로 적기")
    sides = [str(x) for x in ((c.get("meta") or {}).get("sides") or [])][:2]
    if len(sides) == 2:
        for i, s in enumerate(sc):
            if s.get("type") == "compare":
                names = [str((col or {}).get("title") or "").replace("*", "") for col in (s.get("cols") or [])]
                hit = [n for n in names if n in sides]
                if len(hit) == 2 and hit != sides:
                    warn.append("인지부하: 장면 %d compare 순서가 %s와 반대. 항상 %s 먼저(왼쪽)" % (i + 1, " → ".join(sides), sides[0]))
                elif len(hit) < 2 and not any((col or {}).get("tone") for col in (s.get("cols") or [])):
                    warn.append("인지부하: 장면 %d compare 제목이 meta.sides 이름과 달라 색이 고정되지 않음" % (i + 1))
    kinds = [s.get("type") for s in sc]
    for j in range(len(kinds) - 2):
        if kinds[j] == kinds[j + 1] == kinds[j + 2] and kinds[j] not in ("chapter",):
            warn.append("인지부하: 장면 %d~%d가 모두 '%s'. 같은 모양이 이어지면 지루해짐, 다른 장면 종류 섞기" % (j + 1, j + 3, kinds[j]))
            break


STRUCT_KEYS = {"type", "tone", "key", "img", "icon", "icons", "logo", "storageKey", "id", "href", "where", "okLabel", "label", "chip"}


def _content_strings(node, out):
    """Reader-facing text only: skip structural values and fixed row titles of detail popups."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for x in node:
            _content_strings(x, out)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in STRUCT_KEYS:
                continue
            if k == "detail" and isinstance(v, list):
                _content_strings([x[1] if isinstance(x, list) and len(x) > 1 else x for x in v], out)
                continue
            _content_strings(v, out)


def _plain(node):
    out = []
    _content_strings(node, out)
    return TAG_RE.sub(" ", " ".join(x for x in out if not x.startswith("@")))


def lint_load(c, warn):
    """Cognitive-load checks (references/cognitive-load.md). Warnings only, never block the build."""
    meta = c.get("meta") or {}
    secs = c.get("sections") or []
    sides = [str(x) for x in (meta.get("sides") or [])][:2]
    purpose = meta.get("purpose")
    P = "인지부하: "
    if not meta.get("goal"):
        warn.append(P + "meta.goal 없음. '누가 읽고 무엇을 정하거나 하는가'를 한 문장으로 적기")
    blocks = [(i, b) for i, s in enumerate(secs) for b in (s.get("blocks") or [])]
    # 1) verdict numbers must be comparable: many different units = reader converts in head
    for i, b in blocks:
        if b.get("type") == "verdict":
            units = {str(s[1]).strip() for s in (b.get("stats") or []) if isinstance(s, list) and len(s) > 1 and str(s[1]).strip()}
            if len(units) > (2 if (purpose == "decide" or sides) else 3):
                warn.append(P + "섹션 %d 결론 숫자 단위 %d종(%s). 같은 잣대로 비교되는 숫자만 남기거나 compare 표로 옮기기"
                            % (i + 1, len(units), ", ".join(sorted(units))))
    # 2) mixed-subject cells: two things crammed in one card -> use compare
    pair = re.compile(r"<b>[^<]{1,24}</b>[^<]{0,80}·\s*<b>[^<]{1,24}</b>")
    for i, b in blocks:
        if b.get("type") in ("dict", "folders", "chips"):
            items = b.get("items") or []
            mixed = 0
            for x in items:
                t = json.dumps(x, ensure_ascii=False)
                if pair.search(t.replace('\\"', '"')) or (len(sides) == 2 and all(sd in t for sd in sides)):
                    mixed += 1
            if mixed >= 3:
                warn.append(P + "섹션 %d %s 항목 %d개가 한 칸에 두 대상을 섞음. compare 블록(왼쪽/오른쪽 고정)으로 바꾸기" % (i + 1, b.get("type"), mixed))
    # 3) same phrase in many scenes (cover counts as a scene)
    stop = {w.lower() for w in TOKEN_RE.findall(" ".join(sides + [str(meta.get("brand") or "")] + [str(x) for x in (meta.get("terms") or [])]))}
    rep_min = 3 if purpose == "decide" else 5
    scene_texts = [_plain(c.get("cover") or {})] + [_plain([s.get("title"), s.get("lede"), [b for b in (s.get("blocks") or []) if b.get("type") != "ledger"]]) for s in secs]
    seen = {}
    for k, txt in enumerate(scene_texts):
        toks = [t.lower() for t in TOKEN_RE.findall(txt)]
        grams = set()
        for n in (2, 3):
            for j in range(len(toks) - n + 1):
                g = toks[j:j + n]
                if all(any(t.startswith(sw) for sw in stop if len(sw) >= 2) or t in stop or len(t) < 2 or t.isdigit() for t in g):  # Korean particles: 코드가 ~ 코드
                    continue
                if sum(len(t) for t in g) < 5:
                    continue
                grams.add(" ".join(g))
        for g in grams:
            seen.setdefault(g, set()).add(k)
    rep = sorted(((len(v), g) for g, v in seen.items() if len(v) >= rep_min), reverse=True)
    # keep only maximal phrases (drop sub-phrases of a reported longer one)
    shown = []
    for n, g in rep:
        if not any(g in h for _, h in shown):
            shown.append((n, g))
    if shown:
        warn.append(P + "같은 말이 여러 장면에 반복: %s. 한 장면에서만 자세히, 나머지는 빼기"
                    % ", ".join("'%s'(%d장면)" % (g, n) for n, g in shown[:4]))
    # 4) uncertainty only at the end -> reader can't tell while reading
    ledger_no = [x for _, b in blocks if b.get("type") == "ledger" for x in (b.get("no") or [])]
    body = json.dumps([[b for b in (s.get("blocks") or []) if b.get("type") != "ledger"] for s in secs], ensure_ascii=False)
    if ledger_no and "unv" not in body and "미확인" not in body:
        warn.append(P + "미확인 %d건이 마지막 장에만 있음. 본문 해당 자리에 <span class=\"unv\">미확인</span> 붙이기" % len(ledger_no))
    # 5) decision documents: answer first, few scenes
    if purpose == "decide":
        first = [b.get("type") for b in ((secs[0].get("blocks") if secs else None) or [])]
        if not ({"decide", "verdict"} & set(first)):
            warn.append(P + "purpose=decide인데 첫 장면에 decide/verdict 없음. 답을 먼저 보여 주기")
        if len(secs) > 6:
            warn.append(P + "결정용 자료인데 섹션 %d개(권장 6개 이하). 반복·배경 장면 합치기" % len(secs))
    # 7) lightest useful medium (Visual Intelligence v8): very short content may not need a magazine
    if 0 < len(secs) < 3:
        warn.append(P + "섹션 %d개. 매거진보다 표 하나나 짧은 답이 더 가벼울 수 있음(보고에 이유 적기)" % len(secs))
    # 8) same layout over and over (dashboard fatigue)
    firsts = [((s.get("blocks") or [{}])[0] or {}).get("type") for s in secs]
    for j in range(len(firsts) - 2):
        if firsts[j] and firsts[j] != "steps" and firsts[j] == firsts[j + 1] == firsts[j + 2]:
            warn.append(P + "섹션 %d~%d가 모두 '%s'로 시작. 같은 모양 반복, 표현 바꾸거나 합치기" % (j + 1, j + 3, firsts[j]))
            break
    # 6) fixed side/colour mapping: left/first = sides[0] = accent2 (a2), right/second = sides[1] = accent (a1)
    if len(sides) == 2:
        want = {sides[0]: "a2", sides[1]: "a1"}
        for i, b in blocks:
            t = b.get("type")
            if t == "folders":
                for f in b.get("items") or []:
                    tag = str(f.get("tag") or "")
                    hit = [sd for sd in sides if sd in tag]
                    if len(hit) == 1 and f.get("tone") != want[hit[0]]:
                        warn.append(P + "섹션 %d folders '%s' 색이 다른 장면과 반대. %s는 tone '%s'" % (i + 1, f.get("name"), hit[0], want[hit[0]]))
            if t in ("lanes", "scenes"):
                order = []
                for it in b.get("items") or []:
                    txt = json.dumps(it, ensure_ascii=False)
                    hit = [sd for sd in sides if sd in txt]
                    if len(hit) == 1:
                        order.append(hit[0])
                if len(order) == 2 and order != sides:
                    warn.append(P + "섹션 %d %s 순서가 %s와 반대. 항상 %s 먼저(왼쪽)" % (i + 1, t, " → ".join(sides), sides[0]))
            if t == "compare" and b.get("cols"):
                names = [x if isinstance(x, str) else (x or {}).get("name") for x in b.get("cols")]
                if names[:2] != sides:
                    warn.append(P + "섹션 %d compare 열 순서가 meta.sides와 다름" % (i + 1))


def lint(c, warn):
    if (c.get("meta") or {}).get("kind") == "explainer":
        return lint_explainer(c, warn)
    secs = c.get("sections") or []
    if not secs:
        warn.append("sections가 비어 있음")
    for i, s in enumerate(secs):
        for b in s.get("blocks") or []:
            if b.get("type") not in BLOCKS:
                warn.append("섹션 %d: 모르는 블록 '%s'" % (i + 1, b.get("type")))
    REQ = {"words": ("items", "say"), "steps": ("items", "title"), "faq": ("items", None), "checklist": ("items", None),
           "diagram": ("nodes", "title"), "dict": ("items", None), "cases": ("groups", "items"),
           "compare": ("rows", None), "decide": ("items", "q")}
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
    unused = sorted(k for k in (c.get("images") or {}) if k not in refs)
    if unused:
        warn.append("등록만 하고 안 쓴 그림: %s (빼면 파일이 가벼워짐)" % unused)
    meta = c.get("meta") or {}
    if meta.get("mode", "deck") == "deck":
        for i, s in enumerate(secs):
            blocks = s.get("blocks") or []
            if len(blocks) > 3:
                warn.append("섹션 %d(%d번 장면): 블록 %d개(넘겨 보기는 2~3개 권장, 섹션 나누기)" % (i + 1, i + 2, len(blocks)))
            for b in blocks:
                t = b.get("type")
                if t in DENSITY:
                    key, lim = DENSITY[t]
                    n = len(b.get(key) or [])
                    if n > lim:
                        warn.append("섹션 %d(%d번 장면): %s 항목 %d개(권장 %d개 이하). 장면 안 스크롤이 생길 수 있음" % (i + 1, i + 2, t, n, lim))
                if t == "cases":
                    n = sum(len(g.get("items") or []) for g in (b.get("groups") or []))
                    if n > 4:
                        warn.append("섹션 %d(%d번 장면): cases 카드 %d개(권장 4개 이하). 그룹을 두 장면으로 나누기" % (i + 1, i + 2, n))
    ser = meta.get("series")
    if ser:
        items = ser.get("items") if isinstance(ser, dict) else None
        if not isinstance(items, list) or not items:
            warn.append("meta.series.items 목록 필요")
        elif sum(1 for x in items if isinstance(x, dict) and x.get("current")) != 1:
            warn.append("meta.series.items 중 current:true는 하나여야 함")
    for i, s in enumerate(secs):
        for b in s.get("blocks") or []:
            if b.get("type") == "compare":
                if len(b.get("cols") or meta.get("sides") or []) < 2:
                    warn.append("필수: 섹션 %d compare에 cols 2개 또는 meta.sides 필요" % (i + 1))
                if any(not isinstance(r, list) or len(r) < 3 for r in (b.get("rows") or [])):
                    warn.append("필수: 섹션 %d compare.rows는 [기준, 왼쪽, 오른쪽, 유리(선택)]" % (i + 1))
    lint_load(c, warn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--theme")
    ap.add_argument("--accent")
    ap.add_argument("--ratio", choices=["16:9", "9:16"], help="설명 영상: 16:9 PPT판 / 9:16 숏폼판")
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
    if a.ratio:
        meta["ratio"] = a.ratio
    if meta.get("theme", "paper") not in THEMES:
        print("경고: 모르는 theme '%s' -> paper" % meta.get("theme"))
        meta["theme"] = "paper"
    warn = []
    lint(c, warn)
    base = os.path.dirname(os.path.abspath(a.content))
    c["images"] = {k: resolve(v, base, a.lib, warn) for k, v in (c.get("images") or {}).items()}

    tpl = a.template
    if meta.get("kind") == "explainer" and a.template == TEMPLATE:
        tpl = EXPLAINER
    with open(tpl, encoding="utf-8") as f:
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
    print("  내용 %d자 / 결과 %dKB / %s %d개 / 이미지 %d개 / 옷 %s"
          % (len(raw_content), os.path.getsize(a.out) // 1024, "장면" if meta.get("kind") == "explainer" else "섹션",
             len(c.get("scenes") or c.get("sections") or []),
             len(c["images"]), meta.get("theme", "paper")))
    for w in warn:
        print("  경고: " + w)
    return 1 if (warn and a.strict) or any(w.startswith("필수") for w in warn) else 0


if __name__ == "__main__":
    sys.exit(main())
