#!/bin/bash
# For convert_cif_to_pdbqt.sh script:  
## Make the script executable:
chmod +x batch_prepare_pdbqt.sh

## Run script
# ./batch_prepare_pdbqt.sh

# Define input and output directories
INPUT_DIR="./Mutants_1_2_3"
OUTPUT_DIR="./pdbqt_files"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Loop through all .pdb files in the input directory
for pdb_file in "$INPUT_DIR"/*.pdb; do
    # Extract filename without extension
    base_name=$(basename "$pdb_file" .pdb)

    echo "Processing: $pdb_file ..."

    # Convert PDB to PDBQT using prepare_ligand4.py
    output_pdbqt="$OUTPUT_DIR/${base_name}.pdbqt"
    prepare_ligand4.py -l "$pdb_file" -o "$output_pdbqt" -A bonds_hydrogens

    if [[ -f "$output_pdbqt" ]]; then
        echo "✅ Successfully created: $output_pdbqt"
    else
        echo "❌ Failed to create: $output_pdbqt"
    fi

    echo "-----------------------------------"
done

echo "🎉 Batch conversion completed! PDBQT files saved in $OUTPUT_DIR"