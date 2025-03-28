#!/bin/bash

# Process all PDB files in directory
for pdb_file in *.pdb; do
    # Generate base name without extension
    base_name=$(basename "${pdb_file}" .pdb)
    
    # Run Prodigy and save to log file
    prodigy "${pdb_file}" --temperature 25.0 > "${base_name}.log" 2>&1

    # Extract relevant data from log file
    predicted_affinity=$(grep -oP 'Predicted affinity: \K[-\d.]+' "${base_name}.log")
    temperature=$(grep -oP 'Temperature: \K[\d.]+' "${base_name}.log")
    distance_cutoff=$(grep -oP 'Distance cutoff: \K[\d.]+' "${base_name}.log")
    acc_threshold=$(grep -oP 'Accessibility threshold: \K[\d.]+' "${base_name}.log")

    # Create CSV header if not exists
    if [ ! -f "results.csv" ]; then
        echo "PDB File,Predicted Affinity (kcal/mol),Temperature (C),Distance Cutoff (Å),Accessibility Threshold" > results.csv
    fi

    # Append data to CSV
    echo "${base_name},${predicted_affinity},${temperature},${distance_cutoff},${acc_threshold}" >> results.csv
done
