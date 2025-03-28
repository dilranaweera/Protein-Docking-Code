#!/bin/bash

# Automatically detect the path of the prodigy.py script
PRODIGY_PATH=$(find ~ -type f -name "prodigy.py" 2>/dev/null | head -n 1)

# Ensure PRODIGY is found
if [[ -z "$PRODIGY_PATH" ]]; then
    echo "❌ Error: PRODIGY not found! Clone it from https://github.com/haddocking/prodigy"
    exit 1
fi

# Extract the directory of prodigy.py
PRODIGY_DIR=$(dirname "$PRODIGY_PATH")

# Define input and output directories
INPUT_DIR="./home/dilrana/Desktop/Kuzcera/af_ecm1_hecm1/converted_files/pdb"  # Change if necessary
OUTPUT_FILE="prodigy_results.csv"

# Ensure input directory exists
if [[ ! -d "$INPUT_DIR" ]]; then
    echo "❌ Error: Input directory '$INPUT_DIR' not found!"
    exit 1
fi

# Write header to output CSV file
echo "PDB_File,Binding_Energy_kcal/mol" > "$OUTPUT_FILE"

# Loop through all PDB files in the input directory
for pdb_file in "$INPUT_DIR"/*.pdb; do
    base_name=$(basename "$pdb_file" .pdb)

    echo "🔄 Processing: $pdb_file ..."

    # Run PRODIGY from its directory
    energy=$(
        python "$PRODIGY_DIR/prodigy.py" -i "$pdb_file" -c A B |
        grep "Binding affinity" | awk '{print $NF}'
    )

    # Check if energy was extracted
    if [[ -z "$energy" ]]; then
        echo "❌ Failed to process $pdb_file"
        continue
    fi

    # Save results to CSV
    echo "$base_name,$energy" >> "$OUTPUT_FILE"
    echo "✅ $pdb_file → ΔG = $energy kcal/mol"
done

echo "🎉 Batch processing completed! Results saved in $OUTPUT_FILE"