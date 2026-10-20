-- ====================================================================
-- SDF 1 — SUPABASE CƏDVƏLİ VƏ TƏHLÜKƏSİZLİK QAYDALARI (RLS)
-- Supabase Dashboard -> "SQL Editor" bölməsinə yapışdırıb "RUN" edin.
-- Skript təkrar işlədilə bilər (mövcud bazanı da yeniləyir, məlumatları silmir).
-- ====================================================================

-- 1. Nəticələr cədvəli
CREATE TABLE IF NOT EXISTS public.exam_submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    student_name TEXT NOT NULL,
    student_group TEXT NOT NULL,
    student_id TEXT,                 -- siyahıdakı sıra nömrəsi (1-35)
    variant TEXT NOT NULL,
    score INTEGER NOT NULL,
    max_score INTEGER DEFAULT 100,
    violations INTEGER DEFAULT 0,
    status TEXT NOT NULL,            -- 'TAMAMLANDI', 'KƏNARLAŞDIRILDI_3_HAQQ', 'VAXT_BİTDİ'
    answers JSONB,                   -- tələbənin bütün cavabları
    breakdown JSONB,                 -- {scores: {T1: 10, T2: 6, ...}, grading, violation_log, ...}
    annulled_at TIMESTAMP WITH TIME ZONE  -- müəllim "yenidən başlat" edibsə: nəticə ləğv olunub
);

-- Köhnə bazalar üçün (sütun yoxdursa əlavə edir)
ALTER TABLE public.exam_submissions ADD COLUMN IF NOT EXISTS annulled_at TIMESTAMP WITH TIME ZONE;

-- 2. Row Level Security
ALTER TABLE public.exam_submissions ENABLE ROW LEVEL SECURITY;

-- Qayda 1: anonim istifadəçi (tələbə) YALNIZ nəticə göndərə bilər — məntiqli dəyərlərlə
DROP POLICY IF EXISTS "Anonim tələbə nəticə göndərə bilər" ON public.exam_submissions;
CREATE POLICY "Anonim tələbə nəticə göndərə bilər"
ON public.exam_submissions
FOR INSERT
TO anon
WITH CHECK (
    score BETWEEN 0 AND 100
    AND violations BETWEEN 0 AND 3
    AND status IN ('TAMAMLANDI', 'KƏNARLAŞDIRILDI_3_HAQQ', 'VAXT_BİTDİ')
    AND char_length(student_name) BETWEEN 1 AND 100
    AND char_length(student_group) <= 30
    AND annulled_at IS NULL
);

-- Qayda 2: anonim istifadəçi cədvəli OXUYA BİLMƏZ.
-- (Köhnə versiyadakı "USING (true)" qaydası anon açarı olan hər kəsə — yəni hər
--  tələbəyə — bütün cavabları oxumağa imkan verirdi. O qayda silinir.)
DROP POLICY IF EXISTS "Müəllim nəticələri oxuya bilər" ON public.exam_submissions;

-- 3. Müəllim şifrəsinin yoxlanması (yalnız serverdə; tələbələr bu funksiyanı çağıra bilməz).
--    Şifrənin heşi bazadakı sdf1_admin cədvəlində saxlanılır (skriptdə şifrə yazılmır).
--    Şifrəni təyin etmək / dəyişmək üçün SQL Editor-da AYRICA bu bir sətri işlədin
--    (SIFRENIZ əvəzinə öz şifrənizi yazın; Vercel-dəki ADMIN_PASSWORD ilə eyni olmalıdır):
--
--    INSERT INTO public.sdf1_admin (id, hash) VALUES (1, encode(sha256(convert_to('SIFRENIZ', 'UTF8')), 'hex'))
--    ON CONFLICT (id) DO UPDATE SET hash = excluded.hash;
--
CREATE TABLE IF NOT EXISTS public.sdf1_admin (id INTEGER PRIMARY KEY CHECK (id = 1), hash TEXT NOT NULL);
ALTER TABLE public.sdf1_admin ENABLE ROW LEVEL SECURITY;   -- siyasət yoxdur: anon və authenticated oxuya bilməz
REVOKE ALL ON public.sdf1_admin FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public._sdf1_check_admin(p_password TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_hash TEXT;
BEGIN
    SELECT hash INTO v_hash FROM public.sdf1_admin WHERE id = 1;
    IF v_hash IS NULL THEN
        RAISE EXCEPTION 'Müəllim şifrəsi hələ təyin edilməyib (supabase_setup.sql-dəki 3-cü bölmənin şərhindəki INSERT sətrini işlədin)' USING ERRCODE = '28P01';
    END IF;
    IF encode(sha256(convert_to(coalesce(p_password, ''), 'UTF8')), 'hex') <> v_hash THEN
        RAISE EXCEPTION 'İcazə yoxdur: yanlış müəllim şifrəsi' USING ERRCODE = '28P01';
    END IF;
END;
$$;
REVOKE ALL ON FUNCTION public._sdf1_check_admin(TEXT) FROM PUBLIC, anon, authenticated;

-- 4. Müəllim paneli: bütün nəticələri oxumaq (şifrə ilə)
CREATE OR REPLACE FUNCTION public.admin_list_submissions(p_password TEXT)
RETURNS SETOF public.exam_submissions
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._sdf1_check_admin(p_password);
    RETURN QUERY SELECT * FROM public.exam_submissions ORDER BY created_at DESC;
END;
$$;
REVOKE ALL ON FUNCTION public.admin_list_submissions(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.admin_list_submissions(TEXT) TO anon, authenticated;

-- 5. Müəllim paneli: tələbənin nəticəsini ləğv edib imtahanı yenidən başlatmağa icazə vermək (şifrə ilə).
--    Nəticə silinmir, "ləğv edilib" kimi işarələnir (tarixçə qalır).
CREATE OR REPLACE FUNCTION public.admin_reset_submission(p_password TEXT, p_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._sdf1_check_admin(p_password);
    UPDATE public.exam_submissions SET annulled_at = now() WHERE id = p_id AND annulled_at IS NULL;
END;
$$;
REVOKE ALL ON FUNCTION public.admin_reset_submission(TEXT, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.admin_reset_submission(TEXT, UUID) TO anon, authenticated;

-- 6. Tələbə portalı: bu sıra nömrəsi ilə artıq (ləğv edilməmiş) nəticə varmı?
--    Varsa, imtahan yenidən başlaya bilməz — yalnız müəllim "yenidən başlat" etdikdən sonra.
CREATE OR REPLACE FUNCTION public.seat_is_taken(p_group TEXT, p_sira TEXT)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.exam_submissions
        WHERE student_group = p_group AND student_id = p_sira AND annulled_at IS NULL
    );
$$;
REVOKE ALL ON FUNCTION public.seat_is_taken(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.seat_is_taken(TEXT, TEXT) TO anon, authenticated;

-- 7. Tələbə portalı: müəllim mənim nəticəmi ləğv edibmi? (yalnız öz nəticəsinin gizli id-si ilə)
CREATE OR REPLACE FUNCTION public.submission_was_reset(p_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (SELECT 1 FROM public.exam_submissions WHERE id = p_id AND annulled_at IS NOT NULL);
$$;
REVOKE ALL ON FUNCTION public.submission_was_reset(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.submission_was_reset(UUID) TO anon, authenticated;

-- ====================================================================
-- CANLI İZLƏMƏ (imtahan gedərkən müəllim tələbəni görür)
-- ====================================================================

-- 8. Hazırda imtahan yazan tələbələrin canlı vəziyyəti (hər tələbə üçün bir sətir)
CREATE TABLE IF NOT EXISTS public.exam_live (
    session_id UUID PRIMARY KEY,
    student_group TEXT NOT NULL,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    variant TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    violations INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,             -- 'active' (işləyir), 'finished' (bitirdi), 'terminated' (kənarlaşdırıldı)
    progress JSONB                   -- {answers, tested, answered, violation_log}
);
ALTER TABLE public.exam_live ENABLE ROW LEVEL SECURITY;
-- Heç bir RLS qaydası yoxdur: tələbələr cədvəli birbaşa nə oxuya, nə yaza bilər — yalnız aşağıdakı funksiyalarla.

-- 9. Tələbə portalı: canlı vəziyyəti göndərmək — student_heartbeat (aşağıda, 13-cü bölmədə)

-- 10. Müəllim paneli: canlı vəziyyəti oxumaq (şifrə ilə; son 6 saat)
CREATE OR REPLACE FUNCTION public.admin_list_live(p_password TEXT)
RETURNS SETOF public.exam_live
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._sdf1_check_admin(p_password);
    RETURN QUERY SELECT * FROM public.exam_live
        WHERE last_seen > now() - interval '6 hours'
        ORDER BY last_seen DESC;
END;
$$;
REVOKE ALL ON FUNCTION public.admin_list_live(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.admin_list_live(TEXT) TO anon, authenticated;

-- ====================================================================
-- NÖMRƏ KİLİDİ: bir nömrə ilə eyni anda yalnız BİR imtahan gedə bilər
-- ====================================================================

-- 11. Köhnə/təkrar aktiv sessiyaları təmizlə (unikal indeksdən əvvəl)
UPDATE public.exam_live SET state = 'expired'
WHERE state = 'active' AND started_at < now() - interval '100 minutes';

UPDATE public.exam_live l SET state = 'released'
WHERE l.state = 'active' AND EXISTS (
    SELECT 1 FROM public.exam_live o
    WHERE o.state = 'active' AND o.student_group = l.student_group AND o.student_id = l.student_id
      AND (o.last_seen > l.last_seen OR (o.last_seen = l.last_seen AND o.session_id > l.session_id)));

-- Eyni qrup + nömrə üçün yalnız bir aktiv sessiya (eyni anda iki kliklə belə — verilənlər bazası səviyyəsində)
CREATE UNIQUE INDEX IF NOT EXISTS exam_live_one_active_seat
    ON public.exam_live (student_group, student_id) WHERE state = 'active';

-- 12. Tələbə portalı: imtahana başlayarkən nömrəni tutmaq.
--     Nəticə: 'ok' | 'submitted' (bu nömrə ilə nəticə artıq var) | 'in_use' (bu nömrə ilə hazırda imtahan gedir)
CREATE OR REPLACE FUNCTION public.claim_seat(
    p_session_id UUID, p_group TEXT, p_sira TEXT, p_name TEXT, p_variant TEXT, p_started_at TIMESTAMP WITH TIME ZONE)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF p_session_id IS NULL OR p_sira !~ '^[0-9]{1,3}$'
       OR char_length(coalesce(p_name, '')) NOT BETWEEN 1 AND 100 OR char_length(coalesce(p_group, '')) > 30 THEN
        RAISE EXCEPTION 'Yanlış məlumat' USING ERRCODE = '22023';
    END IF;

    IF EXISTS (SELECT 1 FROM public.exam_submissions
               WHERE student_group = p_group AND student_id = p_sira AND annulled_at IS NULL) THEN
        RETURN 'submitted';
    END IF;

    -- vaxtı çoxdan bitmiş (bağlanıb tərk edilmiş) sessiyalar nömrəni tutmur
    UPDATE public.exam_live SET state = 'expired'
    WHERE student_group = p_group AND student_id = p_sira AND state = 'active'
      AND started_at < now() - interval '100 minutes';

    BEGIN
        INSERT INTO public.exam_live
            (session_id, student_group, student_id, student_name, variant, started_at, last_seen, violations, state, progress)
        VALUES
            (p_session_id, p_group, p_sira, p_name, p_variant, p_started_at, now(), 0, 'active', '{}'::jsonb)
        ON CONFLICT (session_id) DO NOTHING;
    EXCEPTION WHEN unique_violation THEN
        RETURN 'in_use';
    END;

    -- eyni session_id ilə təkrar çağırış (məs. şəbəkə təkrarı) — yenə 'ok'
    IF EXISTS (SELECT 1 FROM public.exam_live WHERE session_id = p_session_id AND state = 'active') THEN
        RETURN 'ok';
    END IF;
    RETURN 'in_use';
END;
$$;
REVOKE ALL ON FUNCTION public.claim_seat(UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMP WITH TIME ZONE) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.claim_seat(UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMP WITH TIME ZONE) TO anon, authenticated;

-- 13. student_heartbeat indi sessiyanın vəziyyətini qaytarır (müəllim nömrəni azad edibsə: 'released')
DROP FUNCTION IF EXISTS public.student_heartbeat(UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMP WITH TIME ZONE, INTEGER, TEXT, JSONB);
CREATE FUNCTION public.student_heartbeat(
    p_session_id UUID, p_group TEXT, p_sira TEXT, p_name TEXT, p_variant TEXT,
    p_started_at TIMESTAMP WITH TIME ZONE, p_violations INTEGER, p_state TEXT, p_progress JSONB)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_state TEXT;
BEGIN
    IF p_session_id IS NULL
       OR p_sira !~ '^[0-9]{1,3}$'
       OR char_length(coalesce(p_name, '')) NOT BETWEEN 1 AND 100
       OR char_length(coalesce(p_group, '')) > 30
       OR p_state NOT IN ('active', 'finished', 'terminated')
       OR p_violations NOT BETWEEN 0 AND 3
       OR octet_length(coalesce(p_progress::text, '')) > 300000 THEN
        RAISE EXCEPTION 'Yanlış məlumat' USING ERRCODE = '22023';
    END IF;

    UPDATE public.exam_live AS l SET
        last_seen  = now(),
        violations = GREATEST(l.violations, p_violations),
        state      = CASE WHEN l.state = 'active' THEN p_state ELSE l.state END,
        progress   = p_progress
    WHERE l.session_id = p_session_id
    RETURNING l.state INTO v_state;

    IF NOT FOUND THEN
        -- köhnə versiyadan qalan sessiya: nömrə boşdursa yaz, deyilsə 'in_use'
        BEGIN
            INSERT INTO public.exam_live
                (session_id, student_group, student_id, student_name, variant, started_at, last_seen, violations, state, progress)
            VALUES
                (p_session_id, p_group, p_sira, p_name, p_variant, p_started_at, now(), p_violations, p_state, p_progress);
            v_state := p_state;
        EXCEPTION WHEN unique_violation THEN
            RETURN 'in_use';
        END;
    END IF;
    RETURN v_state;
END;
$$;
REVOKE ALL ON FUNCTION public.student_heartbeat(UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMP WITH TIME ZONE, INTEGER, TEXT, JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.student_heartbeat(UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMP WITH TIME ZONE, INTEGER, TEXT, JSONB) TO anon, authenticated;

-- 14. Müəllim paneli: davam edən sessiyanı dayandırıb nömrəni azad etmək (məs. kompüter xarab olub)
CREATE OR REPLACE FUNCTION public.admin_release_live(p_password TEXT, p_session_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    PERFORM public._sdf1_check_admin(p_password);
    UPDATE public.exam_live SET state = 'released' WHERE session_id = p_session_id AND state = 'active';
END;
$$;
REVOKE ALL ON FUNCTION public.admin_release_live(TEXT, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.admin_release_live(TEXT, UUID) TO anon, authenticated;
