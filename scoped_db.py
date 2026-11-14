"""
scoped_db.py - Pembungkus (proxy) Supabase yang MENGHADKAN bacaan (SELECT) ikut daerah PPD.

Cara kerja:
  - Setiap aplikasi daerah (cth Gombak = BG) memanggil set_scope("BG") sekali.
  - Semua supa.table(X).select(...) pada jadual yang ada data daerah akan ditapis
    di PELAYAN (server-side) -> Gombak hanya tarik data Gombak, Klang hanya tarik data Klang.
  - Aplikasi JPN: scope = None -> tiada tapisan (baca semua daerah).
  - Tulis (insert / update / delete / upsert) TIDAK diubah.
  - limit(>1000) dipaginasi automatik (had asal Supabase = 1000 baris setiap request,
    sebelum ini data > 1000 baris senyap-senyap terpotong).
"""
import time
from types import SimpleNamespace

PAGE = 1000
SCOPED_TABLES = {"sekolah_master", "guru_master", "pusat_master", "bilik_kebal_master", "cadangan_sup", "zon_bilik_kebal"}

_CODES = {}          # {scope: (masa, [kod_sekolah])}
_CODES_TTL = 3600


def district_school_codes(raw, scope):
    """Senarai kod sekolah dalam satu daerah (dari sekolah_master, di-cache 1 jam)."""
    hit = _CODES.get(scope)
    if hit and time.time() - hit[0] < _CODES_TTL:
        return hit[1]
    codes, a = [], 0
    try:
        while True:
            r = raw.table("sekolah_master").select("kod_sekolah").ilike("kod_ppd", scope).range(a, a + PAGE - 1).execute()
            d = r.data or []
            codes += [str(x.get("kod_sekolah") or "").strip().upper() for x in d if x.get("kod_sekolah")]
            if len(d) < PAGE:
                break
            a += PAGE
    except Exception:
        codes = []
    codes = sorted(set(c for c in codes if c.replace("_", "").isalnum()))
    _CODES[scope] = (time.time(), codes)
    return codes


def _variants(table, scope, codes):
    """Senarai (fungsi_tapis, boleh_kosong). Cuba ikut keutamaan sehingga ada hasil."""
    ppd = lambda q: q.ilike("kod_ppd", scope)
    if table in ("guru_master", "cadangan_sup"):
        v = []
        if codes:
            v.append((lambda q: q.or_(f"kod_ppd.ilike.{scope},kod_sekolah.in.({','.join(codes)})"), True))
        v.append((ppd, True))
        return v
    if table in ("sekolah_master", "zon_bilik_kebal"):
        return [(ppd, True)]
    if table == "pusat_master":
        return [(ppd, False),
                (lambda q: q.ilike("no_pusat", scope + "%"), False),
                (lambda q: q.ilike("kod_pusat", scope + "%"), True)]
    if table == "bilik_kebal_master":
        return [(ppd, False), (lambda q: q.ilike("kod_bilik_kebal", scope + "%"), True)]
    return []


def _row_in_scope(r, scope, codes):
    """Tapisan setempat (jalan terakhir jika tapisan server gagal - cth lajur tiada)."""
    kp = str(r.get("kod_ppd") or r.get("KOD_PPD") or "").strip().upper()
    if kp:
        return kp == scope
    ks = str(r.get("kod_sekolah") or r.get("KOD_SEKOLAH") or "").strip().upper()
    if ks and codes:
        return ks in codes
    for k in ("no_pusat", "kod_pusat", "kod_bilik_kebal"):
        v = str(r.get(k) or "").strip().upper()
        if v:
            return v.startswith(scope)
    return True


class _ScopedQuery:
    def __init__(self, client, table):
        self._client = client
        self._table = table
        self._ops = []          # [(nama, args, kwargs)]  args=None -> akses atribut (cth .not_)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "not_":
            self._ops.append((name, None, None))
            return self

        def _rec(*a, **k):
            self._ops.append((name, a, k))
            return self
        return _rec

    # --- bina & jalankan rantaian sebenar ---
    def _chain(self, var):
        q = self._client.raw.table(self._table)
        limit = None
        for name, a, k in self._ops:
            if name == "limit" and a is not None:
                limit = a[0] if a else None
                continue
            q = getattr(q, name) if a is None else getattr(q, name)(*a, **k)
            if name == "select" and var is not None:
                q = var(q)
        return q, limit

    def _run(self, var, paginate):
        q, limit = self._chain(var)
        if limit is None:
            return q.execute()
        if limit <= PAGE or not paginate:
            return q.limit(limit).execute()
        rows, first, a = [], None, 0
        while a < limit:
            b = min(a + PAGE, limit) - 1
            q, _ = self._chain(var)
            r = q.range(a, b).execute()
            first = first or r
            d = r.data or []
            rows.extend(d)
            if len(d) < (b - a + 1):
                break
            a = b + 1
        return SimpleNamespace(data=rows, count=getattr(first, "count", None))

    def execute(self):
        scope = self._client.scope()
        is_select = bool(self._ops) and self._ops[0][0] == "select"
        if not (scope and is_select and self._table in SCOPED_TABLES):
            res = self._run(None, paginate=is_select)
            if not is_select:                                   # tulisan berjaya -> kosongkan cache bacaan jadual itu
                try:
                    cb = self._client.on_write
                    if cb:
                        cb(self._table)
                except Exception:
                    pass
            return res
        codes = district_school_codes(self._client.raw, scope) if self._table in ("guru_master", "cadangan_sup") else []
        variants = _variants(self._table, scope, codes)
        for i, (var, empty_ok) in enumerate(variants):
            try:
                res = self._run(var, paginate=True)
            except Exception:
                continue
            if (res.data) or empty_ok or i == len(variants) - 1:
                return res
        # jalan terakhir: tarik tanpa tapisan server, tapis di sini
        res = self._run(None, paginate=True)
        res.data = [r for r in (res.data or []) if _row_in_scope(r, scope, codes)]
        return res


class ScopedSupabase:
    def __init__(self, raw, scope_fn):
        self.raw = raw
        self.scope = scope_fn
        self.on_write = None            # fungsi(table) dipanggil selepas insert/update/delete/upsert

    def table(self, name):
        return _ScopedQuery(self, name)

    def __getattr__(self, name):          # rpc, storage, auth ... terus ke klien sebenar
        return getattr(self.raw, name)
