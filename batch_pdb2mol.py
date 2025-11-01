import os
import subprocess

# Set your input and output directories
input_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/targets'         # directory with .pdb files
output_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/molfiles'       # output directory to save .mol files
os.makedirs(output_dir, exist_ok=True)

# Loop through all PDB files in input_dir
for filename in os.listdir(input_dir):
    if filename.lower().endswith('.pdb'):
        pdb_file = os.path.join(input_dir, filename)
        mol_file = os.path.join(output_dir, os.path.splitext(filename)[0] + '.mol')
        # Run obabel conversion
        cmd = ['obabel', '-ipdb', pdb_file, '-omol', '-O', mol_file] 
        print(f"Converting {filename} → {os.path.basename(mol_file)}")
        subprocess.run(cmd, check=True)

print(f"\n✅ Conversion complete. All .mol files saved in: {output_dir}")