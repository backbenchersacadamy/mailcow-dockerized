#!/bin/bash
# Neuraal branding - seeds the UI strings and logos that mailcow stores in Redis
# instead of on disk.
#
# This runs automatically at the end of the php-fpm container entrypoint
# (see data/Dockerfiles/phpfpm/docker-entrypoint.sh, "Run hooks"), so a plain
# `docker compose up -d` is all that is needed - no extra deployment step.
#
# Values are only written when the key is empty, exactly like mailcow's own
# entrypoint seeds Q_MAX_AGE or PASSWD_POLICY. Anything an admin later changes
# under Admin > Configuration > Customize is therefore never overwritten.

set -o pipefail

BRAND_NAME="Neuraal Mail"
UI_FOOTER="&copy; Neuraal"

if [[ ! -z ${REDIS_SLAVEOF_IP} ]]; then
  REDIS_HOST=${REDIS_SLAVEOF_IP}
  REDIS_PORT=${REDIS_SLAVEOF_PORT}
else
  REDIS_HOST="redis"
  REDIS_PORT="6379"
fi

REDIS="redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDISPASS} --no-auth-warning --raw"

# Sets a key only if it is currently unset or empty.
seed() {
  local key="$1" value="$2"
  if [[ -z $(${REDIS} GET "${key}") ]]; then
    printf '%s' "${value}" | ${REDIS} -x SET "${key}" > /dev/null
    echo "  seeded ${key}"
  fi
}

# Same, but the value is an SVG file turned into a data: URI.
seed_logo() {
  local key="$1" file="$2"
  [[ -f "${file}" ]] || return 0
  if [[ -z $(${REDIS} GET "${key}") ]]; then
    seed "${key}" "data:image/svg+xml;base64,$(base64 < "${file}" | tr -d '\n')"
  fi
}

echo "Applying Neuraal branding defaults..."

seed TITLE_NAME "${MAILCOW_HOSTNAME} - ${BRAND_NAME}"
seed MAIN_NAME  "${BRAND_NAME}"
seed UI_FOOTER  "${UI_FOOTER}"

seed_logo MAIN_LOGO      /web/img/neuraal-logo.svg
seed_logo MAIN_LOGO_DARK /web/img/neuraal-logo-dark.svg

exit 0
