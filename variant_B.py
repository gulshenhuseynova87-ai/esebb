# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant B)
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_B.py
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
# Tapşırıq T1. Node sinfi və 10 → 20 → 30 bağlı siyahısı (10 bal) — Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə (0–10 bal arası)
#
# 1. Node sinfini tamamlayın: konstruktor data və next sahələrini yaratsın (next əvvəlcə None).
# 2. Node sinfindən istifadə edərək 10 → 20 → 30 bağlı siyahısını qurun; siyahının başı head dəyişənində olsun.
# ======================================================================

with hell("T1"):
    class Node:
        def __init__(self, data):
            # data və next sahələrini yaradın
            pass


    # 10 -> 20 -> 30 bağlı siyahısını qurun (baş düyün: head):
    head = None

    cur = head
    while cur:
        print(cur.data, end=" -> ")
        cur = cur.next
    print("None")   # 10 -> 20 -> 30 -> None olmalıdır


def test_t1():
    return grade(
        (3, "Node(5).data 5, Node(5).next None olmalıdır", lambda: getattr(Node(5), "data", "yox") == 5 and getattr(Node(5), "next", "yox") is None),
        (4, "head-dən başlayaraq 10, 20, 30 olmalıdır", lambda: _ll_list(head, 10)[:3] == [10, 20, 30]),
        (3, "sonuncu düyünün next-i None; bütün düyünlər Node olmalıdır",
         lambda: head.next.next.next is None and all(isinstance(x, Node) for x in (head, head.next, head.next.next))),
    )
check("T1", 10, test_t1)


# ======================================================================
# Tapşırıq T2. İç-içə siyahını düzləşdirmək (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# İç-içə siyahını (siyahılar siyahısını) düz siyahıya çevirib qaytaran duzlesdir(lst) funksiyasını yazın.
# Nümunə: [[1, 2], [3], [4, 5, 6]] → [1, 2, 3, 4, 5, 6].
# ======================================================================

with hell("T2"):
    def duzlesdir(lst):
        # buranı yazın
        pass


    print(duzlesdir([[1, 2], [3], [4, 5, 6]]))   # [1, 2, 3, 4, 5, 6] olmalıdır


def test_t2():
    return grade(
        (4, "[[1, 2], [3], [4, 5, 6]] → [1, 2, 3, 4, 5, 6]", lambda: _eq(_as_list(duzlesdir([[1, 2], [3], [4, 5, 6]])), [1, 2, 3, 4, 5, 6])),
        (3, "boş siyahı → []; [[], [1]] → [1]", lambda: _as_list(duzlesdir([])) == [] and _eq(_as_list(duzlesdir([[], [1]])), [1])),
        (3, "sətirlər: [['a'], ['b', 'c']] → ['a', 'b', 'c']", lambda: _eq(_as_list(duzlesdir([["a"], ["b", "c"]])), ["a", "b", "c"])),
    )
check("T2", 10, test_t2)


# ======================================================================
# Tapşırıq T3. list ilə stek: append() və pop() (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# list ilə stek yaradın: stek siyahısına 1, 2, 3 ədədlərini append() ilə əlavə edin, sonra pop() ilə bir element
# çıxarıb onu cixan dəyişəninə yazın. Stekdə nə qalır?
# ======================================================================

with hell("T3"):
    stek = []
    # 1, 2, 3 ədədlərini append() ilə əlavə edin:

    # pop() ilə bir element çıxarıb cixan dəyişəninə yazın:
    cixan = None

    print(stek, cixan)   # [1, 2] 3 olmalıdır


def test_t3():
    return grade(
        (4, "LIFO: son əlavə olunan 3 çıxmalıdır (cixan = 3)", lambda: cixan == 3),
        (3, "stekdə [1, 2] qalmalıdır", lambda: _as_list(stek) == [1, 2]),
        (3, "append() və pop() istifadə olunmalıdır", lambda: {"append", "pop"} <= _calls("T3")),
    )
check("T3", 10, test_t3)


# ======================================================================
# Tapşırıq T4. Həş cədvəli və Python dict (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Python dict (həş cədvəli) haqqında hansı fikir doğrudur?
#   a) dict elementlərin əlavə olunma sırasını heç vaxt saxlamır
#   b) Açar kimi list istifadə etmək olar
#   c) Axtarış həmişə O(n)-dir, çünki bütün açarlar ardıcıl yoxlanılır
#   d) Açarın həş qiyməti cədvəldəki yeri müəyyən edir, ona görə axtarış və əlavə orta halda O(1)-dir; açar dəyişməz (həşlənən) olmalıdır
# ======================================================================

cavab_T4 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t4():
    assert _h(cavab_T4) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T4", 10, test_t4)


# ======================================================================
# Tapşırıq T5. Point sinfi (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# Point sinfini yazın: konstruktor x və y atributlarını yaratsın, show() metodu isə onları çap etsin
# (məsələn: x = 3, y = 4; çap formatı yoxlanmır, yalnız qiymətlər).
# ======================================================================

with hell("T5"):
    class Point:
        # buranı yazın
        pass


    p = Point(3, 4)
    p.show()   # x = 3, y = 4


def test_t5():
    return grade(
        (3, "Point(3, 4) obyekti yaradılmalıdır", lambda: Point(3, 4) is not None),
        (4, "x və y atributları düzgün saxlanmalıdır", lambda: Point(3, 4).x == 3 and Point(3, 4).y == 4 and Point(-1, 7).y == 7),
        (3, "show() x və y qiymətlərini çap etməlidir", lambda: _ints(_capture(Point(3, 4).show)) == [3, 4] and _ints(_capture(Point(10, 20).show)) == [10, 20]),
    )
check("T5", 10, test_t5)


# ======================================================================
# Tapşırıq T6. İç-içə dövrün zaman mürəkkəbliyi (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Aşağıdakı kodun zaman mürəkkəbliyi nədir?
#
# for i in range(n):
#     for j in range(n):
#         print(i, j)
#
#   a) O(log n)
#   b) O(n)
#   c) O(n²)
#   d) O(2n)
# ======================================================================

cavab_T6 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t6():
    assert _h(cavab_T6) == "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6", "cavab düzgün deyil"
check("T6", 10, test_t6)


# ======================================================================
# Tapşırıq T7. Siyahını tərsinə çevirmək (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahını tərsinə çevirib qaytaran tersine(lst) funksiyasını yazın (istənilən üsulla: kəsik [::-1], reverse() və ya dövr).
# Nümunə: tersine([1, 2, 3, 4, 5]) → [5, 4, 3, 2, 1].
# ======================================================================

with hell("T7"):
    def tersine(lst):
        # buranı yazın
        pass


    print(tersine([1, 2, 3, 4, 5]))   # [5, 4, 3, 2, 1] olmalıdır


def test_t7():
    return grade(
        (4, "[1, 2, 3, 4, 5] → [5, 4, 3, 2, 1]", lambda: _eq(_as_list(_ret(tersine, [1, 2, 3, 4, 5])), [5, 4, 3, 2, 1])),
        (3, "cüt sayda element: [7, 8] → [8, 7]", lambda: _eq(_as_list(_ret(tersine, [7, 8])), [8, 7])),
        (3, "sətirlərdən ibarət siyahı: ['a', 'b', 'c'] → ['c', 'b', 'a']", lambda: _eq(_as_list(_ret(tersine, ["a", "b", "c"])), ["c", "b", "a"])),
    )
check("T7", 10, test_t7)


# ======================================================================
# Tapşırıq T8. Statik və dinamik strukturlar (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Statik və dinamik strukturlar haqqında hansı fikir doğrudur?
#   a) Python list statik strukturdur, çünki elementlərinə indekslə müraciət olunur
#   b) Statik strukturun ölçüsü icra zamanı dəyişmir və yaddaş əvvəlcədən sabit həcmdə ayrılır; dinamik strukturda (Python list, bağlı siyahı) elementlərin sayı icra zamanı dəyişir
#   c) Dinamik strukturlarda ayrılmış yaddaş heç vaxt azad edilmir
#   d) Statik strukturlar yalnız Python-da, dinamik strukturlar isə yalnız C dilində olur
# ======================================================================

cavab_T8 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t8():
    assert _h(cavab_T8) == "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d", "cavab düzgün deyil"
check("T8", 10, test_t8)


# ======================================================================
# Tapşırıq T9. Queue sinfi: enqueue və dequeue (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# deque əsasında sadə Queue sinfini tamamlayın: enqueue(x) elementi növbənin sonuna əlavə etsin, dequeue() isə öndəki
# elementi çıxarıb qaytarsın (FIFO). Növbə boşdursa, dequeue() xəta vermədən None qaytarsın.
# ======================================================================

with hell("T9"):
    from collections import deque


    class Queue:
        def __init__(self):
            self.items = deque()

        def enqueue(self, x):
            # buranı yazın
            pass

        def dequeue(self):
            # buranı yazın (növbə boşdursa None qaytarsın)
            pass


    q = Queue()
    q.enqueue(10)
    q.enqueue(20)
    print(q.dequeue())   # 10 olmalıdır


def test_t9():
    def fifo():
        q = Queue()
        q.enqueue(10); q.enqueue(20)
        return q.dequeue() == 10
    def ardicil():
        q = Queue()
        q.enqueue(1); q.enqueue(2)
        r1 = q.dequeue(); q.enqueue(3)
        return (r1, q.dequeue(), q.dequeue()) == (1, 2, 3)
    def bos():
        q = Queue()
        q.enqueue("x")
        return q.dequeue() == "x" and q.dequeue() is None
    return grade(
        (4, "enqueue(10), enqueue(20)-dən sonra dequeue() 10 qaytarmalıdır (FIFO)", fifo),
        (3, "çıxarılma ardıcıllığı 1, 2, 3 olmalıdır", ardicil),
        (3, "boş növbədə dequeue() xəta verməməli, None qaytarmalıdır", bos),
    )
check("T9", 10, test_t9)


# ======================================================================
# Tapşırıq T10. Növbə və collections.deque (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Python-da növbə (FIFO) üçün list əvəzinə niyə collections.deque istifadə olunur?
#   a) deque elementləri avtomatik sıralayır
#   b) deque LIFO prinsipi ilə işləyir
#   c) list-in sonuna element əlavə etmək mümkün deyil
#   d) list.pop(0) O(n)-dir, çünki qalan elementlər sola sürüşdürülür; deque.popleft() isə O(1)-dir
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
