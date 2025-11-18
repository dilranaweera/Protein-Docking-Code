#!/bin/zsh
# bulk_sftp_with_progress.zsh
# Sequential SFTP downloader with single-auth SSH master, per-dir logs, master log,
# and a textual progress bar per subdirectory (polling file counts).
#
# Usage:
#   1. Edit USER PARAMETERS below to match your environment.
#   2. Run: script
#
# Notes:
#  - Requires: OpenSSH client (macOS default) and zsh.
#  - You must be on VPN (if needed) before running.
#  - You will be prompted for your SSH password ONCE to start the master connection.
#  - Script reuses that connection for subsequent sftp/ssh commands.
#  - Transfers are sequential (one directory at a time), safe for HPC environments.

set -euo pipefail

### USER PARAMETERS

REMOTE_USER="dil2024"
REMOTE_HOST="10.98.8.66"                   # <-- host you ssh into
REMOTE_BASE="/data4/jhoopes/Second4kbackup"  # <-- remote parent path containing XXX_main dirs
LOCAL_BASE="/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25" # <-- where to save on your Mac
LOG_DIR="${LOCAL_BASE}/logs"                 # master + per-dir logs
JOBS=1                                       # not used for parallel here; kept for clarity
POLL_INTERVAL=1                              # seconds between progress polls
# list of directories (already *_main)
dirs=(
"WKQ_main" "WRN_main" "WRQ_main" "QNW_main" "WWN_main" "RHF_main" "YQF_main" "RNW_main" "RQF_main" "QHW_main"
"NWQ_main" "RKW_main" "RQW_main" "RFK_main" "WKN_main" "RRQ_main" "RSW_main" "YNY_main" "WRM_main" "YSW_main"
"YKV_main" "NRN_main" "WRK_main" "WQK_main" "YKY_main" "YKF_main" "RNF_main" "YNW_main" "RWQ_main" "VRK_main"
"RNY_main" "WYQ_main" "YRF_main" "MNW_main" "WWI_main" "VWR_main" "VHK_main" "WYH_main" "QQK_main" "WRC_main"
"WKW_main" "WRR_main" "WHK_main" "YKW_main" "YGK_main" "SKK_main" "MKR_main" "VFK_main" "YNF_main" "RRT_main"
"WRG_main" "RWN_main" "WQY_main" "WKT_main" "WQF_main" "YWH_main" "MGR_main" "YGR_main" "WTW_main" "RRH_main"
"YRH_main" "WRI_main" "YRN_main" "VFR_main" "NRQ_main" "RYK_main" "YWK_main" "MRK_main" "RHK_main" "WKF_main"
"WWR_main" "NKW_main" "YRR_main" "WQR_main" "YRY_main" "RRN_main" "QNF_main" "MHK_main" "MKN_main" "WNF_main"
"QKF_main" "YKM_main" "YLY_main" "YQY_main" "YRL_main" "PWK_main" "WWH_main" "SHK_main" "VGK_main" "YWQ_main"
"TKF_main" "SKY_main" "WGR_main" "VKN_main" "WSW_main" "WNI_main" "WHN_main" "VWN_main" "TNW_main" "WKK_main"
)

### helper functions

# Print a simple progress bar in terminal
# Args: current, total, width, prefix
progress_bar() {
  local cur=$1; local tot=$2; local width=$3; local prefix="$4"
  if (( tot <= 0 )); then
    printf "%s [%-${width}s] %d/%d\r" "$prefix" "?" 0 0
    return
  fi
  local pct=$(( cur * 100 / (tot) ))
  local filled=$(( pct * width / 100 ))
  local empty=$(( width - filled ))
  local bar_filled="$(printf '%0.s#' $(seq 1 $filled))"
  local bar_empty="$(printf '%0.s-' $(seq 1 $empty))"
  printf "%s [%s%s] %3d%% %d/%d\r" "$prefix" "$bar_filled" "$bar_empty" "$pct" "$cur" "$tot"
}

# Ensure directories exist
mkdir -p "${LOCAL_BASE}"
mkdir -p "${LOG_DIR}"

MASTER_LOG="${LOG_DIR}/master_transfer.log"
echo "==== Bulk SFTP transfer started: $(date -u +"%Y-%m-%d %H:%M:%SZ") ====" >> "${MASTER_LOG}"

### Start SSH ControlMaster (persistent connection)
# Use a unique control socket
CTRL_DIR="$HOME/.ssh/sftp_ctrl"
mkdir -p "$CTRL_DIR"
CTRL_SOCK="${CTRL_DIR}/ctrl_${REMOTE_USER}@${REMOTE_HOST}"

# If a master is already running with the socket, reuse; otherwise start one (asks for password once)
if ssh -o BatchMode=yes -S "${CTRL_SOCK}" -O check "${REMOTE_USER}@${REMOTE_HOST}" 2>/dev/null; then
  echo "Using existing SSH master connection."
else
  echo "Starting SSH master connection (you will be prompted for password once)..."
  # -M: master, -S socket, -fN: background no command
  ssh -o ControlMaster=yes -o ControlPath="${CTRL_SOCK}" -o ControlPersist=600 -fN "${REMOTE_USER}@${REMOTE_HOST}"
  if [ $? -ne 0 ]; then
    echo "ERROR: failed to establish master SSH connection to ${REMOTE_HOST}" | tee -a "${MASTER_LOG}"
    exit 1
  fi
fi

### Main loop: sequentially download each directory using sftp batch

for d in "${dirs[@]}"; do
  echo "---------------------------------------------"
  echo "Starting download for: ${d}"
  DIR_LOG="${LOG_DIR}/${d}.log"
  echo "Directory: ${d}" > "${DIR_LOG}"
  echo "Start: $(date -u +"%Y-%m-%d %H:%M:%SZ")" >> "${DIR_LOG}"

  remote_dir="${REMOTE_BASE}/${d}"
  local_dir="${LOCAL_BASE}/${d}"

  # create local dir
  mkdir -p "${local_dir}"

  # 1) Get remote file count (regular files) using the master connection
  remote_count_raw=$(ssh -S "${CTRL_SOCK}" "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc 'if [ -d \"${remote_dir}\" ]; then find \"${remote_dir}\" -type f | wc -l; else echo 0; fi'" 2>>"${DIR_LOG}") || remote_count_raw=0
  remote_total=$(echo "${remote_count_raw}" | tr -d '[:space:]')
  if [[ -z "${remote_total}" ]]; then remote_total=0; fi
  echo "Remote files to download: ${remote_total}" >> "${DIR_LOG}"

  # 2) Create sftp batch file to cd into remote dir, lcd to local, and mget *
  batchfile=$(mktemp)
  cat > "${batchfile}" <<EOF
cd ${remote_dir}
lcd ${local_dir}
mget *
EOF

  # 3) Run sftp in background and capture its output into directory log
  #    Use ControlPath to reuse master connection (no password prompt)
  echo "Running sftp batch..." >> "${DIR_LOG}"
  sftp -oControlPath="${CTRL_SOCK}" -b "${batchfile}" "${REMOTE_USER}@${REMOTE_HOST}" >> "${DIR_LOG}" 2>&1 &
  sftp_pid=$!

  # 4) Monitor progress by polling local file count while sftp runs
  downloaded=0
  spinner=( '|' '/' '-' '\' )
  spin_idx=0
  start_time=$(date +%s)
  while kill -0 "${sftp_pid}" 2>/dev/null; do
    # count files in local dir (regular files only)
    downloaded_raw=$(find "${local_dir}" -type f 2>/dev/null | wc -l)
    downloaded=$(echo "${downloaded_raw}" | tr -d '[:space:]')
    # print progress bar
    progress_bar "${downloaded}" "${remote_total}" 40 " ${d}"
    # small spinner to show activity
    printf " %s" "${spinner[spin_idx]}"
    spin_idx=$(( (spin_idx + 1) % ${#spinner[@]} ))
    sleep ${POLL_INTERVAL}
    # erase spinner char (move back)
    printf "\b"
  done

  # wait to capture exit code
  wait "${sftp_pid}"
  sftp_status=$?

  # final counts
  final_downloaded_raw=$(find "${local_dir}" -type f 2>/dev/null | wc -l)
  final_downloaded=$(echo "${final_downloaded_raw}" | tr -d '[:space:]')
  end_time=$(date +%s)
  elapsed=$((end_time - start_time))

  # cleanup batchfile
  rm -f "${batchfile}"

  # Summary and logs
  if [ "${sftp_status}" -eq 0 ]; then
    echo ""   # newline after progress bar
    echo "Completed ${d}: ${final_downloaded}/${remote_total} files in ${elapsed}s" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
    echo "STATUS: OK" >> "${DIR_LOG}"
  else
    echo ""  # newline after progress bar
    echo "FAILED ${d}: exit ${sftp_status}; downloaded ${final_downloaded}/${remote_total} files; see ${DIR_LOG}" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
    echo "STATUS: FAILED (exit ${sftp_status})" >> "${DIR_LOG}"
  fi

  echo "End: $(date -u +"%Y-%m-%d %H:%M:%SZ")" >> "${DIR_LOG}"
  echo "---------------------------------------------" >> "${DIR_LOG}"
  # short pause to be polite to the remote filesystem
  sleep 0.5
done

### Close the SSH master connection

echo "Closing SSH master connection..."
ssh -S "${CTRL_SOCK}" -O exit "${REMOTE_USER}@${REMOTE_HOST}" 2>/dev/null || true

echo "==== Completed: $(date -u +"%Y-%m-%d %H:%M:%SZ") ====" >> "${MASTER_LOG}"
echo "All done. Per-directory logs are in ${LOG_DIR}, master log is ${MASTER_LOG}"