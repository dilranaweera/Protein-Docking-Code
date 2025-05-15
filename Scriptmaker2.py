import os
import subprocess

def create_and_run_scripts(ligands_dir):
    ligands_dir = os.path.abspath(ligands_dir)
    scripts_dir = os.path.join(ligands_dir)
    
    # Create a directory for generated scripts if it doesn't exist
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
    
    # Loop through all .pdbqt files in the directory
    for ligand in os.listdir(ligands_dir):
        if ligand.endswith(".pdbqt") and ligand != "4g1m_ab.pdbqt":  # Exclude receptor file
            ligand_path = os.path.join(ligands_dir, ligand)
            
            # Extract the base name of the ligand without the file extension
            ligand_name = ligand.split('.')[0]
            
            # Construct the target output file path
            output_trg = os.path.join(ligands_dir, f"4g1m_{ligand_name}.trg")
            
            # Generate a new Python script name for this ligand
            script_name = os.path.join(scripts_dir, f"run_{ligand_name}.py")
            
            # Construct the Python command for the current ligand
            command = f"""import subprocess
import os
import shutil
import glob

output_file = f"{ligand_name}_adcp_output.txt"
# Define directory for organizing results
main_folder = f"{ligand_name}_main"
# Create the folder if it does not exist
if not os.path.exists(main_folder):
    os.makedirs(main_folder)

# Expand the ~ symbol to the full home directory
command = os.path.expanduser("~/ADFR10/bin/adcp -t 4g1m_{ligand_name}.trg -s {ligand_name}FV -N 200 -n 500000 -cyc -o 4g1m_{ligand_name}_redocking -ref {ligand} -nc 0.8")

# Run the command
with open(output_file, "w") as out_file:
    process = subprocess.run(command, shell=True, check=True, stdout=out_file, stderr=out_file, text=True)

# Move all files with "RGD" in their name into the RGD_main folder
for file in glob.glob(f"*{ligand_name}*"):
    if file != main_folder:  # Exclude the main folder
        shutil.move(file, os.path.join(main_folder, file))

"""
            
            # Write the Python command to the script file
            with open(script_name, 'w') as script_file:
                script_file.write(command)
            
            # Make the script executable
            os.chmod(script_name, 0o755)
            
            # Run the script
            print(f"Running Python script: {script_name}")
            subprocess.run(["python3", script_name], check=True)

if __name__ == "__main__":
    ligands_dir = os.getcwd()  # Set ligands_dir to the current working directory
    create_and_run_scripts(ligands_dir)