import os

def prepare_vina_docking(residue_pos):
    pdbqt_dir = f"Mutants_{residue_pos}"  # Directory containing mutant ligands
    docking_dir = f"Docking_{residue_pos}"  # Output directory
    config_template = "config_template.txt"  # Template file
    receptor = "receptor.pdbqt"  # Receptor file

    # Ensure docking directory exists
    os.makedirs(docking_dir, exist_ok=True)

    # Read the template once to avoid redundant file reads
    with open(config_template, 'r') as template:
        template_content = template.read()

    for ligand in os.listdir(pdbqt_dir):
        if ligand.endswith(".pdbqt"):
            ligand_base = os.path.splitext(ligand)[0]  # Remove .pdbqt extension

            # Ensure correct file naming: "1fuv_ed2_ALA5"
            ligand_name_corrected = f"{ligand_base}_{residue_pos}"

            # Create a unique directory for each ligand mutation
            ligand_dir = os.path.join(docking_dir, ligand_name_corrected)
            os.makedirs(ligand_dir, exist_ok=True)

            # Copy receptor and ligand to ligand-specific directory
            os.system(f"cp {receptor} {ligand_dir}/")
            os.system(f"cp {os.path.join(pdbqt_dir, ligand)} {ligand_dir}/")

            # Create the config.txt file
            config_path = os.path.join(ligand_dir, "config.txt")
            with open(config_path, 'w') as config:
                config_content = template_content.replace("$LIGAND", ligand)
                config.write(config_content)

    print(f"Docking configurations successfully generated in {docking_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python prepare_vina_docking.py <residue_position>")
        sys.exit(1)
    
    prepare_vina_docking(sys.argv[1])