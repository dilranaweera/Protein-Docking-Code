import os
import sys
from pdbfixer import PDBFixer
from openmm.app import PDBFile

# Define input and output directories
INPUT_DIR = "./pdb"
OUTPUT_DIR = "./fixed_pdb_files"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# List all PDB files in the directory
pdb_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".pdb")]

if not pdb_files:
    print("❌ No PDB files found in", INPUT_DIR)
    sys.exit(1)

# Loop through each PDB file and process it
for pdb_file in pdb_files:
    input_path = os.path.join(INPUT_DIR, pdb_file)
    output_path = os.path.join(OUTPUT_DIR, pdb_file)

    print(f"🔄 Processing {pdb_file}...")

    try:
        # Load the PDB file into PDBFixer
        fixer = PDBFixer(filename=input_path)

        # Add missing heavy atoms and hydrogens
        fixer.findMissingResidues()
        fixer.findMissingAtoms()
        fixer.addMissingAtoms()
        fixer.addMissingHydrogens(pH=7.4)  # Adjust pH if needed

        # Save the fixed PDB file
        with open(output_path, "w") as out_file:
            PDBFile.writeFile(fixer.topology, fixer.positions, out_file)

        print(f"✅ Successfully fixed and saved: {output_path}")

    except Exception as e:
        print(f"❌ Error processing {pdb_file}: {e}")

print("🎉 Batch fixing completed! Check the 'fixed_pdb_files' directory.")