# -*- coding: utf-8 -*-
"""Sadə Markdown -> HTML çevirici (tapşırıq mətnləri üçün) və exam_data.js yazıcısı."""
import html
import json
import re


def _inline(text):
    keep = []

    def stash(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"

    text = re.sub(r"\$\$.+?\$\$|\$[^$\n]+\$|`[^`\n]+`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)

    def restore(m):
        tok = keep[int(m.group(1))]
        if tok.startswith("`"):
            return f"<code>{html.escape(tok[1:-1], quote=False)}</code>"
        return html.escape(tok, quote=False)

    return re.sub(r"\x00(\d+)\x00", restore, text)


def md_to_html(md):
    out, para, lst = [], [], None
    lines = md.split("\n")
    i = 0

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + "<br>".join(_inline(p) for p in para) + "</p>")
            para = []
        if lst:
            tag, entries = lst
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(e)}</li>" for e in entries) + f"</{tag}>")
            lst = None

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f"<pre class=\"md-code\"><code>{html.escape(chr(10).join(code), quote=False)}</code></pre>")
        elif s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            flush()
            out.append(f"<div class=\"math\">{html.escape(s, quote=False)}</div>")
        elif s == "---":
            flush()
            out.append("<hr>")
        elif s.startswith("#"):
            flush()
            level = min(len(s) - len(s.lstrip("#")), 4)
            out.append(f"<h{level + 1}>{_inline(s.lstrip('#').strip())}</h{level + 1}>")
        elif re.match(r"^[-*]\s+", s):
            if para:
                flush()
            if not lst or lst[0] != "ul":
                flush()
                lst = ("ul", [])
            lst[1].append(re.sub(r"^[-*]\s+", "", s))
        elif re.match(r"^\d+\.\s+", s):
            if para:
                flush()
            if not lst or lst[0] != "ol":
                flush()
                lst = ("ol", [])
            lst[1].append(re.sub(r"^\d+\.\s+", "", s))
        elif s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells_ = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells_):
                    rows.append(cells_)
                i += 1
            i -= 1
            body = "".join(
                "<tr>" + "".join(f"<{'th' if r == 0 else 'td'}>{_inline(c)}</{'th' if r == 0 else 'td'}>" for c in row) + "</tr>"
                for r, row in enumerate(rows))
            out.append(f"<table class=\"md-table\">{body}</table>")
        elif not s:
            flush()
        else:
            if lst:
                flush()
            para.append(s)
        i += 1
    flush()
    return "\n".join(out)


def write_exam_data(data, path):
    body = json.dumps(data, ensure_ascii=False, indent=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// AVTOMATİK YARADILIB: python tools/build_bank.py — əl ilə redaktə etməyin.\n")
        f.write("window.EXAM_DATA = " + body + ";\n")
