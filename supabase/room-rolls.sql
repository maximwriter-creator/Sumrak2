-- Сумрак 2096: открытые броски мастера в комнате.
-- Запустить один раз: Supabase → SQL Editor → вставить целиком → Run. Повторный запуск безопасен.
-- Нужен уже запущенный скрипт комнат (room.sql). Скрытые броски мастера на сервер не отправляются вовсе.

create table if not exists public.room_rolls(
  id bigint generated always as identity primary key,
  room text not null references public.rooms(code) on delete cascade,
  t timestamptz not null default now(),
  x text not null check (length(x) between 1 and 400),
  who text not null default 'Мастер' check (length(who) <= 60)
);
create index if not exists room_rolls_room_t on public.room_rolls(room, t desc);
alter table public.room_rolls enable row level security;

drop policy if exists rolls_select on public.room_rolls;
drop policy if exists rolls_insert on public.room_rolls;
drop policy if exists rolls_delete on public.room_rolls;
-- видят мастер и игроки этой комнаты; пишет и удаляет только мастер
create policy rolls_select on public.room_rolls for select to authenticated using (public.is_room_gm(room) or public.in_room(room));
create policy rolls_insert on public.room_rolls for insert to authenticated with check (public.is_room_gm(room));
create policy rolls_delete on public.room_rolls for delete to authenticated using (public.is_room_gm(room));
grant select, insert, delete on public.room_rolls to authenticated;

-- храним последние 200 бросков на комнату
create or replace function public.room_rolls_trim() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  delete from room_rolls where room = new.room and id in (
    select id from room_rolls where room = new.room order by id desc offset 200);
  return null;
end $$;
drop trigger if exists room_rolls_trim on public.room_rolls;
create trigger room_rolls_trim after insert on public.room_rolls for each row execute function public.room_rolls_trim();

do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'room_rolls') then
    alter publication supabase_realtime add table public.room_rolls;
  end if;
end $$;
