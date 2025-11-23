#!/bin/zsh
# bulk_sftp_simple.zsh
# Clean and robust sequential SFTP downloader with per-directory logs and single-password SSH ControlMaster session.
# Inputs: REMOTE USER, HOST, BASES. LOCAL BASES, dir (directories you want to pull from in remote system)

set -euo pipefail

### ----------------------
### USER PARAMETERS
### ----------------------
REMOTE_USER="dil2024"
REMOTE_HOST="10.98.8.66"
REMOTE_BASES=(
"/data4/jhoopes/First4kbackup" 
"/data4/jhoopes/Second4kbackup"
)

# Change to where you want downloads placed on Mac
LOCAL_BASE="/Users/dilrana/Desktop/Kuczera/RGD/ADCPtop100lig11.22.25"

LOG_DIR="${LOCAL_BASE}/logs"

# list of directories
dirs=(
 "KKK_main" "KYK_main" "KNK_main" "KRK_main" "KRW_main" "FKR_main" "RKK_main" "KLW_main"
 "KKY_main" "RRK_main" "WKK_main" "HKK_main" "KRF_main" "GKK_main" "GKW_main" "FKK_main"
 "KKI_main" "WKR_main" "KRR_main" "KCK_main" "KGW_main" "KFW_main" "KFK_main" "LKK_main"
 "KKW_main" "KKF_main" "WYK_main" "RYK_main" "FKW_main" "KGK_main" "FRK_main" "KQK_main"
 "KCW_main" "RKR_main" "FNK_main" "LKW_main" "KLY_main" "RWK_main" "FWK_main" "KGY_main"
 "KNY_main" "EKR_main" "KYR_main" "WRK_main" "WFK_main" "WKW_main" "RKY_main" "WWK_main"
 "YKK_main" "KYF_main" "KWK_main" "KNR_main" "MKK_main" "WGK_main" "RMK_main" "KKM_main"
 "HYK_main" "RKF_main" "YKR_main" "HKR_main" "KYY_main" "KLR_main" "KKR_main" "KHW_main"
 "KKS_main" "GWK_main" "YWK_main" "QKW_main" "KLK_main" "FRW_main" "FQK_main" "GCK_main"
 "YYK_main" "WKY_main" "RCK_main" "RRW_main" "RNK_main" "FFK_main" "KKN_main" "KVR_main"
 "KWR_main" "MRK_main" "RQK_main" "FYW_main" "GRK_main" "HKW_main" "FKF_main" "FRR_main"
 "GVK_main" "RKW_main" "WRR_main" "RLK_main" "KNW_main" "KTW_main" "GNK_main" "GYK_main"
 "KFH_main" "WQK_main" "QYK_main" "RCW_main" 
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
  exit_code=$?

  rm -f "${batchfile}"

  if [[ exit_code -eq 0 ]]; then
    echo "[$(date)] SUCCESS: ${d}" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
  else
    echo "[$(date)] FAILED: ${d} exit code ${exit_code}" | tee -a "${DIR_LOG}" "${MASTER_LOG}"
  fi

done

### Close SSH ControlMaster

echo "Closing SSH master connection..."
ssh -S "${CTRL_SOCK}" -O exit "${REMOTE_USER}@${REMOTE_HOST}" 2>/dev/null || true

echo "=== Completed: $(date) ===" >> "${MASTER_LOG}"
echo "All done. Logs are located at: ${LOG_DIR}"