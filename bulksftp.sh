#!/bin/zsh
# bulk_sftp_simple.zsh
# Clean and robust sequential SFTP downloader with per-directory logs
# and single-password SSH ControlMaster session.

set -euo pipefail

### ----------------------
### USER PARAMETERS
### ----------------------
REMOTE_USER="dil2024"
REMOTE_HOST="10.98.8.66"
REMOTE_BASE="/data4/jhoopes/Second4kbackup"

# Change to where you want downloads placed on Mac
LOCAL_BASE="/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25"

LOG_DIR="${LOCAL_BASE}/logs"

# list of directories
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


### Setup folders
 
mkdir -p "${LOCAL_BASE}"
mkdir -p "${LOG_DIR}"

MASTER_LOG="${LOG_DIR}/master_transfer.log"
echo "=== Bulk SFTP started: $(date) ===" >> "${MASTER_LOG}"


### Start SSH ControlMaster

CTRL_DIR="$HOME/.ssh/sftp_ctrl"
mkdir -p "$CTRL_DIR"
CTRL_SOCK="${CTRL_DIR}/ctrl_${REMOTE_USER}@${REMOTE_HOST}"

echo "Starting SSH master connection (enter password once)..."
ssh -o ControlMaster=yes -o ControlPath="${CTRL_SOCK}" -o ControlPersist=600 -fN "${REMOTE_USER}@${REMOTE_HOST}"


### Main download loop

for d in "${dirs[@]}"; do

  echo "Downloading: ${d}"
  DIR_LOG="${LOG_DIR}/${d}.log"

  remote_dir="${REMOTE_BASE}/${d}"
  local_dir="${LOCAL_BASE}/${d}"

  mkdir -p "${local_dir}"

  # SFTP batch file to get everything inside the directory
  batchfile=$(mktemp)
  cat > "${batchfile}" <<EOF
cd ${remote_dir}
lcd ${local_dir}
mget *
EOF

  echo "[$(date)] Starting ${d}" > "${DIR_LOG}"

  # Run SFTP
  sftp -oControlPath="${CTRL_SOCK}" -b "${batchfile}" "${REMOTE_USER}@${REMOTE_HOST}" >> "${DIR_LOG}" 2>&1
  status=$?

  rm -f "${batchfile}"

  if [[ $status -eq 0 ]]; then
    echo "[$(date)] SUCCESS: ${d}" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
  else
    echo "[$(date)] FAILED: ${d} exit code ${status}" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
  fi

done

### Close SSH ControlMaster

echo "Closing SSH master connection..."
ssh -S "${CTRL_SOCK}" -O exit "${REMOTE_USER}@${REMOTE_HOST}" 2>/dev/null || true

echo "=== Completed: $(date) ===" >> "${MASTER_LOG}"
echo "All done. Logs are located at: ${LOG_DIR}"