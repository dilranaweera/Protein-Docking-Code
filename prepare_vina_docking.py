import os

def prepare_vina_docking(residue_pos):
    pdbqt_dir = f"Mutants_{residue_pos}"
    docking_dir = f"Docking_{residue_pos}"
    config_template = "config_template.txt"
    receptor = "4g1m_ab.pdbqt"  # Make sure the receptor file exists in the current directory

    os.makedirs(docking_dir, exist_ok=True)

    with open(config_template, 'r') as template, 
open(os.path.join(docking_dir, "config_template.txt"), 'w') as output:
        for line in template:
            if line.strip().startswith("ligand"):
                output.write("ligand = $LIGAND\n")
            else:
                output.write(line)

    for ligand in os.listdir(pdbqt_dir):
        if ligand.endswith(".pdbqt"):
            ligand_name = os.path.splitext(ligand)[0]
            ligand_dir = os.path.join(docking_dir, ligand_name)
            os.makedirs(ligand_dir, exist_ok=True)
            
            os.system(f"cp {receptor} {ligand_dir}/")
            os.system(f"cp {os.path.join(pdbqt_dir, 
ligand)} {ligand_dir}/")
            
            with open(os.path.join(docking_dir, "config_template.txt"), 
'r') as template, open(os.path.join(ligand_dir, "config.txt"), 'w') as config:
                config_content = template.read().replace("$LIGAND", ligand)
                config.write(config_content)

    print(f"Docking preparations complete. Files are in {docking_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python prepare_vina_docking.py <residue_position>")
        sys.exit(1)

    prepare_vina_docking(sys.argv[1])