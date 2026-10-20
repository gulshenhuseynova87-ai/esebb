# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant E)
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_E.py
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
# Tapşırıq T1. Bağlı siyahının elementlərini çap etmək (10 bal) — Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə (0–10 bal arası)
#
# Bağlı siyahının bütün elementlərini başdan sona ardıcıllıqla çap edən cap_et(head) funksiyasını yazın
# (məsələn: 10 -> 20 -> 30 -> None; çap formatı yoxlanmır, yalnız qiymətlər və onların sırası).
# Boş siyahıda (head = None) xəta verməməlidir.
# ======================================================================

with hell("T1"):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None


    def cap_et(head):
        # buranı yazın
        pass


    head = Node(10)
    head.next = Node(20)
    head.next.next = Node(30)
    cap_et(head)   # 10 -> 20 -> 30 -> None


def test_t1():
    return grade(
        (4, "10 -> 20 -> 30 siyahısı üçün 10, 20, 30 çap olunmalıdır", lambda: _ints(_capture(cap_et, _ll([10, 20, 30]))) == [10, 20, 30]),
        (3, "başqa siyahı: 5 -> 1 üçün 5, 1", lambda: _ints(_capture(cap_et, _ll([5, 1]))) == [5, 1]),
        (3, "tək düyünlü siyahı; boş siyahıda xəta olmamalıdır", lambda: _ints(_capture(cap_et, _ll([7]))) == [7] and _ints(_capture(cap_et, None)) == []),
    )
check("T1", 10, test_t1)


# ======================================================================
# Tapşırıq T2. Stek və onun əməliyyatları (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Stek hansı prinsiplə işləyir və Python list ilə onun əsas əməliyyatları necə yerinə yetirilir?
#   a) FIFO; push — append(x), pop — pop(0)
#   b) Stekdə elementlərə yalnız indekslə müraciət olunur, push və pop əməliyyatları yoxdur
#   c) FIFO; push — appendleft(x), pop — popleft()
#   d) LIFO; push — append(x), pop — pop(), peek — stek[-1]
# ======================================================================

cavab_T2 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t2():
    assert _h(cavab_T2) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T2", 10, test_t2)


# ======================================================================
# Tapşırıq T3. Yalnız müsbət ədədləri saxlamaq (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahıdan mənfi ədədləri çıxarıb yalnız müsbət ədədlərdən ibarət yeni siyahı qaytaran yalniz_musbet(lst) funksiyasını yazın.
# Nümunə: yalniz_musbet([3, -1, 4, -5, 2]) → [3, 4, 2].
# ======================================================================

with hell("T3"):
    def yalniz_musbet(lst):
        # buranı yazın
        pass


    print(yalniz_musbet([3, -1, 4, -5, 2]))   # [3, 4, 2] olmalıdır


def test_t3():
    return grade(
        (4, "[3, -1, 4, -5, 2] → [3, 4, 2]", lambda: _eq(_as_list(_ret(yalniz_musbet, [3, -1, 4, -5, 2])), [3, 4, 2])),
        (3, "elementlərin sırası saxlanmalıdır: [9, -1, 1] → [9, 1]", lambda: _eq(_as_list(_ret(yalniz_musbet, [9, -1, 1])), [9, 1])),
        (3, "0 müsbət deyil; mənfi siyahı üçün []", lambda: _eq(_as_list(_ret(yalniz_musbet, [0, -2, 5])), [5]) and _eq(_as_list(_ret(yalniz_musbet, [-1, -2])), [])),
    )
check("T3", 10, test_t3)


# ======================================================================
# Tapşırıq T4. Stek və növbədən çıxan element (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# 1, 2, 3 ədədləri əvvəlcə stekə (list), sonra növbəyə (deque) əlavə olunur. Hər birindən bir element çıxarılır.
# stek_ve_novbe() funksiyasını yazın: bu əməliyyatları yerinə yetirib (stekden_cixan, novbeden_cixan) cütünü qaytarsın.
# ======================================================================

with hell("T4"):
    from collections import deque


    def stek_ve_novbe():
        stek, novbe = [], deque()
        # 1, 2, 3 ədədlərini hər ikisinə əlavə edin və hər birindən bir element çıxarın
        pass


    print(stek_ve_novbe())   # (3, 1) olmalıdır


def test_t4():
    def cut():
        r = _as_list(stek_ve_novbe())
        return isinstance(r, list) and len(r) == 2
    return grade(
        (3, "nəticə iki elementli cüt olmalıdır", cut),
        (4, "stekdən 3 çıxmalıdır (LIFO)", lambda: _as_list(stek_ve_novbe())[0] == 3),
        (3, "növbədən 1 çıxmalıdır (FIFO)", lambda: _as_list(stek_ve_novbe())[1] == 1 and "popleft" in _calls("T4")),
    )
check("T4", 10, test_t4)


# ======================================================================
# Tapşırıq T5. Ağac: kök, yarpaq, dərinlik, hündürlük (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Ağac anlayışları haqqında hansı fikir doğrudur?
#   a) Kökün dərinliyi 0-dır; düyünün dərinliyi ondan kökə qədər, hündürlüyü isə ondan ən uzaq yarpağa qədər olan kənarların sayıdır
#   b) Kök — heç bir uşağı olmayan düyündür
#   c) Yarpaq — valideyni olmayan düyündür
#   d) Ağacda istənilən iki düyün arasında bir neçə yol ola bilər
# ======================================================================

cavab_T5 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t5():
    assert _h(cavab_T5) == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb", "cavab düzgün deyil"
check("T5", 10, test_t5)


# ======================================================================
# Tapşırıq T6. Müsbət ədədlərin sayı (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahıda neçə müsbət ədəd (0-dan böyük) olduğunu qaytaran musbet_say(lst) funksiyasını yazın.
# Nümunə: musbet_say([3, -1, 0, 5, -2]) → 2.
# ======================================================================

with hell("T6"):
    def musbet_say(lst):
        # buranı yazın
        pass


    print(musbet_say([3, -1, 0, 5, -2]))   # 2 olmalıdır


def test_t6():
    return grade(
        (4, "[3, -1, 0, 5, -2] üçün 2 olmalıdır", lambda: _eq(musbet_say([3, -1, 0, 5, -2]), 2)),
        (3, "boş və ya yalnız mənfi siyahı üçün 0", lambda: musbet_say([]) == 0 and musbet_say([-1, -2]) == 0 and musbet_say([]) is not None),
        (3, "0 müsbət sayılmamalıdır", lambda: _eq(musbet_say([0, 0, 1]), 1) and _eq(musbet_say([1, 2, 3]), 3)),
    )
check("T6", 10, test_t6)


# ======================================================================
# Tapşırıq T7. Təkrarlanan elementləri silmək (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahıdakı təkrarlanan elementləri silib, hər elementi bir dəfə saxlayan siyahı qaytaran unikal(lst) funksiyasını yazın
# (set istifadə edə bilərsiniz; elementlərin sırası yoxlanmır).
# Nümunə: unikal([1, 2, 2, 3, 1]) → [1, 2, 3].
# ======================================================================

with hell("T7"):
    def unikal(lst):
        # buranı yazın
        pass


    print(unikal([1, 2, 2, 3, 1]))   # [1, 2, 3] olmalıdır


def test_t7():
    return grade(
        (4, "[1, 2, 2, 3, 1] → 1, 2, 3 (hər biri bir dəfə)", lambda: sorted(_as_list(_ret(unikal, [1, 2, 2, 3, 1]))) == [1, 2, 3]),
        (3, "boş siyahı → []; [5, 5, 5] → [5]", lambda: _as_list(_ret(unikal, [])) == [] and _as_list(_ret(unikal, [5, 5, 5])) == [5]),
        (3, "sətirlər: ['a', 'b', 'a', 'c', 'b'] → a, b, c", lambda: sorted(_as_list(_ret(unikal, ["a", "b", "a", "c", "b"]))) == ["a", "b", "c"]),
    )
check("T7", 10, test_t7)


# ======================================================================
# Tapşırıq T8. Ardıcıl dövrlərin zaman mürəkkəbliyi (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Aşağıdakı kodun zaman mürəkkəbliyi nədir?
#
# for i in range(n):
#     print(i)
# for j in range(n):
#     print(j)
#
#   a) O(n²)
#   b) O(log n)
#   c) O(1)
#   d) O(n)
# ======================================================================

cavab_T8 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t8():
    assert _h(cavab_T8) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T8", 10, test_t8)


# ======================================================================
# Tapşırıq T9. Cüt ədədlər (list comprehension) (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahıdakı cüt ədədləri list comprehension vasitəsilə yeni siyahıya seçib qaytaran cut_ededler(lst) funksiyasını yazın.
# Nümunə: cut_ededler([1, 2, 3, 4, 5, 6]) → [2, 4, 6].
# ======================================================================

with hell("T9"):
    def cut_ededler(lst):
        # list comprehension ilə yazın
        pass


    print(cut_ededler([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))   # [2, 4, 6, 8, 10] olmalıdır


def test_t9():
    return grade(
        (4, "[1..10] → [2, 4, 6, 8, 10]", lambda: _eq(_as_list(cut_ededler(list(range(1, 11)))), [2, 4, 6, 8, 10])),
        (3, "mənfi cüt ədədlər və 0 da seçilməlidir", lambda: _eq(_as_list(cut_ededler([-4, -3, 0, 7])), [-4, 0])),
        (3, "list comprehension istifadə olunmalıdır", lambda: "ListComp" in _nodes("T9") and _eq(_as_list(cut_ededler([1, 3])), [])),
    )
check("T9", 10, test_t9)


# ======================================================================
# Tapşırıq T10. Zaman və yaddaş mürəkkəbliyi (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# n elementli massivdə ən böyük elementi tapan alqoritm massivi bir dəfə keçir və yalnız bir köməkçi dəyişən (m) istifadə edir. Onun zaman T(n) və əlavə yaddaş S(n) mürəkkəbliyi hansıdır?
#   a) T(n) = O(1), S(n) = O(n)
#   b) T(n) = O(n), S(n) = O(n)
#   c) T(n) = O(n²), S(n) = O(1)
#   d) T(n) = O(n), S(n) = O(1)
# ======================================================================

cavab_T10 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t10():
    assert _h(cavab_T10) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
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
