#!/bin/bash

### Modify the SLURM SBATCH below

#SBATCH --job-name=ADCP_Docking     # Names your job for easy identification
#SBATCH --output=adcp_%j.out        # Saves standard output to this file (%j = job ID)
#SBATCH --error=adcp_%j.err         # Saves error messages to this file
#SBATCH --time=2-00:00:00           # Sets 2-day maximum runtime
#SBATCH --partition=standard        # Assigns job to the "standard" compute partition
#SBATCH --nodes=1                   # Requests 1 compute node
#SBATCH --ntasks-per-node=40        # Requests 40 tasks on that node
#SBATCH --cpus-per-task=1           # Assigns 1 CPU per task
#SBATCH --mem=4G                    # Requests 4GB of memory
#SBATCH --array=0-7999              # Creates a job array with 8000 tasks (0-7999)

# Exit on error
set -e
trap "echo 'Job terminated by signal'; exit 1" SIGTERM SIGINT

# Fix naming since each file is running with each BASH script separately. Standardize the naming
# Get all ligand files
mapfile -t all_ligands < <(ls *.pdbqt | grep -v "4g1m_ab.pdbqt")

# The current array task determines which ligand to process
TASK_ID=$SLURM_ARRAY_TASK_ID
if [[ $TASK_ID -ge ${#all_ligands[@]} ]]; then
    echo "No ligand found for task ID $TASK_ID"
    exit 0
fi

# Get the ligand for this task
ligand="${all_ligands[$TASK_ID]}"
ligand_name="${ligand%.*}"
output_dir="${ligand_name}_results"

echo "Processing $ligand_name (Task $TASK_ID)"

if [[ -d "$output_dir" ]]; then
    echo "Results for $ligand_name already exist, skipping"
    exit 0
fi

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
echo "Completed $ligand_name (Task $TASK_ID)"