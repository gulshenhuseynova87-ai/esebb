# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant D)
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_D.py
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
# Tapşırıq T1. len() əməliyyatının mürəkkəbliyi (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# len(lst) əməliyyatının mürəkkəbliyi nədir və niyə?
#   a) O(1), çünki list öz uzunluğunu ayrıca saxlayır və len() hazır qiyməti qaytarır
#   b) O(log n), çünki siyahı ikiyə bölünərək sayılır
#   c) O(n²), çünki hər element bütün digərləri ilə müqayisə olunur
#   d) O(n), çünki len() elementləri bir-bir sayır
# ======================================================================

cavab_T1 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t1():
    assert _h(cavab_T1) == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb", "cavab düzgün deyil"
check("T1", 10, test_t1)


# ======================================================================
# Tapşırıq T2. Siyahıda xətti axtarış (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahıda verilmiş elementi axtaran axtar(lst, x) funksiyasını yazın: element tapılsa onun (ilk rast gəlinən) indeksini,
# tapılmasa -1 qaytarsın.
# Nümunə: axtar([4, 5, 6, 8], 6) → 2; axtar([4, 5, 6, 8], 7) → -1.
# ======================================================================

with hell("T2"):
    def axtar(lst, x):
        # buranı yazın
        pass


    print(axtar([4, 5, 6, 8], 6))   # 2 olmalıdır
    print(axtar([4, 5, 6, 8], 7))   # -1 olmalıdır


def test_t2():
    return grade(
        (4, "axtar([4, 5, 6, 8], 6) 2 olmalıdır", lambda: axtar([4, 5, 6, 8], 6) == 2),
        (3, "tapılmayan element və boş siyahı üçün -1", lambda: axtar([4, 5, 6, 8], 7) == -1 and axtar([], 1) == -1),
        (3, "təkrarlanan elementdə ilk indeks; sonuncu element də tapılmalıdır", lambda: axtar([3, 1, 3], 3) == 0 and axtar([9, 8, 7], 7) == 2),
    )
check("T2", 10, test_t2)


# ======================================================================
# Tapşırıq T3. Ən kiçik və ən böyük element (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahının ən kiçik və ən böyük elementini min() və max() funksiyaları ilə tapıb (en_kicik, en_boyuk) cütü kimi qaytaran
# min_max(lst) funksiyasını yazın.
# Nümunə: min_max([5, 3, 8, 1]) → (1, 8).
# ======================================================================

with hell("T3"):
    def min_max(lst):
        # buranı yazın
        pass


    print(min_max([5, 3, 8, 1]))   # (1, 8) olmalıdır


def test_t3():
    return grade(
        (4, "min_max([5, 3, 8, 1]) (1, 8) olmalıdır", lambda: _eq(_as_list(min_max([5, 3, 8, 1])), [1, 8])),
        (3, "mənfi ədədlər: [-4, 0, -9] → (-9, 0)", lambda: _eq(_as_list(min_max([-4, 0, -9])), [-9, 0])),
        (3, "tək elementli siyahı: [6] → (6, 6)", lambda: _eq(_as_list(min_max([6])), [6, 6])),
    )
check("T3", 10, test_t3)


# ======================================================================
# Tapşırıq T4. Xətti və qeyri-xətti strukturlar (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Hansı cavabda strukturlar düzgün qruplaşdırılıb (birinci qrup — xətti, ikinci qrup — qeyri-xətti)?
#   a) Xətti: massiv, ağac; qeyri-xətti: bağlı siyahı, qraf
#   b) Xətti: massiv, stek, növbə, bağlı siyahı; qeyri-xətti: ağac, qraf
#   c) Xətti: qraf, həş cədvəli; qeyri-xətti: massiv, növbə
#   d) Xətti: ağac, qraf; qeyri-xətti: stek, növbə
# ======================================================================

cavab_T4 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t4():
    assert _h(cavab_T4) == "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d", "cavab düzgün deyil"
check("T4", 10, test_t4)


# ======================================================================
# Tapşırıq T5. Kvadratlar siyahısı (list comprehension) (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# 1-dən n-ə qədər (n daxil) ədədlərin kvadratlarından ibarət siyahını list comprehension ilə yaradıb qaytaran
# kvadratlar(n) funksiyasını yazın.
# Nümunə: kvadratlar(10) → [1, 4, 9, 16, 25, 36, 49, 64, 81, 100].
# ======================================================================

with hell("T5"):
    def kvadratlar(n):
        # list comprehension ilə yazın
        pass


    print(kvadratlar(10))   # [1, 4, 9, ..., 100] olmalıdır


def test_t5():
    return grade(
        (4, "kvadratlar(10) → [1, 4, 9, ..., 100]", lambda: _eq(_as_list(kvadratlar(10)), [x * x for x in range(1, 11)])),
        (3, "n daxil olmalıdır: kvadratlar(3) → [1, 4, 9]; kvadratlar(1) → [1]", lambda: _eq(_as_list(kvadratlar(3)), [1, 4, 9]) and _eq(_as_list(kvadratlar(1)), [1])),
        (3, "list comprehension istifadə olunmalıdır", lambda: "ListComp" in _nodes("T5") and _eq(_as_list(kvadratlar(0)), [])),
    )
check("T5", 10, test_t5)


# ======================================================================
# Tapşırıq T6. Bağlı siyahı və Python list (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Bağlı siyahını Python list ilə müqayisə edin. Hansı fikir doğrudur?
#   a) Python list-in başına element əlavə etmək O(1)-dir
#   b) Bağlı siyahıda i-ci elementə müraciət O(1)-dir
#   c) Bağlı siyahının düyünləri yaddaşda ardıcıl yerləşir
#   d) Bağlı siyahının başına əlavə/silmə O(1)-dir, lakin i-ci elementə çatmaq O(n)-dir; list-də isə indekslə müraciət O(1)-dir
# ======================================================================

cavab_T6 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t6():
    assert _h(cavab_T6) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T6", 10, test_t6)


# ======================================================================
# Tapşırıq T7. Stack sinfi: push və pop (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# Sadə Stack sinfini tamamlayın: push(x) elementi stekin üstünə əlavə etsin, pop() isə üstdəki elementi çıxarıb qaytarsın.
# Stek boşdursa, pop() xəta vermədən None qaytarsın.
# ======================================================================

with hell("T7"):
    class Stack:
        def __init__(self):
            self.items = []

        def push(self, x):
            # buranı yazın
            pass

        def pop(self):
            # buranı yazın (stek boşdursa None qaytarsın)
            pass


    s = Stack()
    s.push(1)
    s.push(2)
    print(s.pop())   # 2 olmalıdır


def test_t7():
    def lifo():
        s = Stack()
        for x in (1, 2, 3):
            s.push(x)
        return s.pop() == 3
    def ardicil():
        s = Stack()
        s.push("a"); s.push("b")
        r1 = s.pop(); s.push("c")
        return (r1, s.pop(), s.pop()) == ("b", "c", "a")
    def bos():
        s = Stack()
        s.push(5)
        return s.pop() == 5 and s.pop() is None
    return grade(
        (4, "push(1), push(2), push(3)-dən sonra pop() 3 qaytarmalıdır (LIFO)", lifo),
        (3, "çıxarılma ardıcıllığı b, c, a olmalıdır", ardicil),
        (3, "boş stekdə pop() xəta verməməli, None qaytarmalıdır", bos),
    )
check("T7", 10, test_t7)


# ======================================================================
# Tapşırıq T8. Amortizasiya olunmuş təhlil: list.append() (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# list.append() əməliyyatının amortizasiya olunmuş mürəkkəbliyi niyə O(1)-dir?
#   a) Amortizasiya ehtimala əsaslanan orta haldır, ona görə nəticə zəmanətli deyil
#   b) Python list bağlı siyahıdır, ona görə sona əlavə həmişə O(1)-dir
#   c) Tutum bitəndə elementlər daha böyük massivə köçürülür (O(n)), lakin tutum hər dəfə müəyyən nisbətdə artdığı üçün bu nadir baş verir və n əlavə üçün ümumi iş O(n) olur
#   d) append() heç vaxt elementləri köçürmür
# ======================================================================

cavab_T8 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t8():
    assert _h(cavab_T8) == "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6", "cavab düzgün deyil"
check("T8", 10, test_t8)


# ======================================================================
# Tapşırıq T9. İki sıralanmış siyahını birləşdirmək (sorted() olmadan) (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# Artan sıra ilə düzülmüş iki siyahını bir sıralanmış siyahıda birləşdirən birlesdir(a, b) funksiyasını yazın.
# sorted() və sort() istifadə etməyin — iki göstərici (i, j) ilə birləşdirin.
# Nümunə: birlesdir([1, 4, 7], [2, 3, 8]) → [1, 2, 3, 4, 7, 8].
# ======================================================================

with hell("T9"):
    def birlesdir(a, b):
        # sorted() istifadə etmədən yazın
        pass


    print(birlesdir([1, 4, 7], [2, 3, 8]))   # [1, 2, 3, 4, 7, 8] olmalıdır


def test_t9():
    return grade(
        (4, "[1, 4, 7] və [2, 3, 8] → [1, 2, 3, 4, 7, 8]", lambda: _eq(_as_list(birlesdir([1, 4, 7], [2, 3, 8])), [1, 2, 3, 4, 7, 8])),
        (3, "boş siyahı və bərabər elementlər", lambda: _eq(_as_list(birlesdir([], [1, 2])), [1, 2]) and _eq(_as_list(birlesdir([5], [])), [5]) and _eq(_as_list(birlesdir([1, 3], [1, 2])), [1, 1, 2, 3])),
        (3, "sorted()/sort() istifadə olunmamalıdır", lambda: not (_calls("T9") & {"sorted", "sort"}) and _eq(_as_list(birlesdir([10], [1, 20])), [1, 10, 20])),
    )
check("T9", 10, test_t9)


# ======================================================================
# Tapşırıq T10. Bağlı siyahının sonuna düyün əlavə etmək (10 bal) — Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə (0–10 bal arası)
#
# Bağlı siyahının sonuna data qiymətli yeni düyün əlavə edən və siyahının başını (head) qaytaran
# sona_elave(head, data) funksiyasını yazın. Siyahı boşdursa (head = None), yeni düyün siyahının başı olur.
# ======================================================================

with hell("T10"):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None


    def sona_elave(head, data):
        # buranı yazın
        pass


    head = Node(10)
    head.next = Node(20)
    head.next.next = Node(30)
    head = sona_elave(head, 40)

    cur = head
    while cur:
        print(cur.data, end=" -> ")
        cur = cur.next
    print("None")   # 10 -> 20 -> 30 -> 40 -> None olmalıdır


def test_t10():
    def adi():
        h = _ll([10, 20, 30])
        r = sona_elave(h, 40)
        return _ll_list(r if r is not None else h) == [10, 20, 30, 40]
    def ardicil():
        h = _ll([1])
        h = sona_elave(h, 2) or h
        h = sona_elave(h, 3) or h
        return _ll_list(h) == [1, 2, 3]
    return grade(
        (4, "10 -> 20 -> 30 siyahısına 40 əlavə edildikdə [10, 20, 30, 40]", adi),
        (3, "boş siyahıya əlavə etdikdə yeni düyün qaytarılmalıdır", lambda: _ll_list(sona_elave(None, 5)) == [5]),
        (3, "ardıcıl əlavələrdən sonra [1, 2, 3]", ardicil),
    )
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
