-- Сумрак 2096: бестиарий мастера и общий порядок ходов (инициатива) в комнате.
-- Запустить один раз: Supabase → SQL Editor → вставить → Run. Повторный запуск безопасен. Ничего не удаляет.

-- 1. Порядок ходов: мастер пишет, игроки комнаты читают (права те же, что у rooms).
alter table public.rooms add column if not exists gm_init jsonb not null default '{}'::jsonb;
alter table public.rooms replica identity full;
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'rooms') then
    alter publication supabase_realtime add table public.rooms;
  end if;
end $$;

-- 2. Бестиарий: копия на сервере, видит и меняет только сам мастер (своё устройство).
create table if not exists public.gm_bestiary(
  uid uuid primary key default auth.uid(),
  npcs jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.gm_bestiary enable row level security;
drop policy if exists bestiary_select on public.gm_bestiary;
drop policy if exists bestiary_insert on public.gm_bestiary;
drop policy if exists bestiary_update on public.gm_bestiary;
drop policy if exists bestiary_delete on public.gm_bestiary;
create policy bestiary_select on public.gm_bestiary for select to authenticated using (uid = auth.uid());
create policy bestiary_insert on public.gm_bestiary for insert to authenticated with check (uid = auth.uid());
create policy bestiary_update on public.gm_bestiary for update to authenticated using (uid = auth.uid()) with check (uid = auth.uid());
create policy bestiary_delete on public.gm_bestiary for delete to authenticated using (uid = auth.uid());
grant select, insert, update, delete on public.gm_bestiary to authenticated;
