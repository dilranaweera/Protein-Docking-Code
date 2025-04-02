#!/bin/bash
#----------
#Instructions to run:
#make a folder to run your code inside
#make an input directory(folder) named alphafold_results, put all of your folders containing CIF files inside this directory
#make an output directory(folder) named prodigy_results
#put the previous directories in the folder you will run the code in and make sure the code is also in the folder
#open up your terminal and use the cd comand to enter your test folder
#to prepare your computer to run the command: chmod +x Frag_test.sh
#to run your code use the command: ./Frag_test.sh   

input_directory="./alphafold_results"
output_directory="./prodigy_results"

# Check if the input directory exists
if [ ! -d "$input_directory" ]; then
  echo "Directory $input_directory does not exist."
  exit 1
fi

# Ensure obabel and prodigy are installed
command -v obabel >/dev/null 2>&1 || { echo "obabel is required but not installed. Exiting."; exit 1; }
command -v prodigy >/dev/null 2>&1 || { echo "prodigy is required but not installed. Exiting."; exit 1; }

# Loop through each item in the input directory
for folder in "$input_directory"/*/; do
  # Check if it's a directory
  if [ -d "$folder" ]; then
    echo "Processing folder: $folder"
    # Perform actions inside each folder
    for cif_file in "$folder"/*.cif; do
      # Get filename without extension
      base_name=$(basename "$cif_file" .cif)
      echo "Processing: $cif_file ..."
      
      # Step 1: Make output folder
      new_folder="${output_directory}/${base_name}_output"
    
      # Check if the output folder already exists, if not, create it
      if [ ! -d "$new_folder" ]; then
        mkdir "$new_folder"
        echo "Created new folder: $new_folder"
      else
        echo "Folder $new_folder already exists."
      fi
      
      # Step 2: Convert CIF to PDB
      pdb_file="${new_folder}/${base_name}.pdb"
      obabel "$cif_file" -O "$pdb_file"
      if [ $? -ne 0 ]; then
        echo "Error: obabel failed to convert $cif_file to PDB"
        continue  # Skip to the next CIF file
      fi
      echo "Final PDB file saved to $pdb_file"
      
      # Step 3: Copy CIF file to the new folder
      cp "$cif_file" "$new_folder/"
      echo "CIF file copied to $new_folder"
      
      # Step 4: Run Prodigy on PDB file to create a log file, pymol file, and IC file
      log_file="${new_folder}/${base_name}.log"
      
      # Run the prodigy command and redirect the output to the log file
      echo "Running prodigy on $pdb_file..."
      prodigy "$pdb_file" --selection A B --contact_list --pymol_selection > "$log_file" 2>&1
      if [ $? -ne 0 ]; then
        echo "Error: prodigy failed on $pdb_file"
        continue  # Skip to the next PDB file
      fi
      
      echo "Output saved to $log_file"
    done
  fi
done

echo "Script complete"
#---------------------------