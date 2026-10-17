-- Сумрак 2096: броски мастера в комнате (видны игрокам этой комнаты).
-- Запустить один раз: Supabase → SQL Editor → вставить → Run. Повторный запуск безопасен. Ничего не удаляет.
alter table public.rooms add column if not exists gm_log jsonb not null default '[]'::jsonb;
alter table public.rooms replica identity full;
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'rooms') then
    alter publication supabase_realtime add table public.rooms;
  end if;
end $$;
