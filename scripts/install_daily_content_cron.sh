#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/socrates-site-automation/repo}"
OUTPUT_DIR="${OUTPUT_DIR:-/opt/socrates-site-automation/output/site}"
STATE_FILE="${STATE_FILE:-/opt/socrates-site-automation/state/site_automation_state.json}"
DOCROOT="${DOCROOT:-/www/wwwroot/ixinxiang.xyz}"
TOPICS_PER_RUN="${TOPICS_PER_RUN:-2}"
LOCALES="${LOCALES:-en-US,zh-CN}"
CRON_SCHEDULE="${CRON_SCHEDULE:-15 3 * * *}"
LOG_FILE="${LOG_FILE:-/var/log/socrates-site-automation.log}"
CRON_FILE="${CRON_FILE:-/etc/cron.d/socrates-site-automation}"
SCRIPT_PATH="${SCRIPT_PATH:-$REPO_DIR/scripts/run_daily_site_automation.sh}"

cat >"$CRON_FILE" <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
REPO_DIR=$REPO_DIR
OUTPUT_DIR=$OUTPUT_DIR
STATE_FILE=$STATE_FILE
DOCROOT=$DOCROOT
TOPICS_PER_RUN=$TOPICS_PER_RUN
LOCALES=$LOCALES

$CRON_SCHEDULE root $SCRIPT_PATH >> $LOG_FILE 2>&1
EOF

chmod 644 "$CRON_FILE"
touch "$LOG_FILE"

if command -v systemctl >/dev/null 2>&1; then
  systemctl reload crond 2>/dev/null || systemctl reload cron 2>/dev/null || true
fi

echo "Installed cron file at $CRON_FILE"
echo "Scheduled: $CRON_SCHEDULE"
echo "Log file: $LOG_FILE"
