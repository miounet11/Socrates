#!/usr/bin/env bash

set -euo pipefail

HOST="${1:?usage: scripts/deploy_site.sh <host> [user]}"
USER_NAME="${2:-root}"
TARGET_ROOT="${TARGET_ROOT:-/var/www/socrates-site}"
NGINX_CONF_SOURCE="${NGINX_CONF_SOURCE:-deploy/nginx/ixinxiang.xyz.conf}"
NGINX_CONF_TARGET="${NGINX_CONF_TARGET:-/etc/nginx/conf.d/ixinxiang.xyz.conf}"
SITE_SOURCE="${SITE_SOURCE:-site/}"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"
RELEASE_DIR="${TARGET_ROOT}/releases/${TIMESTAMP}"

SSH_CMD=(ssh -o StrictHostKeyChecking=no "${USER_NAME}@${HOST}")
SCP_CMD=(scp -o StrictHostKeyChecking=no)
RSYNC_BASE=(rsync -az --delete -e "ssh -o StrictHostKeyChecking=no")

if command -v sshpass >/dev/null 2>&1 && [[ -n "${SSH_PASSWORD:-}" ]]; then
  SSH_CMD=(sshpass -p "${SSH_PASSWORD}" "${SSH_CMD[@]}")
  SCP_CMD=(sshpass -p "${SSH_PASSWORD}" "${SCP_CMD[@]}")
  RSYNC_BASE=(sshpass -p "${SSH_PASSWORD}" "${RSYNC_BASE[@]}")
fi

"${SSH_CMD[@]}" "mkdir -p '${TARGET_ROOT}/releases' '${RELEASE_DIR}'"
"${RSYNC_BASE[@]}" "${SITE_SOURCE}" "${USER_NAME}@${HOST}:${RELEASE_DIR}/"
"${SCP_CMD[@]}" "${NGINX_CONF_SOURCE}" "${USER_NAME}@${HOST}:${NGINX_CONF_TARGET}"
"${SSH_CMD[@]}" "ln -sfn '${RELEASE_DIR}' '${TARGET_ROOT}/current'"
"${SSH_CMD[@]}" "nginx -t && systemctl reload nginx"

echo "Deployed ${SITE_SOURCE} to ${USER_NAME}@${HOST}:${RELEASE_DIR}"
echo "Current symlink: ${TARGET_ROOT}/current"
