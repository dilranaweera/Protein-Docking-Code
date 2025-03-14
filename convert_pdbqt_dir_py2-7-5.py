import os
import sys
import subprocess

def convert_to_pdbqt(input_dir):
    pdbqt_dir = "PDBQT_" + input_dir
    os.makedirs(pdbqt_dir) if not os.path.exists(pdbqt_dir) else None

    for file in os.listdir(input_dir):
        if file.endswith(".pdb"):
            input_file = os.path.join(input_dir, file)
            output_file = os.path.join(pdbqt_dir, file.replace(".pdb", ".pdbqt"))
            
            cmd = [
                "obabel",
                input_file, "-O", output_file,
                "-xr",  # Remove hydrogens from receptor
                "-p", "7.4",  # Set pH
                "--partialcharge", "gasteiger",
                "--kekulize"  # Force kekulization
            ]
            
            try:
                subprocess.check_call(cmd)
                print("Converted {}".format(file))
            except subprocess.CalledProcessError as e:
                print("Failed to convert {}: {}".format(file, e))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    convert_to_pdbqt(input_dir)