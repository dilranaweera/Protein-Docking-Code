#!/bin/bash

# Base directory containing all results
BASE_DIR="/Users/dilrana/Desktop/Kuczera/af_ecm1_hecm1/cif_files/prodigy_results"

# Output CSV file
OUTPUT_CSV="${BASE_DIR}/aggregated_results.csv"

# Create CSV header
echo "Category,Value,Source Directory" > "$OUTPUT_CSV"

# Process all log files in subdirectories
find "$BASE_DIR" -type f -name "*.log" -print0 | while IFS= read -r -d $'\0' log_file; do
    # Extract directory path relative to base
    rel_path=$(dirname "${log_file#$BASE_DIR/}")
    
    # Process log file with awk
    awk -F ': ' -v dir="$rel_path" '
    BEGIN {OFS=","}
    {
        # Remove ANSI escape codes and clean line
        gsub(/\x1b\[[0-9;]*m/,"",$0)
        gsub(/^[[:space:]]+|[[:space:]]+$/,"",$0)
        
        # Split into category and value
        if (match($0, /^(\[.+?\])(.*)/, parts)) {
            category = parts[1]
            value = parts[2]
            gsub(/^[[:space:]:]+/,"",value)  # Clean up value
            print category, value, dir
        }
    }' "$log_file" >> "$OUTPUT_CSV"
done

echo "Processing complete. Results saved to: $OUTPUT_CSV"