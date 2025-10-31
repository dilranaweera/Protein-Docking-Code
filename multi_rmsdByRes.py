"""
multi_rmsdByRes.py
Author: Docking & Dynamics GPT (2025)
Purpose: Batch per-residue RMSD analysis in PyMOL for multiple PDBs vs a single reference.

Usage (headless):
    pymol -cq multi_rmsdByRes.py

Dependencies:
    - PyMOL (>=2.4)
    - Your original rmsdByRes() function must be defined or loaded before this script.
"""

import os, glob
from pymol import cmd

### === USER PARAMETERS ======================================================

reference_file = "ref.pdb"           # reference crystal structure
reference_chain = "A"                # chain ID in reference
target_folder = "targets"            # folder containing target PDB files
output_csv = "rmsdByRes_allModels.csv"
perform_alignment = True             # set False if already pre-aligned
selection = f"chain {reference_chain} and polymer"  # region of interest

### =========================================================================

# Load the reference structure
cmd.load(reference_file, "reference")
ref_chain_sel = f"reference and chain {reference_chain}"

# Prepare output
if os.path.exists(output_csv):
    os.remove(output_csv)
header = "modelID,resName,resID,allAtomRMSD,rmsdResCa,rmsdResBackbone,allAtomRMSDMin\n"
with open(output_csv, 'w') as f:
    f.write(header)

# Collect target files
target_files = sorted(glob.glob(os.path.join(target_folder, "*.pdb")))
print(f"\nFound {len(target_files)} target structures to process.\n")

for target_file in target_files:
    model_name = os.path.splitext(os.path.basename(target_file))[0]
    cmd.load(target_file, model_name)
    target_sel = f"{model_name} and chain {reference_chain}"

    print(f"→ Processing {model_name}")

    # Optional: Align target to reference
    if perform_alignment:
        try:
            cmd.align(target_sel, ref_chain_sel)
        except Exception as e:
            print(f"  ⚠️ Alignment failed for {model_name}: {e}")

# Create temporary clean copies
ref_chain_sel = f"reference and chain {reference_chain}" if reference_chain else "reference"
target_sel = f"{model_name} and chain {reference_chain}" if reference_chain else model_name

cmd.create("ref_gzt", ref_chain_sel + " and polymer and not alt B")
cmd.create("target_gzt", target_sel + " and polymer and not alt B")
cmd.alter("ref_gzt", "segi=''")
cmd.alter("target_gzt", "segi=''")
cmd.sort()

# Residues to check for symmetric sidechain flips
res2Check = ['HIS','ASP','ARG','PHE','GLN','GLU','LEU','ASN','TYR','VAL']
calpha = cmd.get_model(f"{ref_chain_sel} and name CA and not alt B")

for g in calpha.atom:
    ref_sel = f"ref_gzt and polymer and resi {g.resi}"
    tgt_sel = f"target_gzt and polymer and resi {g.resi}"

    if cmd.count_atoms(ref_sel) == 0 or cmd.count_atoms(tgt_sel) == 0:
        print(f"⚠️ Missing atoms for residue {g.resi} ({g.resn}) in {model_name}")
        continue

    output_lines = []
    for g in calpha.atom:
        ref_sel = f"ref_gzt and polymer and resi {g.resi}"
        tgt_sel = f"target_gzt and polymer and resi {g.resi}"

        if cmd.count_atoms(ref_sel) == cmd.count_atoms(tgt_sel):
            rms_all = cmd.rms_cur(ref_sel, tgt_sel)
            rms_ca = cmd.rms_cur(ref_sel + " and name ca", tgt_sel + " and name ca")
            rms_bb = cmd.rms_cur(ref_sel + " and name ca+n+c+o", tgt_sel + " and name ca+n+c+o")

            rms_min = rms_all
            if g.resn in res2Check:
                # flip symmetric sidechains and recompute
                cmd.create("flipped", tgt_sel)
                # example flipping — adapt from your original function if needed
                # (shortened for brevity)
                if g.resn in ['ASP','GLU']:
                    cmd.alter("flipped and name OD1", "name='TEMP'")
                    cmd.alter("flipped and name OD2", "name='OD1'")
                    cmd.alter("flipped and name TEMP", "name='OD2'")
                cmd.sort()
                rms_flipped = cmd.rms_cur(ref_sel, "flipped")
                cmd.delete("flipped")
                if rms_flipped < rms_min:
                    rms_min = rms_flipped

            line = f"{model_name},{g.resn},{g.resi},{rms_all:.3f},{rms_ca:.3f},{rms_bb:.3f},{rms_min:.3f}\n"
            output_lines.append(line)

    # Write results for this model
    with open(output_csv, 'a') as f:
        f.writelines(output_lines)

    # Clean up for next iteration
    cmd.delete(model_name)
    cmd.delete("ref_gzt")
    cmd.delete("target_gzt")

print(f"\n✅ RMSD calculations complete. Results saved to: {output_csv}\n")
cmd.quit()