-- Jalankan sekali di Supabase > SQL Editor
create table if not exists kata_laluan (
  id bigserial primary key,
  peranan text not null check (peranan in ('JPN','PPD','SUP')),
  kod text not null,                    -- 'JPN', kod PPD (cth BG) atau kod sekolah (cth BGS001)
  hash text not null,                   -- pbkdf2_sha256$pusingan$garam$hash
  dikemas timestamptz default now(),
  unique (peranan, kod)
);
-- Lindungi jadual: kunci anon TIDAK boleh baca/tulis. Aplikasi guna SUPABASE_SERVICE_KEY (Secrets).
alter table kata_laluan enable row level security;
