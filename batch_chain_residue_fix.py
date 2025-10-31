import os

input_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/targets'        # Directory of your docked PDBs
output_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/fixedtargets'              # Where to write fixed files
os.makedirs(output_dir, exist_ok=True)

start_resi_c = 5001   # Chain A (to C) peptide residue renumber start

for filename in os.listdir(input_dir):
    if not filename.endswith('.pdb'):
        continue
    input_file = os.path.join(input_dir, filename)
    output_file = os.path.join(output_dir, filename)

    # For renumbering chain C (was chain A): track each unique residue
    resmap_c = {}
    current_resi_c = start_resi_c

    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line in fin:
            if line.startswith(('ATOM', 'HETATM')) and len(line) > 21:
                chain = line[21]
                resnum_raw = line[22:26]
                resnum_int = int(resnum_raw)

                # Chain A (peptide): becomes C, new numbering
                if chain == 'A':
                    new_chain = 'C'
                    key = (chain, resnum_int)
                    if key not in resmap_c:
                        resmap_c[key] = current_resi_c
                        current_resi_c += 1
                    new_resnum = resmap_c[key]
                    resnum_str = f"{new_resnum:>4}"

                    line = line[:21] + new_chain + resnum_str + line[26:]
                # Chain B: becomes A, preserve numbering
                elif chain == 'B':
                    new_chain = 'A'
                    line = line[:21] + new_chain + line[22:]
                # Chain C: becomes B, preserve numbering
                elif chain == 'C':
                    new_chain = 'B'
                    line = line[:21] + new_chain + line[22:]
                # All other chains: untouched
                fout.write(line)
            else:
                fout.write(line)
    print(f"Processed {filename}")

print(f"\n✅ All PDB files processed! Chain modifications and renumbering complete. Output: {output_dir}")