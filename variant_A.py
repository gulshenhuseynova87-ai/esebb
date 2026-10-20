# -*- coding: utf-8 -*-
"""
BAKI MÜHƏNDİSLİK UNİVERSİTETİ (BMU)
Fənn: Verilənlərin strukturu və alqoritmlər — 2-ci kurs, SDF 1 (Variant A)
Maksimum bal: 100 (10 tapşırıq: 4 nəzəri + 6 praktiki, hər biri 10 bal)

İSTİFADƏ QAYDASI
1. Nəzəri suallarda düzgün variantın hərfini (a, b, c və ya d) `cavab_T..` dəyişəninə yazın.
2. Kod tapşırıqlarında funksiyanı `with hell("T..."):` blokunun İÇİNDƏ yazın
   (blokun içindəki sətirlər 4 boşluq girintili olmalıdır). `pass` əvəzinə funksiyanın gövdəsini yazın.
3. Faylı işə salın:   python variant_A.py
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
# Tapşırıq T1. Stek ilə sözü tərsinə çevirmək (10 bal) — Kod tapşırığı · Stek və növbə · qismən qiymətləndirmə (0–10 bal arası)
#
# Stekdən istifadə edərək ters(soz) funksiyasını yazın: hərfləri append() ilə stekə əlavə edin, sonra pop() ilə
# çıxararaq tərs sözü qurun və qaytarın.
# Nümunə: ters("Python") → "nohtyP".
# ======================================================================

with hell("T1"):
    def ters(soz):
        stek = []
        # buranı yazın
        pass


    print(ters("Python"))   # nohtyP olmalıdır


def test_t1():
    return grade(
        (4, "ters('Python') 'nohtyP' olmalıdır", lambda: ters("Python") == "nohtyP"),
        (3, "boş sətir və tək hərf", lambda: ters("") == "" and ters("a") == "a"),
        (3, "stekdən istifadə olunmalıdır (append() və pop())", lambda: "pop" in _calls("T1") and ters("abc") == "cba"),
    )
check("T1", 10, test_t1)


# ======================================================================
# Tapşırıq T2. Bağlı siyahının növləri (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Halqa (dairəvi) bağlı siyahını adi tək bağlı siyahıdan nə fərqləndirir?
#   a) i-ci elementə indekslə O(1) müddətdə müraciət olunur
#   b) Hər düyündə həm next, həm də prev istinadı olur
#   c) Son düyün None əvəzinə baş (head) düyünə işarə edir
#   d) Düyünlər yaddaşda ardıcıl yerləşir
# ======================================================================

cavab_T2 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t2():
    assert _h(cavab_T2) == "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6", "cavab düzgün deyil"
check("T2", 10, test_t2)


# ======================================================================
# Tapşırıq T3. Bağlı siyahıda axtarış (10 bal) — Kod tapşırığı · Bağlı siyahı · qismən qiymətləndirmə (0–10 bal arası)
#
# Bağlı siyahıda verilmiş qiyməti axtaran siyahida_var(head, x) funksiyasını yazın: qiymət varsa True, yoxdursa False
# qaytarsın. Boş siyahı (head = None) üçün False.
# ======================================================================

with hell("T3"):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None


    def siyahida_var(head, x):
        # buranı yazın
        pass


    head = Node(10)
    head.next = Node(20)
    head.next.next = Node(30)
    print(siyahida_var(head, 20))   # True olmalıdır
    print(siyahida_var(head, 99))   # False olmalıdır


def test_t3():
    return grade(
        (4, "10 -> 20 -> 30 siyahısında 20 tapılmalıdır (True)", lambda: siyahida_var(_ll([10, 20, 30]), 20) == True),
        (3, "99 yoxdur (False); sonuncu element 30 tapılmalıdır", lambda: siyahida_var(_ll([10, 20, 30]), 99) is not None and siyahida_var(_ll([10, 20, 30]), 99) == False and siyahida_var(_ll([10, 20, 30]), 30) == True),
        (3, "boş siyahı üçün False; tək düyünlü siyahı", lambda: siyahida_var(None, 5) is not None and siyahida_var(None, 5) == False and siyahida_var(_ll([7]), 7) == True),
    )
check("T3", 10, test_t3)


# ======================================================================
# Tapşırıq T4. 3 × 3 sıfır matrisi (10 bal) — Kod tapşırığı · List: comprehension, matris və sinif · qismən qiymətləndirmə (0–10 bal arası)
#
# Bütün elementləri 0 olan 3 × 3 ölçülü matris (siyahılar siyahısı) yaradın, onun ortadakı elementinə 5 yazın və
# matrisi qaytaran matris_yarat() funksiyasını yazın. Sətirlər bir-birindən asılı olmamalıdır
# ([[0] * 3] * 3 səhvdir!).
# ======================================================================

with hell("T4"):
    def matris_yarat():
        # buranı yazın
        pass


    for setir in matris_yarat() or []:
        print(setir)
    # [0, 0, 0]
    # [0, 5, 0]
    # [0, 0, 0]


def test_t4():
    return grade(
        (3, "3 sətir və hər sətirdə 3 element olmalıdır", lambda: len(matris_yarat()) == 3 and all(len(s) == 3 for s in matris_yarat())),
        (4, "ortadakı element 5, qalanları 0 olmalıdır", lambda: _eq(matris_yarat(), [[0, 0, 0], [0, 5, 0], [0, 0, 0]])),
        (3, "sətirlər ayrı-ayrı siyahılar olmalıdır ([[0] * 3] * 3 səhvdir)", lambda: len({id(s) for s in matris_yarat()}) == 3),
    )
check("T4", 10, test_t4)


# ======================================================================
# Tapşırıq T5. Ən böyük element (max() olmadan) (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Boş olmayan siyahının ən böyük elementini qaytaran en_boyuk(lst) funksiyasını yazın.
# max() və sorted() funksiyalarından istifadə etməyin.
# Nümunə: en_boyuk([5, 3, 8, 1]) → 8.
# ======================================================================

with hell("T5"):
    def en_boyuk(lst):
        # max() funksiyasından istifadə etmədən yazın
        pass


    print(en_boyuk([5, 3, 8, 1]))   # 8 olmalıdır


def test_t5():
    return grade(
        (4, "en_boyuk([5, 3, 8, 1]) 8 olmalıdır", lambda: _eq(en_boyuk([5, 3, 8, 1]), 8)),
        (3, "mənfi ədədlər və tək elementli siyahı", lambda: _eq(en_boyuk([-7, -2, -9]), -2) and _eq(en_boyuk([4]), 4)),
        (3, "max()/sorted() istifadə olunmamalıdır", lambda: not (_calls("T5") & {"max", "sorted", "sort"}) and _eq(en_boyuk([1, 9, 9, 2]), 9)),
    )
check("T5", 10, test_t5)


# ======================================================================
# Tapşırıq T6. O, Ω və Θ notasiyaları (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# T(n) = 3n² + 5n + 2 funksiyası üçün ən dəqiq qiymətləndirmə (həm yuxarı, həm aşağı sərhəd) hansıdır?
#   a) Θ(1)
#   b) Ω(n³)
#   c) Θ(n)
#   d) Θ(n²)
# ======================================================================

cavab_T6 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t6():
    assert _h(cavab_T6) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T6", 10, test_t6)


# ======================================================================
# Tapşırıq T7. Siyahının ədədi ortası (10 bal) — Kod tapşırığı · List: əsas əməliyyatlar · qismən qiymətləndirmə (0–10 bal arası)
#
# Siyahının elementlərinin ədədi ortasını qaytaran orta(lst) funksiyasını yazın. Boş siyahı üçün 0 qaytarsın.
# Nümunə: orta([2, 4, 6, 8]) → 5.0.
# ======================================================================

with hell("T7"):
    def orta(lst):
        # buranı yazın
        pass


    print(orta([2, 4, 6, 8]))   # 5.0 olmalıdır


def test_t7():
    return grade(
        (4, "orta([2, 4, 6, 8]) 5.0 olmalıdır", lambda: _is_num(orta([2, 4, 6, 8])) and _eq(orta([2, 4, 6, 8]), 5.0)),
        (3, "boş siyahı üçün 0 qaytarılmalıdır (xəta yox)", lambda: _is_num(orta([])) and orta([]) == 0),
        (3, "kəsr nəticə: orta([1, 2]) 1.5 olmalıdır", lambda: _is_num(orta([1, 2])) and _eq(orta([1, 2]), 1.5) and _eq(orta([-3, 3]), 0)),
    )
check("T7", 10, test_t7)


# ======================================================================
# Tapşırıq T8. Binar axtarış ağacının (BST) xassəsi (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# Binar axtarış ağacının (BST) əsas xassəsi hansıdır?
#   a) Hər düyünün tam olaraq iki uşağı var
#   b) Kök həmişə ağacdakı ən kiçik qiymətdir
#   c) Bütün yarpaqlar eyni dərinlikdə yerləşir
#   d) Hər düyün üçün sol alt ağacdakı bütün qiymətlər düyünün qiymətindən kiçik, sağ alt ağacdakılar isə böyükdür
# ======================================================================

cavab_T8 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t8():
    assert _h(cavab_T8) == "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4", "cavab düzgün deyil"
check("T8", 10, test_t8)


# ======================================================================
# Tapşırıq T9. Ən uzun söz (10 bal) — Kod tapşırığı · List alqoritmləri · qismən qiymətləndirmə (0–10 bal arası)
#
# Sözlər siyahısında ən uzun sözü qaytaran en_uzun(sozler) funksiyasını yazın.
# Nümunə: en_uzun(["ev", "kitab", "qələm", "kompüter"]) → "kompüter".
# ======================================================================

with hell("T9"):
    def en_uzun(sozler):
        # buranı yazın
        pass


    print(en_uzun(["ev", "kitab", "qələm", "kompüter"]))   # kompüter olmalıdır


def test_t9():
    return grade(
        (4, "['ev', 'kitab', 'qələm', 'kompüter'] → 'kompüter'", lambda: en_uzun(["ev", "kitab", "qələm", "kompüter"]) == "kompüter"),
        (3, "tək söz və birinci yerdə olan ən uzun söz", lambda: en_uzun(["a"]) == "a" and en_uzun(["abc", "de"]) == "abc"),
        (3, "ortada olan ən uzun söz; bərabər uzunluqda istənilən biri", lambda: en_uzun(["x", "yyy", "zz"]) == "yyy" and en_uzun(["ab", "cd", "e"]) in ("ab", "cd")),
    )
check("T9", 10, test_t9)


# ======================================================================
# Tapşırıq T10. Python-da ikiölçülü massiv (matris) (10 bal) — Nəzəri sual (yalnız 0 və ya 10 bal)
#
# 3 sətir və 4 sütundan ibarət, bütün elementləri 0 olan matrisi düzgün yaradan ifadə hansıdır (sətirlər bir-birindən asılı olmamalıdır)?
#   a) matris = [[0] * 4 for _ in range(3)]
#   b) matris = [[0] * 4] * 3
#   c) matris = [[0] * 3] * 4
#   d) matris = [0] * 12
# ======================================================================

cavab_T10 = ""      # düzgün variantın hərfi: "a", "b", "c" və ya "d"


def test_t10():
    assert _h(cavab_T10) == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb", "cavab düzgün deyil"
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
