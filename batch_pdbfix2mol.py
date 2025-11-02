import os
import subprocess
from pdbfixer import pdbfixer
from openmm.app import PDBFile
from openmm.unit import nanometer

# === USER CONFIGURATION ===

# Input directory containing original PDB files to fix
input_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/targets'   

# Temporary directory to save fixed PDB files before conversion
fixed_pdb_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/fixedtargets' 
os.makedirs(fixed_pdb_dir, exist_ok=True)

# Output directory for final .mol files
mol_output_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/molfiles'  
os.makedirs(mol_output_dir, exist_ok=True)

# PDBFixer settings
add_missing_residues = True                 # Fix missing residues in middle of chains
keep_heterogens_option = True               # True to keep water?, False for none
ph_value = 7.4                             # pH for adding hydrogens

# Add water box/ion options here (optional)------------------------

# Step 1: Batch fix PDB files using PDBFixer
for filename in os.listdir(input_dir):
    if not filename.lower().endswith('.pdb'):
        continue
    
    input_file = os.path.join(input_dir, filename)
    fixed_file = os.path.join(fixed_pdb_dir, filename)
    print(f"Fixing {filename} ...")
    
    fixer = PDBFixer(filename=input_file)
    
    if add_missing_residues:
        fixer.findMissingResidues()
        # Remove terminal missing residues (optionally)
        chains = list(fixer.topology.chains())
        keys_to_delete = []
        for key in fixer.missingResidues.keys():
            chain = chains[key[0]]
            if key[1] == 0 or key[1] == len(list(chain.residues())):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del fixer.missingResidues[key]
    
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    
    fixer.removeHeterogens(keep_heterogens_option)  # True keeps water only
    
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    
    fixer.addMissingHydrogens(ph_value)
    
    # Optional: Code for Adding water box and ions goes here
    
    # Save fixed PDB
    with open(fixed_file, 'w') as out_file:
        PDBFile.writeFile(fixer.topology, fixer.positions, out_file)
    
    print(f"Fixed PDB saved as {fixed_file}")

print("\n✅ All PDB files fixed successfully.\n")

# Step 2: Convert fixed PDB files to MOL format using Open Babel
for filename in os.listdir(fixed_pdb_dir):
    if not filename.lower().endswith('.pdb'):
        continue
    fixed_file = os.path.join(fixed_pdb_dir, filename)
    mol_file = os.path.join(mol_output_dir, os.path.splitext(filename)[0] + '.mol')
    
    cmd = ['obabel', '-ipdb', fixed_file, '-omol', '-O', mol_file]
    print(f"Converting {filename} → {os.path.basename(mol_file)}")
    subprocess.run(cmd, check=True)

print(f"\n✅ Conversion complete. All .mol files saved in: {mol_output_dir}")
