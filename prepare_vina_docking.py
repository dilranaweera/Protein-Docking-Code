import os

def prepare_vina_docking(residue_pos):
    pdbqt_dir = f"Mutants_{residue_pos}"
    docking_dir = f"Docking_{residue_pos}"
    config_template = "config_template.txt"
    receptor = "4g1m_ab.pdbqt"  # Make sure the receptor file exists in the current directory

    os.makedirs(docking_dir, exist_ok=True)

    with open(config_template, 'r') as template:
        template_content = template.read()

    for ligand in os.listdir(pdbqt_dir):
        if ligand.endswith(".pdbqt"):
            ligand_name = os.path.splitext(ligand)[0]
            config_file_name = f"config_{ligand_name}.txt"
            config_file_path = os.path.join(docking_dir, config_file_name)

            # Replace placeholders in the config content
            config_content = template_content.replace("$LIGAND", ligand)  # Correctly replace $LIGAND placeholder
            config_content = config_content.replace("receptor = receptor.pdbqt", f"receptor = {receptor}")  # Ensure the receptor name is correct

            with open(config_file_path, 'w') as config:
                config.write(config_content)

    print(f"Docking preparations complete. Files are in {docking_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python prepare_vina_docking.py <residue_position>")
        sys.exit(1)

    prepare_vina_docking(sys.argv[1])