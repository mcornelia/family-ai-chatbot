#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="${HOME}/Applications/family-ai-chatbot"
SUPPORT_ROOT="${HOME}/Library/Application Support/Family AI Courier"
LOG_ROOT="${HOME}/Library/Logs/Family AI Courier"
LAUNCH_AGENT="${HOME}/Library/LaunchAgents/com.family-ai.courier.plist"
PYTHON_BIN=""
ACTIVATE=false
UNINSTALL=false

if [[ "${1:-}" == "--activate" ]]; then
  ACTIVATE=true
elif [[ "${1:-}" == "--uninstall" ]]; then
  UNINSTALL=true
elif [[ $# -gt 0 ]]; then
  echo "Usage: ./install.sh [--activate|--uninstall]" >&2
  exit 2
fi

if [[ "${UNINSTALL}" == true ]]; then
  launchctl bootout "gui/$(id -u)/com.family-ai.courier" 2>/dev/null || true
  rm -f "${LAUNCH_AGENT}" "${INSTALL_ROOT}/courier.py"
  rmdir "${INSTALL_ROOT}" 2>/dev/null || true
  echo "Removed the installed Courier runtime and LaunchAgent."
  echo "Preserved configuration, state, outbox, and logs under your Library folder."
  exit 0
fi

for candidate in python3.13 python3.12 python3.11 python3; do
  candidate_path="$(command -v "${candidate}" 2>/dev/null || true)"
  if [[ -n "${candidate_path}" ]] && "${candidate_path}" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    PYTHON_BIN="${candidate_path}"
    break
  fi
done

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Python 3.11 or newer was not found on PATH." >&2
  exit 1
fi

mkdir -p "${INSTALL_ROOT}" "${SUPPORT_ROOT}/outbox" "${LOG_ROOT}" "${HOME}/Library/LaunchAgents"
chmod 700 "${SUPPORT_ROOT}" "${SUPPORT_ROOT}/outbox" "${LOG_ROOT}"
install -m 755 "${PROJECT_ROOT}/courier.py" "${INSTALL_ROOT}/courier.py"

CONFIG_PATH="${SUPPORT_ROOT}/config.json"
STATE_PATH="${SUPPORT_ROOT}/state.json"
if [[ ! -e "${CONFIG_PATH}" ]]; then
  install -m 600 "${PROJECT_ROOT}/config.example.json" "${CONFIG_PATH}"
  echo "Created ${CONFIG_PATH}"
else
  echo "Preserved existing ${CONFIG_PATH}"
fi

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

rendered_plist="$(mktemp "${TMPDIR:-/tmp}/family-ai-courier.XXXXXX")"
trap 'rm -f "${rendered_plist}"' EXIT

sed \
  -e "s|__PYTHON__|$(escape_sed_replacement "${PYTHON_BIN}")|g" \
  -e "s|__COURIER__|$(escape_sed_replacement "${INSTALL_ROOT}/courier.py")|g" \
  -e "s|__CONFIG__|$(escape_sed_replacement "${CONFIG_PATH}")|g" \
  -e "s|__STATE__|$(escape_sed_replacement "${STATE_PATH}")|g" \
  -e "s|__LOG__|$(escape_sed_replacement "${LOG_ROOT}/courier.log")|g" \
  -e "s|__STDOUT__|$(escape_sed_replacement "${LOG_ROOT}/launchd.log")|g" \
  -e "s|__STDERR__|$(escape_sed_replacement "${LOG_ROOT}/courier.error.log")|g" \
  -e "s|__USER_HOME__|$(escape_sed_replacement "${HOME}")|g" \
  "${PROJECT_ROOT}/com.family-ai.courier.plist.template" > "${rendered_plist}"
install -m 600 "${rendered_plist}" "${LAUNCH_AGENT}"

echo "Installed the Courier and LaunchAgent definition."
echo "Edit ${CONFIG_PATH}, replace every REPLACE_ value, and keep dry_run true for the first test."

if [[ "${ACTIVATE}" != true ]]; then
  echo "When configuration and macOS permissions are ready, run: ./install.sh --activate"
  exit 0
fi

if grep -q 'REPLACE_' "${CONFIG_PATH}"; then
  echo "Refusing to activate while ${CONFIG_PATH} still contains REPLACE_ placeholders." >&2
  exit 1
fi

IMSG_PATH="$("${PYTHON_BIN}" -c 'import json,sys; print(json.load(open(sys.argv[1]))["imsg_path"])' "${CONFIG_PATH}")"
CODEX_PATH="$("${PYTHON_BIN}" -c 'import json,sys; print(json.load(open(sys.argv[1]))["codex_path"])' "${CONFIG_PATH}")"
if [[ ! -x "${IMSG_PATH}" ]]; then
  echo "imsg is not executable at ${IMSG_PATH}." >&2
  exit 1
fi
if [[ ! -x "${CODEX_PATH}" ]]; then
  echo "Codex is not executable at ${CODEX_PATH}." >&2
  exit 1
fi

"${CODEX_PATH}" login status
"${PYTHON_BIN}" "${INSTALL_ROOT}/courier.py" --config "${CONFIG_PATH}" list-outbox >/dev/null

launchctl bootout "gui/$(id -u)/com.family-ai.courier" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${LAUNCH_AGENT}"
launchctl print "gui/$(id -u)/com.family-ai.courier"

echo "Courier activated. Keep dry_run true until a foreground test has passed."
