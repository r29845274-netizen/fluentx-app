-- Applied to staging and production on 2026-10-08.
-- Retires legacy key/bootstrap and invitation-based privileged role claims.
-- Modern owner-bootstrap with verified OWNER_EMAIL remains untouched.
DO $migration$
BEGIN
  IF to_regclass('public.admin_bootstrap_keys') IS NOT NULL THEN
    UPDATE public.admin_bootstrap_keys SET consumed_at = now()
    WHERE consumed_at IS NULL;
  END IF;
  IF to_regclass('public.admin_bootstrap') IS NOT NULL THEN
    UPDATE public.admin_bootstrap SET used_at = now()
    WHERE used_at IS NULL;
  END IF;
  IF to_regclass('public.admin_invites') IS NOT NULL THEN
    UPDATE public.admin_invites SET active = false WHERE active = true;
  END IF;
  IF to_regprocedure('public.claim_first_owner(text)') IS NOT NULL THEN
    EXECUTE $ddl$
    CREATE OR REPLACE FUNCTION public.claim_first_owner(p_setup_code text)
    RETURNS text LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
    AS $body$ BEGIN RAISE EXCEPTION 'retired' USING ERRCODE='42501'; END; $body$;
    $ddl$;
    REVOKE ALL ON FUNCTION public.claim_first_owner(text)
    FROM PUBLIC, anon, authenticated;
  END IF;
  IF to_regprocedure('public.claim_admin_invite()') IS NOT NULL THEN
    EXECUTE $ddl$
    CREATE OR REPLACE FUNCTION public.claim_admin_invite()
    RETURNS text LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
    AS $body$ BEGIN RAISE EXCEPTION 'retired' USING ERRCODE='42501'; END; $body$;
    $ddl$;
    REVOKE ALL ON FUNCTION public.claim_admin_invite()
    FROM PUBLIC, anon, authenticated;
  END IF;
END;
$migration$;
