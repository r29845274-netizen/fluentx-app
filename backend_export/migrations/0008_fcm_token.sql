-- FluentX — push notification token storage
-- One FCM token per user (last-registered device wins for MVP — a
-- multi-device token table is a straightforward upgrade if needed).

alter table public.user_home_stats
  add column if not exists fcm_token text;

-- Sending actual push campaigns (e.g. "your streak is about to
-- expire") requires a separate admin-side scheduler/cron calling the
-- FCM Admin API with these tokens — that's server infrastructure
-- outside this Flutter app's scope, not something the client can do
-- on its own.
