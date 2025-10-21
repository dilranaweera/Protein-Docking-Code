import os
import subprocess
import shutil
from multiprocessing import Pool, cpu_count

def process_ligand(ligand):
    if not ligand.endswith(".pdbqt") or ligand == "4g1m_ab.pdbqt":
        return

    ligand_name = ligand.split('.')[0]
    workspace = f"{ligand_name}_workspace"
    result_dir = f"{ligand_name}_results"
    
    if os.path.exists(result_dir):
        print(f"Skipping {ligand_name}, results exist")
        return

    try:
        # Create isolated workspace
        os.makedirs(workspace, exist_ok=True)
        
        # Copy required files
        shutil.copy2(ligand, os.path.join(workspace, ligand))
        shutil.copy2(f"4g1m_{ligand_name}.trg", os.path.join(workspace, f"4g1m_{ligand_name}.trg"))

        # Run ADCP in isolated directory
        os.chdir(workspace)
        cmd = os.path.expanduser(
            f"~/ADFR10/bin/adcp -t 4g1m_{ligand_name}.trg "
            f"-s {ligand_name}FV -N 200 -n 500000 -cyc "
            f"-o 4g1m_{ligand_name}_redocking -ref {ligand} -nc 0.8"
        )
        
        with open("adcp_output.txt", "w") as f:
            subprocess.run(cmd, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)

    except Exception as e:
        print(f"Error processing {ligand_name}: {str(e)}")
        return
    finally:
        # Return to original directory and clean up
        os.chdir("..")
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        shutil.move(workspace, result_dir)

if __name__ == "__main__":
    # Set thread limits for stability
    os.environ["OMP_NUM_THREADS"] = "1"
    
    ligands = [f for f in os.listdir() if f.endswith(".pdbqt") and f != "4g1m_ab.pdbqt"]
    
    # Use 75% of available cores with process pooling
    num_workers = max(1, int(cpu_count() * 0.75))
    
    print(f"Processing {len(ligands)} ligands with {num_workers} workers")
    
    with Pool(processes=num_workers) as pool:
        # Process in batches to prevent memory bloat
        batch_size = num_workers * 2
        for i in range(0, len(ligands), batch_size):
            pool.map(process_ligand, ligands[i:i+batch_size])


#     tar -cvzf my_archive.tar.gz my_directory