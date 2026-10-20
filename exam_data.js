// AVTOMATİK YARADILIB: python tools/build_bank.py — əl ilə redaktə etməyin.
window.EXAM_DATA = {
 "version": 3,
 "harness": "\nimport ast\nimport builtins\nimport contextlib\nimport copy\nimport hashlib\nimport io\nimport json\nimport math\nimport re\nimport sys\nimport textwrap\nimport time\n\ntry:\n    import numpy as np\nexcept Exception:\n    np = None\n\n# Yalnız təhlükəsizlik üçün zəruri modullar bloklanır; digər standart kitabxanalar (collections, itertools, heapq, ...) sərbəstdir\n_BLOCKED_MODULES = (\"js\", \"pyodide\", \"pyodide_js\", \"_pyodide\", \"micropip\", \"subprocess\", \"socket\")\n_real_import = builtins.__import__\n\n\ndef _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):\n    if name.split(\".\")[0] in _BLOCKED_MODULES:\n        raise ImportError(f\"'{name}' modulu imtahanda qadağandır\")\n    return _real_import(name, globals, locals, fromlist, level)\n\n\ndef _h(x):\n    return hashlib.sha256(str(x).strip().lower().encode()).hexdigest()\n\n\ndef _plain(v):\n    \"\"\"numpy/tuple/set/deque tiplərini adi Python siyahı-dəyərlərinə çevirir (tolerant müqayisə üçün).\"\"\"\n    if hasattr(v, \"tolist\"):\n        v = v.tolist()\n    if type(v).__name__ == \"deque\":\n        v = list(v)\n    if isinstance(v, (list, tuple)):\n        return [_plain(x) for x in v]\n    if isinstance(v, dict):\n        return {k: _plain(x) for k, x in v.items()}\n    return v\n\n\ndef _eq(a, b):\n    \"\"\"Tolerant bərabərlik: list≈tuple≈deque, 1.0≈1, float-lar üçün kiçik xəta payı.\"\"\"\n    a, b = _plain(a), _plain(b)\n    if isinstance(a, list) and isinstance(b, list):\n        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))\n    if isinstance(a, dict) and isinstance(b, dict):\n        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)\n    if isinstance(a, bool) or isinstance(b, bool):\n        return a is b if isinstance(a, bool) and isinstance(b, bool) else False\n    if isinstance(a, float) or isinstance(b, float):\n        try:\n            return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)\n        except TypeError:\n            return False\n    return a == b\n\n\nclass _N:\n    \"\"\"Testlər üçün ehtiyat bağlı siyahı düyünü.\"\"\"\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef _ll_list(head, limit=10000):\n    \"\"\"Bağlı siyahını Python siyahısına çevirir.\"\"\"\n    out = []\n    while head is not None and len(out) < limit:\n        out.append(head.data)\n        head = head.next\n    return out\n\n\ndef _ret(fn, *args):\n    \"\"\"Funksiyanı arqumentlərin surəti ilə çağırır. Funksiya nəticəni qaytarmayıb siyahını yerində\n    dəyişibsə (None qaytarıbsa), dəyişdirilmiş siyahı nəticə sayılır.\"\"\"\n    cp = [copy.deepcopy(a) for a in args]\n    r = fn(*cp)\n    if r is None and cp and isinstance(cp[0], list):\n        return cp[0]\n    return r\n\n\ndef _as_list(r):\n    if isinstance(r, (list, tuple, set, frozenset)) or type(r).__name__ == \"deque\":\n        return list(r)\n    return r\n\n\ndef _capture(fn, *args):\n    \"\"\"Funksiyanın çap etdiyini (və qaytardığını) mətn kimi qaytarır.\"\"\"\n    buf = io.StringIO()\n    with contextlib.redirect_stdout(buf):\n        r = fn(*args)\n    text = buf.getvalue()\n    if r is not None:\n        text += \"\\n\" + (\" \".join(map(str, r)) if isinstance(r, (list, tuple)) else str(r))\n    return text\n\n\ndef _ints(text):\n    return [int(x) for x in re.findall(r\"-?\\d+\", str(text))]\n\n\ndef _is_num(x):\n    return isinstance(x, (int, float)) and not isinstance(x, bool)\n\n\nOK_MSG = \"✅ Tapşırıq {t}: DÜZGÜNDÜR (+{p} bal)\"\nPARTIAL_MSG = \"🟡 Tapşırıq {t}: QİSMƏN DÜZGÜNDÜR (+{p} / {m} bal)\"\nFAIL_MSG = \"❌ Tapşırıq {t}: XƏTA — Nəticə gözlənilən cavaba uyğun deyil\"\n\n\n_ACTIVE = {\"tracer\": None}\n\n\ndef _rearm():\n    \"\"\"Vaxt limiti aşıldıqda Python izləmə funksiyasını söndürür; növbəti hissə üçün yenidən qoşuruq.\"\"\"\n    if _ACTIVE[\"tracer\"] is not None:\n        sys.settrace(_ACTIVE[\"tracer\"])\n\n\ndef grade(*items):\n    \"\"\"\n    Qismən bal üçün: items = (çəki, \"yoxlanılan hissə\", çağırıla bilən) ...\n    Hər hissə ayrıca yoxlanılır; ödənən hissələrin çəkisi toplanır (yalan / boş nəticə = ödənməyib).\n    Qaytarır: (qazanılan_çəki, ümumi_çəki, [ödənməyən hissələrin təsviri]).\n    \"\"\"\n    got = tot = 0\n    failed = []\n    for w, label, fn in items:\n        tot += w\n        _rearm()\n        try:\n            if not fn():\n                raise AssertionError\n            got += w\n        except AssertionError:\n            failed.append(label)\n        except (Exception, SystemExit) as e:\n            failed.append(f\"{label} ({type(e).__name__}: {e})\")\n    return (got, tot, failed)\n\n\ndef _exec_limited(code, ns, budget, out, display=False, filename=\"<kod>\"):\n    \"\"\"Kodu vaxt limiti ilə icra edir (sonsuz dövrlər brauzeri dondurmasın).\"\"\"\n    deadline = time.monotonic() + budget\n\n    def tracer(frame, event, arg):\n        # yalnız tələbə kodu və testlər izlənir (yoxlama mühərrikinin öz funksiyaları yox)\n        if frame.f_code.co_filename not in (\"<kod>\", \"<test>\"):\n            return None\n        if time.monotonic() > deadline:\n            raise TimeoutError(f\"icra {budget:g} saniyədən çox çəkdi (sonsuz dövr ola bilər)\")\n        return tracer\n\n    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):\n        _ACTIVE[\"tracer\"] = tracer\n        sys.settrace(tracer)\n        try:\n            _run_code(code, ns, display, filename)\n        finally:\n            sys.settrace(None)\n            _ACTIVE[\"tracer\"] = None\n\n\ndef _run_code(code, ns, display, filename):\n    \"\"\"Jupyter kimi: xananın son sətri ifadədirsə, qiyməti çap olunur.\"\"\"\n    tree = ast.parse(code, filename)\n    last = None\n    if display and tree.body and isinstance(tree.body[-1], ast.Expr):\n        last = ast.Expression(tree.body.pop().value)\n    exec(compile(tree, filename, \"exec\"), ns)\n    if last is not None:\n        value = eval(compile(last, filename, \"eval\"), ns)\n        if value is not None:\n            print(repr(value))\n\n\nclass _Out(io.StringIO):\n    \"\"\"Çıxışı məhdudlaşdırır: sonsuz print dövrü yaddaşı doldurmasın.\"\"\"\n    LIMIT = 200_000\n\n    def write(self, s):\n        if self.tell() < self.LIMIT:\n            return super().write(s[: self.LIMIT - self.tell()])\n        return len(s)\n\n\n# ----------------------------------------------------------------------\n# Kodun hazırlanması (Colab / Jupyter kimi yumşaq qaydalar)\n# ----------------------------------------------------------------------\n_INVISIBLE = str.maketrans({\"﻿\": None, \"​\": None, \"‌\": None, \"‍\": None, \"⁠\": None})\n_SPACES = str.maketrans({\" \": \" \", \" \": \" \", \" \": \" \", \" \": \" \", \"　\": \" \"})\n_QUOTES = str.maketrans({\"“\": '\"', \"”\": '\"', \"„\": '\"', \"‘\": \"'\", \"’\": \"'\",\n                         \"–\": \"-\", \"−\": \"-\"})\n\n\ndef _lead_tabs(code):\n    out = []\n    for line in code.split(\"\\n\"):\n        lead = re.match(r\"[ \\t]*\", line).group(0)\n        if \"\\t\" in lead:\n            line = lead.expandtabs(4) + line[len(lead):]\n        out.append(line)\n    return \"\\n\".join(out)\n\n\ndef _strip_prompts(code):\n    lines = code.split(\"\\n\")\n    body = [l for l in lines if l.strip()]\n    if body and all(l.lstrip().startswith((\">>>\", \"...\")) for l in body):\n        return \"\\n\".join(re.sub(r\"^\\s*(>>>|\\.\\.\\.) ?\", \"\", l) for l in lines)\n    return code\n\n\ndef _strip_magics(code):\n    return \"\\n\".join(l for l in code.split(\"\\n\")\n                     if not (l.lstrip().startswith((\"%\", \"!\")) and not l.lstrip().startswith(\"!=\")))\n\n\ndef _compiles(code):\n    try:\n        compile(code, \"<kod>\", \"exec\")\n        return True\n    except Exception:\n        return False\n\n\ndef normalize_code(code):\n    \"\"\"Tələbə kodunu icraya hazırlayır. Əsas düzəlişlər həmişə edilir; qalanları yalnız kod əks halda\n    kompilyasiya olunmursa sınanır (sətir daxilindəki mətnlər pozulmasın).\"\"\"\n    code = str(code).replace(\"\\r\\n\", \"\\n\").replace(\"\\r\", \"\\n\").translate(_INVISIBLE)\n    code = _lead_tabs(code)\n    if _compiles(code):\n        return code\n    c = textwrap.dedent(code)\n    candidates = [c]\n    c = _strip_magics(_strip_prompts(c))\n    candidates.append(textwrap.dedent(c))\n    c = c.translate(_SPACES)\n    candidates.append(textwrap.dedent(_lead_tabs(c)))\n    c = c.translate(_QUOTES)\n    candidates.append(textwrap.dedent(_lead_tabs(c)))\n    for cand in candidates:\n        if _compiles(cand):\n            return cand\n    return code\n\n\ndef _error_line(exc):\n    ln = None\n    tb = exc.__traceback__\n    while tb is not None:\n        if tb.tb_frame.f_code.co_filename == \"<kod>\":\n            ln = tb.tb_lineno\n        tb = tb.tb_next\n    return ln\n\n\ndef _describe(exc):\n    if \"'___'\" in str(exc):\n        return \"`___` boşluqları hələ doldurulmayıb\"\n    if isinstance(exc, IndentationError):\n        line = (exc.text or \"\").strip()\n        return (f\"Girinti (boşluq) xətası, sətir {exc.lineno}: {exc.msg}\" + (f\" → {line}\" if line else \"\")\n                + \". Blokun (def, if, for, while, class) içindəki sətirlər eyni sayda boşluqla başlamalıdır.\")\n    if isinstance(exc, SyntaxError):\n        line = (exc.text or \"\").strip()\n        return f\"Sintaksis xətası (sətir {exc.lineno}): {exc.msg}\" + (f\" → {line}\" if line else \"\")\n    if isinstance(exc, TimeoutError):\n        return f\"TimeoutError: {exc}\"\n    s = f\"{type(exc).__name__}: {exc}\"\n    ln = _error_line(exc)\n    return s + (f\" (sətir {ln})\" if ln else \"\")\n\n\ndef _coerce(value):\n    if value is None:\n        return None\n    s = str(value).strip()\n    if s == \"\":\n        return None\n    if re.fullmatch(r\"[+-]?\\d+\", s):\n        return int(s)\n    return s\n\n\ndef _make_input():\n    counter = [0]\n\n    def _input(prompt=\"\"):\n        counter[0] += 1\n        value = str(counter[0])\n        print(f\"{prompt}{value}    ← input() avtomatik: {value}\")\n        return value\n\n    return _input\n\n\ndef _make_builtins():\n    return dict(vars(builtins), __import__=_guarded_import, input=_make_input())\n\n\ndef run_variant(steps, answers, upto=None, budget=10.0):\n    \"\"\"\n    steps   : exam_data.js-dəki addımlar (tapşırıq ardıcıllığı ilə)\n    answers : {\"T1\": \"<kod>\", \"T2\": \"b\", ...}\n    upto    : yalnız bu tapşırığın testinə qədər icra et («Kodu yoxla» düyməsi üçün)\n    Nəticə  : {\"results\": {id: {ok, pts, max, partial, msg, detail}}, \"output\": {id: stdout}}\n    \"\"\"\n    answers = answers or {}\n    src = {}\n    ns = {\n        \"__name__\": \"__main__\",\n        \"__builtins__\": _make_builtins(),\n        \"math\": math, \"hashlib\": hashlib, \"_h\": _h, \"_eq\": _eq, \"grade\": grade,\n        \"_ll_list\": _ll_list, \"_ret\": _ret, \"_as_list\": _as_list, \"_capture\": _capture,\n        \"_ints\": _ints, \"_is_num\": _is_num,\n    }\n    if np is not None:\n        ns[\"np\"] = np\n    errors, results, output = {}, {}, {}\n    defined_by = {}\n\n    def _ll(values):\n        \"\"\"Testlər üçün bağlı siyahı qurur (tələbənin Node sinfi ilə, alınmasa daxili sinif ilə).\"\"\"\n        node_cls = ns.get(\"Node\")\n        head = None\n        for v in reversed(list(values)):\n            node = None\n            if isinstance(node_cls, type):\n                try:\n                    node = node_cls(v)\n                    if getattr(node, \"data\", object()) != v:\n                        node = None\n                except Exception:\n                    node = None\n            if node is None:\n                node = _N(v)\n            node.next = head\n            head = node\n        return head\n\n    def _tree(task):\n        try:\n            return ast.parse(src.get(task, \"\"))\n        except Exception:\n            return None\n\n    def _calls(task):\n        \"\"\"Tələbə kodunda çağırılan funksiya/metod adları (məs. sum, max, sorted, pop).\"\"\"\n        names = set()\n        tree = _tree(task)\n        for node in (ast.walk(tree) if tree else []):\n            if isinstance(node, ast.Call):\n                f = node.func\n                if isinstance(f, ast.Name):\n                    names.add(f.id)\n                elif isinstance(f, ast.Attribute):\n                    names.add(f.attr)\n        return names\n\n    def _nodes(task):\n        \"\"\"Tələbə kodunda olan sintaktik konstruksiyalar (məs. ListComp, For, While).\"\"\"\n        tree = _tree(task)\n        return {type(n).__name__ for n in ast.walk(tree)} if tree else set()\n\n    ns.update(_ll=_ll, _calls=_calls, _nodes=_nodes)\n\n    def finish(t, points, pts, detail):\n        if pts >= points:\n            results[t] = {\"ok\": True, \"pts\": points, \"max\": points, \"partial\": False,\n                          \"msg\": OK_MSG.format(t=t, p=points), \"detail\": \"\"}\n            return\n        if t in errors:\n            err = errors[t] if errors[t].startswith(\"`\") else \"kodunuz icra olunarkən xəta baş verdi → \" + errors[t]\n            detail = err if pts == 0 else f\"{detail} | {err}\"\n        partial = pts > 0\n        results[t] = {\"ok\": False, \"pts\": pts, \"max\": points, \"partial\": partial,\n                      \"msg\": (PARTIAL_MSG.format(t=t, p=pts, m=points) if partial else FAIL_MSG.format(t=t)),\n                      \"detail\": detail}\n\n    def check(task_id, points, test):\n        t = task_id.split(\"_\")[0]\n        _rearm()\n        try:\n            res = test()\n        except AssertionError as e:\n            return finish(t, points, 0, str(e) or \"test şərti ödənmədi\")\n        except NameError as e:\n            return finish(t, points, 0, f\"tələb olunan dəyişən/funksiya təyin edilməyib ({e})\")\n        except BaseException as e:\n            return finish(t, points, 0, _describe(e))\n        if isinstance(res, tuple) and len(res) == 3:\n            got, tot, failed = res\n            pts = int(points * got / tot + 0.5) if tot else 0\n            return finish(t, points, pts, \"Ödənməyən hissələr: \" + \"; \".join(failed))\n        return finish(t, points, points, \"\")\n\n    ns[\"check\"] = check\n\n    for st in steps:\n        kind = st[\"k\"]\n        if kind == \"var\":\n            ns[st[\"var\"]] = _coerce(answers.get(st[\"task\"]))\n            continue\n        label = st.get(\"task\")\n        code = st[\"code\"]\n        if kind == \"code\" and label in answers and answers[label] is not None:\n            code = normalize_code(answers[label])\n        if kind == \"code\" and label:\n            src[label] = code\n        out = _Out()\n        try:\n            _exec_limited(code, ns, budget, out, display=(kind == \"code\"),\n                          filename=\"<kod>\" if kind == \"code\" else \"<test>\")\n        except BaseException as e:\n            if label:\n                errors[label] = _describe(e)\n        if kind == \"code\" and label:\n            names = re.findall(r\"^\\s*([A-Za-z_]\\w*)\\s*=(?!=)\", st[\"code\"], re.M)\n            names += re.findall(r\"^\\s*(?:def|class)\\s+([A-Za-z_]\\w*)\", st[\"code\"], re.M)\n            for name in names:\n                defined_by.setdefault(name, label)\n        if label:\n            output[label] = out.getvalue()[-5000:]\n        elif kind == \"test\" and out.getvalue():\n            output[st[\"ids\"][0]] = (output.get(st[\"ids\"][0], \"\") + out.getvalue())[-5000:]\n        if kind == \"test\" and upto and upto in st[\"ids\"]:\n            break\n\n    if upto:\n        results = {k: v for k, v in results.items() if k == upto}\n        output = {k: v for k, v in output.items() if k == upto}\n    return {\"results\": results, \"output\": output}\n\n\ndef run_cell(code, budget=10.0):\n    \"\"\"«▶ İşə sal»: yalnız bu xananı Colab-dakı kimi icra edir (testsiz, bal hesablanmır).\"\"\"\n    ns = {\"__name__\": \"__main__\", \"__builtins__\": _make_builtins(), \"math\": math}\n    if np is not None:\n        ns[\"np\"] = np\n    out = _Out()\n    error = None\n    try:\n        _exec_limited(normalize_code(code), ns, budget, out, display=True)\n    except BaseException as e:\n        error = _describe(e)\n    return {\"output\": out.getvalue()[-8000:], \"error\": error}\n\n\ndef run_json(payload):\n    \"\"\"Pyodide körpüsü: JSON mətn daxil olur, JSON mətn qayıdır.\"\"\"\n    p = json.loads(payload)\n    if p.get(\"mode\") == \"cell\":\n        res = run_cell(p.get(\"code\", \"\"), p.get(\"budget\", 10.0))\n    else:\n        res = run_variant(p[\"steps\"], p.get(\"answers\"), p.get(\"upto\"), p.get(\"budget\", 10.0))\n    return json.dumps(res, ensure_ascii=False)\n",
 "variants": {
  "A": {
   "name": "Variant A",
   "max_score": 100,
   "items": [
    {
     "type": "task",
     "id": "T1"
    },
    {
     "type": "task",
     "id": "T2"
    },
    {
     "type": "task",
     "id": "T3"
    },
    {
     "type": "task",
     "id": "T4"
    },
    {
     "type": "task",
     "id": "T5"
    },
    {
     "type": "task",
     "id": "T6"
    },
    {
     "type": "task",
     "id": "T7"
    },
    {
     "type": "task",
     "id": "T8"
    },
    {
     "type": "task",
     "id": "T9"
    },
    {
     "type": "task",
     "id": "T10"
    }
   ],
   "tasks": [
    {
     "id": "T1",
     "title": "Tapşırıq T1. Stek ilə sözü tərsinə çevirmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T1. Stek ilə sözü tərsinə çevirmək (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Stekdən istifadə edərək <code>ters(soz)</code> funksiyasını yazın: hərfləri <code>append()</code> ilə stekə əlavə edin, sonra <code>pop()</code> ilə<br>çıxararaq tərs sözü qurun və <b>qaytarın</b>.<br>Nümunə: <code>ters(\"Python\")</code> → <code>\"nohtyP\"</code>.</p>",
     "starter": "def ters(soz):\n    stek = []\n    # buranı yazın\n    pass\n\n\nprint(ters(\"Python\"))   # nohtyP olmalıdır"
    },
    {
     "id": "T2",
     "title": "Tapşırıq T2. Bağlı siyahının növləri (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T2. Bağlı siyahının növləri (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Halqa (dairəvi) bağlı siyahını adi tək bağlı siyahıdan nə fərqləndirir?</p>",
     "options": {
      "a": "i-ci elementə indekslə O(1) müddətdə müraciət olunur",
      "b": "Hər düyündə həm <code>next</code>, həm də <code>prev</code> istinadı olur",
      "c": "Son düyün <code>None</code> əvəzinə baş (head) düyünə işarə edir",
      "d": "Düyünlər yaddaşda ardıcıl yerləşir"
     }
    },
    {
     "id": "T3",
     "title": "Tapşırıq T3. Bağlı siyahıda axtarış (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T3. Bağlı siyahıda axtarış (10 bal)</h4>\n<p><i>Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Bağlı siyahıda verilmiş qiyməti axtaran <code>siyahida_var(head, x)</code> funksiyasını yazın: qiymət varsa <code>True</code>, yoxdursa <code>False</code><br>qaytarsın. Boş siyahı (<code>head = None</code>) üçün <code>False</code>.</p>",
     "starter": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef siyahida_var(head, x):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nprint(siyahida_var(head, 20))   # True olmalıdır\nprint(siyahida_var(head, 99))   # False olmalıdır"
    },
    {
     "id": "T4",
     "title": "Tapşırıq T4. 3 × 3 sıfır matrisi (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T4. 3 × 3 sıfır matrisi (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Bütün elementləri <code>0</code> olan <code>3 × 3</code> ölçülü matris (siyahılar siyahısı) yaradın, onun <b>ortadakı</b> elementinə <code>5</code> yazın və<br>matrisi <b>qaytaran</b> <code>matris_yarat()</code> funksiyasını yazın. Sətirlər bir-birindən asılı olmamalıdır<br>(<code>[[0] * 3] * 3</code> səhvdir!).</p>",
     "starter": "def matris_yarat():\n    # buranı yazın\n    pass\n\n\nfor setir in matris_yarat() or []:\n    print(setir)\n# [0, 0, 0]\n# [0, 5, 0]\n# [0, 0, 0]"
    },
    {
     "id": "T5",
     "title": "Tapşırıq T5. Ən böyük element (max() olmadan) (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T5. Ən böyük element (max() olmadan) (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Boş olmayan siyahının ən böyük elementini <b>qaytaran</b> <code>en_boyuk(lst)</code> funksiyasını yazın.<br><b><code>max()</code> və <code>sorted()</code> funksiyalarından istifadə etməyin.</b><br>Nümunə: <code>en_boyuk([5, 3, 8, 1])</code> → <code>8</code>.</p>",
     "starter": "def en_boyuk(lst):\n    # max() funksiyasından istifadə etmədən yazın\n    pass\n\n\nprint(en_boyuk([5, 3, 8, 1]))   # 8 olmalıdır"
    },
    {
     "id": "T6",
     "title": "Tapşırıq T6. O, Ω və Θ notasiyaları (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T6. O, Ω və Θ notasiyaları (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>T(n) = 3n² + 5n + 2 funksiyası üçün ən dəqiq qiymətləndirmə (həm yuxarı, həm aşağı sərhəd) hansıdır?</p>",
     "options": {
      "a": "Θ(1)",
      "b": "Ω(n³)",
      "c": "Θ(n)",
      "d": "Θ(n²)"
     }
    },
    {
     "id": "T7",
     "title": "Tapşırıq T7. Siyahının ədədi ortası (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T7. Siyahının ədədi ortası (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahının elementlərinin ədədi ortasını <b>qaytaran</b> <code>orta(lst)</code> funksiyasını yazın. Boş siyahı üçün <code>0</code> qaytarsın.<br>Nümunə: <code>orta([2, 4, 6, 8])</code> → <code>5.0</code>.</p>",
     "starter": "def orta(lst):\n    # buranı yazın\n    pass\n\n\nprint(orta([2, 4, 6, 8]))   # 5.0 olmalıdır"
    },
    {
     "id": "T8",
     "title": "Tapşırıq T8. Binar axtarış ağacının (BST) xassəsi (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T8. Binar axtarış ağacının (BST) xassəsi (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Binar axtarış ağacının (BST) əsas xassəsi hansıdır?</p>",
     "options": {
      "a": "Hər düyünün tam olaraq iki uşağı var",
      "b": "Kök həmişə ağacdakı ən kiçik qiymətdir",
      "c": "Bütün yarpaqlar eyni dərinlikdə yerləşir",
      "d": "Hər düyün üçün sol alt ağacdakı bütün qiymətlər düyünün qiymətindən kiçik, sağ alt ağacdakılar isə böyükdür"
     }
    },
    {
     "id": "T9",
     "title": "Tapşırıq T9. Ən uzun söz (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T9. Ən uzun söz (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Sözlər siyahısında ən uzun sözü <b>qaytaran</b> <code>en_uzun(sozler)</code> funksiyasını yazın.<br>Nümunə: <code>en_uzun([\"ev\", \"kitab\", \"qələm\", \"kompüter\"])</code> → <code>\"kompüter\"</code>.</p>",
     "starter": "def en_uzun(sozler):\n    # buranı yazın\n    pass\n\n\nprint(en_uzun([\"ev\", \"kitab\", \"qələm\", \"kompüter\"]))   # kompüter olmalıdır"
    },
    {
     "id": "T10",
     "title": "Tapşırıq T10. Python-da ikiölçülü massiv (matris) (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T10. Python-da ikiölçülü massiv (matris) (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>3 sətir və 4 sütundan ibarət, bütün elementləri 0 olan matrisi <b>düzgün</b> yaradan ifadə hansıdır (sətirlər bir-birindən asılı olmamalıdır)?</p>",
     "options": {
      "a": "<code>matris = [[0] * 4 for _ in range(3)]</code>",
      "b": "<code>matris = [[0] * 4] * 3</code>",
      "c": "<code>matris = [[0] * 3] * 4</code>",
      "d": "<code>matris = [0] * 12</code>"
     }
    }
   ],
   "steps": [
    {
     "k": "code",
     "task": "T1",
     "code": "def ters(soz):\n    stek = []\n    # buranı yazın\n    pass\n\n\nprint(ters(\"Python\"))   # nohtyP olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T1"
     ],
     "code": "def test_t1():\n    return grade(\n        (4, \"ters('Python') 'nohtyP' olmalıdır\", lambda: ters(\"Python\") == \"nohtyP\"),\n        (3, \"boş sətir və tək hərf\", lambda: ters(\"\") == \"\" and ters(\"a\") == \"a\"),\n        (3, \"stekdən istifadə olunmalıdır (append() və pop())\", lambda: \"pop\" in _calls(\"T1\") and ters(\"abc\") == \"cba\"),\n    )\ncheck(\"T1\", 10, test_t1)"
    },
    {
     "k": "var",
     "task": "T2",
     "var": "cavab_T2"
    },
    {
     "k": "test",
     "ids": [
      "T2"
     ],
     "code": "def test_t2():\n    assert _h(cavab_T2) == \"2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6\", \"cavab düzgün deyil\"\ncheck(\"T2\", 10, test_t2)"
    },
    {
     "k": "code",
     "task": "T3",
     "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef siyahida_var(head, x):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nprint(siyahida_var(head, 20))   # True olmalıdır\nprint(siyahida_var(head, 99))   # False olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T3"
     ],
     "code": "def test_t3():\n    return grade(\n        (4, \"10 -> 20 -> 30 siyahısında 20 tapılmalıdır (True)\", lambda: siyahida_var(_ll([10, 20, 30]), 20) == True),\n        (3, \"99 yoxdur (False); sonuncu element 30 tapılmalıdır\", lambda: siyahida_var(_ll([10, 20, 30]), 99) is not None and siyahida_var(_ll([10, 20, 30]), 99) == False and siyahida_var(_ll([10, 20, 30]), 30) == True),\n        (3, \"boş siyahı üçün False; tək düyünlü siyahı\", lambda: siyahida_var(None, 5) is not None and siyahida_var(None, 5) == False and siyahida_var(_ll([7]), 7) == True),\n    )\ncheck(\"T3\", 10, test_t3)"
    },
    {
     "k": "code",
     "task": "T4",
     "code": "def matris_yarat():\n    # buranı yazın\n    pass\n\n\nfor setir in matris_yarat() or []:\n    print(setir)\n# [0, 0, 0]\n# [0, 5, 0]\n# [0, 0, 0]"
    },
    {
     "k": "test",
     "ids": [
      "T4"
     ],
     "code": "def test_t4():\n    return grade(\n        (3, \"3 sətir və hər sətirdə 3 element olmalıdır\", lambda: len(matris_yarat()) == 3 and all(len(s) == 3 for s in matris_yarat())),\n        (4, \"ortadakı element 5, qalanları 0 olmalıdır\", lambda: _eq(matris_yarat(), [[0, 0, 0], [0, 5, 0], [0, 0, 0]])),\n        (3, \"sətirlər ayrı-ayrı siyahılar olmalıdır ([[0] * 3] * 3 səhvdir)\", lambda: len({id(s) for s in matris_yarat()}) == 3),\n    )\ncheck(\"T4\", 10, test_t4)"
    },
    {
     "k": "code",
     "task": "T5",
     "code": "def en_boyuk(lst):\n    # max() funksiyasından istifadə etmədən yazın\n    pass\n\n\nprint(en_boyuk([5, 3, 8, 1]))   # 8 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T5"
     ],
     "code": "def test_t5():\n    return grade(\n        (4, \"en_boyuk([5, 3, 8, 1]) 8 olmalıdır\", lambda: _eq(en_boyuk([5, 3, 8, 1]), 8)),\n        (3, \"mənfi ədədlər və tək elementli siyahı\", lambda: _eq(en_boyuk([-7, -2, -9]), -2) and _eq(en_boyuk([4]), 4)),\n        (3, \"max()/sorted() istifadə olunmamalıdır\", lambda: not (_calls(\"T5\") & {\"max\", \"sorted\", \"sort\"}) and _eq(en_boyuk([1, 9, 9, 2]), 9)),\n    )\ncheck(\"T5\", 10, test_t5)"
    },
    {
     "k": "var",
     "task": "T6",
     "var": "cavab_T6"
    },
    {
     "k": "test",
     "ids": [
      "T6"
     ],
     "code": "def test_t6():\n    assert _h(cavab_T6) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T6\", 10, test_t6)"
    },
    {
     "k": "code",
     "task": "T7",
     "code": "def orta(lst):\n    # buranı yazın\n    pass\n\n\nprint(orta([2, 4, 6, 8]))   # 5.0 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T7"
     ],
     "code": "def test_t7():\n    return grade(\n        (4, \"orta([2, 4, 6, 8]) 5.0 olmalıdır\", lambda: _is_num(orta([2, 4, 6, 8])) and _eq(orta([2, 4, 6, 8]), 5.0)),\n        (3, \"boş siyahı üçün 0 qaytarılmalıdır (xəta yox)\", lambda: _is_num(orta([])) and orta([]) == 0),\n        (3, \"kəsr nəticə: orta([1, 2]) 1.5 olmalıdır\", lambda: _is_num(orta([1, 2])) and _eq(orta([1, 2]), 1.5) and _eq(orta([-3, 3]), 0)),\n    )\ncheck(\"T7\", 10, test_t7)"
    },
    {
     "k": "var",
     "task": "T8",
     "var": "cavab_T8"
    },
    {
     "k": "test",
     "ids": [
      "T8"
     ],
     "code": "def test_t8():\n    assert _h(cavab_T8) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T8\", 10, test_t8)"
    },
    {
     "k": "code",
     "task": "T9",
     "code": "def en_uzun(sozler):\n    # buranı yazın\n    pass\n\n\nprint(en_uzun([\"ev\", \"kitab\", \"qələm\", \"kompüter\"]))   # kompüter olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T9"
     ],
     "code": "def test_t9():\n    return grade(\n        (4, \"['ev', 'kitab', 'qələm', 'kompüter'] → 'kompüter'\", lambda: en_uzun([\"ev\", \"kitab\", \"qələm\", \"kompüter\"]) == \"kompüter\"),\n        (3, \"tək söz və birinci yerdə olan ən uzun söz\", lambda: en_uzun([\"a\"]) == \"a\" and en_uzun([\"abc\", \"de\"]) == \"abc\"),\n        (3, \"ortada olan ən uzun söz; bərabər uzunluqda istənilən biri\", lambda: en_uzun([\"x\", \"yyy\", \"zz\"]) == \"yyy\" and en_uzun([\"ab\", \"cd\", \"e\"]) in (\"ab\", \"cd\")),\n    )\ncheck(\"T9\", 10, test_t9)"
    },
    {
     "k": "var",
     "task": "T10",
     "var": "cavab_T10"
    },
    {
     "k": "test",
     "ids": [
      "T10"
     ],
     "code": "def test_t10():\n    assert _h(cavab_T10) == \"ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb\", \"cavab düzgün deyil\"\ncheck(\"T10\", 10, test_t10)"
    }
   ]
  },
  "B": {
   "name": "Variant B",
   "max_score": 100,
   "items": [
    {
     "type": "task",
     "id": "T1"
    },
    {
     "type": "task",
     "id": "T2"
    },
    {
     "type": "task",
     "id": "T3"
    },
    {
     "type": "task",
     "id": "T4"
    },
    {
     "type": "task",
     "id": "T5"
    },
    {
     "type": "task",
     "id": "T6"
    },
    {
     "type": "task",
     "id": "T7"
    },
    {
     "type": "task",
     "id": "T8"
    },
    {
     "type": "task",
     "id": "T9"
    },
    {
     "type": "task",
     "id": "T10"
    }
   ],
   "tasks": [
    {
     "id": "T1",
     "title": "Tapşırıq T1. Node sinfi və 10 → 20 → 30 bağlı siyahısı (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T1. Node sinfi və 10 → 20 → 30 bağlı siyahısı (10 bal)</h4>\n<p><i>Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<ol><li><code>Node</code> sinfini tamamlayın: konstruktor <code>data</code> və <code>next</code> sahələrini yaratsın (<code>next</code> əvvəlcə <code>None</code>).</li><li><code>Node</code> sinfindən istifadə edərək 10 → 20 → 30 bağlı siyahısını qurun; siyahının başı <code>head</code> dəyişənində olsun.</li></ol>",
     "starter": "class Node:\n    def __init__(self, data):\n        # data və next sahələrini yaradın\n        pass\n\n\n# 10 -> 20 -> 30 bağlı siyahısını qurun (baş düyün: head):\nhead = None\n\ncur = head\nwhile cur:\n    print(cur.data, end=\" -> \")\n    cur = cur.next\nprint(\"None\")   # 10 -> 20 -> 30 -> None olmalıdır"
    },
    {
     "id": "T2",
     "title": "Tapşırıq T2. İç-içə siyahını düzləşdirmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T2. İç-içə siyahını düzləşdirmək (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>İç-içə siyahını (siyahılar siyahısını) düz siyahıya çevirib <b>qaytaran</b> <code>duzlesdir(lst)</code> funksiyasını yazın.<br>Nümunə: <code>[[1, 2], [3], [4, 5, 6]]</code> → <code>[1, 2, 3, 4, 5, 6]</code>.</p>",
     "starter": "def duzlesdir(lst):\n    # buranı yazın\n    pass\n\n\nprint(duzlesdir([[1, 2], [3], [4, 5, 6]]))   # [1, 2, 3, 4, 5, 6] olmalıdır"
    },
    {
     "id": "T3",
     "title": "Tapşırıq T3. list ilə stek: append() və pop() (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T3. list ilə stek: append() və pop() (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p><code>list</code> ilə stek yaradın: <code>stek</code> siyahısına 1, 2, 3 ədədlərini <code>append()</code> ilə əlavə edin, sonra <code>pop()</code> ilə bir element<br>çıxarıb onu <code>cixan</code> dəyişəninə yazın. Stekdə nə qalır?</p>",
     "starter": "stek = []\n# 1, 2, 3 ədədlərini append() ilə əlavə edin:\n\n# pop() ilə bir element çıxarıb cixan dəyişəninə yazın:\ncixan = None\n\nprint(stek, cixan)   # [1, 2] 3 olmalıdır"
    },
    {
     "id": "T4",
     "title": "Tapşırıq T4. Həş cədvəli və Python dict (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T4. Həş cədvəli və Python dict (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Python <code>dict</code> (həş cədvəli) haqqında hansı fikir doğrudur?</p>",
     "options": {
      "a": "<code>dict</code> elementlərin əlavə olunma sırasını heç vaxt saxlamır",
      "b": "Açar kimi <code>list</code> istifadə etmək olar",
      "c": "Axtarış həmişə O(n)-dir, çünki bütün açarlar ardıcıl yoxlanılır",
      "d": "Açarın həş qiyməti cədvəldəki yeri müəyyən edir, ona görə axtarış və əlavə orta halda O(1)-dir; açar dəyişməz (həşlənən) olmalıdır"
     }
    },
    {
     "id": "T5",
     "title": "Tapşırıq T5. Point sinfi (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T5. Point sinfi (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p><code>Point</code> sinfini yazın: konstruktor <code>x</code> və <code>y</code> atributlarını yaratsın, <code>show()</code> metodu isə onları çap etsin<br>(məsələn: <code>x = 3, y = 4</code>; çap formatı yoxlanmır, yalnız qiymətlər).</p>",
     "starter": "class Point:\n    # buranı yazın\n    pass\n\n\np = Point(3, 4)\np.show()   # x = 3, y = 4"
    },
    {
     "id": "T6",
     "title": "Tapşırıq T6. İç-içə dövrün zaman mürəkkəbliyi (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T6. İç-içə dövrün zaman mürəkkəbliyi (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Aşağıdakı kodun zaman mürəkkəbliyi nədir?</p>\n<pre class=\"md-code\"><code>for i in range(n):\n    for j in range(n):\n        print(i, j)</code></pre>",
     "options": {
      "a": "O(log n)",
      "b": "O(n)",
      "c": "O(n²)",
      "d": "O(2n)"
     }
    },
    {
     "id": "T7",
     "title": "Tapşırıq T7. Siyahını tərsinə çevirmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T7. Siyahını tərsinə çevirmək (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahını tərsinə çevirib <b>qaytaran</b> <code>tersine(lst)</code> funksiyasını yazın (istənilən üsulla: kəsik <code>[::-1]</code>, <code>reverse()</code> və ya dövr).<br>Nümunə: <code>tersine([1, 2, 3, 4, 5])</code> → <code>[5, 4, 3, 2, 1]</code>.</p>",
     "starter": "def tersine(lst):\n    # buranı yazın\n    pass\n\n\nprint(tersine([1, 2, 3, 4, 5]))   # [5, 4, 3, 2, 1] olmalıdır"
    },
    {
     "id": "T8",
     "title": "Tapşırıq T8. Statik və dinamik strukturlar (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T8. Statik və dinamik strukturlar (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Statik və dinamik strukturlar haqqında hansı fikir doğrudur?</p>",
     "options": {
      "a": "Python list statik strukturdur, çünki elementlərinə indekslə müraciət olunur",
      "b": "Statik strukturun ölçüsü icra zamanı dəyişmir və yaddaş əvvəlcədən sabit həcmdə ayrılır; dinamik strukturda (Python list, bağlı siyahı) elementlərin sayı icra zamanı dəyişir",
      "c": "Dinamik strukturlarda ayrılmış yaddaş heç vaxt azad edilmir",
      "d": "Statik strukturlar yalnız Python-da, dinamik strukturlar isə yalnız C dilində olur"
     }
    },
    {
     "id": "T9",
     "title": "Tapşırıq T9. Queue sinfi: enqueue və dequeue (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T9. Queue sinfi: enqueue və dequeue (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p><code>deque</code> əsasında sadə <code>Queue</code> sinfini tamamlayın: <code>enqueue(x)</code> elementi növbənin sonuna əlavə etsin, <code>dequeue()</code> isə öndəki<br>elementi çıxarıb qaytarsın (FIFO). Növbə boşdursa, <code>dequeue()</code> xəta vermədən <code>None</code> qaytarsın.</p>",
     "starter": "from collections import deque\n\n\nclass Queue:\n    def __init__(self):\n        self.items = deque()\n\n    def enqueue(self, x):\n        # buranı yazın\n        pass\n\n    def dequeue(self):\n        # buranı yazın (növbə boşdursa None qaytarsın)\n        pass\n\n\nq = Queue()\nq.enqueue(10)\nq.enqueue(20)\nprint(q.dequeue())   # 10 olmalıdır"
    },
    {
     "id": "T10",
     "title": "Tapşırıq T10. Növbə və collections.deque (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T10. Növbə və collections.deque (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Python-da növbə (FIFO) üçün <code>list</code> əvəzinə niyə <code>collections.deque</code> istifadə olunur?</p>",
     "options": {
      "a": "<code>deque</code> elementləri avtomatik sıralayır",
      "b": "<code>deque</code> LIFO prinsipi ilə işləyir",
      "c": "<code>list</code>-in sonuna element əlavə etmək mümkün deyil",
      "d": "<code>list.pop(0)</code> O(n)-dir, çünki qalan elementlər sola sürüşdürülür; <code>deque.popleft()</code> isə O(1)-dir"
     }
    }
   ],
   "steps": [
    {
     "k": "code",
     "task": "T1",
     "code": "class Node:\n    def __init__(self, data):\n        # data və next sahələrini yaradın\n        pass\n\n\n# 10 -> 20 -> 30 bağlı siyahısını qurun (baş düyün: head):\nhead = None\n\ncur = head\nwhile cur:\n    print(cur.data, end=\" -> \")\n    cur = cur.next\nprint(\"None\")   # 10 -> 20 -> 30 -> None olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T1"
     ],
     "code": "def test_t1():\n    return grade(\n        (3, \"Node(5).data 5, Node(5).next None olmalıdır\", lambda: getattr(Node(5), \"data\", \"yox\") == 5 and getattr(Node(5), \"next\", \"yox\") is None),\n        (4, \"head-dən başlayaraq 10, 20, 30 olmalıdır\", lambda: _ll_list(head, 10)[:3] == [10, 20, 30]),\n        (3, \"sonuncu düyünün next-i None; bütün düyünlər Node olmalıdır\",\n         lambda: head.next.next.next is None and all(isinstance(x, Node) for x in (head, head.next, head.next.next))),\n    )\ncheck(\"T1\", 10, test_t1)"
    },
    {
     "k": "code",
     "task": "T2",
     "code": "def duzlesdir(lst):\n    # buranı yazın\n    pass\n\n\nprint(duzlesdir([[1, 2], [3], [4, 5, 6]]))   # [1, 2, 3, 4, 5, 6] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T2"
     ],
     "code": "def test_t2():\n    return grade(\n        (4, \"[[1, 2], [3], [4, 5, 6]] → [1, 2, 3, 4, 5, 6]\", lambda: _eq(_as_list(duzlesdir([[1, 2], [3], [4, 5, 6]])), [1, 2, 3, 4, 5, 6])),\n        (3, \"boş siyahı → []; [[], [1]] → [1]\", lambda: _as_list(duzlesdir([])) == [] and _eq(_as_list(duzlesdir([[], [1]])), [1])),\n        (3, \"sətirlər: [['a'], ['b', 'c']] → ['a', 'b', 'c']\", lambda: _eq(_as_list(duzlesdir([[\"a\"], [\"b\", \"c\"]])), [\"a\", \"b\", \"c\"])),\n    )\ncheck(\"T2\", 10, test_t2)"
    },
    {
     "k": "code",
     "task": "T3",
     "code": "stek = []\n# 1, 2, 3 ədədlərini append() ilə əlavə edin:\n\n# pop() ilə bir element çıxarıb cixan dəyişəninə yazın:\ncixan = None\n\nprint(stek, cixan)   # [1, 2] 3 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T3"
     ],
     "code": "def test_t3():\n    return grade(\n        (4, \"LIFO: son əlavə olunan 3 çıxmalıdır (cixan = 3)\", lambda: cixan == 3),\n        (3, \"stekdə [1, 2] qalmalıdır\", lambda: _as_list(stek) == [1, 2]),\n        (3, \"append() və pop() istifadə olunmalıdır\", lambda: {\"append\", \"pop\"} <= _calls(\"T3\")),\n    )\ncheck(\"T3\", 10, test_t3)"
    },
    {
     "k": "var",
     "task": "T4",
     "var": "cavab_T4"
    },
    {
     "k": "test",
     "ids": [
      "T4"
     ],
     "code": "def test_t4():\n    assert _h(cavab_T4) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T4\", 10, test_t4)"
    },
    {
     "k": "code",
     "task": "T5",
     "code": "class Point:\n    # buranı yazın\n    pass\n\n\np = Point(3, 4)\np.show()   # x = 3, y = 4"
    },
    {
     "k": "test",
     "ids": [
      "T5"
     ],
     "code": "def test_t5():\n    return grade(\n        (3, \"Point(3, 4) obyekti yaradılmalıdır\", lambda: Point(3, 4) is not None),\n        (4, \"x və y atributları düzgün saxlanmalıdır\", lambda: Point(3, 4).x == 3 and Point(3, 4).y == 4 and Point(-1, 7).y == 7),\n        (3, \"show() x və y qiymətlərini çap etməlidir\", lambda: _ints(_capture(Point(3, 4).show)) == [3, 4] and _ints(_capture(Point(10, 20).show)) == [10, 20]),\n    )\ncheck(\"T5\", 10, test_t5)"
    },
    {
     "k": "var",
     "task": "T6",
     "var": "cavab_T6"
    },
    {
     "k": "test",
     "ids": [
      "T6"
     ],
     "code": "def test_t6():\n    assert _h(cavab_T6) == \"2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6\", \"cavab düzgün deyil\"\ncheck(\"T6\", 10, test_t6)"
    },
    {
     "k": "code",
     "task": "T7",
     "code": "def tersine(lst):\n    # buranı yazın\n    pass\n\n\nprint(tersine([1, 2, 3, 4, 5]))   # [5, 4, 3, 2, 1] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T7"
     ],
     "code": "def test_t7():\n    return grade(\n        (4, \"[1, 2, 3, 4, 5] → [5, 4, 3, 2, 1]\", lambda: _eq(_as_list(_ret(tersine, [1, 2, 3, 4, 5])), [5, 4, 3, 2, 1])),\n        (3, \"cüt sayda element: [7, 8] → [8, 7]\", lambda: _eq(_as_list(_ret(tersine, [7, 8])), [8, 7])),\n        (3, \"sətirlərdən ibarət siyahı: ['a', 'b', 'c'] → ['c', 'b', 'a']\", lambda: _eq(_as_list(_ret(tersine, [\"a\", \"b\", \"c\"])), [\"c\", \"b\", \"a\"])),\n    )\ncheck(\"T7\", 10, test_t7)"
    },
    {
     "k": "var",
     "task": "T8",
     "var": "cavab_T8"
    },
    {
     "k": "test",
     "ids": [
      "T8"
     ],
     "code": "def test_t8():\n    assert _h(cavab_T8) == \"3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d\", \"cavab düzgün deyil\"\ncheck(\"T8\", 10, test_t8)"
    },
    {
     "k": "code",
     "task": "T9",
     "code": "from collections import deque\n\n\nclass Queue:\n    def __init__(self):\n        self.items = deque()\n\n    def enqueue(self, x):\n        # buranı yazın\n        pass\n\n    def dequeue(self):\n        # buranı yazın (növbə boşdursa None qaytarsın)\n        pass\n\n\nq = Queue()\nq.enqueue(10)\nq.enqueue(20)\nprint(q.dequeue())   # 10 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T9"
     ],
     "code": "def test_t9():\n    def fifo():\n        q = Queue()\n        q.enqueue(10); q.enqueue(20)\n        return q.dequeue() == 10\n    def ardicil():\n        q = Queue()\n        q.enqueue(1); q.enqueue(2)\n        r1 = q.dequeue(); q.enqueue(3)\n        return (r1, q.dequeue(), q.dequeue()) == (1, 2, 3)\n    def bos():\n        q = Queue()\n        q.enqueue(\"x\")\n        return q.dequeue() == \"x\" and q.dequeue() is None\n    return grade(\n        (4, \"enqueue(10), enqueue(20)-dən sonra dequeue() 10 qaytarmalıdır (FIFO)\", fifo),\n        (3, \"çıxarılma ardıcıllığı 1, 2, 3 olmalıdır\", ardicil),\n        (3, \"boş növbədə dequeue() xəta verməməli, None qaytarmalıdır\", bos),\n    )\ncheck(\"T9\", 10, test_t9)"
    },
    {
     "k": "var",
     "task": "T10",
     "var": "cavab_T10"
    },
    {
     "k": "test",
     "ids": [
      "T10"
     ],
     "code": "def test_t10():\n    assert _h(cavab_T10) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T10\", 10, test_t10)"
    }
   ]
  },
  "C": {
   "name": "Variant C",
   "max_score": 100,
   "items": [
    {
     "type": "task",
     "id": "T1"
    },
    {
     "type": "task",
     "id": "T2"
    },
    {
     "type": "task",
     "id": "T3"
    },
    {
     "type": "task",
     "id": "T4"
    },
    {
     "type": "task",
     "id": "T5"
    },
    {
     "type": "task",
     "id": "T6"
    },
    {
     "type": "task",
     "id": "T7"
    },
    {
     "type": "task",
     "id": "T8"
    },
    {
     "type": "task",
     "id": "T9"
    },
    {
     "type": "task",
     "id": "T10"
    }
   ],
   "tasks": [
    {
     "id": "T1",
     "title": "Tapşırıq T1. Siyahının cəmi (sum() olmadan) (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T1. Siyahının cəmi (sum() olmadan) (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahının elementlərinin cəmini <b>qaytaran</b> <code>cem(lst)</code> funksiyasını yazın.<br><b><code>sum()</code> funksiyasından istifadə etməyin</b> — cəmi dövrlə hesablayın.<br>Nümunə: <code>cem([1, 2, 3, 4])</code> → <code>10</code>; boş siyahı üçün <code>0</code>.</p>",
     "starter": "def cem(lst):\n    # sum() funksiyasından istifadə etmədən yazın\n    pass\n\n\nprint(cem([1, 2, 3, 4]))   # 10 olmalıdır"
    },
    {
     "id": "T2",
     "title": "Tapşırıq T2. Bağlı siyahının elementlərinin cəmi (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T2. Bağlı siyahının elementlərinin cəmi (10 bal)</h4>\n<p><i>Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Bağlı siyahının bütün elementlərinin cəmini <b>qaytaran</b> <code>ll_cem(head)</code> funksiyasını yazın.<br>Boş siyahı (<code>head = None</code>) üçün <code>0</code>.</p>",
     "starter": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef ll_cem(head):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nprint(ll_cem(head))   # 60 olmalıdır"
    },
    {
     "id": "T3",
     "title": "Tapşırıq T3. Stekin boş olub-olmadığını yoxlamaq (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T3. Stekin boş olub-olmadığını yoxlamaq (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Stekin (siyahının) boş olub-olmadığını yoxlayan <code>is_empty(stek)</code> funksiyasını yazın: boşdursa <code>True</code>, əks halda <code>False</code> qaytarsın.<br>Nümunə: <code>is_empty([])</code> → <code>True</code>, <code>is_empty([1, 2])</code> → <code>False</code>.</p>",
     "starter": "def is_empty(stek):\n    # buranı yazın\n    pass\n\n\nprint(is_empty([]))       # True olmalıdır\nprint(is_empty([1, 2]))   # False olmalıdır"
    },
    {
     "id": "T4",
     "title": "Tapşırıq T4. Yaddaşın stek və heap sahələri (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T4. Yaddaşın stek və heap sahələri (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Yaddaşın stek (call stack) və heap sahələri haqqında hansı fikir doğrudur?</p>",
     "options": {
      "a": "Dərin rekursiya heap sahəsini doldurur, stek isə dəyişmir",
      "b": "Heap stekdən həmişə sürətlidir və LIFO qaydası ilə işləyir",
      "c": "Python-da bütün obyektlər (list, dict) stek sahəsində saxlanılır, heap istifadə olunmur",
      "d": "Stekdə funksiya çağırışlarının lokal dəyişənləri, parametrləri və qayıdış ünvanı saxlanılır və funksiya bitəndə avtomatik təmizlənir; heap isə dinamik yaradılan obyektlər üçündür"
     }
    },
    {
     "id": "T5",
     "title": "Tapşırıq T5. İki siyahını birləşdirib sıralamaq (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T5. İki siyahını birləşdirib sıralamaq (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>İki siyahını birləşdirib <b>artan sıra ilə</b> düzülmüş yeni siyahı <b>qaytaran</b> <code>birlesdir_sirala(a, b)</code> funksiyasını yazın<br>(<code>sorted()</code> və ya <code>sort()</code> istifadə edə bilərsiniz).<br>Nümunə: <code>birlesdir_sirala([3, 1, 4], [2, 5])</code> → <code>[1, 2, 3, 4, 5]</code>.</p>",
     "starter": "def birlesdir_sirala(a, b):\n    # buranı yazın\n    pass\n\n\nprint(birlesdir_sirala([3, 1, 4], [2, 5]))   # [1, 2, 3, 4, 5] olmalıdır"
    },
    {
     "id": "T6",
     "title": "Tapşırıq T6. Nəzəri mürəkkəblik və real icra vaxtı (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T6. Nəzəri mürəkkəblik və real icra vaxtı (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Bir alqoritm O(n log n), digəri O(n²) mürəkkəbliyə malikdir. Kiçik n üçün O(n²) alqoritmi daha sürətli işləyə bilərmi?</p>",
     "options": {
      "a": "Xeyr, O(n log n) alqoritm istənilən n üçün həmişə daha sürətlidir",
      "b": "Xeyr, real icra vaxtı aparatdan və keşdən asılı deyil",
      "c": "Bəli: nəzəri qiymət sabit vuruqları atır; məsələn, n = 100 üçün 100·n·log n ≈ 66 400, n² isə 10 000-dir",
      "d": "Bəli, çünki böyük O notasiyası yalnız kiçik n üçün keçərlidir"
     }
    },
    {
     "id": "T7",
     "title": "Tapşırıq T7. collections.deque ilə növbə (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T7. collections.deque ilə növbə (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p><code>collections.deque</code> ilə boş növbə (<code>q</code>) yaradın, ona <code>\"A\"</code>, <code>\"B\"</code>, <code>\"C\"</code> elementlərini əlavə edin və <code>popleft()</code> ilə bir element<br>çıxarıb onu <code>cixan</code> dəyişəninə yazın. Hansı element çıxır?</p>",
     "starter": "from collections import deque\n\nq = deque()\n# \"A\", \"B\", \"C\" elementlərini əlavə edin:\n\n# popleft() ilə bir element çıxarıb cixan dəyişəninə yazın:\ncixan = None\n\nprint(cixan, q)"
    },
    {
     "id": "T8",
     "title": "Tapşırıq T8. Ən yaxşı, ən pis və orta hal (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T8. Ən yaxşı, ən pis və orta hal (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>n elementli siyahıda xətti axtarış üçün ən yaxşı və ən pis hal hansıdır?</p>",
     "options": {
      "a": "Ən yaxşı hal O(log n), ən pis hal O(n)",
      "b": "Ən yaxşı hal O(1) — element birinci yerdədir; ən pis hal O(n) — element sonuncudur və ya yoxdur",
      "c": "Hər iki hal O(1)-dir, çünki siyahıya indekslə müraciət olunur",
      "d": "Ən yaxşı hal O(n), ən pis hal O(n²)"
     }
    },
    {
     "id": "T9",
     "title": "Tapşırıq T9. Siyahını 1 mövqe sola sürüşdürmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T9. Siyahını 1 mövqe sola sürüşdürmək (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahının elementlərini 1 mövqe sola sürüşdürən (birinci element sona keçir) və nəticəni <b>qaytaran</b> <code>sola_surusdur(lst)</code><br>funksiyasını yazın. Boş siyahı boş qalmalıdır.<br>Nümunə: <code>[1, 2, 3, 4]</code> → <code>[2, 3, 4, 1]</code>.</p>",
     "starter": "def sola_surusdur(lst):\n    # buranı yazın\n    pass\n\n\nprint(sola_surusdur([1, 2, 3, 4]))   # [2, 3, 4, 1] olmalıdır"
    },
    {
     "id": "T10",
     "title": "Tapşırıq T10. Qraf və onun Python-da təsviri (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T10. Qraf və onun Python-da təsviri (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Qraf haqqında hansı fikir doğrudur?</p>",
     "options": {
      "a": "Qrafda dövr (cycle) ola bilməz",
      "b": "Qraf G = (V, E) təpələr və kənarlar çoxluğudur; Python-da adətən qonşuluq siyahısı (lüğət) və ya qonşuluq matrisi ilə təsvir olunur",
      "c": "Qraf xətti strukturdur, çünki təpələr ardıcıl düzülür",
      "d": "Qrafın hər təpəsinin yalnız bir valideyni olur"
     }
    }
   ],
   "steps": [
    {
     "k": "code",
     "task": "T1",
     "code": "def cem(lst):\n    # sum() funksiyasından istifadə etmədən yazın\n    pass\n\n\nprint(cem([1, 2, 3, 4]))   # 10 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T1"
     ],
     "code": "def test_t1():\n    return grade(\n        (4, \"cem([1, 2, 3, 4]) 10 olmalıdır\", lambda: _eq(cem([1, 2, 3, 4]), 10)),\n        (3, \"boş siyahı üçün 0, mənfi ədədlərlə də düzgün cəm\", lambda: cem([]) == 0 and cem([]) is not None and _eq(cem([-5, 5, 7]), 7)),\n        (3, \"sum() istifadə olunmamalıdır (cəm dövrlə hesablanmalıdır)\", lambda: \"sum\" not in _calls(\"T1\") and _eq(cem([2.5, 2.5, 10]), 15)),\n    )\ncheck(\"T1\", 10, test_t1)"
    },
    {
     "k": "code",
     "task": "T2",
     "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef ll_cem(head):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nprint(ll_cem(head))   # 60 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T2"
     ],
     "code": "def test_t2():\n    return grade(\n        (4, \"10 -> 20 -> 30 üçün cəm 60 olmalıdır\", lambda: _eq(ll_cem(_ll([10, 20, 30])), 60)),\n        (3, \"boş siyahı üçün 0; tək düyünlü [7] üçün 7\", lambda: ll_cem(None) == 0 and ll_cem(None) is not None and _eq(ll_cem(_ll([7])), 7)),\n        (3, \"mənfi qiymətlər: -5 -> 5 -> 1 üçün 1\", lambda: _eq(ll_cem(_ll([-5, 5, 1])), 1)),\n    )\ncheck(\"T2\", 10, test_t2)"
    },
    {
     "k": "code",
     "task": "T3",
     "code": "def is_empty(stek):\n    # buranı yazın\n    pass\n\n\nprint(is_empty([]))       # True olmalıdır\nprint(is_empty([1, 2]))   # False olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T3"
     ],
     "code": "def test_t3():\n    def cycle():\n        s = [5]\n        a = is_empty(s)\n        s.pop()\n        return a is not None and a == False and is_empty(s) == True\n    return grade(\n        (4, \"is_empty([]) True olmalıdır\", lambda: is_empty([]) == True),\n        (3, \"is_empty([1, 2]) False olmalıdır\", lambda: is_empty([1, 2]) is not None and is_empty([1, 2]) == False),\n        (3, \"push/pop-dan sonra: [5] → False, pop-dan sonra → True\", cycle),\n    )\ncheck(\"T3\", 10, test_t3)"
    },
    {
     "k": "var",
     "task": "T4",
     "var": "cavab_T4"
    },
    {
     "k": "test",
     "ids": [
      "T4"
     ],
     "code": "def test_t4():\n    assert _h(cavab_T4) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T4\", 10, test_t4)"
    },
    {
     "k": "code",
     "task": "T5",
     "code": "def birlesdir_sirala(a, b):\n    # buranı yazın\n    pass\n\n\nprint(birlesdir_sirala([3, 1, 4], [2, 5]))   # [1, 2, 3, 4, 5] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T5"
     ],
     "code": "def test_t5():\n    return grade(\n        (4, \"[3, 1, 4] və [2, 5] → [1, 2, 3, 4, 5]\", lambda: _eq(_as_list(birlesdir_sirala([3, 1, 4], [2, 5])), [1, 2, 3, 4, 5])),\n        (3, \"təkrarlanan elementlər saxlanmalıdır: [2, 2] və [1] → [1, 2, 2]\", lambda: _eq(_as_list(birlesdir_sirala([2, 2], [1])), [1, 2, 2])),\n        (3, \"boş siyahı ilə: [] və [9, -1] → [-1, 9]\", lambda: _eq(_as_list(birlesdir_sirala([], [9, -1])), [-1, 9])),\n    )\ncheck(\"T5\", 10, test_t5)"
    },
    {
     "k": "var",
     "task": "T6",
     "var": "cavab_T6"
    },
    {
     "k": "test",
     "ids": [
      "T6"
     ],
     "code": "def test_t6():\n    assert _h(cavab_T6) == \"2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6\", \"cavab düzgün deyil\"\ncheck(\"T6\", 10, test_t6)"
    },
    {
     "k": "code",
     "task": "T7",
     "code": "from collections import deque\n\nq = deque()\n# \"A\", \"B\", \"C\" elementlərini əlavə edin:\n\n# popleft() ilə bir element çıxarıb cixan dəyişəninə yazın:\ncixan = None\n\nprint(cixan, q)"
    },
    {
     "k": "test",
     "ids": [
      "T7"
     ],
     "code": "def test_t7():\n    from collections import deque as _dq\n    return grade(\n        (4, \"FIFO: ilk əlavə olunan 'A' çıxmalıdır (cixan = 'A')\", lambda: cixan == \"A\"),\n        (3, \"növbədə ['B', 'C'] qalmalıdır\", lambda: _as_list(q) == [\"B\", \"C\"]),\n        (3, \"q collections.deque olmalıdır\", lambda: isinstance(q, _dq) and len(q) == 2),\n    )\ncheck(\"T7\", 10, test_t7)"
    },
    {
     "k": "var",
     "task": "T8",
     "var": "cavab_T8"
    },
    {
     "k": "test",
     "ids": [
      "T8"
     ],
     "code": "def test_t8():\n    assert _h(cavab_T8) == \"3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d\", \"cavab düzgün deyil\"\ncheck(\"T8\", 10, test_t8)"
    },
    {
     "k": "code",
     "task": "T9",
     "code": "def sola_surusdur(lst):\n    # buranı yazın\n    pass\n\n\nprint(sola_surusdur([1, 2, 3, 4]))   # [2, 3, 4, 1] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T9"
     ],
     "code": "def test_t9():\n    return grade(\n        (4, \"[1, 2, 3, 4] → [2, 3, 4, 1]\", lambda: _eq(_as_list(_ret(sola_surusdur, [1, 2, 3, 4])), [2, 3, 4, 1])),\n        (3, \"[5, 6] → [6, 5]; [7] → [7]\", lambda: _eq(_as_list(_ret(sola_surusdur, [5, 6])), [6, 5]) and _eq(_as_list(_ret(sola_surusdur, [7])), [7])),\n        (3, \"boş siyahı xəta verməməli, [] qalmalıdır; sətirlər də işləməlidir\", lambda: _as_list(_ret(sola_surusdur, [])) == [] and _eq(_as_list(_ret(sola_surusdur, [\"a\", \"b\", \"c\"])), [\"b\", \"c\", \"a\"])),\n    )\ncheck(\"T9\", 10, test_t9)"
    },
    {
     "k": "var",
     "task": "T10",
     "var": "cavab_T10"
    },
    {
     "k": "test",
     "ids": [
      "T10"
     ],
     "code": "def test_t10():\n    assert _h(cavab_T10) == \"3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d\", \"cavab düzgün deyil\"\ncheck(\"T10\", 10, test_t10)"
    }
   ]
  },
  "D": {
   "name": "Variant D",
   "max_score": 100,
   "items": [
    {
     "type": "task",
     "id": "T1"
    },
    {
     "type": "task",
     "id": "T2"
    },
    {
     "type": "task",
     "id": "T3"
    },
    {
     "type": "task",
     "id": "T4"
    },
    {
     "type": "task",
     "id": "T5"
    },
    {
     "type": "task",
     "id": "T6"
    },
    {
     "type": "task",
     "id": "T7"
    },
    {
     "type": "task",
     "id": "T8"
    },
    {
     "type": "task",
     "id": "T9"
    },
    {
     "type": "task",
     "id": "T10"
    }
   ],
   "tasks": [
    {
     "id": "T1",
     "title": "Tapşırıq T1. len() əməliyyatının mürəkkəbliyi (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T1. len() əməliyyatının mürəkkəbliyi (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p><code>len(lst)</code> əməliyyatının mürəkkəbliyi nədir və niyə?</p>",
     "options": {
      "a": "O(1), çünki list öz uzunluğunu ayrıca saxlayır və <code>len()</code> hazır qiyməti qaytarır",
      "b": "O(log n), çünki siyahı ikiyə bölünərək sayılır",
      "c": "O(n²), çünki hər element bütün digərləri ilə müqayisə olunur",
      "d": "O(n), çünki <code>len()</code> elementləri bir-bir sayır"
     }
    },
    {
     "id": "T2",
     "title": "Tapşırıq T2. Siyahıda xətti axtarış (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T2. Siyahıda xətti axtarış (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahıda verilmiş elementi axtaran <code>axtar(lst, x)</code> funksiyasını yazın: element tapılsa onun (ilk rast gəlinən) <b>indeksini</b>,<br>tapılmasa <code>-1</code> qaytarsın.<br>Nümunə: <code>axtar([4, 5, 6, 8], 6)</code> → <code>2</code>; <code>axtar([4, 5, 6, 8], 7)</code> → <code>-1</code>.</p>",
     "starter": "def axtar(lst, x):\n    # buranı yazın\n    pass\n\n\nprint(axtar([4, 5, 6, 8], 6))   # 2 olmalıdır\nprint(axtar([4, 5, 6, 8], 7))   # -1 olmalıdır"
    },
    {
     "id": "T3",
     "title": "Tapşırıq T3. Ən kiçik və ən böyük element (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T3. Ən kiçik və ən böyük element (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahının ən kiçik və ən böyük elementini <code>min()</code> və <code>max()</code> funksiyaları ilə tapıb <b><code>(en_kicik, en_boyuk)</code> cütü kimi qaytaran</b><br><code>min_max(lst)</code> funksiyasını yazın.<br>Nümunə: <code>min_max([5, 3, 8, 1])</code> → <code>(1, 8)</code>.</p>",
     "starter": "def min_max(lst):\n    # buranı yazın\n    pass\n\n\nprint(min_max([5, 3, 8, 1]))   # (1, 8) olmalıdır"
    },
    {
     "id": "T4",
     "title": "Tapşırıq T4. Xətti və qeyri-xətti strukturlar (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T4. Xətti və qeyri-xətti strukturlar (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Hansı cavabda strukturlar düzgün qruplaşdırılıb (birinci qrup — xətti, ikinci qrup — qeyri-xətti)?</p>",
     "options": {
      "a": "Xətti: massiv, ağac; qeyri-xətti: bağlı siyahı, qraf",
      "b": "Xətti: massiv, stek, növbə, bağlı siyahı; qeyri-xətti: ağac, qraf",
      "c": "Xətti: qraf, həş cədvəli; qeyri-xətti: massiv, növbə",
      "d": "Xətti: ağac, qraf; qeyri-xətti: stek, növbə"
     }
    },
    {
     "id": "T5",
     "title": "Tapşırıq T5. Kvadratlar siyahısı (list comprehension) (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T5. Kvadratlar siyahısı (list comprehension) (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>1-dən <code>n</code>-ə qədər (n daxil) ədədlərin kvadratlarından ibarət siyahını <b>list comprehension</b> ilə yaradıb <b>qaytaran</b><br><code>kvadratlar(n)</code> funksiyasını yazın.<br>Nümunə: <code>kvadratlar(10)</code> → <code>[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]</code>.</p>",
     "starter": "def kvadratlar(n):\n    # list comprehension ilə yazın\n    pass\n\n\nprint(kvadratlar(10))   # [1, 4, 9, ..., 100] olmalıdır"
    },
    {
     "id": "T6",
     "title": "Tapşırıq T6. Bağlı siyahı və Python list (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T6. Bağlı siyahı və Python list (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Bağlı siyahını Python <code>list</code> ilə müqayisə edin. Hansı fikir doğrudur?</p>",
     "options": {
      "a": "Python list-in başına element əlavə etmək O(1)-dir",
      "b": "Bağlı siyahıda i-ci elementə müraciət O(1)-dir",
      "c": "Bağlı siyahının düyünləri yaddaşda ardıcıl yerləşir",
      "d": "Bağlı siyahının başına əlavə/silmə O(1)-dir, lakin i-ci elementə çatmaq O(n)-dir; list-də isə indekslə müraciət O(1)-dir"
     }
    },
    {
     "id": "T7",
     "title": "Tapşırıq T7. Stack sinfi: push və pop (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T7. Stack sinfi: push və pop (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Sadə <code>Stack</code> sinfini tamamlayın: <code>push(x)</code> elementi stekin üstünə əlavə etsin, <code>pop()</code> isə üstdəki elementi çıxarıb qaytarsın.<br>Stek boşdursa, <code>pop()</code> xəta vermədən <code>None</code> qaytarsın.</p>",
     "starter": "class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, x):\n        # buranı yazın\n        pass\n\n    def pop(self):\n        # buranı yazın (stek boşdursa None qaytarsın)\n        pass\n\n\ns = Stack()\ns.push(1)\ns.push(2)\nprint(s.pop())   # 2 olmalıdır"
    },
    {
     "id": "T8",
     "title": "Tapşırıq T8. Amortizasiya olunmuş təhlil: list.append() (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T8. Amortizasiya olunmuş təhlil: list.append() (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p><code>list.append()</code> əməliyyatının amortizasiya olunmuş mürəkkəbliyi niyə O(1)-dir?</p>",
     "options": {
      "a": "Amortizasiya ehtimala əsaslanan orta haldır, ona görə nəticə zəmanətli deyil",
      "b": "Python list bağlı siyahıdır, ona görə sona əlavə həmişə O(1)-dir",
      "c": "Tutum bitəndə elementlər daha böyük massivə köçürülür (O(n)), lakin tutum hər dəfə müəyyən nisbətdə artdığı üçün bu nadir baş verir və n əlavə üçün ümumi iş O(n) olur",
      "d": "<code>append()</code> heç vaxt elementləri köçürmür"
     }
    },
    {
     "id": "T9",
     "title": "Tapşırıq T9. İki sıralanmış siyahını birləşdirmək (sorted() olmadan) (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T9. İki sıralanmış siyahını birləşdirmək (sorted() olmadan) (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Artan sıra ilə düzülmüş iki siyahını bir sıralanmış siyahıda birləşdirən <code>birlesdir(a, b)</code> funksiyasını yazın.<br><b><code>sorted()</code> və <code>sort()</code> istifadə etməyin</b> — iki göstərici (<code>i</code>, <code>j</code>) ilə birləşdirin.<br>Nümunə: <code>birlesdir([1, 4, 7], [2, 3, 8])</code> → <code>[1, 2, 3, 4, 7, 8]</code>.</p>",
     "starter": "def birlesdir(a, b):\n    # sorted() istifadə etmədən yazın\n    pass\n\n\nprint(birlesdir([1, 4, 7], [2, 3, 8]))   # [1, 2, 3, 4, 7, 8] olmalıdır"
    },
    {
     "id": "T10",
     "title": "Tapşırıq T10. Bağlı siyahının sonuna düyün əlavə etmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T10. Bağlı siyahının sonuna düyün əlavə etmək (10 bal)</h4>\n<p><i>Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Bağlı siyahının sonuna <code>data</code> qiymətli yeni düyün əlavə edən və siyahının başını (<code>head</code>) <b>qaytaran</b><br><code>sona_elave(head, data)</code> funksiyasını yazın. Siyahı boşdursa (<code>head = None</code>), yeni düyün siyahının başı olur.</p>",
     "starter": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef sona_elave(head, data):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nhead = sona_elave(head, 40)\n\ncur = head\nwhile cur:\n    print(cur.data, end=\" -> \")\n    cur = cur.next\nprint(\"None\")   # 10 -> 20 -> 30 -> 40 -> None olmalıdır"
    }
   ],
   "steps": [
    {
     "k": "var",
     "task": "T1",
     "var": "cavab_T1"
    },
    {
     "k": "test",
     "ids": [
      "T1"
     ],
     "code": "def test_t1():\n    assert _h(cavab_T1) == \"ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb\", \"cavab düzgün deyil\"\ncheck(\"T1\", 10, test_t1)"
    },
    {
     "k": "code",
     "task": "T2",
     "code": "def axtar(lst, x):\n    # buranı yazın\n    pass\n\n\nprint(axtar([4, 5, 6, 8], 6))   # 2 olmalıdır\nprint(axtar([4, 5, 6, 8], 7))   # -1 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T2"
     ],
     "code": "def test_t2():\n    return grade(\n        (4, \"axtar([4, 5, 6, 8], 6) 2 olmalıdır\", lambda: axtar([4, 5, 6, 8], 6) == 2),\n        (3, \"tapılmayan element və boş siyahı üçün -1\", lambda: axtar([4, 5, 6, 8], 7) == -1 and axtar([], 1) == -1),\n        (3, \"təkrarlanan elementdə ilk indeks; sonuncu element də tapılmalıdır\", lambda: axtar([3, 1, 3], 3) == 0 and axtar([9, 8, 7], 7) == 2),\n    )\ncheck(\"T2\", 10, test_t2)"
    },
    {
     "k": "code",
     "task": "T3",
     "code": "def min_max(lst):\n    # buranı yazın\n    pass\n\n\nprint(min_max([5, 3, 8, 1]))   # (1, 8) olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T3"
     ],
     "code": "def test_t3():\n    return grade(\n        (4, \"min_max([5, 3, 8, 1]) (1, 8) olmalıdır\", lambda: _eq(_as_list(min_max([5, 3, 8, 1])), [1, 8])),\n        (3, \"mənfi ədədlər: [-4, 0, -9] → (-9, 0)\", lambda: _eq(_as_list(min_max([-4, 0, -9])), [-9, 0])),\n        (3, \"tək elementli siyahı: [6] → (6, 6)\", lambda: _eq(_as_list(min_max([6])), [6, 6])),\n    )\ncheck(\"T3\", 10, test_t3)"
    },
    {
     "k": "var",
     "task": "T4",
     "var": "cavab_T4"
    },
    {
     "k": "test",
     "ids": [
      "T4"
     ],
     "code": "def test_t4():\n    assert _h(cavab_T4) == \"3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d\", \"cavab düzgün deyil\"\ncheck(\"T4\", 10, test_t4)"
    },
    {
     "k": "code",
     "task": "T5",
     "code": "def kvadratlar(n):\n    # list comprehension ilə yazın\n    pass\n\n\nprint(kvadratlar(10))   # [1, 4, 9, ..., 100] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T5"
     ],
     "code": "def test_t5():\n    return grade(\n        (4, \"kvadratlar(10) → [1, 4, 9, ..., 100]\", lambda: _eq(_as_list(kvadratlar(10)), [x * x for x in range(1, 11)])),\n        (3, \"n daxil olmalıdır: kvadratlar(3) → [1, 4, 9]; kvadratlar(1) → [1]\", lambda: _eq(_as_list(kvadratlar(3)), [1, 4, 9]) and _eq(_as_list(kvadratlar(1)), [1])),\n        (3, \"list comprehension istifadə olunmalıdır\", lambda: \"ListComp\" in _nodes(\"T5\") and _eq(_as_list(kvadratlar(0)), [])),\n    )\ncheck(\"T5\", 10, test_t5)"
    },
    {
     "k": "var",
     "task": "T6",
     "var": "cavab_T6"
    },
    {
     "k": "test",
     "ids": [
      "T6"
     ],
     "code": "def test_t6():\n    assert _h(cavab_T6) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T6\", 10, test_t6)"
    },
    {
     "k": "code",
     "task": "T7",
     "code": "class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, x):\n        # buranı yazın\n        pass\n\n    def pop(self):\n        # buranı yazın (stek boşdursa None qaytarsın)\n        pass\n\n\ns = Stack()\ns.push(1)\ns.push(2)\nprint(s.pop())   # 2 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T7"
     ],
     "code": "def test_t7():\n    def lifo():\n        s = Stack()\n        for x in (1, 2, 3):\n            s.push(x)\n        return s.pop() == 3\n    def ardicil():\n        s = Stack()\n        s.push(\"a\"); s.push(\"b\")\n        r1 = s.pop(); s.push(\"c\")\n        return (r1, s.pop(), s.pop()) == (\"b\", \"c\", \"a\")\n    def bos():\n        s = Stack()\n        s.push(5)\n        return s.pop() == 5 and s.pop() is None\n    return grade(\n        (4, \"push(1), push(2), push(3)-dən sonra pop() 3 qaytarmalıdır (LIFO)\", lifo),\n        (3, \"çıxarılma ardıcıllığı b, c, a olmalıdır\", ardicil),\n        (3, \"boş stekdə pop() xəta verməməli, None qaytarmalıdır\", bos),\n    )\ncheck(\"T7\", 10, test_t7)"
    },
    {
     "k": "var",
     "task": "T8",
     "var": "cavab_T8"
    },
    {
     "k": "test",
     "ids": [
      "T8"
     ],
     "code": "def test_t8():\n    assert _h(cavab_T8) == \"2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6\", \"cavab düzgün deyil\"\ncheck(\"T8\", 10, test_t8)"
    },
    {
     "k": "code",
     "task": "T9",
     "code": "def birlesdir(a, b):\n    # sorted() istifadə etmədən yazın\n    pass\n\n\nprint(birlesdir([1, 4, 7], [2, 3, 8]))   # [1, 2, 3, 4, 7, 8] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T9"
     ],
     "code": "def test_t9():\n    return grade(\n        (4, \"[1, 4, 7] və [2, 3, 8] → [1, 2, 3, 4, 7, 8]\", lambda: _eq(_as_list(birlesdir([1, 4, 7], [2, 3, 8])), [1, 2, 3, 4, 7, 8])),\n        (3, \"boş siyahı və bərabər elementlər\", lambda: _eq(_as_list(birlesdir([], [1, 2])), [1, 2]) and _eq(_as_list(birlesdir([5], [])), [5]) and _eq(_as_list(birlesdir([1, 3], [1, 2])), [1, 1, 2, 3])),\n        (3, \"sorted()/sort() istifadə olunmamalıdır\", lambda: not (_calls(\"T9\") & {\"sorted\", \"sort\"}) and _eq(_as_list(birlesdir([10], [1, 20])), [1, 10, 20])),\n    )\ncheck(\"T9\", 10, test_t9)"
    },
    {
     "k": "code",
     "task": "T10",
     "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef sona_elave(head, data):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\nhead = sona_elave(head, 40)\n\ncur = head\nwhile cur:\n    print(cur.data, end=\" -> \")\n    cur = cur.next\nprint(\"None\")   # 10 -> 20 -> 30 -> 40 -> None olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T10"
     ],
     "code": "def test_t10():\n    def adi():\n        h = _ll([10, 20, 30])\n        r = sona_elave(h, 40)\n        return _ll_list(r if r is not None else h) == [10, 20, 30, 40]\n    def ardicil():\n        h = _ll([1])\n        h = sona_elave(h, 2) or h\n        h = sona_elave(h, 3) or h\n        return _ll_list(h) == [1, 2, 3]\n    return grade(\n        (4, \"10 -> 20 -> 30 siyahısına 40 əlavə edildikdə [10, 20, 30, 40]\", adi),\n        (3, \"boş siyahıya əlavə etdikdə yeni düyün qaytarılmalıdır\", lambda: _ll_list(sona_elave(None, 5)) == [5]),\n        (3, \"ardıcıl əlavələrdən sonra [1, 2, 3]\", ardicil),\n    )\ncheck(\"T10\", 10, test_t10)"
    }
   ]
  },
  "E": {
   "name": "Variant E",
   "max_score": 100,
   "items": [
    {
     "type": "task",
     "id": "T1"
    },
    {
     "type": "task",
     "id": "T2"
    },
    {
     "type": "task",
     "id": "T3"
    },
    {
     "type": "task",
     "id": "T4"
    },
    {
     "type": "task",
     "id": "T5"
    },
    {
     "type": "task",
     "id": "T6"
    },
    {
     "type": "task",
     "id": "T7"
    },
    {
     "type": "task",
     "id": "T8"
    },
    {
     "type": "task",
     "id": "T9"
    },
    {
     "type": "task",
     "id": "T10"
    }
   ],
   "tasks": [
    {
     "id": "T1",
     "title": "Tapşırıq T1. Bağlı siyahının elementlərini çap etmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T1. Bağlı siyahının elementlərini çap etmək (10 bal)</h4>\n<p><i>Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Bağlı siyahının bütün elementlərini başdan sona ardıcıllıqla <b>çap edən</b> <code>cap_et(head)</code> funksiyasını yazın<br>(məsələn: <code>10 -&gt; 20 -&gt; 30 -&gt; None</code>; çap formatı yoxlanmır, yalnız qiymətlər və onların sırası).<br>Boş siyahıda (<code>head = None</code>) xəta verməməlidir.</p>",
     "starter": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef cap_et(head):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\ncap_et(head)   # 10 -> 20 -> 30 -> None"
    },
    {
     "id": "T2",
     "title": "Tapşırıq T2. Stek və onun əməliyyatları (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T2. Stek və onun əməliyyatları (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Stek hansı prinsiplə işləyir və Python <code>list</code> ilə onun əsas əməliyyatları necə yerinə yetirilir?</p>",
     "options": {
      "a": "FIFO; push — <code>append(x)</code>, pop — <code>pop(0)</code>",
      "b": "Stekdə elementlərə yalnız indekslə müraciət olunur, push və pop əməliyyatları yoxdur",
      "c": "FIFO; push — <code>appendleft(x)</code>, pop — <code>popleft()</code>",
      "d": "LIFO; push — <code>append(x)</code>, pop — <code>pop()</code>, peek — <code>stek[-1]</code>"
     }
    },
    {
     "id": "T3",
     "title": "Tapşırıq T3. Yalnız müsbət ədədləri saxlamaq (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T3. Yalnız müsbət ədədləri saxlamaq (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahıdan mənfi ədədləri çıxarıb <b>yalnız müsbət ədədlərdən</b> ibarət yeni siyahı <b>qaytaran</b> <code>yalniz_musbet(lst)</code> funksiyasını yazın.<br>Nümunə: <code>yalniz_musbet([3, -1, 4, -5, 2])</code> → <code>[3, 4, 2]</code>.</p>",
     "starter": "def yalniz_musbet(lst):\n    # buranı yazın\n    pass\n\n\nprint(yalniz_musbet([3, -1, 4, -5, 2]))   # [3, 4, 2] olmalıdır"
    },
    {
     "id": "T4",
     "title": "Tapşırıq T4. Stek və növbədən çıxan element (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T4. Stek və növbədən çıxan element (10 bal)</h4>\n<p><i>Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>1, 2, 3 ədədləri əvvəlcə stekə (<code>list</code>), sonra növbəyə (<code>deque</code>) əlavə olunur. Hər birindən bir element çıxarılır.<br><code>stek_ve_novbe()</code> funksiyasını yazın: bu əməliyyatları yerinə yetirib <b><code>(stekden_cixan, novbeden_cixan)</code> cütünü qaytarsın</b>.</p>",
     "starter": "from collections import deque\n\n\ndef stek_ve_novbe():\n    stek, novbe = [], deque()\n    # 1, 2, 3 ədədlərini hər ikisinə əlavə edin və hər birindən bir element çıxarın\n    pass\n\n\nprint(stek_ve_novbe())   # (3, 1) olmalıdır"
    },
    {
     "id": "T5",
     "title": "Tapşırıq T5. Ağac: kök, yarpaq, dərinlik, hündürlük (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T5. Ağac: kök, yarpaq, dərinlik, hündürlük (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Ağac anlayışları haqqında hansı fikir doğrudur?</p>",
     "options": {
      "a": "Kökün dərinliyi 0-dır; düyünün dərinliyi ondan kökə qədər, hündürlüyü isə ondan ən uzaq yarpağa qədər olan kənarların sayıdır",
      "b": "Kök — heç bir uşağı olmayan düyündür",
      "c": "Yarpaq — valideyni olmayan düyündür",
      "d": "Ağacda istənilən iki düyün arasında bir neçə yol ola bilər"
     }
    },
    {
     "id": "T6",
     "title": "Tapşırıq T6. Müsbət ədədlərin sayı (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T6. Müsbət ədədlərin sayı (10 bal)</h4>\n<p><i>Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahıda neçə müsbət ədəd (0-dan böyük) olduğunu <b>qaytaran</b> <code>musbet_say(lst)</code> funksiyasını yazın.<br>Nümunə: <code>musbet_say([3, -1, 0, 5, -2])</code> → <code>2</code>.</p>",
     "starter": "def musbet_say(lst):\n    # buranı yazın\n    pass\n\n\nprint(musbet_say([3, -1, 0, 5, -2]))   # 2 olmalıdır"
    },
    {
     "id": "T7",
     "title": "Tapşırıq T7. Təkrarlanan elementləri silmək (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T7. Təkrarlanan elementləri silmək (10 bal)</h4>\n<p><i>Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahıdakı təkrarlanan elementləri silib, hər elementi bir dəfə saxlayan siyahı <b>qaytaran</b> <code>unikal(lst)</code> funksiyasını yazın<br>(<code>set</code> istifadə edə bilərsiniz; elementlərin sırası yoxlanmır).<br>Nümunə: <code>unikal([1, 2, 2, 3, 1])</code> → <code>[1, 2, 3]</code>.</p>",
     "starter": "def unikal(lst):\n    # buranı yazın\n    pass\n\n\nprint(unikal([1, 2, 2, 3, 1]))   # [1, 2, 3] olmalıdır"
    },
    {
     "id": "T8",
     "title": "Tapşırıq T8. Ardıcıl dövrlərin zaman mürəkkəbliyi (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T8. Ardıcıl dövrlərin zaman mürəkkəbliyi (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>Aşağıdakı kodun zaman mürəkkəbliyi nədir?</p>\n<pre class=\"md-code\"><code>for i in range(n):\n    print(i)\nfor j in range(n):\n    print(j)</code></pre>",
     "options": {
      "a": "O(n²)",
      "b": "O(log n)",
      "c": "O(1)",
      "d": "O(n)"
     }
    },
    {
     "id": "T9",
     "title": "Tapşırıq T9. Cüt ədədlər (list comprehension) (10 bal)",
     "pts": 10,
     "kind": "code",
     "html": "<h4>Tapşırıq T9. Cüt ədədlər (list comprehension) (10 bal)</h4>\n<p><i>Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə: 0–10 bal arası (hər düzgün hissə üçün ayrıca bal)</i></p>\n<p>Siyahıdakı cüt ədədləri <b>list comprehension</b> vasitəsilə yeni siyahıya seçib <b>qaytaran</b> <code>cut_ededler(lst)</code> funksiyasını yazın.<br>Nümunə: <code>cut_ededler([1, 2, 3, 4, 5, 6])</code> → <code>[2, 4, 6]</code>.</p>",
     "starter": "def cut_ededler(lst):\n    # list comprehension ilə yazın\n    pass\n\n\nprint(cut_ededler([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))   # [2, 4, 6, 8, 10] olmalıdır"
    },
    {
     "id": "T10",
     "title": "Tapşırıq T10. Zaman və yaddaş mürəkkəbliyi (10 bal)",
     "pts": 10,
     "kind": "choice",
     "html": "<h4>Tapşırıq T10. Zaman və yaddaş mürəkkəbliyi (10 bal)</h4>\n<p><i>Nəzəri sual · Nəzəri anlayış və mövzu · düzgün variantı seçin (yalnız 0 və ya 10 bal)</i></p>\n<p>n elementli massivdə ən böyük elementi tapan alqoritm massivi bir dəfə keçir və yalnız bir köməkçi dəyişən (<code>m</code>) istifadə edir. Onun zaman T(n) və əlavə yaddaş S(n) mürəkkəbliyi hansıdır?</p>",
     "options": {
      "a": "T(n) = O(1), S(n) = O(n)",
      "b": "T(n) = O(n), S(n) = O(n)",
      "c": "T(n) = O(n²), S(n) = O(1)",
      "d": "T(n) = O(n), S(n) = O(1)"
     }
    }
   ],
   "steps": [
    {
     "k": "code",
     "task": "T1",
     "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\ndef cap_et(head):\n    # buranı yazın\n    pass\n\n\nhead = Node(10)\nhead.next = Node(20)\nhead.next.next = Node(30)\ncap_et(head)   # 10 -> 20 -> 30 -> None"
    },
    {
     "k": "test",
     "ids": [
      "T1"
     ],
     "code": "def test_t1():\n    return grade(\n        (4, \"10 -> 20 -> 30 siyahısı üçün 10, 20, 30 çap olunmalıdır\", lambda: _ints(_capture(cap_et, _ll([10, 20, 30]))) == [10, 20, 30]),\n        (3, \"başqa siyahı: 5 -> 1 üçün 5, 1\", lambda: _ints(_capture(cap_et, _ll([5, 1]))) == [5, 1]),\n        (3, \"tək düyünlü siyahı; boş siyahıda xəta olmamalıdır\", lambda: _ints(_capture(cap_et, _ll([7]))) == [7] and _ints(_capture(cap_et, None)) == []),\n    )\ncheck(\"T1\", 10, test_t1)"
    },
    {
     "k": "var",
     "task": "T2",
     "var": "cavab_T2"
    },
    {
     "k": "test",
     "ids": [
      "T2"
     ],
     "code": "def test_t2():\n    assert _h(cavab_T2) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T2\", 10, test_t2)"
    },
    {
     "k": "code",
     "task": "T3",
     "code": "def yalniz_musbet(lst):\n    # buranı yazın\n    pass\n\n\nprint(yalniz_musbet([3, -1, 4, -5, 2]))   # [3, 4, 2] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T3"
     ],
     "code": "def test_t3():\n    return grade(\n        (4, \"[3, -1, 4, -5, 2] → [3, 4, 2]\", lambda: _eq(_as_list(_ret(yalniz_musbet, [3, -1, 4, -5, 2])), [3, 4, 2])),\n        (3, \"elementlərin sırası saxlanmalıdır: [9, -1, 1] → [9, 1]\", lambda: _eq(_as_list(_ret(yalniz_musbet, [9, -1, 1])), [9, 1])),\n        (3, \"0 müsbət deyil; mənfi siyahı üçün []\", lambda: _eq(_as_list(_ret(yalniz_musbet, [0, -2, 5])), [5]) and _eq(_as_list(_ret(yalniz_musbet, [-1, -2])), [])),\n    )\ncheck(\"T3\", 10, test_t3)"
    },
    {
     "k": "code",
     "task": "T4",
     "code": "from collections import deque\n\n\ndef stek_ve_novbe():\n    stek, novbe = [], deque()\n    # 1, 2, 3 ədədlərini hər ikisinə əlavə edin və hər birindən bir element çıxarın\n    pass\n\n\nprint(stek_ve_novbe())   # (3, 1) olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T4"
     ],
     "code": "def test_t4():\n    def cut():\n        r = _as_list(stek_ve_novbe())\n        return isinstance(r, list) and len(r) == 2\n    return grade(\n        (3, \"nəticə iki elementli cüt olmalıdır\", cut),\n        (4, \"stekdən 3 çıxmalıdır (LIFO)\", lambda: _as_list(stek_ve_novbe())[0] == 3),\n        (3, \"növbədən 1 çıxmalıdır (FIFO)\", lambda: _as_list(stek_ve_novbe())[1] == 1 and \"popleft\" in _calls(\"T4\")),\n    )\ncheck(\"T4\", 10, test_t4)"
    },
    {
     "k": "var",
     "task": "T5",
     "var": "cavab_T5"
    },
    {
     "k": "test",
     "ids": [
      "T5"
     ],
     "code": "def test_t5():\n    assert _h(cavab_T5) == \"ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb\", \"cavab düzgün deyil\"\ncheck(\"T5\", 10, test_t5)"
    },
    {
     "k": "code",
     "task": "T6",
     "code": "def musbet_say(lst):\n    # buranı yazın\n    pass\n\n\nprint(musbet_say([3, -1, 0, 5, -2]))   # 2 olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T6"
     ],
     "code": "def test_t6():\n    return grade(\n        (4, \"[3, -1, 0, 5, -2] üçün 2 olmalıdır\", lambda: _eq(musbet_say([3, -1, 0, 5, -2]), 2)),\n        (3, \"boş və ya yalnız mənfi siyahı üçün 0\", lambda: musbet_say([]) == 0 and musbet_say([-1, -2]) == 0 and musbet_say([]) is not None),\n        (3, \"0 müsbət sayılmamalıdır\", lambda: _eq(musbet_say([0, 0, 1]), 1) and _eq(musbet_say([1, 2, 3]), 3)),\n    )\ncheck(\"T6\", 10, test_t6)"
    },
    {
     "k": "code",
     "task": "T7",
     "code": "def unikal(lst):\n    # buranı yazın\n    pass\n\n\nprint(unikal([1, 2, 2, 3, 1]))   # [1, 2, 3] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T7"
     ],
     "code": "def test_t7():\n    return grade(\n        (4, \"[1, 2, 2, 3, 1] → 1, 2, 3 (hər biri bir dəfə)\", lambda: sorted(_as_list(_ret(unikal, [1, 2, 2, 3, 1]))) == [1, 2, 3]),\n        (3, \"boş siyahı → []; [5, 5, 5] → [5]\", lambda: _as_list(_ret(unikal, [])) == [] and _as_list(_ret(unikal, [5, 5, 5])) == [5]),\n        (3, \"sətirlər: ['a', 'b', 'a', 'c', 'b'] → a, b, c\", lambda: sorted(_as_list(_ret(unikal, [\"a\", \"b\", \"a\", \"c\", \"b\"]))) == [\"a\", \"b\", \"c\"]),\n    )\ncheck(\"T7\", 10, test_t7)"
    },
    {
     "k": "var",
     "task": "T8",
     "var": "cavab_T8"
    },
    {
     "k": "test",
     "ids": [
      "T8"
     ],
     "code": "def test_t8():\n    assert _h(cavab_T8) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T8\", 10, test_t8)"
    },
    {
     "k": "code",
     "task": "T9",
     "code": "def cut_ededler(lst):\n    # list comprehension ilə yazın\n    pass\n\n\nprint(cut_ededler([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))   # [2, 4, 6, 8, 10] olmalıdır"
    },
    {
     "k": "test",
     "ids": [
      "T9"
     ],
     "code": "def test_t9():\n    return grade(\n        (4, \"[1..10] → [2, 4, 6, 8, 10]\", lambda: _eq(_as_list(cut_ededler(list(range(1, 11)))), [2, 4, 6, 8, 10])),\n        (3, \"mənfi cüt ədədlər və 0 da seçilməlidir\", lambda: _eq(_as_list(cut_ededler([-4, -3, 0, 7])), [-4, 0])),\n        (3, \"list comprehension istifadə olunmalıdır\", lambda: \"ListComp\" in _nodes(\"T9\") and _eq(_as_list(cut_ededler([1, 3])), [])),\n    )\ncheck(\"T9\", 10, test_t9)"
    },
    {
     "k": "var",
     "task": "T10",
     "var": "cavab_T10"
    },
    {
     "k": "test",
     "ids": [
      "T10"
     ],
     "code": "def test_t10():\n    assert _h(cavab_T10) == \"18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4\", \"cavab düzgün deyil\"\ncheck(\"T10\", 10, test_t10)"
    }
   ]
  }
 }
};
