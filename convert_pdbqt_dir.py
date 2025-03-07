## Func: converts an entire directory of pdb files into pdbqts
# Command: python convert_pdbqt_dir.py <directory>

import os
import subprocess

def convert_to_pdbqt_with_kekulization(input_dir):
    # Create output directory for PDBQT files
    pdbqt_dir = f"PDBQT_{input_dir}"
    os.makedirs(pdbqt_dir, exist_ok=True)

    for file in os.listdir(input_dir):
        input_file = os.path.join(input_dir, file)
        if os.path.isfile(input_file) and file.endswith(".pdb"):
            file_name, _ = os.path.splitext(file)
            output_file = os.path.join(pdbqt_dir, f"{file_name}.pdbqt")
            
            # Command to convert PDB to PDBQT with kekulization
            command = [
                "obabel",
                input_file,
                "-O", output_file,
                "-xr",  # Remove hydrogens from receptor
                "-p", "7.4",  # Set pH to 7.4
                "--partialcharge", "gasteiger",  # Assign Gasteiger partial charges
                "--kekulize"  # Force kekulization for aromatic structures
            ]
            
            try:
                # Run the conversion command
                subprocess.run(command, check=True)
                print(f"Converted {file} to {output_file} with kekulization.")
            except subprocess.CalledProcessError as e:
                print(f"Error converting {file}: {e}")

    print(f"Conversion complete. PDBQT files are in {pdbqt_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python convert_to_pdbqt.py <input_directory>")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    if not os.path.isdir(input_directory):
        print(f"Error: {input_directory} is not a valid directory")
        sys.exit(1)
    
    convert_to_pdbqt_with_kekulization(input_directory)