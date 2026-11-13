This module is the first piece of a generic **app shell**: the core
tools to publish single page apps (SPA) from Odoo, without Odoo's web
client, so that any app can use them, not only the Shopfloor ones.

Shopfloor is its first user: the generic parts of its mobile apps move
here piece by piece, with the satellite modules below, and Shopfloor
becomes one of their consumers.

## Order

The core grows one block at a time, each with its unit tests (Vitest, in
`js_tests/` at the repository root):

1. the event hub, with the unit test setup;
2. the import map mixin, `app.shell.mixin.importmap`, when Shopfloor moves
   to the core;
3. the fetch helper;
4. the registries, the transport, the config registry and the app shell.

The full plan, with the Shopfloor side of each step, is in
<https://github.com/OCA/web-app-shell/issues/7>.

## Structure

A small core, plus satellite modules for specific features. Each
satellite is a feature someone can install on its own, not one module
per file.

- **`app_shell_core`** (this module): generic and dependency-free.
  - Import map, versioning, overrides, and the `app.shell.mixin.importmap`.
  - App page and PWA plumbing: page controller, manifest, icons, app info.
  - Runtime registries: config, generic registry, utils, colors.
  - REST client (`odoo.esm.js`, `fetch.js`) and the vanilla event hub.
  - Auth handler registry (the auth modules plug into it).
- **`app_shell_bus`**: client for Odoo's bus (websocket worker, no Odoo
  web client), the app's bus channel, and the worker version in app info.
  Depends on core and `bus`.
- **`app_shell_sync`**: sync manager, version detection and update flow,
  upgrade manager, connectivity status. Depends on core and
  `app_shell_bus`. Kept apart from the bus, so that an app can receive
  notifications without the sync behaviour.
- **`app_shell_i18n`**: translation registry, the en/fr/de catalogues,
  and the language settings page. Depends on core only.
- **`app_shell_demo`**: the demo mode machinery and the mocked backend.
  Demo data stays in each app: only the framework moves.
- **`app_shell_ui`**: generic UI components and theme: screen, list,
  manual select, searchbar and filters, date picker, number spinner,
  priority widget, user information and confirmation, report issue, detail
  card and mixin. These are Vue 2 components today: the module is named
  by purpose, and a Vue 3 rewrite is expected to replace them rather than
  move them.
- **Auth modules** (eg: `shopfloor_mobile_base_auth_api_key`) stay
  satellites of core, as today.

Suggested order: core, then `app_shell_bus` (already built), then
`app_shell_i18n` and `app_shell_ui` (cheapest moves, most reuse), then
`app_shell_sync` (depends on the bus), then `app_shell_demo` once another
app needs it.

## Stays in the app module (Shopfloor)

The domain part, which is not a shell concern:

- scenarios: the scenario state machine (`scenario/mixins`), form
  scenarios, and the scan-anything service;
- profiles and menus: the profile settings page and the menu wiring;
- router and homepage, which map the app's menus and scenarios to routes;
- the Shopfloor app record and its app info.

## Open points

- `loginpage`: generic, but tied to the auth flow. Move it with auth.
- `settings`: the settings page registry is generic, the profile entry is
  not.
- App record basics (URL, auth type, languages, running environment), now
  in `shopfloor_base`: they belong in core too. A separate and larger
  move.

## Design principles

- No dependency on `base_rest` or `component` in the core: REST services
  belong to each app.
- Mixins on the app's model rather than new tables, so that apps adopt
  the pieces without data migration.
- Backward compatibility for apps moving to it: template ids kept as
  extension points, legacy import map entries for moved JS files.
- Framework-agnostic runtime services (plain JS), so they can be shared
  by Vue 2, Vue 3 or plain JS apps.

## Short term

- Test the mixin in the core itself, with a test app model (today tested
  through `shopfloor.app` in `shopfloor_mobile_base`).
- Reusable UI test commands and tasks, the docker compose setup and the CI
  workflow, to test apps in a real browser.
- Support Odoo 16, to backport and forward port the same files.
