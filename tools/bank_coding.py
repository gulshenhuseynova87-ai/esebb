# -*- coding: utf-8 -*-
"""Verilənlərin_strukturu_suallar_telebeler_ucun.docx — praktik tapşırıqlar -> 30 kod yazma tapşırığı (5 kateqoriya).

Bütün kod tapşırıqları 0–10 bal arası QİSMƏN qiymətləndirilir: test `return grade((çəki, "hissə", lambda: şərt), ...)`
ilə bitir, hər ödənən hissənin çəkisi toplanır (çəkilərin cəmi 10-dur).

Testlərdə istifadə olunan köməkçilər (grader_core.py):
  _eq(a, b)        tolerant bərabərlik (list≈tuple, 1.0≈1)
  _ret(f, lst)     funksiyanı siyahının surəti ilə çağırır; None qaytarıb siyahını yerində dəyişibsə — dəyişmiş siyahı
  _as_list(x)      list/tuple/set/deque -> list
  _ll([..])        testlər üçün bağlı siyahı qurur;  _ll_list(head) -> [..]
  _capture(f, ..)  funksiyanın çap etdiyi (və qaytardığı) mətn;  _ints(mətn) -> mətndəki tam ədədlər
  _calls(T)        tələbə kodunda çağırılan funksiya/metod adları;  _nodes(T) — kodda olan AST düyün növləri
Testlərdə {T} tapşırığın id-si ilə əvəz olunur (məs. T3).
"""
import textwrap

CATEGORIES = {
    1: "List: əsas əməliyyatlar",
    2: "List: comprehension, matris və sinif",
    3: "List alqoritmləri",
    4: "Stek və növbə",
    5: "Bağlı siyahı",
}
CAT_SHORT = {1: "List · əsas", 2: "List · comprehension", 3: "List · alqoritm", 4: "Stek · növbə", 5: "Bağlı siyahı"}

CODING = {}


def task(num, cat, title, desc, starter, solution, test, partial=True):
    CODING[num] = dict(num=num, cat=cat, title=title, desc=textwrap.dedent(desc).strip(),
                       starter=starter.strip("\n"), solution=solution.strip("\n"),
                       test=textwrap.dedent(test).strip("\n"), partial=partial)


NODE = '''class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
'''

SAMPLE_LL = '''head = Node(10)
head.next = Node(20)
head.next.next = Node(30)'''

PRINT_LL = '''cur = head
while cur:
    print(cur.data, end=" -> ")
    cur = cur.next
print("None")'''


# ===================== Kateqoriya 1: List — əsas əməliyyatlar =====================
task(1, 1, "Siyahının cəmi (sum() olmadan)",
 """
 Siyahının elementlərinin cəmini **qaytaran** `cem(lst)` funksiyasını yazın.
 **`sum()` funksiyasından istifadə etməyin** — cəmi dövrlə hesablayın.
 Nümunə: `cem([1, 2, 3, 4])` → `10`; boş siyahı üçün `0`.
 """,
 """
def cem(lst):
    # sum() funksiyasından istifadə etmədən yazın
    pass


print(cem([1, 2, 3, 4]))   # 10 olmalıdır
""",
 """
def cem(lst):
    s = 0
    for x in lst:
        s += x
    return s
""",
 """
return grade(
    (4, "cem([1, 2, 3, 4]) 10 olmalıdır", lambda: _eq(cem([1, 2, 3, 4]), 10)),
    (3, "boş siyahı üçün 0, mənfi ədədlərlə də düzgün cəm", lambda: cem([]) == 0 and cem([]) is not None and _eq(cem([-5, 5, 7]), 7)),
    (3, "sum() istifadə olunmamalıdır (cəm dövrlə hesablanmalıdır)", lambda: "sum" not in _calls("{T}") and _eq(cem([2.5, 2.5, 10]), 15)),
)
""")

task(2, 1, "Ən böyük element (max() olmadan)",
 """
 Boş olmayan siyahının ən böyük elementini **qaytaran** `en_boyuk(lst)` funksiyasını yazın.
 **`max()` və `sorted()` funksiyalarından istifadə etməyin.**
 Nümunə: `en_boyuk([5, 3, 8, 1])` → `8`.
 """,
 """
def en_boyuk(lst):
    # max() funksiyasından istifadə etmədən yazın
    pass


print(en_boyuk([5, 3, 8, 1]))   # 8 olmalıdır
""",
 """
def en_boyuk(lst):
    m = lst[0]
    for x in lst[1:]:
        if x > m:
            m = x
    return m
""",
 """
return grade(
    (4, "en_boyuk([5, 3, 8, 1]) 8 olmalıdır", lambda: _eq(en_boyuk([5, 3, 8, 1]), 8)),
    (3, "mənfi ədədlər və tək elementli siyahı", lambda: _eq(en_boyuk([-7, -2, -9]), -2) and _eq(en_boyuk([4]), 4)),
    (3, "max()/sorted() istifadə olunmamalıdır", lambda: not (_calls("{T}") & {"max", "sorted", "sort"}) and _eq(en_boyuk([1, 9, 9, 2]), 9)),
)
""")

task(3, 1, "Müsbət ədədlərin sayı",
 """
 Siyahıda neçə müsbət ədəd (0-dan böyük) olduğunu **qaytaran** `musbet_say(lst)` funksiyasını yazın.
 Nümunə: `musbet_say([3, -1, 0, 5, -2])` → `2`.
 """,
 """
def musbet_say(lst):
    # buranı yazın
    pass


print(musbet_say([3, -1, 0, 5, -2]))   # 2 olmalıdır
""",
 """
def musbet_say(lst):
    say = 0
    for x in lst:
        if x > 0:
            say += 1
    return say
""",
 """
return grade(
    (4, "[3, -1, 0, 5, -2] üçün 2 olmalıdır", lambda: _eq(musbet_say([3, -1, 0, 5, -2]), 2)),
    (3, "boş və ya yalnız mənfi siyahı üçün 0", lambda: musbet_say([]) == 0 and musbet_say([-1, -2]) == 0 and musbet_say([]) is not None),
    (3, "0 müsbət sayılmamalıdır", lambda: _eq(musbet_say([0, 0, 1]), 1) and _eq(musbet_say([1, 2, 3]), 3)),
)
""")

task(4, 1, "Siyahının ədədi ortası",
 """
 Siyahının elementlərinin ədədi ortasını **qaytaran** `orta(lst)` funksiyasını yazın. Boş siyahı üçün `0` qaytarsın.
 Nümunə: `orta([2, 4, 6, 8])` → `5.0`.
 """,
 """
def orta(lst):
    # buranı yazın
    pass


print(orta([2, 4, 6, 8]))   # 5.0 olmalıdır
""",
 """
def orta(lst):
    if len(lst) == 0:
        return 0
    return sum(lst) / len(lst)
""",
 """
return grade(
    (4, "orta([2, 4, 6, 8]) 5.0 olmalıdır", lambda: _is_num(orta([2, 4, 6, 8])) and _eq(orta([2, 4, 6, 8]), 5.0)),
    (3, "boş siyahı üçün 0 qaytarılmalıdır (xəta yox)", lambda: _is_num(orta([])) and orta([]) == 0),
    (3, "kəsr nəticə: orta([1, 2]) 1.5 olmalıdır", lambda: _is_num(orta([1, 2])) and _eq(orta([1, 2]), 1.5) and _eq(orta([-3, 3]), 0)),
)
""")

task(5, 1, "Siyahını tərsinə çevirmək",
 """
 Siyahını tərsinə çevirib **qaytaran** `tersine(lst)` funksiyasını yazın (istənilən üsulla: kəsik `[::-1]`, `reverse()` və ya dövr).
 Nümunə: `tersine([1, 2, 3, 4, 5])` → `[5, 4, 3, 2, 1]`.
 """,
 """
def tersine(lst):
    # buranı yazın
    pass


print(tersine([1, 2, 3, 4, 5]))   # [5, 4, 3, 2, 1] olmalıdır
""",
 """
def tersine(lst):
    return lst[::-1]
""",
 """
return grade(
    (4, "[1, 2, 3, 4, 5] → [5, 4, 3, 2, 1]", lambda: _eq(_as_list(_ret(tersine, [1, 2, 3, 4, 5])), [5, 4, 3, 2, 1])),
    (3, "cüt sayda element: [7, 8] → [8, 7]", lambda: _eq(_as_list(_ret(tersine, [7, 8])), [8, 7])),
    (3, "sətirlərdən ibarət siyahı: ['a', 'b', 'c'] → ['c', 'b', 'a']", lambda: _eq(_as_list(_ret(tersine, ["a", "b", "c"])), ["c", "b", "a"])),
)
""")

task(6, 1, "Ən kiçik və ən böyük element",
 """
 Siyahının ən kiçik və ən böyük elementini `min()` və `max()` funksiyaları ilə tapıb **`(en_kicik, en_boyuk)` cütü kimi qaytaran**
 `min_max(lst)` funksiyasını yazın.
 Nümunə: `min_max([5, 3, 8, 1])` → `(1, 8)`.
 """,
 """
def min_max(lst):
    # buranı yazın
    pass


print(min_max([5, 3, 8, 1]))   # (1, 8) olmalıdır
""",
 """
def min_max(lst):
    return min(lst), max(lst)
""",
 """
return grade(
    (4, "min_max([5, 3, 8, 1]) (1, 8) olmalıdır", lambda: _eq(_as_list(min_max([5, 3, 8, 1])), [1, 8])),
    (3, "mənfi ədədlər: [-4, 0, -9] → (-9, 0)", lambda: _eq(_as_list(min_max([-4, 0, -9])), [-9, 0])),
    (3, "tək elementli siyahı: [6] → (6, 6)", lambda: _eq(_as_list(min_max([6])), [6, 6])),
)
""")


# ===================== Kateqoriya 2: List — comprehension, matris, sinif =====================
task(7, 2, "Cüt ədədlər (list comprehension)",
 """
 Siyahıdakı cüt ədədləri **list comprehension** vasitəsilə yeni siyahıya seçib **qaytaran** `cut_ededler(lst)` funksiyasını yazın.
 Nümunə: `cut_ededler([1, 2, 3, 4, 5, 6])` → `[2, 4, 6]`.
 """,
 """
def cut_ededler(lst):
    # list comprehension ilə yazın
    pass


print(cut_ededler([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))   # [2, 4, 6, 8, 10] olmalıdır
""",
 """
def cut_ededler(lst):
    return [x for x in lst if x % 2 == 0]
""",
 """
return grade(
    (4, "[1..10] → [2, 4, 6, 8, 10]", lambda: _eq(_as_list(cut_ededler(list(range(1, 11)))), [2, 4, 6, 8, 10])),
    (3, "mənfi cüt ədədlər və 0 da seçilməlidir", lambda: _eq(_as_list(cut_ededler([-4, -3, 0, 7])), [-4, 0])),
    (3, "list comprehension istifadə olunmalıdır", lambda: "ListComp" in _nodes("{T}") and _eq(_as_list(cut_ededler([1, 3])), [])),
)
""")

task(8, 2, "Kvadratlar siyahısı (list comprehension)",
 """
 1-dən `n`-ə qədər (n daxil) ədədlərin kvadratlarından ibarət siyahını **list comprehension** ilə yaradıb **qaytaran**
 `kvadratlar(n)` funksiyasını yazın.
 Nümunə: `kvadratlar(10)` → `[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]`.
 """,
 """
def kvadratlar(n):
    # list comprehension ilə yazın
    pass


print(kvadratlar(10))   # [1, 4, 9, ..., 100] olmalıdır
""",
 """
def kvadratlar(n):
    return [x ** 2 for x in range(1, n + 1)]
""",
 """
return grade(
    (4, "kvadratlar(10) → [1, 4, 9, ..., 100]", lambda: _eq(_as_list(kvadratlar(10)), [x * x for x in range(1, 11)])),
    (3, "n daxil olmalıdır: kvadratlar(3) → [1, 4, 9]; kvadratlar(1) → [1]", lambda: _eq(_as_list(kvadratlar(3)), [1, 4, 9]) and _eq(_as_list(kvadratlar(1)), [1])),
    (3, "list comprehension istifadə olunmalıdır", lambda: "ListComp" in _nodes("{T}") and _eq(_as_list(kvadratlar(0)), [])),
)
""")

task(9, 2, "Yalnız müsbət ədədləri saxlamaq",
 """
 Siyahıdan mənfi ədədləri çıxarıb **yalnız müsbət ədədlərdən** ibarət yeni siyahı **qaytaran** `yalniz_musbet(lst)` funksiyasını yazın.
 Nümunə: `yalniz_musbet([3, -1, 4, -5, 2])` → `[3, 4, 2]`.
 """,
 """
def yalniz_musbet(lst):
    # buranı yazın
    pass


print(yalniz_musbet([3, -1, 4, -5, 2]))   # [3, 4, 2] olmalıdır
""",
 """
def yalniz_musbet(lst):
    return [x for x in lst if x > 0]
""",
 """
return grade(
    (4, "[3, -1, 4, -5, 2] → [3, 4, 2]", lambda: _eq(_as_list(_ret(yalniz_musbet, [3, -1, 4, -5, 2])), [3, 4, 2])),
    (3, "elementlərin sırası saxlanmalıdır: [9, -1, 1] → [9, 1]", lambda: _eq(_as_list(_ret(yalniz_musbet, [9, -1, 1])), [9, 1])),
    (3, "0 müsbət deyil; mənfi siyahı üçün []", lambda: _eq(_as_list(_ret(yalniz_musbet, [0, -2, 5])), [5]) and _eq(_as_list(_ret(yalniz_musbet, [-1, -2])), [])),
)
""")

task(10, 2, "3 × 3 sıfır matrisi",
 """
 Bütün elementləri `0` olan `3 × 3` ölçülü matris (siyahılar siyahısı) yaradın, onun **ortadakı** elementinə `5` yazın və
 matrisi **qaytaran** `matris_yarat()` funksiyasını yazın. Sətirlər bir-birindən asılı olmamalıdır
 (`[[0] * 3] * 3` səhvdir!).
 """,
 """
def matris_yarat():
    # buranı yazın
    pass


for setir in matris_yarat() or []:
    print(setir)
# [0, 0, 0]
# [0, 5, 0]
# [0, 0, 0]
""",
 """
def matris_yarat():
    m = [[0] * 3 for _ in range(3)]
    m[1][1] = 5
    return m
""",
 """
return grade(
    (3, "3 sətir və hər sətirdə 3 element olmalıdır", lambda: len(matris_yarat()) == 3 and all(len(s) == 3 for s in matris_yarat())),
    (4, "ortadakı element 5, qalanları 0 olmalıdır", lambda: _eq(matris_yarat(), [[0, 0, 0], [0, 5, 0], [0, 0, 0]])),
    (3, "sətirlər ayrı-ayrı siyahılar olmalıdır ([[0] * 3] * 3 səhvdir)", lambda: len({id(s) for s in matris_yarat()}) == 3),
)
""")

task(11, 2, "Point sinfi",
 """
 `Point` sinfini yazın: konstruktor `x` və `y` atributlarını yaratsın, `show()` metodu isə onları çap etsin
 (məsələn: `x = 3, y = 4`; çap formatı yoxlanmır, yalnız qiymətlər).
 """,
 """
class Point:
    # buranı yazın
    pass


p = Point(3, 4)
p.show()   # x = 3, y = 4
""",
 """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def show(self):
        print(f"x = {self.x}, y = {self.y}")
""",
 """
return grade(
    (3, "Point(3, 4) obyekti yaradılmalıdır", lambda: Point(3, 4) is not None),
    (4, "x və y atributları düzgün saxlanmalıdır", lambda: Point(3, 4).x == 3 and Point(3, 4).y == 4 and Point(-1, 7).y == 7),
    (3, "show() x və y qiymətlərini çap etməlidir", lambda: _ints(_capture(Point(3, 4).show)) == [3, 4] and _ints(_capture(Point(10, 20).show)) == [10, 20]),
)
""")

task(12, 2, "İki siyahını birləşdirib sıralamaq",
 """
 İki siyahını birləşdirib **artan sıra ilə** düzülmüş yeni siyahı **qaytaran** `birlesdir_sirala(a, b)` funksiyasını yazın
 (`sorted()` və ya `sort()` istifadə edə bilərsiniz).
 Nümunə: `birlesdir_sirala([3, 1, 4], [2, 5])` → `[1, 2, 3, 4, 5]`.
 """,
 """
def birlesdir_sirala(a, b):
    # buranı yazın
    pass


print(birlesdir_sirala([3, 1, 4], [2, 5]))   # [1, 2, 3, 4, 5] olmalıdır
""",
 """
def birlesdir_sirala(a, b):
    return sorted(a + b)
""",
 """
return grade(
    (4, "[3, 1, 4] və [2, 5] → [1, 2, 3, 4, 5]", lambda: _eq(_as_list(birlesdir_sirala([3, 1, 4], [2, 5])), [1, 2, 3, 4, 5])),
    (3, "təkrarlanan elementlər saxlanmalıdır: [2, 2] və [1] → [1, 2, 2]", lambda: _eq(_as_list(birlesdir_sirala([2, 2], [1])), [1, 2, 2])),
    (3, "boş siyahı ilə: [] və [9, -1] → [-1, 9]", lambda: _eq(_as_list(birlesdir_sirala([], [9, -1])), [-1, 9])),
)
""")


# ===================== Kateqoriya 3: List alqoritmləri =====================
task(13, 3, "Siyahıda xətti axtarış",
 """
 Siyahıda verilmiş elementi axtaran `axtar(lst, x)` funksiyasını yazın: element tapılsa onun (ilk rast gəlinən) **indeksini**,
 tapılmasa `-1` qaytarsın.
 Nümunə: `axtar([4, 5, 6, 8], 6)` → `2`; `axtar([4, 5, 6, 8], 7)` → `-1`.
 """,
 """
def axtar(lst, x):
    # buranı yazın
    pass


print(axtar([4, 5, 6, 8], 6))   # 2 olmalıdır
print(axtar([4, 5, 6, 8], 7))   # -1 olmalıdır
""",
 """
def axtar(lst, x):
    for i in range(len(lst)):
        if lst[i] == x:
            return i
    return -1
""",
 """
return grade(
    (4, "axtar([4, 5, 6, 8], 6) 2 olmalıdır", lambda: axtar([4, 5, 6, 8], 6) == 2),
    (3, "tapılmayan element və boş siyahı üçün -1", lambda: axtar([4, 5, 6, 8], 7) == -1 and axtar([], 1) == -1),
    (3, "təkrarlanan elementdə ilk indeks; sonuncu element də tapılmalıdır", lambda: axtar([3, 1, 3], 3) == 0 and axtar([9, 8, 7], 7) == 2),
)
""")

task(14, 3, "Təkrarlanan elementləri silmək",
 """
 Siyahıdakı təkrarlanan elementləri silib, hər elementi bir dəfə saxlayan siyahı **qaytaran** `unikal(lst)` funksiyasını yazın
 (`set` istifadə edə bilərsiniz; elementlərin sırası yoxlanmır).
 Nümunə: `unikal([1, 2, 2, 3, 1])` → `[1, 2, 3]`.
 """,
 """
def unikal(lst):
    # buranı yazın
    pass


print(unikal([1, 2, 2, 3, 1]))   # [1, 2, 3] olmalıdır
""",
 """
def unikal(lst):
    return list(set(lst))
""",
 """
return grade(
    (4, "[1, 2, 2, 3, 1] → 1, 2, 3 (hər biri bir dəfə)", lambda: sorted(_as_list(_ret(unikal, [1, 2, 2, 3, 1]))) == [1, 2, 3]),
    (3, "boş siyahı → []; [5, 5, 5] → [5]", lambda: _as_list(_ret(unikal, [])) == [] and _as_list(_ret(unikal, [5, 5, 5])) == [5]),
    (3, "sətirlər: ['a', 'b', 'a', 'c', 'b'] → a, b, c", lambda: sorted(_as_list(_ret(unikal, ["a", "b", "a", "c", "b"]))) == ["a", "b", "c"]),
)
""")

task(15, 3, "Siyahını 1 mövqe sola sürüşdürmək",
 """
 Siyahının elementlərini 1 mövqe sola sürüşdürən (birinci element sona keçir) və nəticəni **qaytaran** `sola_surusdur(lst)`
 funksiyasını yazın. Boş siyahı boş qalmalıdır.
 Nümunə: `[1, 2, 3, 4]` → `[2, 3, 4, 1]`.
 """,
 """
def sola_surusdur(lst):
    # buranı yazın
    pass


print(sola_surusdur([1, 2, 3, 4]))   # [2, 3, 4, 1] olmalıdır
""",
 """
def sola_surusdur(lst):
    if not lst:
        return lst
    return lst[1:] + lst[:1]
""",
 """
return grade(
    (4, "[1, 2, 3, 4] → [2, 3, 4, 1]", lambda: _eq(_as_list(_ret(sola_surusdur, [1, 2, 3, 4])), [2, 3, 4, 1])),
    (3, "[5, 6] → [6, 5]; [7] → [7]", lambda: _eq(_as_list(_ret(sola_surusdur, [5, 6])), [6, 5]) and _eq(_as_list(_ret(sola_surusdur, [7])), [7])),
    (3, "boş siyahı xəta verməməli, [] qalmalıdır; sətirlər də işləməlidir", lambda: _as_list(_ret(sola_surusdur, [])) == [] and _eq(_as_list(_ret(sola_surusdur, ["a", "b", "c"])), ["b", "c", "a"])),
)
""")

task(16, 3, "İki sıralanmış siyahını birləşdirmək (sorted() olmadan)",
 """
 Artan sıra ilə düzülmüş iki siyahını bir sıralanmış siyahıda birləşdirən `birlesdir(a, b)` funksiyasını yazın.
 **`sorted()` və `sort()` istifadə etməyin** — iki göstərici (`i`, `j`) ilə birləşdirin.
 Nümunə: `birlesdir([1, 4, 7], [2, 3, 8])` → `[1, 2, 3, 4, 7, 8]`.
 """,
 """
def birlesdir(a, b):
    # sorted() istifadə etmədən yazın
    pass


print(birlesdir([1, 4, 7], [2, 3, 8]))   # [1, 2, 3, 4, 7, 8] olmalıdır
""",
 """
def birlesdir(a, b):
    i, j = 0, 0
    netice = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            netice.append(a[i])
            i += 1
        else:
            netice.append(b[j])
            j += 1
    netice.extend(a[i:])
    netice.extend(b[j:])
    return netice
""",
 """
return grade(
    (4, "[1, 4, 7] və [2, 3, 8] → [1, 2, 3, 4, 7, 8]", lambda: _eq(_as_list(birlesdir([1, 4, 7], [2, 3, 8])), [1, 2, 3, 4, 7, 8])),
    (3, "boş siyahı və bərabər elementlər", lambda: _eq(_as_list(birlesdir([], [1, 2])), [1, 2]) and _eq(_as_list(birlesdir([5], [])), [5]) and _eq(_as_list(birlesdir([1, 3], [1, 2])), [1, 1, 2, 3])),
    (3, "sorted()/sort() istifadə olunmamalıdır", lambda: not (_calls("{T}") & {"sorted", "sort"}) and _eq(_as_list(birlesdir([10], [1, 20])), [1, 10, 20])),
)
""")

task(17, 3, "İç-içə siyahını düzləşdirmək",
 """
 İç-içə siyahını (siyahılar siyahısını) düz siyahıya çevirib **qaytaran** `duzlesdir(lst)` funksiyasını yazın.
 Nümunə: `[[1, 2], [3], [4, 5, 6]]` → `[1, 2, 3, 4, 5, 6]`.
 """,
 """
def duzlesdir(lst):
    # buranı yazın
    pass


print(duzlesdir([[1, 2], [3], [4, 5, 6]]))   # [1, 2, 3, 4, 5, 6] olmalıdır
""",
 """
def duzlesdir(lst):
    netice = []
    for alt in lst:
        for x in alt:
            netice.append(x)
    return netice
""",
 """
return grade(
    (4, "[[1, 2], [3], [4, 5, 6]] → [1, 2, 3, 4, 5, 6]", lambda: _eq(_as_list(duzlesdir([[1, 2], [3], [4, 5, 6]])), [1, 2, 3, 4, 5, 6])),
    (3, "boş siyahı → []; [[], [1]] → [1]", lambda: _as_list(duzlesdir([])) == [] and _eq(_as_list(duzlesdir([[], [1]])), [1])),
    (3, "sətirlər: [['a'], ['b', 'c']] → ['a', 'b', 'c']", lambda: _eq(_as_list(duzlesdir([["a"], ["b", "c"]])), ["a", "b", "c"])),
)
""")

task(18, 3, "Ən uzun söz",
 """
 Sözlər siyahısında ən uzun sözü **qaytaran** `en_uzun(sozler)` funksiyasını yazın.
 Nümunə: `en_uzun(["ev", "kitab", "qələm", "kompüter"])` → `"kompüter"`.
 """,
 """
def en_uzun(sozler):
    # buranı yazın
    pass


print(en_uzun(["ev", "kitab", "qələm", "kompüter"]))   # kompüter olmalıdır
""",
 """
def en_uzun(sozler):
    uzun = sozler[0]
    for s in sozler:
        if len(s) > len(uzun):
            uzun = s
    return uzun
""",
 """
return grade(
    (4, "['ev', 'kitab', 'qələm', 'kompüter'] → 'kompüter'", lambda: en_uzun(["ev", "kitab", "qələm", "kompüter"]) == "kompüter"),
    (3, "tək söz və birinci yerdə olan ən uzun söz", lambda: en_uzun(["a"]) == "a" and en_uzun(["abc", "de"]) == "abc"),
    (3, "ortada olan ən uzun söz; bərabər uzunluqda istənilən biri", lambda: en_uzun(["x", "yyy", "zz"]) == "yyy" and en_uzun(["ab", "cd", "e"]) in ("ab", "cd")),
)
""")


# ===================== Kateqoriya 4: Stek və növbə =====================
task(19, 4, "list ilə stek: append() və pop()",
 """
 `list` ilə stek yaradın: `stek` siyahısına 1, 2, 3 ədədlərini `append()` ilə əlavə edin, sonra `pop()` ilə bir element
 çıxarıb onu `cixan` dəyişəninə yazın. Stekdə nə qalır?
 """,
 """
stek = []
# 1, 2, 3 ədədlərini append() ilə əlavə edin:

# pop() ilə bir element çıxarıb cixan dəyişəninə yazın:
cixan = None

print(stek, cixan)   # [1, 2] 3 olmalıdır
""",
 """
stek = []
stek.append(1)
stek.append(2)
stek.append(3)
cixan = stek.pop()

print(stek, cixan)
""",
 """
return grade(
    (4, "LIFO: son əlavə olunan 3 çıxmalıdır (cixan = 3)", lambda: cixan == 3),
    (3, "stekdə [1, 2] qalmalıdır", lambda: _as_list(stek) == [1, 2]),
    (3, "append() və pop() istifadə olunmalıdır", lambda: {"append", "pop"} <= _calls("{T}")),
)
""")

task(20, 4, "Stek ilə sözü tərsinə çevirmək",
 """
 Stekdən istifadə edərək `ters(soz)` funksiyasını yazın: hərfləri `append()` ilə stekə əlavə edin, sonra `pop()` ilə
 çıxararaq tərs sözü qurun və **qaytarın**.
 Nümunə: `ters("Python")` → `"nohtyP"`.
 """,
 """
def ters(soz):
    stek = []
    # buranı yazın
    pass


print(ters("Python"))   # nohtyP olmalıdır
""",
 """
def ters(soz):
    stek = []
    for ch in soz:
        stek.append(ch)
    netice = ""
    while stek:
        netice += stek.pop()
    return netice
""",
 """
return grade(
    (4, "ters('Python') 'nohtyP' olmalıdır", lambda: ters("Python") == "nohtyP"),
    (3, "boş sətir və tək hərf", lambda: ters("") == "" and ters("a") == "a"),
    (3, "stekdən istifadə olunmalıdır (append() və pop())", lambda: "pop" in _calls("{T}") and ters("abc") == "cba"),
)
""")

task(21, 4, "Stekin boş olub-olmadığını yoxlamaq",
 """
 Stekin (siyahının) boş olub-olmadığını yoxlayan `is_empty(stek)` funksiyasını yazın: boşdursa `True`, əks halda `False` qaytarsın.
 Nümunə: `is_empty([])` → `True`, `is_empty([1, 2])` → `False`.
 """,
 """
def is_empty(stek):
    # buranı yazın
    pass


print(is_empty([]))       # True olmalıdır
print(is_empty([1, 2]))   # False olmalıdır
""",
 """
def is_empty(stek):
    return len(stek) == 0
""",
 """
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
""")

task(22, 4, "Stack sinfi: push və pop",
 """
 Sadə `Stack` sinfini tamamlayın: `push(x)` elementi stekin üstünə əlavə etsin, `pop()` isə üstdəki elementi çıxarıb qaytarsın.
 Stek boşdursa, `pop()` xəta vermədən `None` qaytarsın.
 """,
 """
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
""",
 """
class Stack:
    def __init__(self):
        self.items = []

    def push(self, x):
        self.items.append(x)

    def pop(self):
        if not self.items:
            return None
        return self.items.pop()
""",
 """
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
""")

task(23, 4, "collections.deque ilə növbə",
 """
 `collections.deque` ilə boş növbə (`q`) yaradın, ona `"A"`, `"B"`, `"C"` elementlərini əlavə edin və `popleft()` ilə bir element
 çıxarıb onu `cixan` dəyişəninə yazın. Hansı element çıxır?
 """,
 """
from collections import deque

q = deque()
# "A", "B", "C" elementlərini əlavə edin:

# popleft() ilə bir element çıxarıb cixan dəyişəninə yazın:
cixan = None

print(cixan, q)
""",
 """
from collections import deque

q = deque()
q.append("A")
q.append("B")
q.append("C")
cixan = q.popleft()

print(cixan, q)
""",
 """
from collections import deque as _dq
return grade(
    (4, "FIFO: ilk əlavə olunan 'A' çıxmalıdır (cixan = 'A')", lambda: cixan == "A"),
    (3, "növbədə ['B', 'C'] qalmalıdır", lambda: _as_list(q) == ["B", "C"]),
    (3, "q collections.deque olmalıdır", lambda: isinstance(q, _dq) and len(q) == 2),
)
""")

task(24, 4, "Queue sinfi: enqueue və dequeue",
 """
 `deque` əsasında sadə `Queue` sinfini tamamlayın: `enqueue(x)` elementi növbənin sonuna əlavə etsin, `dequeue()` isə öndəki
 elementi çıxarıb qaytarsın (FIFO). Növbə boşdursa, `dequeue()` xəta vermədən `None` qaytarsın.
 """,
 """
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
""",
 """
from collections import deque


class Queue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, x):
        self.items.append(x)

    def dequeue(self):
        if not self.items:
            return None
        return self.items.popleft()
""",
 """
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
""")

task(25, 4, "Stek və növbədən çıxan element",
 """
 1, 2, 3 ədədləri əvvəlcə stekə (`list`), sonra növbəyə (`deque`) əlavə olunur. Hər birindən bir element çıxarılır.
 `stek_ve_novbe()` funksiyasını yazın: bu əməliyyatları yerinə yetirib **`(stekden_cixan, novbeden_cixan)` cütünü qaytarsın**.
 """,
 """
from collections import deque


def stek_ve_novbe():
    stek, novbe = [], deque()
    # 1, 2, 3 ədədlərini hər ikisinə əlavə edin və hər birindən bir element çıxarın
    pass


print(stek_ve_novbe())   # (3, 1) olmalıdır
""",
 """
from collections import deque


def stek_ve_novbe():
    stek, novbe = [], deque()
    for x in [1, 2, 3]:
        stek.append(x)
        novbe.append(x)
    return stek.pop(), novbe.popleft()
""",
 """
def cut():
    r = _as_list(stek_ve_novbe())
    return isinstance(r, list) and len(r) == 2
return grade(
    (3, "nəticə iki elementli cüt olmalıdır", cut),
    (4, "stekdən 3 çıxmalıdır (LIFO)", lambda: _as_list(stek_ve_novbe())[0] == 3),
    (3, "növbədən 1 çıxmalıdır (FIFO)", lambda: _as_list(stek_ve_novbe())[1] == 1 and "popleft" in _calls("{T}")),
)
""")


# ===================== Kateqoriya 5: Bağlı siyahı =====================
task(26, 5, "Node sinfi və 10 → 20 → 30 bağlı siyahısı",
 """
 1. `Node` sinfini tamamlayın: konstruktor `data` və `next` sahələrini yaratsın (`next` əvvəlcə `None`).
 2. `Node` sinfindən istifadə edərək 10 → 20 → 30 bağlı siyahısını qurun; siyahının başı `head` dəyişənində olsun.
 """,
 """
class Node:
    def __init__(self, data):
        # data və next sahələrini yaradın
        pass


# 10 -> 20 -> 30 bağlı siyahısını qurun (baş düyün: head):
head = None

""" + PRINT_LL + "   # 10 -> 20 -> 30 -> None olmalıdır",
 NODE + "\n\n" + SAMPLE_LL + "\n\n" + PRINT_LL,
 """
return grade(
    (3, "Node(5).data 5, Node(5).next None olmalıdır", lambda: getattr(Node(5), "data", "yox") == 5 and getattr(Node(5), "next", "yox") is None),
    (4, "head-dən başlayaraq 10, 20, 30 olmalıdır", lambda: _ll_list(head, 10)[:3] == [10, 20, 30]),
    (3, "sonuncu düyünün next-i None; bütün düyünlər Node olmalıdır",
     lambda: head.next.next.next is None and all(isinstance(x, Node) for x in (head, head.next, head.next.next))),
)
""")

task(27, 5, "Bağlı siyahının elementlərini çap etmək",
 """
 Bağlı siyahının bütün elementlərini başdan sona ardıcıllıqla **çap edən** `cap_et(head)` funksiyasını yazın
 (məsələn: `10 -> 20 -> 30 -> None`; çap formatı yoxlanmır, yalnız qiymətlər və onların sırası).
 Boş siyahıda (`head = None`) xəta verməməlidir.
 """,
 NODE + "\n\ndef cap_et(head):\n    # buranı yazın\n    pass\n\n\n" + SAMPLE_LL + "\ncap_et(head)   # 10 -> 20 -> 30 -> None",
 NODE + "\n\ndef cap_et(head):\n    cur = head\n    while cur:\n        print(cur.data, end=\" -> \")\n        cur = cur.next\n    print(\"None\")",
 """
return grade(
    (4, "10 -> 20 -> 30 siyahısı üçün 10, 20, 30 çap olunmalıdır", lambda: _ints(_capture(cap_et, _ll([10, 20, 30]))) == [10, 20, 30]),
    (3, "başqa siyahı: 5 -> 1 üçün 5, 1", lambda: _ints(_capture(cap_et, _ll([5, 1]))) == [5, 1]),
    (3, "tək düyünlü siyahı; boş siyahıda xəta olmamalıdır", lambda: _ints(_capture(cap_et, _ll([7]))) == [7] and _ints(_capture(cap_et, None)) == []),
)
""")

task(28, 5, "Bağlı siyahıda axtarış",
 """
 Bağlı siyahıda verilmiş qiyməti axtaran `siyahida_var(head, x)` funksiyasını yazın: qiymət varsa `True`, yoxdursa `False`
 qaytarsın. Boş siyahı (`head = None`) üçün `False`.
 """,
 NODE + "\n\ndef siyahida_var(head, x):\n    # buranı yazın\n    pass\n\n\n" + SAMPLE_LL
 + "\nprint(siyahida_var(head, 20))   # True olmalıdır\nprint(siyahida_var(head, 99))   # False olmalıdır",
 NODE + "\n\ndef siyahida_var(head, x):\n    cur = head\n    while cur:\n        if cur.data == x:\n            return True\n        cur = cur.next\n    return False",
 """
return grade(
    (4, "10 -> 20 -> 30 siyahısında 20 tapılmalıdır (True)", lambda: siyahida_var(_ll([10, 20, 30]), 20) == True),
    (3, "99 yoxdur (False); sonuncu element 30 tapılmalıdır", lambda: siyahida_var(_ll([10, 20, 30]), 99) is not None and siyahida_var(_ll([10, 20, 30]), 99) == False and siyahida_var(_ll([10, 20, 30]), 30) == True),
    (3, "boş siyahı üçün False; tək düyünlü siyahı", lambda: siyahida_var(None, 5) is not None and siyahida_var(None, 5) == False and siyahida_var(_ll([7]), 7) == True),
)
""")

task(29, 5, "Bağlı siyahının sonuna düyün əlavə etmək",
 """
 Bağlı siyahının sonuna `data` qiymətli yeni düyün əlavə edən və siyahının başını (`head`) **qaytaran**
 `sona_elave(head, data)` funksiyasını yazın. Siyahı boşdursa (`head = None`), yeni düyün siyahının başı olur.
 """,
 NODE + "\n\ndef sona_elave(head, data):\n    # buranı yazın\n    pass\n\n\n" + SAMPLE_LL
 + "\nhead = sona_elave(head, 40)\n\n" + PRINT_LL + "   # 10 -> 20 -> 30 -> 40 -> None olmalıdır",
 NODE + "\n\ndef sona_elave(head, data):\n    yeni = Node(data)\n    if head is None:\n        return yeni\n    cur = head\n"
 "    while cur.next:\n        cur = cur.next\n    cur.next = yeni\n    return head",
 """
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
""")

task(30, 5, "Bağlı siyahının elementlərinin cəmi",
 """
 Bağlı siyahının bütün elementlərinin cəmini **qaytaran** `ll_cem(head)` funksiyasını yazın.
 Boş siyahı (`head = None`) üçün `0`.
 """,
 NODE + "\n\ndef ll_cem(head):\n    # buranı yazın\n    pass\n\n\n" + SAMPLE_LL + "\nprint(ll_cem(head))   # 60 olmalıdır",
 NODE + "\n\ndef ll_cem(head):\n    s = 0\n    cur = head\n    while cur:\n        s += cur.data\n        cur = cur.next\n    return s",
 """
return grade(
    (4, "10 -> 20 -> 30 üçün cəm 60 olmalıdır", lambda: _eq(ll_cem(_ll([10, 20, 30])), 60)),
    (3, "boş siyahı üçün 0; tək düyünlü [7] üçün 7", lambda: ll_cem(None) == 0 and ll_cem(None) is not None and _eq(ll_cem(_ll([7])), 7)),
    (3, "mənfi qiymətlər: -5 -> 5 -> 1 üçün 1", lambda: _eq(ll_cem(_ll([-5, 5, 1])), 1)),
)
""")
