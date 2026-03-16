#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/socrates-site-automation/repo}"
OUTPUT_DIR="${OUTPUT_DIR:-/opt/socrates-site-automation/output/site}"
STATE_FILE="${STATE_FILE:-/opt/socrates-site-automation/state/site_automation_state.json}"
DOCROOT="${DOCROOT:-/www/wwwroot/ixinxiang.xyz}"
TOPICS_PER_RUN="${TOPICS_PER_RUN:-2}"
LOCALES="${LOCALES:-en-US,zh-CN}"
VENV_DIR="${VENV_DIR:-$REPO_DIR/.venv}"
SYSTEM_PYTHON="${SYSTEM_PYTHON:-$(command -v python3.11 || command -v python3)}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
PIP_BIN="${PIP_BIN:-$VENV_DIR/bin/pip}"
SOCRATES_BIN="${SOCRATES_BIN:-$VENV_DIR/bin/socrates}"

mkdir -p "$OUTPUT_DIR" "$(dirname "$STATE_FILE")" "$DOCROOT"

cd "$REPO_DIR"
if ! git pull --ff-only; then
  echo "warning: git pull failed, continuing with the current checkout" >&2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
fi

"$PIP_BIN" install --disable-pip-version-check -q -e "$REPO_DIR"

# Refresh the base static site while preserving generated library pages.
rsync -a --delete \
  --exclude 'library/' \
  --exclude 'zh/library/' \
  "$REPO_DIR/site/" "$OUTPUT_DIR/"
mkdir -p "$OUTPUT_DIR/library" "$OUTPUT_DIR/zh/library"
rsync -a "$REPO_DIR/site/library/" "$OUTPUT_DIR/library/"
rsync -a "$REPO_DIR/site/zh/library/" "$OUTPUT_DIR/zh/library/"

"$SOCRATES_BIN" site-generate \
  --publish-dir "$OUTPUT_DIR" \
  --state-file "$STATE_FILE" \
  --topics-per-run "$TOPICS_PER_RUN" \
  --locales "$LOCALES"

rsync -a --delete "$OUTPUT_DIR/" "$DOCROOT/"
