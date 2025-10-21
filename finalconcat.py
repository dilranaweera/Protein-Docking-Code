import os

def merge_concat(receptor_file, ligand_file, output_file):
    """Concatenate receptor and ligand PDBs into one output PDB."""
    with open(receptor_file, 'r') as rec, open(ligand_file, 'r') as lig, open(output_file, 'w') as out:
        # Copy receptor lines, excluding END
        for line in rec:
            if not line.startswith("END"):
                out.write(line)
        # Copy ligand lines, excluding HEADER and END
        for line in lig:
            if not line.startswith("HEADER") and not line.startswith("END"):
                out.write(line)
        # Write final END record
        out.write("END\n")

def process_all(receptor_file, base_dir):
    """Process all ligand folders and generate prodigy-ready merged PDBs."""
    for folder in os.listdir(base_dir):
        if folder.endswith("_main"):  # only look at XXX_main folders
            ligand_code = folder.replace("_main", "")  # e.g. XXX

            # Loop through ranked 1–10 ligands
            for rank in range(1, 11):
                ligand_file = os.path.join(
                    base_dir, folder, f"4g1m_{ligand_code}_redocking_ranked_{rank}.pdb"
                )
                output_file = os.path.join(
                    base_dir, f"{ligand_code}_{rank}_prodigy.pdb"
                )

                if os.path.isfile(ligand_file):
                    print(f"Processing {ligand_file} -> {output_file}")
                    merge_concat(receptor_file, ligand_file, output_file)
                else:
                    print(f"WARNING: Missing ligand file {ligand_file}")

if __name__ == "__main__":
    base_dir = os.getcwd()  # working directory with all folders
    receptor_file = os.path.join(base_dir, "4g1m_abchainswap.pdb")

    if not os.path.isfile(receptor_file):
        print(f"ERROR: Receptor file not found: {receptor_file}")
    else:
        process_all(receptor_file, base_dir)
