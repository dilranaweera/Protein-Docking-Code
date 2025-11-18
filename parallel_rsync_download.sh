#!/bin/zsh

# ---- USER PARAMETERS ----
REMOTE_USER="dil2024"
REMOTE_HOST="10.98.8.66"
REMOTE_BASE="/data4/jhoopes/Second4kbackup"
LOCAL_BASE="/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25"

# Number of parallel downloads
JOBS=4

# 100 peptide directories
dirs=(
"WKQ_main" "WRN_main" "WRQ_main" "QNW_main" "WWN_main" "RHF_main" "YQF_main" "RNW_main" "RQF_main" "QHW_main" "NWQ_main" "RKW_main" "RQW_main" "RFK_main"
"WKN_main" "RRQ_main" "RSW_main" "YNY_main" "WRM_main" "YSW_main" "YKV_main" "NRN_main" "WRK_main" "WQK_main" "YKY_main" "YKF_main" "RNF_main" "YNW_main"
"RWQ_main" "VRK_main" "RNY_main" "WYQ_main" "YRF_main" "MNW_main" "WWI_main" "VWR_main" "VHK_main" "WYH_main" "QQK_main" "WRC_main" "WKW_main" "WRR_main"
"WHK_main" "YKW_main" "YGK_main" "SKK_main" "MKR_main" "VFK_main" "YNF_main" "RRT_main" "WRG_main" "RWN_main" "WQY_main" "WKT_main" "WQF_main" "YWH_main"
"MGR_main" "YGR_main" "WTW_main" "RRH_main" "YRH_main" "WRI_main" "YRN_main" "VFR_main" "NRQ_main" "RYK_main" "YWK_main" "MRK_main" "RHK_main" "WKF_main"
"WWR_main" "NKW_main" "YRR_main" "WQR_main" "YRY_main" "RRN_main" "QNF_main" "MHK_main" "MKN_main" "WNF_main" "QKF_main" "YKM_main" "YLY_main" "YQY_main"
"YRL_main" "PWK_main" "WWH_main" "SHK_main" "VGK_main" "YWQ_main" "TKF_main" "SKY_main" "WGR_main" "VKN_main" "WSW_main" "WNI_main" "WHN_main" "VWN_main"
"TNW_main" "WKK_main"
)

# Start ssh-agent if not running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval $(ssh-agent -s)
fi

# Add SSH key (will prompt for password if needed)
ssh-add -t 3600 ~/.ssh/id_rsa 2>/dev/null

echo "🔐 SSH-Agent running (password caching active)"
echo "📊 Starting parallel rsync downloads ($JOBS parallel jobs)..."
echo ""

# Export variables for parallel
export REMOTE_USER REMOTE_HOST REMOTE_BASE LOCAL_BASE

# Use GNU parallel
parallel --eta -j "$JOBS" --joblog rsync_joblog.txt --halt 1 '
    d={}
    remote_path="${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/${d}/"
    local_path="${LOCAL_BASE}/${d}/"
    
    echo "⬇️  [$(date +%H:%M:%S)] Downloading: $d"
    
    rsync -avz --progress --partial --stats -e "ssh -o ConnectTimeout=10" \
        "$remote_path" \
        "$local_path" 2>&1 | sed "s/^/    /"  # Indent rsync output for clarity
    
    if [ $? -eq 0 ]; then
        echo "✅ Completed: $d"
    else
        echo "❌ Failed: $d"
    fi
    echo ""
' ::: "${dirs[@]}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Sync completed!"
echo "📁 All files saved to: $LOCAL_BASE"
echo "📋 Log saved to: rsync_joblog.txt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"