# -*- coding: utf-8 -*-
"""
BMU — Verilənlərin strukturu və alqoritmlər, 2-ci kurs (SDF 1)
35 tələbənin 5 varianta (A–E) bərabər bölgüsü — hər varianta dəqiq 7 tələbə.

Qayda (index.html ilə EYNİ): variant = VARIANTLAR[(sira_no - 1) % 5]
  1, 6, 11, 16, 21, 26, 31 → A    2, 7, 12, 17, 22, 27, 32 → B
  3, 8, 13, 18, 23, 28, 33 → C    4, 9, 14, 19, 24, 29, 34 → D
  5, 10, 15, 20, 25, 30, 35 → E

Tələbə portala daxil olarkən "Sıra nömrəsi" xanasına bu siyahıdakı nömrəsini yazır.

İstifadə:
  python telebeler_35.py                  # şablon siyahı (Tələbə 1 ... Tələbə 35)
  python telebeler_35.py siyahi.txt       # hər sətirdə bir ad-soyad (35 sətir)
  python telebeler_35.py siyahi.txt --csv bolgu.csv   # bölgünü Excel üçün saxla
"""

import argparse
import csv
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VARIANTLAR = ["A", "B", "C", "D", "E"]
QRUP_OLCUSU = 35


def variant_for(sira_no):
    """Sıra nömrəsinə (1-dən başlayaraq) görə deterministik variant."""
    n = int(sira_no)
    if n < 1:
        raise ValueError("Sıra nömrəsi 1 və ya daha böyük olmalıdır")
    return VARIANTLAR[(n - 1) % len(VARIANTLAR)]


def build_roster(names=None):
    names = list(names or [f"Tələbə {i}" for i in range(1, QRUP_OLCUSU + 1)])
    if len(names) != QRUP_OLCUSU:
        raise SystemExit(f"Siyahıda {len(names)} ad var, {QRUP_OLCUSU} olmalıdır.")
    return [{"sira": i, "ad_soyad": name, "variant": variant_for(i)} for i, name in enumerate(names, start=1)]


def check_balance(roster):
    counts = {v: 0 for v in VARIANTLAR}
    for t in roster:
        counts[t["variant"]] += 1
    expected = len(roster) // len(VARIANTLAR)
    assert all(c == expected for c in counts.values()), f"Bölgü bərabər deyil: {counts}"
    return counts


def print_distribution(roster):
    print("=" * 52)
    print(f"{'Sıra':<6}{'Ad Soyad':<32}{'Variant':<10}")
    print("-" * 52)
    for t in roster:
        print(f"{t['sira']:<6}{t['ad_soyad']:<32}Variant {t['variant']}")
    print("=" * 52)

    counts = check_balance(roster)
    print("\nVariantlar üzrə tələbə sayı:")
    for v in VARIANTLAR:
        sira = ", ".join(str(t["sira"]) for t in roster if t["variant"] == v)
        print(f"  * Variant {v}: {counts[v]} tələbə  (sıra: {sira})")
    print(f"\n✅ Bölgü bərabərdir: {len(roster)} tələbə / {len(VARIANTLAR)} variant = {counts['A']} tələbə hər varianta")


def main():
    ap = argparse.ArgumentParser(description="35 tələbənin 5 varianta bərabər bölgüsü")
    ap.add_argument("siyahi", nargs="?", help="Hər sətirdə bir ad-soyad olan mətn faylı (UTF-8)")
    ap.add_argument("--csv", help="Bölgünü CSV faylına yaz")
    args = ap.parse_args()

    names = None
    if args.siyahi:
        with open(args.siyahi, encoding="utf-8-sig") as f:
            names = [line.strip() for line in f if line.strip()]

    roster = build_roster(names)
    print_distribution(roster)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["sira", "ad_soyad", "variant"], delimiter=";")
            w.writeheader()
            w.writerows(roster)
        print(f"📄 CSV saxlanıldı: {args.csv}")


if __name__ == "__main__":
    main()
