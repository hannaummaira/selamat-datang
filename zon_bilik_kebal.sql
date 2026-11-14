-- Jalankan sekali di Supabase > SQL Editor
create table if not exists zon_bilik_kebal (
  id bigserial primary key,
  kod_ppd text not null,
  kod_bilik_kebal text not null,
  kod_sekolah text not null unique,   -- satu sekolah hanya dalam satu zon
  created_at timestamptz default now()
);
alter table zon_bilik_kebal disable row level security;
