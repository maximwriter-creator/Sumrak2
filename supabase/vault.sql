-- Сумрак 2096: облачная копия персонажей.
-- Запустить один раз: Supabase → SQL Editor → вставить → Run. Повторный запуск безопасен.
-- Доступ только через функции ниже; по ключу хранилища (хранится только его SHA-256).

create table if not exists public.char_vault (
  owner      text        not null,               -- sha256 ключа хранилища
  char_id    text        not null,
  name       text        not null default '',
  data       jsonb       not null,
  updated_at timestamptz not null default now(),
  primary key (owner, char_id)
);

alter table public.char_vault enable row level security;
-- политик нет: напрямую таблицу не читает и не пишет никто, только функции
revoke all on public.char_vault from anon, authenticated;

create or replace function public.vault_owner(p_key text) returns text
language plpgsql immutable as $$
begin
  if p_key is null or length(p_key) < 16 then
    raise exception 'Слишком короткий ключ хранилища';
  end if;
  return encode(sha256(convert_to(upper(replace(p_key, '-', '')), 'UTF8')), 'hex');
end $$;

create or replace function public.vault_put(p_key text, p_char text, p_name text, p_data jsonb, p_updated timestamptz)
returns void language plpgsql security definer set search_path = public as $$
begin
  if octet_length(p_data::text) > 3000000 then
    raise exception 'Персонаж слишком большой для облачной копии';
  end if;
  insert into char_vault(owner, char_id, name, data, updated_at)
  values (vault_owner(p_key), p_char, coalesce(p_name, ''), p_data, coalesce(p_updated, now()))
  on conflict (owner, char_id) do update
    set name = excluded.name, data = excluded.data, updated_at = excluded.updated_at;
end $$;

create or replace function public.vault_list(p_key text)
returns table(char_id text, name text, updated_at timestamptz, size int)
language sql security definer set search_path = public as $$
  select char_id, name, updated_at, octet_length(data::text)
  from char_vault where owner = vault_owner(p_key) order by updated_at desc;
$$;

create or replace function public.vault_get(p_key text, p_char text)
returns jsonb language sql security definer set search_path = public as $$
  select data from char_vault where owner = vault_owner(p_key) and char_id = p_char;
$$;

create or replace function public.vault_del(p_key text, p_char text)
returns void language sql security definer set search_path = public as $$
  delete from char_vault where owner = vault_owner(p_key) and char_id = p_char;
$$;

revoke all on function public.vault_put(text, text, text, jsonb, timestamptz) from public;
revoke all on function public.vault_list(text) from public;
revoke all on function public.vault_get(text, text) from public;
revoke all on function public.vault_del(text, text) from public;
grant execute on function public.vault_owner(text) to anon, authenticated;
grant execute on function public.vault_put(text, text, text, jsonb, timestamptz) to anon, authenticated;
grant execute on function public.vault_list(text) to anon, authenticated;
grant execute on function public.vault_get(text, text) to anon, authenticated;
grant execute on function public.vault_del(text, text) to anon, authenticated;

-- Для мастера: список всех выгруженных персонажей и просмотр листа (только чтение).
create or replace function public.vault_all(p_q text default null)
returns table(owner text, char_id text, name text, updated_at timestamptz, cls int, cls2 int, rank_lvl int)
language sql security definer set search_path = public as $$
  select owner, char_id, name, updated_at,
         nullif(data->'cls'->>'i','')::int, nullif(data->'cls2'->>'i','')::int, nullif(data->>'rankLvl','')::int
  from char_vault
  where p_q is null or p_q = '' or name ilike '%' || p_q || '%'
  order by lower(name), updated_at desc
  limit 1000;
$$;

create or replace function public.vault_peek(p_owner text, p_char text)
returns jsonb language sql security definer set search_path = public as $$
  select data from char_vault where owner = p_owner and char_id = p_char;
$$;

revoke all on function public.vault_all(text) from public;
revoke all on function public.vault_peek(text, text) from public;
grant execute on function public.vault_all(text) to anon, authenticated;
grant execute on function public.vault_peek(text, text) to anon, authenticated;
