import os
import sys
import openbabel

def convert_to_pdbqt_with_kekulization(input_dir):
    obConversion = openbabel.OBConversion()
    obConversion.SetInAndOutFormats("pdb", "pdbqt")
    
    # Create output directory for PDBQT files
    pdbqt_dir = "PDBQT_" + input_dir
    if not os.path.exists(pdbqt_dir):  # Check if directory exists (no exist_ok in Python 2.7)
        os.makedirs(pdbqt_dir)

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
            
            print("Converted {} to {} with kekulization.".format(file, output_file))

    print("Conversion complete. PDBQT files are in {}".format(pdbqt_dir))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_pdbqt_dir.py <directory>")
        sys.exit(1)

    input_directory = sys.argv[1]
    if not os.path.isdir(input_directory):
        print("Error: {} is not a valid directory".format(input_directory))
        sys.exit(1)

    convert_to_pdbqt_with_kekulization(input_directory)