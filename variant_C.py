# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant C)
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_C.py
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

results = {}
_errors = {}


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
    return {type(n).__name__ for n in ast.walk(tree)} if tree else set()


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
        _errors[self.task_id] = f"kodunuz icra olunarkən xəta baş verdi → {exc_type.__name__}: {exc}"
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
                print(f"✅ Tapşırıq {tid}: DÜZGÜNDÜR (+{points} bal)")
                return
            reason = "Ödənməyən hissələr: " + "; ".join(failed)
            if pts > 0:
                print(f"🟡 Tapşırıq {tid}: QİSMƏN DÜZGÜNDÜR (+{pts} / {points} bal)")
                print(f"   ↳ {reason}")
                return
        else:
            results[task_id] = points
            print(f"✅ Tapşırıq {tid}: DÜZGÜNDÜR (+{points} bal)")
            return
    except AssertionError as e:
        reason = str(e) or "test şərti ödənmədi"
    except NameError as e:
        reason = f"tələb olunan dəyişən/funksiya təyin edilməyib ({e})"
    except Exception as e:
        reason = f"{type(e).__name__}: {e}"
    results[task_id] = 0
    if tid in _errors:
        reason = _errors[tid]
    print(f"❌ Tapşırıq {tid}: XƏTA — Çıxış formatı və ya hesablanmış dəyər gözlənilən nəticəyə uyğun deyil!")
    print(f"   ↳ Səbəb: {reason}")


ad_soyad = "..."      # Bura ad və soyadınızı yazın


# ======================================================================
# Tapşırıq T1. Siyahının cəmi (sum() olmadan) (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahının elementlərinin cəmini qaytaran cem(lst) funksiyasını yazın.
# sum() funksiyasından istifadə etməyin — cəmi dövrlə hesablayın.
# Nümunə: cem([1, 2, 3, 4]) → 10; boş siyahı üçün 0.
# ======================================================================

with hell("T1"):
    def cem(lst):
        # sum() funksiyasından istifadə etmədən yazın
        pass


    print(cem([1, 2, 3, 4]))   # 10 olmalıdır


def test_t1():
    return grade(
        (4, "cem([1, 2, 3, 4]) 10 olmalıdır", lambda: _eq(cem([1, 2, 3, 4]), 10)),
        (3, "boş siyahı üçün 0, mənfi ədədlərlə də düzgün cəm", lambda: cem([]) == 0 and cem([]) is not None and _eq(cem([-5, 5, 7]), 7)),
        (3, "sum() istifadə olunmamalıdır (cəm dövrlə hesablanmalıdır)", lambda: "sum" not in _calls("T1") and _eq(cem([2.5, 2.5, 10]), 15)),
    )
check("T1", 10, test_t1)


# ======================================================================
# Tapşırıq T2. Bağlı siyahının elementlərinin cəmi (10 bal) — Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə (0–10 bal arası)
#
# Bağlı siyahının bütün elementlərinin cəmini qaytaran ll_cem(head) funksiyasını yazın.
# Boş siyahı (head = None) üçün 0.
# ======================================================================

with hell("T2"):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None


    def ll_cem(head):
        # buranı yazın
        pass


    head = Node(10)
    head.next = Node(20)
    head.next.next = Node(30)
    print(ll_cem(head))   # 60 olmalıdır


def test_t2():
    return grade(
        (4, "10 -> 20 -> 30 üçün cəm 60 olmalıdır", lambda: _eq(ll_cem(_ll([10, 20, 30])), 60)),
        (3, "boş siyahı üçün 0; tək düyünlü [7] üçün 7", lambda: ll_cem(None) == 0 and ll_cem(None) is not None and _eq(ll_cem(_ll([7])), 7)),
        (3, "mənfi qiymətlər: -5 -> 5 -> 1 üçün 1", lambda: _eq(ll_cem(_ll([-5, 5, 1])), 1)),
    )
check("T2", 10, test_t2)


# ======================================================================
# Tapşırıq T3. Stekin boş olub-olmadığını yoxlamaq (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# Stekin (siyahının) boş olub-olmadığını yoxlayan is_empty(stek) funksiyasını yazın: boşdursa True, əks halda False qaytarsın.
# Nümunə: is_empty([]) → True, is_empty([1, 2]) → False.
# ======================================================================

with hell("T3"):
    def is_empty(stek):
        # buranı yazın
        pass


    print(is_empty([]))       # True olmalıdır
    print(is_empty([1, 2]))   # False olmalıdır


def test_t3():
    def cycle():
        s = [5]
        a = is_empty(s)
        s.pop()
        return a is not None and a == False and is_empty(s) == True
    return grade(
        (4, "is_empty([]) True olmalıdır", lambda: is_empty([]) == True),
        (3, "is_empty([1, 2]) False olmalıdır", lambda: is_empty([1, 2]) is not None and is_empty([1, 2]) == False),
        (3, "push/pop-dan sonra: [5] → False, pop-dan sonra → True", cycle),
    )
check("T3", 10, test_t3)


# ======================================================================
# Tapşırıq T4. Yaddaşın stek və heap sahələri (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Yaddaşın stek (call stack) və heap sahələri haqqında hansı fikir doğrudur?
#   a) Dərin rekursiya heap sahəsini doldurur, stek isə dəyişmir
#   b) Heap stekdən həmişə sürətlidir və LIFO qaydası ilə işləyir
#   c) Python-da bütün obyektlər (list, dict) stek sahəsində saxlanılır, heap istifadə olunmur
#   d) Stekdə funksiya çağırışlarının lokal dəyişənləri, parametrləri və qayıdış ünvanı saxlanılır və funksiya bitəndə avtomatik təmizlənir; heap isə dinamik yaradılan obyektlər üçündür
# ======================================================================

cavab_T4 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t4():
    assert _h(cavab_T4) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T4", 10, test_t4)


# ======================================================================
# Tapşırıq T5. İki siyahını birləşdirib sıralamaq (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# İki siyahını birləşdirib artan sıra ilə düzülmüş yeni siyahı qaytaran birlesdir_sirala(a, b) funksiyasını yazın
# (sorted() və ya sort() istifadə edə bilərsiniz).
# Nümunə: birlesdir_sirala([3, 1, 4], [2, 5]) → [1, 2, 3, 4, 5].
# ======================================================================

with hell("T5"):
    def birlesdir_sirala(a, b):
        # buranı yazın
        pass


    print(birlesdir_sirala([3, 1, 4], [2, 5]))   # [1, 2, 3, 4, 5] olmalıdır


def test_t5():
    return grade(
        (4, "[3, 1, 4] və [2, 5] → [1, 2, 3, 4, 5]", lambda: _eq(_as_list(birlesdir_sirala([3, 1, 4], [2, 5])), [1, 2, 3, 4, 5])),
        (3, "təkrarlanan elementlər saxlanmalıdır: [2, 2] və [1] → [1, 2, 2]", lambda: _eq(_as_list(birlesdir_sirala([2, 2], [1])), [1, 2, 2])),
        (3, "boş siyahı ilə: [] və [9, -1] → [-1, 9]", lambda: _eq(_as_list(birlesdir_sirala([], [9, -1])), [-1, 9])),
    )
check("T5", 10, test_t5)


# ======================================================================
# Tapşırıq T6. Nəzəri mürəkkəblik və real icra vaxtı (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Bir alqoritm O(n log n), digəri O(n²) mürəkkəbliyə malikdir. Kiçik n üçün O(n²) alqoritmi daha sürətli işləyə bilərmi?
#   a) Xeyr, O(n log n) alqoritm istənilən n üçün həmişə daha sürətlidir
#   b) Xeyr, real icra vaxtı aparatdan və keşdən asılı deyil
#   c) Bəli: nəzəri qiymət sabit vuruqları atır; məsələn, n = 100 üçün 100·n·log n ≈ 66 400, n² isə 10 000-dir
#   d) Bəli, çünki böyük O notasiyası yalnız kiçik n üçün keçərlidir
# ======================================================================

cavab_T6 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t6():
    assert _h(cavab_T6) == "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6", "cavab düzgün deyil"
check("T6", 10, test_t6)


# ======================================================================
# Tapşırıq T7. collections.deque ilə növbə (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# collections.deque ilə boş növbə (q) yaradın, ona "A", "B", "C" elementlərini əlavə edin və popleft() ilə bir element
# çıxarıb onu cixan dəyişəninə yazın. Hansı element çıxır?
# ======================================================================

with hell("T7"):
    from collections import deque

    q = deque()
    # "A", "B", "C" elementlərini əlavə edin:

    # popleft() ilə bir element çıxarıb cixan dəyişəninə yazın:
    cixan = None

    print(cixan, q)


def test_t7():
    from collections import deque as _dq
    return grade(
        (4, "FIFO: ilk əlavə olunan 'A' çıxmalıdır (cixan = 'A')", lambda: cixan == "A"),
        (3, "növbədə ['B', 'C'] qalmalıdır", lambda: _as_list(q) == ["B", "C"]),
        (3, "q collections.deque olmalıdır", lambda: isinstance(q, _dq) and len(q) == 2),
    )
check("T7", 10, test_t7)


# ======================================================================
# Tapşırıq T8. Ən yaxşı, ən pis və orta hal (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# n elementli siyahıda xətti axtarış üçün ən yaxşı və ən pis hal hansıdır?
#   a) Ən yaxşı hal O(log n), ən pis hal O(n)
#   b) Ən yaxşı hal O(1) — element birinci yerdədir; ən pis hal O(n) — element sonuncudur və ya yoxdur
#   c) Hər iki hal O(1)-dir, çünki siyahıya indekslə müraciət olunur
#   d) Ən yaxşı hal O(n), ən pis hal O(n²)
# ======================================================================

cavab_T8 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t8():
    assert _h(cavab_T8) == "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d", "cavab düzgün deyil"
check("T8", 10, test_t8)


# ======================================================================
# Tapşırıq T9. Siyahını 1 mövqe sola sürüşdürmək (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahının elementlərini 1 mövqe sola sürüşdürən (birinci element sona keçir) və nəticəni qaytaran sola_surusdur(lst)
# funksiyasını yazın. Boş siyahı boş qalmalıdır.
# Nümunə: [1, 2, 3, 4] → [2, 3, 4, 1].
# ======================================================================

with hell("T9"):
    def sola_surusdur(lst):
        # buranı yazın
        pass


    print(sola_surusdur([1, 2, 3, 4]))   # [2, 3, 4, 1] olmalıdır


def test_t9():
    return grade(
        (4, "[1, 2, 3, 4] → [2, 3, 4, 1]", lambda: _eq(_as_list(_ret(sola_surusdur, [1, 2, 3, 4])), [2, 3, 4, 1])),
        (3, "[5, 6] → [6, 5]; [7] → [7]", lambda: _eq(_as_list(_ret(sola_surusdur, [5, 6])), [6, 5]) and _eq(_as_list(_ret(sola_surusdur, [7])), [7])),
        (3, "boş siyahı xəta verməməli, [] qalmalıdır; sətirlər də işləməlidir", lambda: _as_list(_ret(sola_surusdur, [])) == [] and _eq(_as_list(_ret(sola_surusdur, ["a", "b", "c"])), ["b", "c", "a"])),
    )
check("T9", 10, test_t9)


# ======================================================================
# Tapşırıq T10. Qraf və onun Python-da təsviri (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Qraf haqqında hansı fikir doğrudur?
#   a) Qrafda dövr (cycle) ola bilməz
#   b) Qraf G = (V, E) təpələr və kənarlar çoxluğudur; Python-da adətən qonşuluq siyahısı (lüğət) və ya qonşuluq matrisi ilə təsvir olunur
#   c) Qraf xətti strukturdur, çünki təpələr ardıcıl düzülür
#   d) Qrafın hər təpəsinin yalnız bir valideyni olur
# ======================================================================

cavab_T10 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t10():
    assert _h(cavab_T10) == "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d", "cavab düzgün deyil"
check("T10", 10, test_t10)



# ======================================================================
# YEKUN NƏTİCƏ
# ======================================================================
MAX_POINTS = {'T1': 10, 'T2': 10, 'T3': 10, 'T4': 10, 'T5': 10, 'T6': 10, 'T7': 10, 'T8': 10, 'T9': 10, 'T10': 10}

total = 0
print()
print(f"{'Tapşırıq':<12}{'Nəticə':<10}{'Bal':>6}")
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
    print(f"{k:<12}{status:<10}{earned:>3}/{p}")

max_total = sum(MAX_POINTS.values())
print("-" * 30)
print(f"YEKUN İMTAHAN BALI: {total} / {max_total}  ({total / max_total * 100:.0f}%)")
