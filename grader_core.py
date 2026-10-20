# -*- coding: utf-8 -*-
"""
SDF yoxlama mühərriki (Verilənlərin strukturu və alqoritmlər) — həm brauzerdə (Pyodide, index.html),
həm də müəllimin kompüterində (yeniden_qiymetlendir.py) eyni kod işləyir.

HARNESS_SOURCE mətni tools/build_bank.py tərəfindən exam_data.js-ə yerləşdirilir.

Yumşaldılmış qaydalar (Colab / Jupyter kimi):
  * hər addıma 10 saniyə vaxt verilir; sonsuz dövr yalnız həmin tapşırığı dayandırır;
  * Tab simvolları, bütün kodun artıq girintisi, ">>> " başlıqları, %magic / !əmr sətirləri,
    “ağıllı” dırnaqlar və görünməz boşluqlar avtomatik düzəldilir;
  * xananın son sətri ifadədirsə, onun qiyməti Jupyter-dəki kimi çap olunur;
  * input() imtahanı dayandırmır — avtomatik 1, 2, 3, … qaytarır;
  * kod tapşırıqları 0–10 bal arası qismən qiymətləndirilir (grade(...) hissələri);
  * qaytarmaq əvəzinə siyahını yerində dəyişən və ya nəticəni çap edən həllər də qəbul olunur.
"""

import types

HARNESS_SOURCE = r'''
import ast
import builtins
import contextlib
import copy
import hashlib
import io
import json
import math
import re
import sys
import textwrap
import time

try:
    import numpy as np
except Exception:
    np = None

# Yalnız təhlükəsizlik üçün zəruri modullar bloklanır; digər standart kitabxanalar (collections, itertools, heapq, ...) sərbəstdir
_BLOCKED_MODULES = ("js", "pyodide", "pyodide_js", "_pyodide", "micropip", "subprocess", "socket")
_real_import = builtins.__import__


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] in _BLOCKED_MODULES:
        raise ImportError(f"'{name}' modulu imtahanda qadağandır")
    return _real_import(name, globals, locals, fromlist, level)


def _h(x):
    return hashlib.sha256(str(x).strip().lower().encode()).hexdigest()


def _plain(v):
    """numpy/tuple/set/deque tiplərini adi Python siyahı-dəyərlərinə çevirir (tolerant müqayisə üçün)."""
    if hasattr(v, "tolist"):
        v = v.tolist()
    if type(v).__name__ == "deque":
        v = list(v)
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    return v


def _eq(a, b):
    """Tolerant bərabərlik: list≈tuple≈deque, 1.0≈1, float-lar üçün kiçik xəta payı."""
    a, b = _plain(a), _plain(b)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b if isinstance(a, bool) and isinstance(b, bool) else False
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
        except TypeError:
            return False
    return a == b


class _N:
    """Testlər üçün ehtiyat bağlı siyahı düyünü."""
    def __init__(self, data):
        self.data = data
        self.next = None


def _ll_list(head, limit=10000):
    """Bağlı siyahını Python siyahısına çevirir."""
    out = []
    while head is not None and len(out) < limit:
        out.append(head.data)
        head = head.next
    return out


def _ret(fn, *args):
    """Funksiyanı arqumentlərin surəti ilə çağırır. Funksiya nəticəni qaytarmayıb siyahını yerində
    dəyişibsə (None qaytarıbsa), dəyişdirilmiş siyahı nəticə sayılır."""
    cp = [copy.deepcopy(a) for a in args]
    r = fn(*cp)
    if r is None and cp and isinstance(cp[0], list):
        return cp[0]
    return r


def _as_list(r):
    if isinstance(r, (list, tuple, set, frozenset)) or type(r).__name__ == "deque":
        return list(r)
    return r


def _capture(fn, *args):
    """Funksiyanın çap etdiyini (və qaytardığını) mətn kimi qaytarır."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*args)
    text = buf.getvalue()
    if r is not None:
        text += "\n" + (" ".join(map(str, r)) if isinstance(r, (list, tuple)) else str(r))
    return text


def _ints(text):
    return [int(x) for x in re.findall(r"-?\d+", str(text))]


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


OK_MSG = "✅ Tapşırıq {t}: DÜZGÜNDÜR (+{p} bal)"
PARTIAL_MSG = "🟡 Tapşırıq {t}: QİSMƏN DÜZGÜNDÜR (+{p} / {m} bal)"
FAIL_MSG = "❌ Tapşırıq {t}: XƏTA — Nəticə gözlənilən cavaba uyğun deyil"


_ACTIVE = {"tracer": None}


def _rearm():
    """Vaxt limiti aşıldıqda Python izləmə funksiyasını söndürür; növbəti hissə üçün yenidən qoşuruq."""
    if _ACTIVE["tracer"] is not None:
        sys.settrace(_ACTIVE["tracer"])


def grade(*items):
    """
    Qismən bal üçün: items = (çəki, "yoxlanılan hissə", çağırıla bilən) ...
    Hər hissə ayrıca yoxlanılır; ödənən hissələrin çəkisi toplanır (yalan / boş nəticə = ödənməyib).
    Qaytarır: (qazanılan_çəki, ümumi_çəki, [ödənməyən hissələrin təsviri]).
    """
    got = tot = 0
    failed = []
    for w, label, fn in items:
        tot += w
        _rearm()
        try:
            if not fn():
                raise AssertionError
            got += w
        except AssertionError:
            failed.append(label)
        except (Exception, SystemExit) as e:
            failed.append(f"{label} ({type(e).__name__}: {e})")
    return (got, tot, failed)


def _exec_limited(code, ns, budget, out, display=False, filename="<kod>"):
    """Kodu vaxt limiti ilə icra edir (sonsuz dövrlər brauzeri dondurmasın)."""
    deadline = time.monotonic() + budget

    def tracer(frame, event, arg):
        # yalnız tələbə kodu və testlər izlənir (yoxlama mühərrikinin öz funksiyaları yox)
        if frame.f_code.co_filename not in ("<kod>", "<test>"):
            return None
        if time.monotonic() > deadline:
            raise TimeoutError(f"icra {budget:g} saniyədən çox çəkdi (sonsuz dövr ola bilər)")
        return tracer

    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        _ACTIVE["tracer"] = tracer
        sys.settrace(tracer)
        try:
            _run_code(code, ns, display, filename)
        finally:
            sys.settrace(None)
            _ACTIVE["tracer"] = None


def _run_code(code, ns, display, filename):
    """Jupyter kimi: xananın son sətri ifadədirsə, qiyməti çap olunur."""
    tree = ast.parse(code, filename)
    last = None
    if display and tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    exec(compile(tree, filename, "exec"), ns)
    if last is not None:
        value = eval(compile(last, filename, "eval"), ns)
        if value is not None:
            print(repr(value))


class _Out(io.StringIO):
    """Çıxışı məhdudlaşdırır: sonsuz print dövrü yaddaşı doldurmasın."""
    LIMIT = 200_000

    def write(self, s):
        if self.tell() < self.LIMIT:
            return super().write(s[: self.LIMIT - self.tell()])
        return len(s)


# ----------------------------------------------------------------------
# Kodun hazırlanması (Colab / Jupyter kimi yumşaq qaydalar)
# ----------------------------------------------------------------------
_INVISIBLE = str.maketrans({"﻿": None, "​": None, "‌": None, "‍": None, "⁠": None})
_SPACES = str.maketrans({" ": " ", " ": " ", " ": " ", " ": " ", "　": " "})
_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'",
                         "–": "-", "−": "-"})


def _lead_tabs(code):
    out = []
    for line in code.split("\n"):
        lead = re.match(r"[ \t]*", line).group(0)
        if "\t" in lead:
            line = lead.expandtabs(4) + line[len(lead):]
        out.append(line)
    return "\n".join(out)


def _strip_prompts(code):
    lines = code.split("\n")
    body = [l for l in lines if l.strip()]
    if body and all(l.lstrip().startswith((">>>", "...")) for l in body):
        return "\n".join(re.sub(r"^\s*(>>>|\.\.\.) ?", "", l) for l in lines)
    return code


def _strip_magics(code):
    return "\n".join(l for l in code.split("\n")
                     if not (l.lstrip().startswith(("%", "!")) and not l.lstrip().startswith("!=")))


def _compiles(code):
    try:
        compile(code, "<kod>", "exec")
        return True
    except Exception:
        return False


def normalize_code(code):
    """Tələbə kodunu icraya hazırlayır. Əsas düzəlişlər həmişə edilir; qalanları yalnız kod əks halda
    kompilyasiya olunmursa sınanır (sətir daxilindəki mətnlər pozulmasın)."""
    code = str(code).replace("\r\n", "\n").replace("\r", "\n").translate(_INVISIBLE)
    code = _lead_tabs(code)
    if _compiles(code):
        return code
    c = textwrap.dedent(code)
    candidates = [c]
    c = _strip_magics(_strip_prompts(c))
    candidates.append(textwrap.dedent(c))
    c = c.translate(_SPACES)
    candidates.append(textwrap.dedent(_lead_tabs(c)))
    c = c.translate(_QUOTES)
    candidates.append(textwrap.dedent(_lead_tabs(c)))
    for cand in candidates:
        if _compiles(cand):
            return cand
    return code


def _error_line(exc):
    ln = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<kod>":
            ln = tb.tb_lineno
        tb = tb.tb_next
    return ln


def _describe(exc):
    if "'___'" in str(exc):
        return "`___` boşluqları hələ doldurulmayıb"
    if isinstance(exc, IndentationError):
        line = (exc.text or "").strip()
        return (f"Girinti (boşluq) xətası, sətir {exc.lineno}: {exc.msg}" + (f" → {line}" if line else "")
                + ". Blokun (def, if, for, while, class) içindəki sətirlər eyni sayda boşluqla başlamalıdır.")
    if isinstance(exc, SyntaxError):
        line = (exc.text or "").strip()
        return f"Sintaksis xətası (sətir {exc.lineno}): {exc.msg}" + (f" → {line}" if line else "")
    if isinstance(exc, TimeoutError):
        return f"TimeoutError: {exc}"
    s = f"{type(exc).__name__}: {exc}"
    ln = _error_line(exc)
    return s + (f" (sətir {ln})" if ln else "")


def _coerce(value):
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    if re.fullmatch(r"[+-]?\d+", s):
        return int(s)
    return s


def _make_input():
    counter = [0]

    def _input(prompt=""):
        counter[0] += 1
        value = str(counter[0])
        print(f"{prompt}{value}    ← input() avtomatik: {value}")
        return value

    return _input


def _make_builtins():
    return dict(vars(builtins), __import__=_guarded_import, input=_make_input())


def run_variant(steps, answers, upto=None, budget=10.0):
    """
    steps   : exam_data.js-dəki addımlar (tapşırıq ardıcıllığı ilə)
    answers : {"T1": "<kod>", "T2": "b", ...}
    upto    : yalnız bu tapşırığın testinə qədər icra et («Kodu yoxla» düyməsi üçün)
    Nəticə  : {"results": {id: {ok, pts, max, partial, msg, detail}}, "output": {id: stdout}}
    """
    answers = answers or {}
    src = {}
    ns = {
        "__name__": "__main__",
        "__builtins__": _make_builtins(),
        "math": math, "hashlib": hashlib, "_h": _h, "_eq": _eq, "grade": grade,
        "_ll_list": _ll_list, "_ret": _ret, "_as_list": _as_list, "_capture": _capture,
        "_ints": _ints, "_is_num": _is_num,
    }
    if np is not None:
        ns["np"] = np
    errors, results, output = {}, {}, {}
    defined_by = {}

    def _ll(values):
        """Testlər üçün bağlı siyahı qurur (tələbənin Node sinfi ilə, alınmasa daxili sinif ilə)."""
        node_cls = ns.get("Node")
        head = None
        for v in reversed(list(values)):
            node = None
            if isinstance(node_cls, type):
                try:
                    node = node_cls(v)
                    if getattr(node, "data", object()) != v:
                        node = None
                except Exception:
                    node = None
            if node is None:
                node = _N(v)
            node.next = head
            head = node
        return head

    def _tree(task):
        try:
            return ast.parse(src.get(task, ""))
        except Exception:
            return None

    def _calls(task):
        """Tələbə kodunda çağırılan funksiya/metod adları (məs. sum, max, sorted, pop)."""
        names = set()
        tree = _tree(task)
        for node in (ast.walk(tree) if tree else []):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name):
                    names.add(f.id)
                elif isinstance(f, ast.Attribute):
                    names.add(f.attr)
        return names

    def _nodes(task):
        """Tələbə kodunda olan sintaktik konstruksiyalar (məs. ListComp, For, While)."""
        tree = _tree(task)
        return {type(n).__name__ for n in ast.walk(tree)} if tree else set()

    ns.update(_ll=_ll, _calls=_calls, _nodes=_nodes)

    def finish(t, points, pts, detail):
        if pts >= points:
            results[t] = {"ok": True, "pts": points, "max": points, "partial": False,
                          "msg": OK_MSG.format(t=t, p=points), "detail": ""}
            return
        if t in errors:
            err = errors[t] if errors[t].startswith("`") else "kodunuz icra olunarkən xəta baş verdi → " + errors[t]
            detail = err if pts == 0 else f"{detail} | {err}"
        partial = pts > 0
        results[t] = {"ok": False, "pts": pts, "max": points, "partial": partial,
                      "msg": (PARTIAL_MSG.format(t=t, p=pts, m=points) if partial else FAIL_MSG.format(t=t)),
                      "detail": detail}

    def check(task_id, points, test):
        t = task_id.split("_")[0]
        _rearm()
        try:
            res = test()
        except AssertionError as e:
            return finish(t, points, 0, str(e) or "test şərti ödənmədi")
        except NameError as e:
            return finish(t, points, 0, f"tələb olunan dəyişən/funksiya təyin edilməyib ({e})")
        except BaseException as e:
            return finish(t, points, 0, _describe(e))
        if isinstance(res, tuple) and len(res) == 3:
            got, tot, failed = res
            pts = int(points * got / tot + 0.5) if tot else 0
            return finish(t, points, pts, "Ödənməyən hissələr: " + "; ".join(failed))
        return finish(t, points, points, "")

    ns["check"] = check

    for st in steps:
        kind = st["k"]
        if kind == "var":
            ns[st["var"]] = _coerce(answers.get(st["task"]))
            continue
        label = st.get("task")
        code = st["code"]
        if kind == "code" and label in answers and answers[label] is not None:
            code = normalize_code(answers[label])
        if kind == "code" and label:
            src[label] = code
        out = _Out()
        try:
            _exec_limited(code, ns, budget, out, display=(kind == "code"),
                          filename="<kod>" if kind == "code" else "<test>")
        except BaseException as e:
            if label:
                errors[label] = _describe(e)
        if kind == "code" and label:
            names = re.findall(r"^\s*([A-Za-z_]\w*)\s*=(?!=)", st["code"], re.M)
            names += re.findall(r"^\s*(?:def|class)\s+([A-Za-z_]\w*)", st["code"], re.M)
            for name in names:
                defined_by.setdefault(name, label)
        if label:
            output[label] = out.getvalue()[-5000:]
        elif kind == "test" and out.getvalue():
            output[st["ids"][0]] = (output.get(st["ids"][0], "") + out.getvalue())[-5000:]
        if kind == "test" and upto and upto in st["ids"]:
            break

    if upto:
        results = {k: v for k, v in results.items() if k == upto}
        output = {k: v for k, v in output.items() if k == upto}
    return {"results": results, "output": output}


def run_cell(code, budget=10.0):
    """«▶ İşə sal»: yalnız bu xananı Colab-dakı kimi icra edir (testsiz, bal hesablanmır)."""
    ns = {"__name__": "__main__", "__builtins__": _make_builtins(), "math": math}
    if np is not None:
        ns["np"] = np
    out = _Out()
    error = None
    try:
        _exec_limited(normalize_code(code), ns, budget, out, display=True)
    except BaseException as e:
        error = _describe(e)
    return {"output": out.getvalue()[-8000:], "error": error}


def run_json(payload):
    """Pyodide körpüsü: JSON mətn daxil olur, JSON mətn qayıdır."""
    p = json.loads(payload)
    if p.get("mode") == "cell":
        res = run_cell(p.get("code", ""), p.get("budget", 10.0))
    else:
        res = run_variant(p["steps"], p.get("answers"), p.get("upto"), p.get("budget", 10.0))
    return json.dumps(res, ensure_ascii=False)
'''


def load_harness():
    """HARNESS_SOURCE-u adi Python modulu kimi yükləyir (CPython-da istifadə üçün)."""
    mod = types.ModuleType("sdf1_harness")
    exec(compile(HARNESS_SOURCE, "sdf1_harness", "exec"), mod.__dict__)
    return mod
