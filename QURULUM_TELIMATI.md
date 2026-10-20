# 🚀 SDF 1: Onlayn İmtahan Portalı (BMU — Verilənlərin strukturu və alqoritmlər, 2-ci kurs)

Brauzerdə işləyən, köçürməyə qarşı qorunan imtahan sistemi. Tələbənin Python kodu brauzerdə **real Python** (Pyodide) ilə bank testləri vasitəsilə yoxlanılır. Kod redaktoru Colab / Jupyter kimi işləyir: girinti avtomatik qoyulur, sintaksis rənglənir, «▶ İşə sal» (Shift+Enter) xananı icra edir, «Kodu yoxla» testlərlə yoxlayır.

**İmtahan strukturu (hər variantda):** 10 tapşırıq = **4 nəzəri** (Hissə 1) + **6 praktiki** (Hissə 2, 5 kateqoriyanın hər birindən ən azı 1), hər biri 10 bal, cəmi 100 bal. Tapşırıqların sırası hər variantda qarışdırılıb, heç bir sual iki variantda təkrarlanmır. Nəzəri suallar **0 və ya 10 bal**, bütün kod tapşırıqları isə **hissə-hissə (0–10 bal arası)** qiymətləndirilir. Bölgü cədvəli: `sual_banki_xeritesi.md`.

---

## 📁 Fayllar

| Fayl | Təyinatı |
|---|---|
| `index.html` | **Tələbə portalı** — giriş yalnız ad-soyad və sıra nömrəsi ilə; tam ekran, 3 xəbərdarlıq, Copy/Paste/DevTools bloku, «Kodu yoxla» düyməsi |
| `admin.html` | **Müəllim paneli** — müəllim şifrəsi ilə, canlı nəticələr, pozuntu jurnalı, Excel ixracı |
| `exam_data.js` | 5 variantın sualları, başlanğıc kodları və testləri (**avtomatik yaradılır**) |
| `sual_banki_xeritesi.md` | Hansı variantda hansı sualın olduğu, qiymətləndirmə növü (**avtomatik yaradılır**) |
| `variant_A.py` … `variant_E.py` | `python variant_X.py` ilə işləyən müstəqil imtahan faylları (**avtomatik yaradılır**) |
| `telebeler_35.py` | 35 tələbənin 5 varianta bərabər bölgüsü (hər varianta 7 nəfər) |
| `yeniden_qiymetlendir.py` | Bazadakı cavabların müəllim kompüterində müstəqil yenidən yoxlanması |
| `grader_core.py` | Yoxlama mühərriki (brauzer və `yeniden_qiymetlendir.py` eyni kodu işlədir) |
| `tools/build_bank.py` | Sual bankından `exam_data.js`, `variant_*.py` və xəritəni yaradan generator |
| `tools/bank_theory.py` | Hissə 1: 20 nəzəri mövzu (hər biri 1 düzgün + 3 səhv cavab) — **düzgün cavablar buradadır** |
| `tools/bank_coding.py` | Hissə 2: 5 kateqoriyada 30 kod tapşırığı, etalon həllər və testlər (0–10 qismən bal) |
| `tools/probes.py` | Qismən bal mexanizmini yoxlayan natamam həllər |
| `supabase_setup.sql` | Supabase cədvəli, RLS qaydaları və şifrəli oxuma funksiyası |

---

## ⚡ Quraşdırma

### 1. Supabase (bir dəfə, və ya bu versiyaya yenilədikdə mütləq)
Supabase Dashboard → **SQL Editor** → `supabase_setup.sql`-in məzmununu yapışdırın → **Run**.

Bu skript:
- tələbələrə yalnız nəticə **göndərmək** icazəsi verir (oxumaq yox);
- nəticələri yalnız müəllim şifrəsi ilə (serverdə yoxlanılan) `admin_list_submissions` funksiyası vasitəsilə oxumağa imkan verir.

> ⚠️ Skript işlədilməyibsə, müəllim paneli sarı xəbərdarlıq göstərəcək: köhnə qayda ilə anon açarı olan hər kəs nəticələri oxuya bilir.

### 2. Variant bölgüsü
```bash
python telebeler_35.py                 # şablon siyahı
python telebeler_35.py siyahi.txt      # hər sətirdə bir ad (35 sətir)
```
Hər tələbəyə **sıra nömrəsini (1–35)** bildirin. Tələbə girişdə yalnız ad-soyad və sıra nömrəsini yazır (qrup soruşulmur; bazada «2-ci kurs» kimi saxlanılır). Variant girişdə göstərilmir, yalnız imtahan başlayanda görünür. Portal variantı `(sıra − 1) % 5` qaydası ilə təyin edir:
`1,6,11,…,31 → A · 2,7,12,…,32 → B · 3,8,13,…,33 → C · 4,9,14,…,34 → D · 5,10,15,…,35 → E` (hər varianta 7 nəfər).

### 3. Tələbələrə link
- **Vercel (GitHub ilə)** — addım-addım:
  1. Zip-i açın. GitHub repo-sunun **kökünə** zip-in **içindəki** faylları yükləyin (Add file → Upload files → hamısını sürükləyin → Commit). `index.html`, `admin.html`, `vercel.json`, `.vercelignore`, `generate-env.js` mütləq kökdə olmalıdır — ayrıca qovluğun içində yox. Köhnə fayllar (məs. `telebeler_20.py`) qalıbsa, silin.
  2. Vercel → Settings → Environment Variables: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ADMIN_PASSWORD` (adlar yalnız böyük latın hərfləri və `_`).
  3. Vercel → Settings → Build and Deployment → **Root Directory** boş olmalıdır (fayllar kökdədirsə).
  4. Deployments → son dərc **Ready** olmalıdır (lazım olsa Redeploy). Saytı `Ctrl+Shift+R` ilə açın: aşağıda «Versiya: VSA-2026-10-20» yazısı görünürsə, yeni versiya dərc olunub.
  5. Tələbə portalı: `https://LAYİHƏ.vercel.app`, admin paneli: `https://LAYİHƏ.vercel.app/admin`.
- **Supabase**: `supabase_setup.sql`-i bütöv işlədin, sonra şifrə üçün:
  `INSERT INTO public.sdf1_admin (id, hash) VALUES (1, encode(sha256(convert_to('ŞİFRƏ', 'UTF8')), 'hex')) ON CONFLICT (id) DO UPDATE SET hash = excluded.hash;`
  (Vercel-dəki `ADMIN_PASSWORD` ilə eyni şifrə).
- **Laboratoriya şəbəkəsi**: müəllim kompüterində `python -m http.server 8000`, tələbələr `http://192.168.X.X:8000` açır.

İnternet tələb olunur: Python mühiti (Pyodide, ~25 MB) və Supabase CDN-dən yüklənir. Python yüklənməsə, nəzəri (test) suallar yenə də yoxlanır, kod tapşırıqları isə "qismən" kimi işarələnir — onları `yeniden_qiymetlendir.py` ilə yoxlayın.

---

## 🛡️ Anti-Cheat
1. Məcburi **tam ekran**; çıxdıqda xəbərdarlıq və tam ekrana qaytarma.
2. **3 xəbərdarlıq**: başqa taba/pəncərəyə keçmək (Alt+Tab daxil — brauzer Alt+Tab-ı bloklaya bilməz, amma dərhal aşkarlayır), brauzeri kiçiltmək, tam ekrandan çıxmaq, səhifəni yeniləmək → səsli siqnal + xəbərdarlıq. 3-cü dəfə imtahan kəsilir, bal **0**, status `KƏNARLAŞDIRILDI_3_HAQQ`.
3. Sağ klik, Copy/Cut/Paste, sürüklə-burax, `F12`, `Ctrl+Shift+I/J/C`, `Ctrl+U` bloklanır (bunlar haqq aparmır, amma jurnala yazılır).
4. Səhifə yenilənsə belə vaxt, haqlar və cavablar itmir (brauzer yaddaşında saxlanılır).
5. Eyni kompüterdə növbəti tələbə üçün: nəticə ekranında **"Müəllim: bu kompüteri sıfırla"** (müəllim şifrəsi ilə).

---

## 🔁 Nəticələrin yoxlanması
Bal tələbənin brauzerində hesablanır. Şübhəli və ya "qismən" nəticələr üçün:
```bash
python yeniden_qiymetlendir.py --password MÜƏLLİM_ŞİFRƏSİ --csv yeni_ballar.csv
```

## 🛠️ Sualları dəyişmək
Nəzəri sualları `tools/bank_theory.py`, kod tapşırıqlarını `tools/bank_coding.py` faylında redaktə edin, sonra:
```bash
python tools/build_bank.py --verify
```
Bu `exam_data.js`, `variant_A.py … variant_E.py` və `sual_banki_xeritesi.md`-ni yenidən yaradır, hər variantın etalon həllə 100/100, boş cavabla 0 verdiyini, `.py` fayllarının sintaksisini və qismən bal mexanizmini yoxlayır.

**Qismən bal necə işləyir?** Tapşırığın testi `return grade((çəki, "hissə", lambda: şərt), ...)` ilə bitirsə, hər ödənən hissənin çəkisi toplanır (çəkilərin cəmi 10-dur). Bu bankdakı bütün 30 kod tapşırığı belə yazılıb (3 hissə: adətən 4 + 3 + 3 bal). Bal tam ədədə yuvarlaqlaşdırılır (bazadakı `score INTEGER` sütunu ilə uyğundur).

## 🐍 Python yoxlamasının yumşaldılmış qaydaları
- Hər addıma 10 saniyə vaxt verilir; sonsuz dövr yalnız həmin tapşırığı dayandırır, brauzeri dondurmur.
- Tab simvolları, bütün kodun artıq girintisi, `>>>` başlıqları, `%magic` / `!əmr` sətirləri, “ağıllı” dırnaqlar və görünməz boşluqlar avtomatik düzəldilir.
- Xananın son sətri ifadədirsə, qiyməti Jupyter-dəki kimi çap olunur; `input()` imtahanı dayandırmır (1, 2, 3, … qaytarır).
- Siyahını qaytarmaq əvəzinə yerində dəyişən və ya nəticəni çap edən həllər də qəbul olunur; list ≈ tuple ≈ deque, 1.0 ≈ 1.
