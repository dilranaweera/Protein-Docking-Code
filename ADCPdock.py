### Script: iterates through all .pdbqt files in a specified directory.
# For each ligand, it runs AGFR to prepare the target file, then runs ADCP for docking.
# After docking, it extracts the relevant information from lines 11-110 of the log file.
## The extracted data is written to a CSV file, with a blank line separating results from different ## ligands.
## Command to run script:
## agfr -r 5GRD_recH.pdbqt -l 5GRD_pepH.pdbqt -o 5GRD.
## adcp -t 5GRD.trg -s sscsscplsk -N 20 -n 500000 -cys -o 5GRD_redocking -ref 5GRD_pepH.pdbqt -nc 0.8


import subprocess
import os
import csv

def extract_docking_results(log_file):
    results = []
    with open(log_file, 'r') as f:
        lines = f.readlines()[10:110]  # Extract lines 11-110
        for line in lines:
            if line.strip().startswith('DOCKED'):
                parts = line.split()
                results.append({
                    'Modes': parts[1],
                    'Kcal/mol': parts[2],
                    'Dist. from RMSD L.B': parts[3],
                    'Dist. from RMSD U.B': parts[4]
                })
    return results

# Directory containing .pdbqt files
ligand_dir = "Mutants_5"
receptor_file = "4g1m_ab.pdbqt"  # Assuming this is the receptor file name
output_csv = "docking_results.csv"

# Get all .pdbqt files in the ligand directory
ligand_files = [f for f in os.listdir(ligand_dir) if f.endswith('.pdbqt')]

with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ['Ligand', 'Modes', 'Kcal/mol', 'Dist. from RMSD L.B', 'Dist. from RMSD U.B']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for ligand_file in ligand_files:
        ligand_path = os.path.join(ligand_dir, ligand_file)
        output_prefix = f"docking_{os.path.splitext(ligand_file)[0]}"
        
        # Prepare target file
        subprocess.run(['agfr', '-r', receptor_file, '-l', ligand_path, '-o', f'{output_prefix}.trg'])
        
        # Run ADCP
        subprocess.run(['adcp', '-t', f'{output_prefix}.trg', '-s', 'sequence', '-N', '20', '-n', '500000', '-o', output_prefix, '-ref', ligand_path, '-nc', '0.8'])
        
        # Extract results from log file
        log_file = f"{output_prefix}.dlg"
        results = extract_docking_results(log_file)
        
        # Write results to CSV
        for result in results:
            result['Ligand'] = ligand_file
            writer.writerow(result)
        
        # Add a blank line to separate results
        writer.writerow({})

print("Docking completed and results saved to", output_csv)