## Func: converts an entire directory of pdb files into pdbqts
# Command: python convert_pdbqt_dir.py <directory>

import openbabel

def convert_to_pdbqt_with_kekulization(input_dir):
    obConversion = openbabel.OBConversion()
    obConversion.SetInAndOutFormats("pdb", "pdbqt")
    
    pdbqt_dir = f"PDBQT_{input_dir}"
    os.makedirs(pdbqt_dir, exist_ok=True)

    for file in os.listdir(input_dir):
        if file.endswith(".pdb"):
            input_file = os.path.join(input_dir, file)
            output_file = os.path.join(pdbqt_dir, file.replace(".pdb", ".pdbqt"))
            
            mol = openbabel.OBMol()
            obConversion.ReadFile(mol, input_file)
            
            # Perform kekulization
            openbabel.OBKekulize(mol)
            
            # Set options for PDBQT conversion
            obConversion.AddOption("r", openbabel.OBConversion.OUTOPTIONS)  # Remove hydrogens
            obConversion.AddOption("p", openbabel.OBConversion.OUTOPTIONS)  # Add polar hydrogens
            obConversion.AddOption("x", openbabel.OBConversion.OUTOPTIONS)  # Compute partial charges
            
            # Convert to PDBQT
            obConversion.WriteFile(mol, output_file)
            
            print(f"Converted {file} to {output_file} with kekulization.")

    print(f"Conversion complete. PDBQT files are in {pdbqt_dir}")