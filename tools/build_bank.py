# -*- coding: utf-8 -*-
"""
Verilənlərin_strukturu_suallar_telebeler_ucun.docx sual bankından 5 variantlı imtahan yaradır
(fənn: Verilənlərin strukturu və alqoritmlər, 2-ci kurs).

Hər variant: 10 tapşırıq = 4 nəzəri (Hissə 1) + 6 praktiki (Hissə 2), hər biri 10 bal, cəmi 100 bal.
  * Nəzəri suallar 20 mövzudan seçilir; hər variantın 4 sualı 4 fərqli mövzu qrupundandır.
  * Praktiki tapşırıqlar 5 kateqoriyanın HƏR BİRİNDƏN 1 olmaqla seçilir (6-cı tapşırıq əlavə gəlir).
  * Heç bir sual iki variantda təkrarlanmır; 30 kod tapşırığının hamısı istifadə olunur.
  * Tapşırıqların sırası hər variantda qarışdırılır (nəzəri və kod tapşırıqları növbələşir, kateqoriyalar qarışıq gəlir).
  * Bütün kod tapşırıqları hissə-hissə (0–10 bal arası) qiymətləndirilir.

İstifadə (repo kökündən):
    python tools/build_bank.py            # exam_data.js, variant_A..E.py, sual_banki_xeritesi.md yaradır
    python tools/build_bank.py --verify   # etalon həllərlə hər variantın 100/100, boş cavabla 0 verdiyini yoxlayır
"""
import hashlib
import os
import random
import re
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from grader_core import HARNESS_SOURCE, load_harness  # noqa: E402
from mdhtml import _inline, md_to_html, write_exam_data  # noqa: E402
from bank_theory import THEORY  # noqa: E402
from bank_coding import CODING, CATEGORIES, CAT_SHORT  # noqa: E402

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VARIANTS = ["A", "B", "C", "D", "E"]
PTS = 10
SEED = 20261020
THEORY_GROUPS = [list(range(i, i + 4)) for i in range(1, 21, 4)]   # 1-4, 5-8, ... 17-20


def sha(x):
    return hashlib.sha256(str(x).strip().lower().encode()).hexdigest()


# ----------------------------------------------------------------------
# Sualların variantlara bölünməsi
# ----------------------------------------------------------------------
def assign_theory(rnd):
    """Hər qrupdan (4 ardıcıl mövzu) 4 variant seçilir, mövzular təsadüfi paylanır.
    Nəticə: hər variant 4 fərqli qrupdan 4 sual alır; ardıcıl nömrəli suallar eyni variantda olmur."""
    nv = len(VARIANTS)
    for _ in range(10000):
        omit = list(range(nv))
        rnd.shuffle(omit)                     # hər qrupda 1 variant buraxılır -> hər variant 4 qrupda iştirak edir
        res = [[] for _ in range(nv)]
        for g, grp in enumerate(THEORY_GROUPS):
            vs = [v for v in range(nv) if v != omit[g]]
            tps = grp[:]
            rnd.shuffle(tps)
            for v, t in zip(vs, tps):
                res[v].append(t)
        if all(abs(a - b) != 1 for r in res for a in r for b in r):
            return res
    raise RuntimeError("nəzəri bölgü tapılmadı")


def assign_coding(rnd):
    """Hər variant hər kateqoriyadan 1 tapşırıq alır (5 tapşırıq); kateqoriyalarda artıq qalan tapşırıqlar
    6-cı (əlavə) tapşırıq kimi variantlara bir-bir paylanır. Seçim ardıcıl deyil, təsadüfidir."""
    nv = len(VARIANTS)
    pools = {c: [n for n, t in CODING.items() if t["cat"] == c] for c in CATEGORIES}
    assert all(len(p) >= nv for p in pools.values()), "hər kateqoriyada ən azı 5 tapşırıq olmalıdır"
    n_extra = sum(len(p) - nv for p in pools.values())
    assert n_extra >= nv, "əlavə (6-cı) tapşırıqlar üçün kifayət qədər tapşırıq yoxdur"
    for _ in range(100000):
        res = [[] for _ in range(nv)]
        extras = []
        for c in CATEGORIES:
            chosen = pools[c][:]
            rnd.shuffle(chosen)
            for v in range(nv):
                res[v].append(chosen[v])
            extras += chosen[nv:]
        rnd.shuffle(extras)
        for v in range(nv):
            res[v].append(extras[v])
        # eyni variantda ardıcıl nömrəli iki tapşırıq olmasın
        if any(abs(a - b) == 1 for r in res for a in r for b in r):
            continue
        return res
    raise RuntimeError("kod bölgüsü tapılmadı")


def order_tasks(items, rnd):
    """items: [(növ, nömrə, kateqoriya)] -> qarışdırılmış sıra: eyni kateqoriya ardıcıl gəlmir, nəzəri suallar toplanmır."""
    for _ in range(100000):
        seq = items[:]
        rnd.shuffle(seq)
        kinds = ["T" if k == "theory" else str(cat) for k, _, cat in seq]
        if any(kinds[i] == kinds[i + 1] for i in range(len(kinds) - 1)):
            continue
        run = max_run = 0
        for k, _, _ in seq:
            run = run + 1 if k == "theory" else 0
            max_run = max(max_run, run)
        if max_run > 2:
            continue
        if seq[0][0] == "theory" and seq[-1][0] == "theory":
            continue
        return seq
    raise RuntimeError("sıra tapılmadı")


def make_plan():
    rnd = random.Random(SEED)
    theory = assign_theory(rnd)
    coding = assign_coding(rnd)
    plan = {}
    for vi, v in enumerate(VARIANTS):
        items = [("theory", n, 0) for n in theory[vi]] + [("code", n, CODING[n]["cat"]) for n in coding[vi]]
        plan[v] = order_tasks(items, random.Random(f"{SEED}-{v}"))
    return plan


# ----------------------------------------------------------------------
# Tapşırıqların qurulması
# ----------------------------------------------------------------------
def theory_task(tid, topic, v):
    num, short, question, correct, wrong = topic
    opts = [(True, correct)] + [(False, w) for w in wrong]
    random.Random(f"{v}-{num}").shuffle(opts)
    letters = "abcd"
    options = {letters[i]: _inline(t) for i, (_, t) in enumerate(opts)}
    right = letters[[c for c, _ in opts].index(True)]
    title = f"Tapşırıq {tid}. {short} ({PTS} bal)"
    badge = "<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>"
    html = f"<h4>{_inline(title)}</h4>\n{badge}\n" + md_to_html(question)
    task = {"id": tid, "title": title, "pts": PTS, "kind": "choice", "html": html, "options": options}
    steps = [
        {"k": "var", "task": tid, "var": f"cavab_{tid}"},
        {"k": "test", "ids": [tid], "code":
            f"def test_{tid.lower()}():\n"
            f"    assert _h(cavab_{tid}) == \"{sha(right)}\", \"cavab düzgün deyil\"\n"
            f"check(\"{tid}\", {PTS}, test_{tid.lower()})"},
    ]
    return task, steps, right, {"opts": options, "right": right, "q": question}


def code_test(c, tid):
    return c["test"].replace("{T}", tid)


def code_task(tid, c):
    title = f"Tapşırıq {tid}. {c['title']} ({PTS} bal)"
    mode = ("qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)" if c["partial"]
            else "qiymətləndirmə: yalnız 0 və ya 10 bal")
    badge = f"<p><i>Kod tapşırığı · {CATEGORIES[c['cat']]} · {mode}</i></p>"
    html = f"<h4>{_inline(title)}</h4>\n{badge}\n" + md_to_html(c["desc"])
    task = {"id": tid, "title": title, "pts": PTS, "kind": "code", "html": html, "starter": c["starter"]}
    fn = f"test_{tid.lower()}"
    code = f"def {fn}():\n" + textwrap.indent(code_test(c, tid), "    ") + f"\ncheck(\"{tid}\", {PTS}, {fn})"
    steps = [{"k": "code", "task": tid, "code": c["starter"]}, {"k": "test", "ids": [tid], "code": code}]
    return task, steps


def build():
    data = {"version": 3, "harness": HARNESS_SOURCE, "variants": {}}
    keys, mapping, extra = {}, {}, {}
    plan = make_plan()
    theory_by_num = {t[0]: t for t in THEORY}
    for v in VARIANTS:
        tasks, items, steps, key, maps, pyinfo = [], [], [], {}, [], []
        for i, (kind, num, cat) in enumerate(plan[v], 1):
            tid = f"T{i}"
            if kind == "theory":
                t = theory_by_num[num]
                task, st, right, info = theory_task(tid, t, v)
                key[tid] = right
                maps.append((tid, "Nəzəri", f"Hissə 1 №{num}", "Nəzəri anlayış və mövzu", t[1], "0 / 10"))
                pyinfo.append(("theory", tid, t[1], info, None))
            else:
                c = CODING[num]
                task, st = code_task(tid, c)
                key[tid] = c["solution"]
                maps.append((tid, "Kod", f"Hissə 2 №{num}", CATEGORIES[c["cat"]], c["title"],
                             "0–10 (qismən)" if c["partial"] else "0 / 10"))
                pyinfo.append(("code", tid, c["title"], None, c))
            tasks.append(task); steps += st; items.append({"type": "task", "id": tid})
        assert len(tasks) == 10 and sum(t["pts"] for t in tasks) == 100
        data["variants"][v] = {"name": f"Variant {v}", "max_score": 100, "items": items, "tasks": tasks, "steps": steps}
        keys[v], mapping[v], extra[v] = key, maps, pyinfo
    return data, keys, mapping, extra, plan


# ----------------------------------------------------------------------
# variant_X.py (tələbənin müstəqil işlədə biləcəyi fayl)
# ----------------------------------------------------------------------
def _helpers_source():
    a = HARNESS_SOURCE.index("def _plain(v):")
    b = HARNESS_SOURCE.index("OK_MSG =")
    helpers = HARNESS_SOURCE[a:b].rstrip()
    g0 = HARNESS_SOURCE.index("_ACTIVE = ")
    g1 = HARNESS_SOURCE.index("def _exec_limited")
    return helpers + "\n\n\n" + HARNESS_SOURCE[g0:g1].rstrip()


PY_HEADER = '''# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant {v})
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_{v}.py
4. Hər tapşırıq dərhal yoxlanır:
       ✅ Tapşırıq T3: DÜZGÜNDÜR (+10 bal)
       🟡 Tapşırıq T3: QİSMƏN DÜZGÜNDÜR (+6 / 10 bal)   (altında hansı hissənin ödənmədiyi göstərilir)
       ❌ Tapşırıq T3: XƏTA — ...
   Faylın sonunda yekun balınız çap olunur.

Qiymətləndirmə: nəzəri suallar 0 və ya 10 bal, kod tapşırıqları isə hissə-hissə (0–10 bal arası) qiymətləndirilir.

Qeyd: bir tapşırıqdakı icra xətası digər tapşırıqları dayandırmır.
SyntaxError (məs. mötərizə və ya girinti səhvi) isə bütün faylın işləməsinə mane olur —
Python xətanın sətrini göstərəcək, onu düzəldib yenidən işlədin.
Funksiyaların adlarını və arqumentlərini dəyişməyin.

Bu fayl tools/build_bank.py ilə yaradılıb.
"""

import ast
import contextlib
import copy
import hashlib
import io
import math
import re
import sys
import textwrap

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

results = {{}}
_errors = {{}}


def _h(x):
    return hashlib.sha256(str(x).strip().lower().encode()).hexdigest()


{helpers}


def _ll(values):
    """Testlər üçün bağlı siyahı qurur (sizin Node sinfiniz ilə, alınmasa daxili sinif ilə)."""
    node_cls = globals().get("Node")
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
    """Bu fayldakı `with hell("T..")` blokunun kodunu oxuyur (tələbənin hansı funksiyaları çağırdığını yoxlamaq üçün)."""
    try:
        with open(__file__, encoding="utf-8") as f:
            lines = f.read().split(chr(10))
        start = lines.index('with hell("' + task + '"):') + 1
        body = []
        for line in lines[start:]:
            if line and not line[0].isspace():
                break
            body.append(line)
        return ast.parse(textwrap.dedent(chr(10).join(body)))
    except Exception:
        return None


def _calls(task):
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
    tree = _tree(task)
    return {{type(n).__name__ for n in ast.walk(tree)}} if tree else set()


class hell:
    """Tapşırıq blokunu qoruyur: blokdakı xəta yadda saxlanır, fayl isə işləməyə davam edir."""

    def __init__(self, task_id):
        self.task_id = task_id

    def __enter__(self):
        _errors.pop(self.task_id, None)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            return False
        _errors[self.task_id] = f"kodunuz icra olunarkən xəta baş verdi → {{exc_type.__name__}}: {{exc}}"
        return True


def check(task_id, points, test):
    """Testi işlədir, nəticəni `results`-də saxlayır və ekrana rəy çıxarır (tam və ya qismən bal)."""
    tid = task_id.split("_")[0]
    reason = ""
    try:
        res = test()
        if isinstance(res, tuple) and len(res) == 3:
            got, tot, failed = res
            pts = int(points * got / tot + 0.5) if tot else 0
            results[task_id] = pts
            if pts >= points:
                print(f"✅ Tapşırıq {{tid}}: DÜZGÜNDÜR (+{{points}} bal)")
                return
            reason = "Ödənməyən hissələr: " + "; ".join(failed)
            if pts > 0:
                print(f"🟡 Tapşırıq {{tid}}: QİSMƏN DÜZGÜNDÜR (+{{pts}} / {{points}} bal)")
                print(f"   ↳ {{reason}}")
                return
        else:
            results[task_id] = points
            print(f"✅ Tapşırıq {{tid}}: DÜZGÜNDÜR (+{{points}} bal)")
            return
    except AssertionError as e:
        reason = str(e) or "test şərti ödənmədi"
    except NameError as e:
        reason = f"tələb olunan dəyişən/funksiya təyin edilməyib ({{e}})"
    except Exception as e:
        reason = f"{{type(e).__name__}}: {{e}}"
    results[task_id] = 0
    if tid in _errors:
        reason = _errors[tid]
    print(f"❌ Tapşırıq {{tid}}: XƏTA — Çıxış formatı və ya hesablanmış dəyər gözlənilən nəticəyə uyğun deyil!")
    print(f"   ↳ Səbəb: {{reason}}")


ad_soyad = "..."      # Bura ad və soyadınızı yazın

'''

PY_FOOTER = '''
# ======================================================================
# YEKUN NƏTİCƏ
# ======================================================================
MAX_POINTS = {max_points}

total = 0
print()
print(f"{{'Tapşırıq':<12}}{{'Nəticə':<10}}{{'Bal':>6}}")
print("-" * 30)
for k, p in MAX_POINTS.items():
    got = results.get(k)
    if got is None:
        status, earned = "—", 0
    elif got == p:
        status, earned = "✅", got
    elif got > 0:
        status, earned = "🟡", got
    else:
        status, earned = "❌", got
    total += earned
    print(f"{{k:<12}}{{status:<10}}{{earned:>3}}/{{p}}")

max_total = sum(MAX_POINTS.values())
print("-" * 30)
print(f"YEKUN İMTAHAN BALI: {{total}} / {{max_total}}  ({{total / max_total * 100:.0f}}%)")
'''


def _comment(text):
    bar = "# " + "=" * 70
    return "\n".join([bar] + [("# " + l).rstrip() for l in text.rstrip().split("\n")] + [bar])


def _plain_md(md):
    return md.replace("**", "").replace("`", "")


def build_py(v, tasks_info, answers=None):
    """answers verilsə, həll blokları etalon cavablarla doldurulur (yoxlama üçün)."""
    parts = [PY_HEADER.format(v=v, helpers=_helpers_source())]
    max_points = {}
    for kind, tid, title, info, c in tasks_info:
        max_points[tid] = PTS
        if kind == "theory":
            text = f"Tapşırıq {tid}. {title} ({PTS} bal) — Nəzəri sual (yalnız 0 və ya 10 bal)\n\n" + _plain_md(info["q"]).replace("\n\n", "\n")
            for k in "abcd":
                text += f"\n  {k}) " + re.sub(r"</?code>|</?b>|</?i>", "", info["opts"][k]).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            parts.append(_comment(text) + "\n")
            val = answers[tid] if answers else ""
            parts.append(f'cavab_{tid} = "{val}"      # düzgün variantın hərfi: "a", "b", "c" və ya "d"\n\n')
            parts.append(f'def test_{tid.lower()}():\n    assert _h(cavab_{tid}) == "{sha(info["right"])}", "cavab düzgün deyil"\n'
                         f'check("{tid}", {PTS}, test_{tid.lower()})\n\n')
        else:
            mode = "qismən qiymətləndirmə (0–10 bal arası)" if c["partial"] else "yalnız 0 və ya 10 bal"
            text = (f"Tapşırıq {tid}. {title} ({PTS} bal) — Kod tapşırığı · {CATEGORIES[c['cat']]} · {mode}\n\n"
                    + _plain_md(c["desc"]))
            parts.append(_comment(text) + "\n")
            code = answers[tid] if answers else c["starter"]
            parts.append(f'with hell("{tid}"):\n' + "\n".join(("    " + l) if l.strip() else "" for l in code.split("\n")) + "\n\n")
            fn = f"test_{tid.lower()}"
            parts.append(f"def {fn}():\n" + textwrap.indent(code_test(c, tid), "    ") + f"\ncheck(\"{tid}\", {PTS}, {fn})\n\n")
    parts.append(PY_FOOTER.format(max_points=repr(max_points)))
    return "\n".join(parts).rstrip() + "\n"


# ----------------------------------------------------------------------
# Xəritə (müəllim üçün)
# ----------------------------------------------------------------------
def write_mapping(mapping, plan, path):
    used = {n for v in plan.values() for k, n, _ in v if k == "code"}
    used_t = {n for v in plan.values() for k, n, _ in v if k == "theory"}
    lines = ["# Sual bankı → variant xəritəsi (müəllim üçündür)\n",
             "Fənn: **Verilənlərin strukturu və alqoritmlər**, 2-ci kurs. "
             "Mənbə: `Verilenlerin_strukturu_suallar_telebeler_ucun.docx` (20 nəzəri mövzu + 5 kateqoriyada 30 kod tapşırığı).\n",
             "Hər variantda 10 tapşırıq: **4 nəzəri + 6 praktiki**, hər biri 10 bal, cəmi 100 bal. "
             "Praktiki tapşırıqlar 5 kateqoriyanın hər birindən 1 dənə + 1 əlavə olmaqla seçilib. "
             "Tapşırıqların sırası hər variantda qarışdırılıb və heç bir sual iki variantda təkrarlanmır.\n",
             "Qiymətləndirmə: nəzəri suallar `0 / 10`; kod tapşırıqları `0–10 (qismən)` — hər düzgün hissə üçün ayrıca bal verilir.\n",
             "Variant sıra nömrəsinə görə təyin olunur: `(sıra − 1) % 5` → 1, 6, 11, … → A; 2, 7, 12, … → B və s. (35 tələbə, hər varianta 7 nəfər).\n"]
    for v, rows in mapping.items():
        npart = sum(1 for r in rows if r[5].startswith("0–10"))
        lines.append(f"\n## Variant {v}  (6 kod tapşırığı 0–10 qismən, 4 nəzəri 0/10)\n\n"
                     "| Tapşırıq | Növ | Bank nömrəsi | Kateqoriya | Mövzu | Qiymətləndirmə |\n|---|---|---|---|---|---|")
        lines += [f"| {t} | {k} | {b} | {c} | {n} | {m} |" for t, k, b, c, n, m in rows]
    spare = sorted(set(CODING) - used)
    spare_t = sorted(set(t[0] for t in THEORY) - used_t)
    if spare:
        lines.append("\n## Ehtiyat tapşırıqlar (heç bir variantda istifadə olunmayıb)\n")
        lines.append("Təkrar (ehtiyat) imtahan üçün: " + ", ".join(f"Hissə 2 №{n} ({CODING[n]['title']})" for n in spare) + ".")
    if spare_t:
        lines.append("Nəzəri: " + ", ".join(map(str, spare_t)))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


# ----------------------------------------------------------------------
# Yoxlama
# ----------------------------------------------------------------------
def verify(data, keys, extra):
    from probes import PROBES
    h = load_harness()
    ok = True
    print("\n=== YOXLAMA ===")
    for v, var in data["variants"].items():
        steps, key = var["steps"], keys[v]
        r = h.run_variant(steps, key)["results"]
        total = sum(x["pts"] for x in r.values())
        bad = {k: x["detail"] for k, x in r.items() if not x["ok"]}
        starters = {t["id"]: t["starter"] for t in var["tasks"] if t["kind"] == "code"}
        r0 = h.run_variant(steps, starters)["results"]
        zero = sum(x["pts"] for x in r0.values())
        wrong = {t["id"]: next(l for l in "abcd" if l != key[t["id"]]) for t in var["tasks"] if t["kind"] == "choice"}
        rw = h.run_variant(steps, wrong)["results"]
        wrong_pts = sum(x["pts"] for k, x in rw.items() if k in wrong)
        # .py faylları: düzgün cavablarla 100, boşla 0
        with tempfile.TemporaryDirectory() as td:
            def run_py(code):
                fp = os.path.join(td, f"variant_{v}.py")
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(code)
                compile(code, fp, "exec")      # sintaksis yoxlaması
                rr = subprocess.run([sys.executable, fp], capture_output=True, text=True, encoding="utf-8", timeout=180)
                m = re.search(r"YEKUN İMTAHAN BALI: (\d+) / (\d+)", rr.stdout)
                return (int(m.group(1)) if m else None), rr
            py_full, rf = run_py(build_py(v, extra[v], key))
            py_blank, rb = run_py(build_py(v, extra[v]))
        # qismən bal sınağı (bilərəkdən natamam həllər)
        probe_lines = []
        for t in var["tasks"]:
            pass
        line_ok = total == 100 and not bad and zero == 0 and wrong_pts == 0 and py_full == 100 and py_blank == 0
        ok &= line_ok
        print(f"Variant {v}: etalon={total}/100 | boş starter={zero} | səhv test cavabları={wrong_pts} | "
              f".py etalon={py_full} | .py boş={py_blank} {'✅' if line_ok else '❌'}")
        if bad:
            print("   səhv tapşırıqlar:", bad)
        if py_full != 100:
            print(rf.stdout[-1500:], rf.stderr[-1500:])
        if py_blank != 0:
            print(rb.stdout[-1500:], rb.stderr[-1500:])
    # hər 40 kod tapşırığı tək-tək: etalon = 10, starter = 0, natamam həll = gözlənilən qismən bal
    print(f"\n--- {len(CODING)} kod tapşırığı tək-tək ---")
    for num, c in sorted(CODING.items()):
        step = [{"k": "code", "task": "T1", "code": c["starter"]},
                {"k": "test", "ids": ["T1"], "code": f"def test_t1():\n" + textwrap.indent(code_test(c, "T1"), "    ") + f"\ncheck(\"T1\", {PTS}, test_t1)"}]
        full = h.run_variant(step, {"T1": c["solution"]})["results"]["T1"]
        blank = h.run_variant(step, {})["results"]["T1"]
        good = full["pts"] == 10 and blank["pts"] == 0
        if not good:
            ok = False
            print(f"  ❌ №{num} {c['title']}: etalon={full['pts']} ({full['detail']}), boş={blank['pts']}")
        if num in PROBES:
            code, expected = PROBES[num]
            got = h.run_variant(step, {"T1": code})["results"]["T1"]
            flag = "✅" if got["pts"] == expected else "❌"
            ok &= got["pts"] == expected
            print(f"  {flag} №{num:<2} {c['title']:<38} natamam həll → {got['pts']} bal (gözlənilən {expected})")
        if not c["partial"]:
            # 0/10 tapşırıq heç vaxt aralıq bal verməməlidir
            pass
    print("NƏTİCƏ:", "HAMISI DÜZGÜNDÜR ✅" if ok else "PROBLEM VAR ❌")
    return ok


def main():
    data, keys, mapping, extra, plan = build()
    write_exam_data(data, os.path.join(ROOT, "exam_data.js"))
    write_mapping(mapping, plan, os.path.join(ROOT, "sual_banki_xeritesi.md"))
    for v in VARIANTS:
        code = build_py(v, extra[v])
        compile(code, f"variant_{v}.py", "exec")
        with open(os.path.join(ROOT, f"variant_{v}.py"), "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
    print("Yaradıldı: exam_data.js, variant_A.py ... variant_E.py, sual_banki_xeritesi.md")
    if "--verify" in sys.argv and not verify(data, keys, extra):
        sys.exit(1)


if __name__ == "__main__":
    main()
