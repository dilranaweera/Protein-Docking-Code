## run: python generate_config_files.py Mutants_5 config_template.txt Docking_5
## python generate_config_files.py <mutants_dir> <config_template_path> <output_dir>

import os

def generate_config_files(mutants_dir, config_template_path, output_dir):
    """
    Generate AutoDock Vina config files for each .pdbqt file in the mutants directory.

    Parameters:
        mutants_dir (str): Path to the directory containing mutant .pdbqt files.
        config_template_path (str): Path to the config template file.
        output_dir (str): Path to the directory where config files will be saved.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the template content
    with open(config_template_path, 'r') as template_file:
        template_content = template_file.read()

    # Iterate over each .pdbqt file in the mutants directory
    for pdbqt_file in os.listdir(mutants_dir):
        if pdbqt_file.endswith(".pdbqt"):
            # Extract the base name of the ligand (e.g., "1fuv_ed2.pdbqt_ALA5")
            ligand_name = os.path.splitext(pdbqt_file)[0]

            # Replace the placeholder "$LIGAND" in the template with the actual ligand file name
            config_content = template_content.replace("$LIGAND", pdbqt_file)

            # Define the name of the output config file
            config_file_name = f"config_{ligand_name}.txt"
            config_file_path = os.path.join(output_dir, config_file_name)

            # Write the updated content to a new config file
            with open(config_file_path, 'w') as config_file:
                config_file.write(config_content)

    print(f"Config files generated successfully in {output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python generate_config_files.py <mutants_dir> <config_template_path> <output_dir>")
        sys.exit(1)

    mutants_dir = sys.argv[1]
    config_template_path = sys.argv[2]
    output_dir = sys.argv[3]

    generate_config_files(mutants_dir, config_template_path, output_dir)