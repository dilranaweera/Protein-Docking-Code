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
mkdir -p "$OUTPUT_DIR/pdb"

# Process each CIF file in the input directory
for cif_file in "$INPUT_DIR"/*.cif; do
    # Get filename without extension
    base_name=$(basename "$cif_file" .cif)

    echo "Processing: $cif_file ..."

    # Step 3: Convert Kekulized SDF to PDB
    pdb_file="$OUTPUT_DIR/pdb/${base_name}.pdb"
    obabel "$cif_file" -O "$pdb_file"
    echo "Final PDB file saved to $pdb_file ✅"

    echo "-----------------------------------"
done

echo "🎉 Batch conversion completed! All converted files are in $OUTPUT_DIR"