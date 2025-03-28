#!/bin/bash

# Define input directory containing PDB files
INPUT_DIR="./pdb"
OUTPUT_FILE="prodigy_results.csv"

# Ensure PRODIGY is installed
if [ ! -f "prodigy.py" ]; then
    echo "Error: PRODIGY is not installed. Clone it from https://github.com/haddocking/prodigy"
    exit 1
fi

# Write header to the output CSV file
echo "PDB_File,Binding_Energy_kcal/mol" > "$OUTPUT_FILE"

# Loop through all PDB files in the input directory
for pdb_file in "$INPUT_DIR"/*.pdb; do
    # Extract the filename without extension
    base_name=$(basename "$pdb_file" .pdb)

    echo "Processing: $pdb_file ..."

    # Run PRODIGY and capture binding energy output
    energy=$(python prodigy.py -i "$pdb_file" -c A B | grep "Binding affinity" | awk '{print $NF}')

    # Check if energy value was extracted
    if [[ -z "$energy" ]]; then
        echo "❌ Failed to process $pdb_file"
        continue
    fi

    # Save results to CSV
    echo "$base_name,$energy" >> "$OUTPUT_FILE"
    echo "✅ $pdb_file → ΔG = $energy kcal/mol"
done

echo "🎉 Batch processing completed! Results saved in $OUTPUT_FILE"