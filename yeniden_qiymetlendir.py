# -*- coding: utf-8 -*-
"""
SDF 1 — nəticələrin müəllim kompüterində yenidən (müstəqil) qiymətləndirilməsi.

Portalda bal tələbənin brauzerində hesablanır. Bu skript bazadakı CAVABLARI
götürüb eyni testlərlə (grader_core.py + exam_data.js) yenidən yoxlayır və
brauzerin göndərdiyi balla müqayisə edir — saxtalaşdırılmış və ya Python
yüklənmədiyi üçün "qismən" yoxlanmış nəticələri aşkar edir.

İstifadə:
  python yeniden_qiymetlendir.py --password MÜƏLLİM_ŞİFRƏSİ       # Supabase-dən oxu
  python yeniden_qiymetlendir.py --json neticeler.json           # JSON faylından oxu
  python yeniden_qiymetlendir.py --password ... --csv yeni_ballar.csv

Tələb: supabase_setup.sql-dəki admin_list_submissions funksiyası bazada olmalıdır.
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request

from grader_core import load_harness

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env(env_path=os.path.join(HERE, ".env")):
    """Sadə .env oxuyucu (əlavə kitabxana tələb etmir)."""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v


load_env()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def load_exam_data(path=os.path.join(HERE, "exam_data.js")):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.index("=") + 1
    return json.loads(text[start:].strip().rstrip(";"))


def fetch_submissions(password, url, key):
    req = urllib.request.Request(
        f"{url}/rest/v1/rpc/admin_list_submissions",
        data=json.dumps({"p_password": password}).encode(),
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Supabase xətası {e.code}: {e.read().decode('utf-8', 'replace')}")


def regrade(submissions, data):
    harness = load_harness()
    rows = []
    for s in submissions:
        letter = str(s.get("variant", "")).replace("Variant", "").strip()
        variant = data["variants"].get(letter)
        answers = s.get("answers") or {}
        if not variant or not isinstance(answers, dict):
            continue
        res = harness.run_variant(variant["steps"], answers)["results"]
        scores = {t["id"]: res.get(t["id"], {}).get("pts", 0) for t in variant["tasks"]}
        new_total = sum(scores.values())
        if str(s.get("status", "")).startswith("KƏNARLAŞDIRILDI"):
            new_total = 0  # qaydaya görə kənarlaşdırılan tələbənin balı 0-dır
        rows.append({
            "sira": s.get("student_id", ""),
            "ad_soyad": s.get("student_name", ""),
            "qrup": s.get("student_group", ""),
            "variant": letter,
            "status": s.get("status", ""),
            "portal_bali": s.get("score", 0),
            "yeni_bal": new_total,
            "ferq": new_total - round(float(s.get("score") or 0)),
            **scores,
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description="SDF 1 nəticələrinin yenidən qiymətləndirilməsi")
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--password", default=ADMIN_PASSWORD, help="Müəllim şifrəsi (Supabase-dən oxumaq üçün, susmaya görə .env-dən)")
    src.add_argument("--json", help="Nəticələrin JSON faylı (siyahı)")
    ap.add_argument("--csv", help="Nəticəni CSV faylına yaz")
    ap.add_argument("--url", default=SUPABASE_URL, help="Supabase URL (susmaya görə .env-dən)")
    ap.add_argument("--key", default=SUPABASE_ANON_KEY, help="Supabase Anon Key (susmaya görə .env-dən)")
    args = ap.parse_args()

    data = load_exam_data()
    if args.json:
        with open(args.json, encoding="utf-8") as f:
            submissions = json.load(f)
    else:
        password = args.password or ADMIN_PASSWORD
        if not password:
            raise SystemExit("Xəta: Müəllim şifrəsi tələb olunur! --password arqumentini verin və ya .env faylında ADMIN_PASSWORD təyin edin.")
        if not args.url or not args.key:
            raise SystemExit("Xəta: Supabase URL və Anon Key tələb olunur! .env faylında SUPABASE_URL və SUPABASE_ANON_KEY təyin edin.")
        submissions = fetch_submissions(password, args.url, args.key)

    rows = regrade(submissions, data)
    print(f"{'Sıra':<6}{'Ad Soyad':<26}{'Var.':<6}{'Portal':>8}{'Yeni':>7}{'Fərq':>7}  Status")
    print("-" * 80)
    for r in rows:
        mark = "" if r["ferq"] == 0 else "   ⚠️"
        print(f"{str(r['sira']):<6}{str(r['ad_soyad'])[:25]:<26}{r['variant']:<6}{r['portal_bali']:>8}{r['yeni_bal']:>7}{r['ferq']:>+7}  {r['status']}{mark}")
    diff = sum(1 for r in rows if r["ferq"] != 0)
    print("-" * 80)
    print(f"Cəmi {len(rows)} nəticə; {diff} nəticədə portal balı ilə fərq var.")

    if args.csv and rows:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(rows)
        print(f"📄 CSV saxlanıldı: {args.csv}")


if __name__ == "__main__":
    main()
