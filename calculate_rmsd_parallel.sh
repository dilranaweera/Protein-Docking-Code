# Usage: chmod +x calculate_rmsd_parallel.sh
# ./calculate_rmsd_parallel.sh ref.pdb docked_dir/ output.csv

REF="$1"
DOCKED_DIR="$2"
OUTPUT="$3"

if [ $# -ne 3 ]; then
  echo "Usage: $0 ref.pdb docked_dir/ output.csv"
  exit 1
fi

# Create temporary RMSD calculation script
cat << 'EOF' > /tmp/calc_rmsd.py
import sys
import rmsd

ref_file, target_file = sys.argv[1], sys.argv[2]
ref_coords = rmsd.get_coordinates(ref_file)
target_coords = rmsd.get_coordinates(target_file)

# Align before computing RMSD
ref_coords, target_coords = rmsd.kabsch_rotate(ref_coords, target_coords)
rmsd_val = rmsd.rmsd(ref_coords, target_coords)
print(rmsd_val)
EOF

export REF
export -f
export PYTHON_SCRIPT=/tmp/calc_rmsd.py

echo "filename,rmsd" > "$OUTPUT"

find "$DOCKED_DIR" -type f -name "*.pdb" | parallel -j+0 '
  RMSD=$(python3 $PYTHON_SCRIPT "$REF" {} 2>/dev/null)
  echo "$(basename {}),$RMSD"
' >> "$OUTPUT"

echo "✅ RMSD calculations complete. Results saved to $OUTPUT"