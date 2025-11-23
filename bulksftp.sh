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
REMOTE_BASE="/data4/jhoopes/Second4kbackup"

# Change to where you want downloads placed on Mac
LOCAL_BASE="/Users/dilrana/Desktop/Kuczera/RGD/PRODtop100lig11.22.25"

LOG_DIR="${LOCAL_BASE}/logs"

# list of directories
dirs=(
"MHR_main"
"MHT_main"
"MHY_main"
"MKT_main"
"MKV_main"
"MLQ_main"
"MQW_main"
"MRN_main"
"MRT_main"
"MWQ_main"
"NWQ_main"
"QHW_main"
"QNL_main"
"QNW_main"
"QQC_main"
"QTF_main"
"RFG_main"
"RHF_main"
"RLG_main"
"RNW_main"
"RQF_main"
"RTF_main"
"SQY_main"
"TQF_main"
"VHH_main"
"VRG_main"
"VRN_main"
"VRQ_main"
"WCG_main"
"WHT_main"
"WKQ_main"
"WND_main"
"WNN_main"
"WNS_main"
"WPE_main"
"WRD_main"
"WRN_main"
"WRQ_main"
"WWN_main"
"YHY_main"
"YQF_main"
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