import os

def prepare_vina_docking(residue_pos):
    pdbqt_dir = f"Mutants_{residue_pos}" #Corrected name for directory containing .pdbqt files
    docking_dir = f"Docking_{residue_pos}"
    config_template = "config_template.txt"
    receptor = "4g1m_ab.pdbqt" #receptor name

    os.makedirs(docking_dir, exist_ok=True)

    with open(config_template, 'r') as template:
        template_content = template.read()

    for ligand in os.listdir(pdbqt_dir):
        if ligand.endswith(".pdbqt"):
            ligand_name = os.path.splitext(ligand)[0] #Correctly gets the file name and extension
            ligand_dir = os.path.join(docking_dir, ligand_name)
            os.makedirs(ligand_dir, exist_ok=True)

            receptor_path = os.path.join(pdbqt_dir, receptor) #Where the files are
            ligand_path = os.path.join(pdbqt_dir, ligand)

            #Copy receptor to the directory
            os.system(f"cp {receptor_path} {ligand_dir}/")
            #Copy .pdbqt ligand name to the directory
            os.system(f"cp {ligand_path} {ligand_dir}/")

            config_content = template_content.replace("$LIGAND", ligand) #Replaces $LIGAND
            config_file_path = os.path.join(ligand_dir, "config.txt") #Proper name with .txt extension
            
            with open(config_file_path, 'w') as config: #Creates correct config files
                config.write(config_content) #Writes the content into it.
            

    print(f"Docking preparations complete. Files are in {docking_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python prepare_vina_docking.py <residue_position>")
        sys.exit(1)

    prepare_vina_docking(sys.argv[1])