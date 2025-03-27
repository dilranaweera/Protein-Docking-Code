# Directions:
# Make two folders: cif_files converted_files
# In the cif_files folder, ensure all of the .cif files needed to be inputted are within that folder. 
# Have the folders and the executable script all in one directory
# Make the script executable: chmod + batch_prepare_pdbqt.sh
# Command: ./batch_prepare_pdbqt.sh
#!/bin/bash

# Define input and output directories
INPUT_DIR="./cif_files"
OUTPUT_DIR="./converted_files"

# Create output directories if they don't exist
mkdir -p "$OUTPUT_DIR/sdf"
mkdir -p "$OUTPUT_DIR/pdb"

# Process each CIF file in the input directory
for cif_file in "$INPUT_DIR"/*.cif; do
    # Get filename without extension
    base_name=$(basename "$cif_file" .cif)

    echo "Processing: $cif_file ..."

    # Step 1: Convert CIF to SDF
    sdf_file="$OUTPUT_DIR/sdf/${base_name}.sdf"
    obabel "$cif_file" -O "$sdf_file" --gen3d --addbond --canonical --strictstereo
    echo "Converted $cif_file to $sdf_file ✅"

    # Step 2: Kekulize SDF
    kekulized_sdf="$OUTPUT_DIR/sdf/${base_name}_kekulized.sdf"
    obabel "$sdf_file" -O "$kekulized_sdf" --kekulize --gen3d
    echo "Kekulized structure saved to $kekulized_sdf ✅"

    # Step 3: Convert Kekulized SDF to PDB
    pdb_file="$OUTPUT_DIR/pdb/${base_name}.pdb"
    obabel "$kekulized_sdf" -O "$pdb_file"
    echo "Final PDB file saved to $pdb_file ✅"

    echo "-----------------------------------"
done

echo "🎉 Batch conversion completed! All converted files are in $OUTPUT_DIR"