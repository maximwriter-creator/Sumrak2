-- Сумрак 2096: «Проект Мекка» — кампейн только по логину и паролю.
-- Запустить после mecca.sql: Supabase → SQL Editor → вставить целиком → Run. Повторный запуск безопасен.
-- После этого читать данные карты напрямую нельзя: только через функции ниже, которые проверяют пароль.
-- Роли: can_edit = true — правка (сейчас: Life), false — только просмотр (можно добавить позже).

alter table public.mecca_editors add column if not exists can_edit boolean not null default true;

-- роль по логину и паролю: 'edit', 'view' или null
create or replace function public.mecca_role(p_login text, p_pass text) returns text
language sql stable security definer set search_path = public as $$
  select case when can_edit then 'edit' else 'view' end
  from mecca_editors
  where login = lower(trim(coalesce(p_login, '')))
    and pass_hash = encode(sha256(convert_to('mecca|' || lower(trim(coalesce(p_login, ''))) || '|' || coalesce(p_pass, ''), 'UTF8')), 'hex');
$$;

-- запись: только роль edit (mecca_put / mecca_del из mecca.sql пользуются этой проверкой)
create or replace function public.mecca_check(p_login text, p_pass text) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(mecca_role(p_login, p_pass) = 'edit', false);
$$;

-- вход: возвращает роль, при ошибке притормаживает подбор пароля
create or replace function public.mecca_login2(p_login text, p_pass text) returns text
language plpgsql security definer set search_path = public as $$
declare r text := mecca_role(p_login, p_pass);
begin
  if r is null then perform pg_sleep(1); end if;
  return r;
end $$;

create or replace function public.mecca_need(p_login text, p_pass text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if mecca_role(p_login, p_pass) is null then
    perform pg_sleep(1);
    raise exception 'mecca: access denied';
  end if;
end $$;

create or replace function public.mecca_list(p_login text, p_pass text, p_coll text)
returns table(id text, data jsonb)
language plpgsql security definer set search_path = public as $$
begin
  perform mecca_need(p_login, p_pass);
  return query select d.id, d.data from mecca_docs d where d.coll = p_coll limit 5000;
end $$;

create or replace function public.mecca_ids(p_login text, p_pass text, p_coll text)
returns setof text
language plpgsql security definer set search_path = public as $$
begin
  perform mecca_need(p_login, p_pass);
  return query select d.id from mecca_docs d where d.coll = p_coll limit 5000;
end $$;

create or replace function public.mecca_get(p_login text, p_pass text, p_coll text, p_id text)
returns jsonb
language plpgsql security definer set search_path = public as $$
declare r jsonb;
begin
  perform mecca_need(p_login, p_pass);
  select d.data into r from mecca_docs d where d.coll = p_coll and d.id = p_id;
  return r;
end $$;

-- закрыть прямое чтение таблицы
drop policy if exists mecca_read on public.mecca_docs;
revoke select, insert, update, delete on public.mecca_docs from anon, authenticated;

revoke all on function public.mecca_role(text, text) from public, anon, authenticated;
revoke all on function public.mecca_check(text, text) from public, anon, authenticated;
revoke all on function public.mecca_need(text, text) from public, anon, authenticated;
revoke all on function public.mecca_login2(text, text) from public;
revoke all on function public.mecca_list(text, text, text) from public;
revoke all on function public.mecca_ids(text, text, text) from public;
revoke all on function public.mecca_get(text, text, text, text) from public;
grant execute on function public.mecca_login2(text, text) to anon, authenticated;
grant execute on function public.mecca_list(text, text, text) to anon, authenticated;
grant execute on function public.mecca_ids(text, text, text) to anon, authenticated;
grant execute on function public.mecca_get(text, text, text, text) to anon, authenticated;

-- Добавить логин только для просмотра (пример, раскомментировать и вписать свои значения):
-- insert into public.mecca_editors(login, pass_hash, can_edit)
-- values ('player', encode(sha256(convert_to('mecca|player|ПАРОЛЬ', 'UTF8')), 'hex'), false)
-- on conflict (login) do update set pass_hash = excluded.pass_hash, can_edit = excluded.can_edit;
