# -*- coding: utf-8 -*-
"""Qismən bal sınağı: bilərəkdən natamam həllər və onların gözlənilən balı (build_bank.py --verify istifadə edir)."""

PROBES = {
    1: ("def cem(lst):\n    return sum(lst)", 7),                                   # sum() istifadə olunub
    2: ("def en_boyuk(lst):\n    m = 0\n    for x in lst:\n        if x > m:\n            m = x\n    return m", 7),  # mənfilər səhv
    4: ("def orta(lst):\n    return sum(lst) / len(lst)", 7),                       # boş siyahıda ZeroDivisionError
    7: ("def cut_ededler(lst):\n    r = []\n    for x in lst:\n        if x % 2 == 0:\n            r.append(x)\n    return r", 7),
    10: ("def matris_yarat():\n    m = [[0] * 3] * 3\n    return m", 3),            # sətirlər eyni obyektdir
    13: ("def axtar(lst, x):\n    return lst.index(x)", 7),                         # tapılmayanda ValueError
    15: ("def sola_surusdur(lst):\n    return lst[1:] + [lst[0]]", 7),             # boş siyahıda IndexError
    16: ("def birlesdir(a, b):\n    return sorted(a + b)", 7),                      # sorted() istifadə olunub
    20: ("def ters(soz):\n    return soz[::-1]", 7),                                # stek istifadə olunmayıb
    22: ("class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, x):\n        self.items.append(x)\n"
         "    def pop(self):\n        return self.items.pop()", 7),               # boş stekdə IndexError
    24: ("from collections import deque\nclass Queue:\n    def __init__(self):\n        self.items = deque()\n"
         "    def enqueue(self, x):\n        self.items.append(x)\n    def dequeue(self):\n        return self.items.pop()", 0),  # LIFO — səhv
    29: ("class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n"
         "def sona_elave(head, data):\n    cur = head\n    while cur.next:\n        cur = cur.next\n    cur.next = Node(data)\n    return head", 7),
    30: ("def ll_cem(head):\n    s = 0\n    while head.next:\n        s += head.data\n        head = head.next\n    return s", 0),
}
