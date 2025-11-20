import os
import re
import subprocess

###############################################
# 1. Rewrite ligand chain to C using pdb-tools
###############################################
def rename_chain_to_C(ligand_file, tmp_file):
    """
    Uses pdb-tools to rename ligand chain → C.
    """
    cmd = ["pdb_chain", "-C", ligand_file]
    with open(tmp_file, "w") as out:
        result = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("ERROR running pdb_chain:")
        print(result.stderr)
        raise RuntimeError("pdb_chain failed")


###############################################
# 2. Merge receptor (A,B) + ligand (C)
###############################################
def merge_receptor_and_ligand(receptor_file, ligand_file, output_file):
    """Merge receptor (Chains A+B) with ligand (Chain C)."""
    tmp_lig = ligand_file + ".chainC"

    # step 1: rewrite ligand chain
    rewrite_ligand_chain(ligand_file, tmp_lig)

    # step 2: concatenate
    with open(receptor_file, 'r') as rec, open(tmp_lig, 'r') as lig, open(output_file, 'w') as out:
        # receptor first
        for line in rec:
            if not line.startswith("END"):
                out.write(line)

        # ligand second (already chain C)
        for line in lig:
            if not line.startswith("END"):
                out.write(line)

        out.write("END\n")

    os.remove(tmp_lig)


###############################################
# 3. Process all directories
###############################################
def process_all(receptor_file, base_dir, output_dir):

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # iterate through folders like XXX_main
    for folder in os.listdir(base_dir):
        if not folder.endswith("_main"):
            continue

        ligand_code = folder.replace("_main", "")
        folder_path = os.path.join(base_dir, folder)

        # identify any “best” file like:
        #   4g1m_MGR_redocking_best_1.00.pdb
        #   4g1m_MHK_redocking_best_1.00.pdb
        best_files = [
            f for f in os.listdir(folder_path)
            if re.match(rf"4g1m_{ligand_code}_redocking_best_", f)
        ]

        if not best_files:
            print(f"WARNING: No best files found in {folder_path}")
            continue

        # process each "best" file
        for bf in best_files:
            ligand_file = os.path.join(folder_path, bf)

            # output name such as:
            #   MGR_best_1.00_dockq.pdb
            outname = bf.replace(f"4g1m_{ligand_code}_", "").replace(".pdb", "")
            output_file = os.path.join(output_dir, f"{ligand_code}_{outname}_dockq.pdb")

            print(f"[OK] Merging receptor + {bf}  →  {output_file}")
            merge_receptor_and_ligand(receptor_file, ligand_file, output_file)


###############################################
# MAIN EXECUTION
###############################################
if __name__ == "__main__":

    BASE_DIR = "/Users/dilrana/Desktop/Kuczera/ADCPtop100outputfiles11.17.25"     # directory containing ligands
    OUTPUT_DIR = "/Users/dilrana/Desktop/Kuczera/DockQ_ready"
    RECEPTOR = "/Users/dilrana/Desktop/Kuczera/4g1m_abcopy.pdb"

    if not os.path.isfile(RECEPTOR):
        print("ERROR: Receptor PDB missing:", RECEPTOR)
        exit(1)

    print("Starting DockQ preprocessing…")
    process_all(RECEPTOR, BASE_DIR, OUTPUT_DIR)
    print("Done. DockQ-ready PDBs in:", OUTPUT_DIR)