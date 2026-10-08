-- Сумрак 2096: комнаты мастера.
-- Вставьте целиком в Supabase → SQL Editor → Run. Повторный запуск безопасен.

create table if not exists public.rooms(
  code text primary key check (code ~ '^[A-Z0-9]{5,8}$'),
  gm uuid not null default auth.uid(),
  title text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists public.room_players(
  room text not null references public.rooms(code) on delete cascade,
  uid uuid not null default auth.uid(),
  char_id text not null,
  name text not null default '',
  sheet jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (room, uid, char_id)
);

create table if not exists public.room_mods(
  room text not null references public.rooms(code) on delete cascade,
  uid uuid not null,
  char_id text not null,
  mods jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (room, uid, char_id)
);

alter table public.rooms enable row level security;
alter table public.room_players enable row level security;
alter table public.room_mods enable row level security;
alter table public.room_players replica identity full;
alter table public.room_mods replica identity full;

-- вспомогательные проверки (security definer, чтобы политики не ссылались друг на друга по кругу)
create or replace function public.is_room_gm(r text) returns boolean
  language sql stable security definer set search_path = public
  as $$ select exists(select 1 from public.rooms where code = r and gm = auth.uid()) $$;
create or replace function public.in_room(r text) returns boolean
  language sql stable security definer set search_path = public
  as $$ select exists(select 1 from public.room_players where room = r and uid = auth.uid()) $$;

drop policy if exists rooms_select on public.rooms;
drop policy if exists rooms_insert on public.rooms;
drop policy if exists rooms_update on public.rooms;
drop policy if exists rooms_delete on public.rooms;
create policy rooms_select on public.rooms for select to authenticated using (gm = auth.uid() or public.in_room(code));
create policy rooms_insert on public.rooms for insert to authenticated with check (gm = auth.uid());
create policy rooms_update on public.rooms for update to authenticated using (gm = auth.uid()) with check (gm = auth.uid());
create policy rooms_delete on public.rooms for delete to authenticated using (gm = auth.uid());

drop policy if exists players_select on public.room_players;
drop policy if exists players_insert on public.room_players;
drop policy if exists players_update on public.room_players;
drop policy if exists players_delete on public.room_players;
create policy players_select on public.room_players for select to authenticated using (uid = auth.uid() or public.is_room_gm(room));
create policy players_insert on public.room_players for insert to authenticated with check (uid = auth.uid());
create policy players_update on public.room_players for update to authenticated using (uid = auth.uid()) with check (uid = auth.uid());
create policy players_delete on public.room_players for delete to authenticated using (uid = auth.uid() or public.is_room_gm(room));

drop policy if exists mods_select on public.room_mods;
drop policy if exists mods_insert on public.room_mods;
drop policy if exists mods_update on public.room_mods;
drop policy if exists mods_delete on public.room_mods;
create policy mods_select on public.room_mods for select to authenticated using (uid = auth.uid() or public.is_room_gm(room));
create policy mods_insert on public.room_mods for insert to authenticated with check (public.is_room_gm(room));
create policy mods_update on public.room_mods for update to authenticated using (public.is_room_gm(room)) with check (public.is_room_gm(room));
create policy mods_delete on public.room_mods for delete to authenticated using (public.is_room_gm(room) or uid = auth.uid());

grant select, insert, update, delete on public.rooms, public.room_players, public.room_mods to authenticated;
grant execute on function public.is_room_gm(text), public.in_room(text) to authenticated;

-- изменения в реальном времени
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'room_players') then
    alter publication supabase_realtime add table public.room_players;
  end if;
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'room_mods') then
    alter publication supabase_realtime add table public.room_mods;
  end if;
end $$;
