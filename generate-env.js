// Vercel build addımı: env.js faylını Vercel mühit dəyişənlərindən yaradır.
// Lokal istifadə:  SUPABASE_URL=... SUPABASE_ANON_KEY=... ADMIN_PASSWORD=... node generate-env.js
// Şifrənin heşini almaq:  node generate-env.js --hash "MƏNİM_ŞİFRƏM"
//
// Dəyişən çatmasa belə dərc DAYANMIR (əks halda Vercel köhnə versiyanı göstərməyə davam edir);
// əvəzində Build Logs-da xəbərdarlıq yazılır və portal girişdə "nəticələr bazaya göndərilə bilmir" göstərir.
const fs = require("fs");
const crypto = require("crypto");

if (process.argv[2] === "--hash") {
    console.log(crypto.createHash("sha256").update(String(process.argv[3] || ""), "utf8").digest("hex"));
    process.exit(0);
}

// Vercel-də yalnız ADMIN_PASSWORD yazmaq kifayətdir — heş burada (Vercel serverində) hesablanır.
const env = {
    SUPABASE_URL: (process.env.SUPABASE_URL || "").trim(),
    SUPABASE_ANON_KEY: (process.env.SUPABASE_ANON_KEY || "").trim(),
    ADMIN_PASSWORD_HASH: (process.env.ADMIN_PASSWORD_HASH || "").trim() ||
        (process.env.ADMIN_PASSWORD ? crypto.createHash("sha256").update(process.env.ADMIN_PASSWORD.trim(), "utf8").digest("hex") : ""),
};
const missing = [];
if (!env.SUPABASE_URL) missing.push("SUPABASE_URL");
if (!env.SUPABASE_ANON_KEY) missing.push("SUPABASE_ANON_KEY");
if (!env.ADMIN_PASSWORD_HASH) missing.push("ADMIN_PASSWORD");
if (missing.length) {
    console.warn("⚠️  XƏBƏRDARLIQ: Vercel → Settings → Environment Variables bölməsində bunlar yoxdur: " + missing.join(", "));
    console.warn("   Sayt dərc olunur, lakin nəticələr bazaya getməyəcək. Dəyişənləri əlavə edib Redeploy edin.");
}
fs.writeFileSync("env.js", "window.__ENV = " + JSON.stringify(env, null, 4) + ";\n", "utf8");
console.log("env.js yaradıldı" + (missing.length ? " (natamam)" : ""));
