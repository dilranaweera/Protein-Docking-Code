import os

input_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/targets'         # Change to your correct input directory
output_dir = '/Users/dilrana/Desktop/Kuczera/RGDdockedtop10PRODIGY/fixedtargets'               # Change to your correct output directory
os.makedirs(output_dir, exist_ok=True)

start_resi_c = 5001       # Chain C ("peptide") renumber starts here

for filename in os.listdir(input_dir):
    if not filename.lower().endswith('.pdb'):
        continue
    input_file = os.path.join(input_dir, filename)
    output_file = os.path.join(output_dir, filename)

    # Map residue (res name + number) → new residue number for chain C, but skip calcium ions
    resmap_c = {}
    current_resi_c = start_resi_c

    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line in fin:
            chain = line[21] if len(line) > 21 else ' '
            resname = line[17:20].strip()
            resnum_raw = line[22:26]
            atom_name = line[12:16].strip()

            # Check if it's an ATOM or HETATM record
            if line.startswith(('ATOM', 'HETATM')) and len(line) > 26:
                # Chain switching logic
                if chain == 'A':
                    new_chain = 'C'
                elif chain == 'B':
                    new_chain = 'A'
                elif chain == 'C':
                    new_chain = 'B'
                else:
                    new_chain = chain  # Leave other chains unchanged

                # Mutant peptide renumbering (Chain C), but do NOT touch calcium ions
                if new_chain == 'C' and resname != 'CA':
                    key = (chain, resnum_raw)
                    if key not in resmap_c:
                        resmap_c[key] = current_resi_c
                        current_resi_c += 1
                    new_resnum = resmap_c[key]
                    resnum_str = f"{new_resnum:>4}"  # Right-justified, 4 spaces
                else:
                    resnum_str = resnum_raw

                # Write the updated PDB record, preserving formatting as much as possible
                revised = line[:21] + new_chain + resnum_str + line[26:]
                fout.write(revised)
            else:
                fout.write(line)
    print(f"Processed {filename}")

print(f"\n✅ All docked PDB files now have matching format and correct chain mapping.\nCalcium ions (resname 'CA') are NOT renumbered to peptide range. Output: {output_dir}")
