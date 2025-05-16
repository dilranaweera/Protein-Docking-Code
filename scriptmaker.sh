#!/bin/bash

### Modify the SLURM SBATCH below

#SBATCH --job-name=ADCP_Docking
#SBATCH --output=adcp_%j.out
#SBATCH --error=adcp_%j.err
#SBATCH --time=2-00:00:00
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=40
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G 
#SBATCH --array=0-7999

# Exit on error and print commands
set -e
trap "echo 'Job terminated by signal'; exit 1" SIGTERM SIGINT

# Load required modules (if needed)
# module load ADFRsuite/1.0

# Main processing loop
for ligand in *.pdbqt; do
    if [[ "$ligand" == "4g1m_ab.pdbqt" ]]; then
        continue  # Skip receptor file
    fi
    
    ligand_name="${ligand%.*}"
    output_dir="${ligand_name}_results"
    
    if [[ -d "$output_dir" ]]; then
        echo "Skipping $ligand_name - results exist"
        continue
    fi
    
    echo "Processing $ligand_name"
    
    # Create isolated workspace
    workspace="${ligand_name}_workspace"
    mkdir -p "$workspace"
    
    # Copy required files
    cp "$ligand" "$workspace/"
    cp "4g1m_${ligand_name}.trg" "$workspace/" 2>/dev/null || :
    
    # Run ADCP in workspace
    (
        cd "$workspace"
        ~/ADFR10/bin/adcp \
            -t "4g1m_${ligand_name}.trg" \
            -s "${ligand_name}FV" \
            -N 200 \
            -n 500000 \
            -cyc \
            -o "4g1m_${ligand_name}_redocking" \
            -ref "$ligand" \
            -nc 0.8 > "${ligand_name}_adcp.out" 2>&1
    )
    
    # Move and clean up
    mv "$workspace" "$output_dir"
    echo "Completed $ligand_name"
done

echo "All ligands processed successfully"
