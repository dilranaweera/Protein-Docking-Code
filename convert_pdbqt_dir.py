## Func: converts an entire directory of pdb files into pdbqts
# Command: python convert_pdbqt_dir.py <directory>

import os
import subprocess

def convert_to_pdbqt(input_dir):
    pdbqt_dir = f"PDBQT_{input_dir}"
    os.makedirs(pdbqt_dir, exist_ok=True)

    for file in os.listdir(input_dir):
        input_file = os.path.join(input_dir, file)
        if os.path.isfile(input_file):
            file_name, file_extension = os.path.splitext(file)
            output_file = os.path.join(pdbqt_dir, f"{file_name}.pdbqt")
            
            command = [
                "obabel",
                input_file,
                "-O", output_file,
                "-xr",
                "-p", "7.4",
                "--partialcharge", "gasteiger",
                "--kekulize"
            ]
            
            try:
                subprocess.run(command, check=True)
                print(f"Converted {file} to {output_file}")
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
    
    convert_to_pdbqt(input_directory)