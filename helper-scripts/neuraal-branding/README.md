# Neuraal branding for the mailcow UI

Everything in this folder rebrands the **mailcow web UI** (`https://<MAILCOW_HOSTNAME>/`)
to Neuraal without blocking upstream updates.

## Why it survives `update.sh`

`update.sh` commits your local state and then runs `git merge -X theirs`.
That means **any change to a file that upstream also touches is silently
discarded**. So the branding is layered on files upstream does not own:

| Layer | Path | Why it is safe |
|---|---|---|
| Bootstrap palette | `data/web/css/themes/neuraal-bootstrap.css` | new file, no upstream counterpart |
| UI polish + dark mode | `data/web/css/build/999-neuraal-theme.css` | new file, auto-loaded (the build dir is globbed) |
| PHP settings | `data/web/inc/vars.local.inc.php` | upstream's designated override file, loaded after `vars.inc.php` |
| Text overrides | `data/web/lang/lang.local.<locale>.json` | new files |
| Logos / favicon | `data/web/img/neuraal-*.svg`, `neuraal-favicon.png` | new files |
| favicon + logo routing | `data/conf/nginx/site.neuraal.custom` | `include`d by the generated site config |
| Logos + UI texts in Redis | `data/hooks/phpfpm/neuraal-branding.sh` | entrypoint hook, runs on every container start |

`git merge -X theirs` only rewrites paths that exist on both sides, and
`update.sh` never runs `git clean` or `git reset --hard`. None of the paths above
exist upstream, so they are carried through every update untouched.

Three of them are listed in mailcow's `.gitignore` (`vars.local.inc.php`,
`data/conf/nginx/*.custom`, `data/hooks/phpfpm/*`) because upstream assumes they
are machine-local. They were added to this fork with `git add -f` so that a
normal `git pull` delivers them - **do not `git rm` them.**

Only **one** tracked file is patched: `data/web/inc/prerequisites.inc.php` gains a
5-line loop that merges `lang.local.<locale>.json` over the shipped language file.
If a future mailcow release rewrites that block the loop is dropped and the text
overrides simply stop applying - nothing breaks. Re-add the block after such an
update (search for `Neuraal branding overlays`).

## Files

The scripts here are **build-time only** - they regenerate committed artefacts and
are never needed on a server.

| Script | Purpose |
|---|---|
| `generate_assets.py` | rebuilds the logo SVGs + favicon master from `data/conf/sogo/custom-fulllogo.svg` |
| `build_theme.py` | rebuilds `neuraal-bootstrap.css` by recolouring lumen's accent family to `#061649` |
| `build_lang_overrides.py` | rebuilds the `lang.local.*.json` overlays from the shipped language files |

`data/web/img/neuraal-favicon.png` is a 128x128 rasterisation of
`neuraal-favicon.svg`; regenerate it with any SVG converter, e.g.
`rsvg-convert -w 128 -h 128 data/web/img/neuraal-favicon.svg > data/web/img/neuraal-favicon.png`.

## Deploying

Nothing special - the normal mailcow routine applies the branding:

```bash
cd /opt/mailcow-dockerized
git pull
docker compose pull
docker compose up -d
```

The Redis-backed logos and UI texts are seeded by
`data/hooks/phpfpm/neuraal-branding.sh`, which the php-fpm entrypoint runs on
every container start. It only writes keys that are empty, so anything changed
under **Admin > Configuration > Customize** is never overwritten.

After the first deploy, hard-refresh the browser - the CSS bundle is cached under
`/cache/<hash>.css`.

## Changing the brand later

* Logos and UI texts: **Admin > Configuration > Customize** in the UI (stored in
  Redis; the hook will not overwrite them).
* Colours: edit `NEURAAL` in `build_theme.py` and the `--neuraal-*` variables in
  `999-neuraal-theme.css`, then re-run `build_theme.py`.
* Wording: edit `BRAND` in `build_lang_overrides.py` and re-run it.
* Defaults applied to a fresh install: `BRAND_NAME` / `UI_FOOTER` in
  `data/hooks/phpfpm/neuraal-branding.sh`.

## Known gaps / follow-ups

* `data/web/templates/base.twig` hardcodes `<meta name="theme-color" content="#F5D76E">`
  (the mobile browser chrome colour). It is a tracked file that upstream edits, so it
  was left alone.
* `data/web/img/yubi.ico` and `data/web/img/rspamd_logo_{dark,light}.png` are currently
  replaced with Neuraal artwork in the working tree. Those are third-party product
  marks (the YubiKey icon in the 2FA dialogs and the Rspamd logo on the Rspamd tab);
  consider restoring them with `git checkout -- data/web/img/yubi.ico data/web/img/rspamd_logo_dark.png data/web/img/rspamd_logo_light.png`.
* `data/conf/sogo/custom-favicon.ico` is tracked upstream and is **not** in `.gitignore`,
  unlike the other SOGo `custom-*` logos. Keep a copy of your version.
* SOGo itself is branded separately through `data/conf/sogo/custom-*` - it is not
  affected by anything in this folder.
