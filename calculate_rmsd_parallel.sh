# File: calculate_rmsd_parallel.sh
# Usage: ./calculate_rmsd_parallel.sh ref.pdb docked_dir/ output.csv

REF="$1"
DOCKED_DIR="$2"
OUTPUT="$3"

if [ $# -ne 3 ]; then
  echo "Usage: $0 ref.pdb docked_dir/ output.csv"
  exit 1
fi

echo "filename,rmsd" > "$OUTPUT"

export REF
export -f

find "$DOCKED_DIR" -type f -name "*.pdb" | parallel -j+0 '
  FILE={}
  RMSD=$(calculate_rmsd --rotation kabsch -n --format pdb "$REF" "$FILE" 2>/dev/null | tail -n 1)
  echo "$(basename "$FILE"),$RMSD"
' >> "$OUTPUT"

echo "✅ RMSD calculations complete. Results saved to $OUTPUT"