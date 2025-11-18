# Directions:
# 1. Make two folders
# 2. Have the folders and the executable script all in one directory
# 3. Make the script executable: chmod +x /path/to/convert_pdb_to_sdf.sh
#!/bin/zsh

# Define input and output directories
INPUT_DIR="/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25"
OUTPUT_DIR="/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25/sdf_files"

# Process each file in the input directory
for pdb_file in "$INPUT_DIR"/*.pdb; do
    # Get filename without extension
    base_name=$(basename "$pdb_file" .pdb)

    echo "Processing: $pdb_file ..."

    # Step 3: Convert PDB to SDF
    pdb_file="$OUTPUT_DIR/pdb/${base_name}.sdf"
    obabel "$pdb_file" -O --log "$sdf_file"
    ## For energy minimization: --minimize --ff-UFF --steps 1500 --sd
    echo "Final PDB file saved to $sdf_file ✅"

    echo "-----------------------------------"
done

echo "Batch conversion completed. All converted files are in $OUTPUT_DIR"