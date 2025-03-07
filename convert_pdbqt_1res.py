## Function: Code converts all pdb files in a directory into pdbqt at a particular residue position 
# command: python convert_to_pdbqt.py 1699
# (1699) = residue position

import os
import subprocess

def convert_to_pdbqt(residue_pos):
    mutants_dir = f"Mutants_{residue_pos}"
    pdbqt_dir = f"PDBQT_{residue_pos}"

    os.makedirs(pdbqt_dir, exist_ok=True)

    for pdb_file in os.listdir(mutants_dir):
        if pdb_file.endswith(".pdb"):
            input_file = os.path.join(mutants_dir, pdb_file)
            output_file = os.path.join(pdbqt_dir, pdb_file.replace(".pdb", ".pdbqt"))
            
            command = [
                "obabel",
                input_file,
                "-O", output_file,
                "-xr",
                "-p", "7.4",
                "--partialcharge", "gasteiger", 
                "--kekulize"
            ]
            
            subprocess.run(command, check=True)

    print(f"Conversion complete. PDBQT files are in {pdbqt_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python convert_to_pdbqt.py <residue_position>")
        sys.exit(1)
    
    convert_to_pdbqt(sys.argv[1])