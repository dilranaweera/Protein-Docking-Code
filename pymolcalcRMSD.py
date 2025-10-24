# Enhanced RGD Peptide RMSD Calculator for PyMOL
# Based on rmsdByResidue from PyMOLWiki
# Optimized for peptide docking analysis

from pymol import cmd, stored
import sys
import os
import csv
from datetime import datetime

def is_non_zero_file(fpath):
    """Check if file exists and has content"""
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

def switchName(residueSelection, atomName1, atomName2):
    """Switch the name of two atoms for symmetry correction"""
    cmd.alter(residueSelection + " and name " + atomName1, 'name="gzt"')
    cmd.alter(residueSelection + " and name " + atomName2, 'name="' + atomName1 + '"')
    cmd.alter(residueSelection + " and name gzt", 'name="' + atomName2 + '"')

def flipAtomName(targetResidueSelection):
    """Handle symmetric residues (essential for RGD variants)"""
    cmd.create("flippedRes", targetResidueSelection + " and not alt B")
    targetResidueCa = cmd.get_model("flippedRes and name CA")
    
    # Symmetry corrections for amino acids commonly in RGD variants
    symmetry_map = {
        'ARG': [('NH1', 'NH2')],
        'HIS': [('ND1', 'CD2'), ('CE1', 'NE2')],
        'ASP': [('OD1', 'OD2')],
        'PHE': [('CD1', 'CD2'), ('CE1', 'CE2')],
        'GLN': [('OE1', 'NE2')],
        'GLU': [('OE1', 'OE2')],
        'LEU': [('CD1', 'CD2')],
        'ASN': [('OD1', 'ND2')],
        'TYR': [('CD1', 'CD2'), ('CE1', 'CE2')],
        'VAL': [('CG1', 'CG2')]
    }
    
    for atom in targetResidueCa.atom:
        if atom.resn in symmetry_map:
            for atom1, atom2 in symmetry_map[atom.resn]:
                switchName("flippedRes", atom1, atom2)
    
    cmd.sort()
    return "flippedRes"

def calculatePeptideRMSD(referenceStructure, targetStructure, peptideChain="A", 
                        outputPrefix="", motifStart=1, motifEnd=3):
    """
    Enhanced RMSD calculation for RGD peptide variants
    
    Parameters:
    - referenceStructure: Wild-type or reference structure name
    - targetStructure: Docked peptide structure name
    - peptideChain: Chain identifier for peptides (usually "A")
    - outputPrefix: Prefix for output files
    - motifStart/motifEnd: Residue range for RGD motif (1-indexed)
    """
    
    # Create clean temporary objects
    cmd.create("ref_temp", f"{referenceStructure} and chain {peptideChain} and polymer and not alt B")
    cmd.alter("ref_temp", "chain='A'")
    cmd.alter("ref_temp", "segi=''")
    
    cmd.create("target_temp", f"{targetStructure} and chain {peptideChain} and polymer and not alt B")
    cmd.alter("target_temp", "chain='A'")
    cmd.alter("target_temp", "segi=''")
    
    # Align structures first (crucial for meaningful RMSD)
    cmd.align("target_temp", "ref_temp")
    
    # Initialize results storage
    results = []
    symmetric_residues = ['HIS', 'ASP', 'ARG', 'PHE', 'GLN', 'GLU', 'LEU', 'ASN', 'TYR', 'VAL']
    
    # Get all CA atoms for iteration
    ca_atoms = cmd.get_model("ref_temp and name CA")
    
    print(f"\nAnalyzing {len(ca_atoms.atom)} residues...")
    print(f"RGD motif region: residues {motifStart}-{motifEnd}")
    
    for atom in ca_atoms.atom:
        resi = atom.resi
        resname = atom.resn
        
        # Check if both structures have this residue
        ref_count = cmd.count_atoms(f"ref_temp and resi {resi}")
        target_count = cmd.count_atoms(f"target_temp and resi {resi}")
        
        if ref_count > 0 and target_count > 0:
            # Calculate different RMSD types
            rmsd_all = cmd.rms_cur(f"ref_temp and resi {resi}", 
                                  f"target_temp and resi {resi}")
            
            rmsd_ca = cmd.rms_cur(f"ref_temp and resi {resi} and name CA", 
                                 f"target_temp and resi {resi} and name CA")
            
            rmsd_backbone = cmd.rms_cur(f"ref_temp and resi {resi} and name CA+N+C+O", 
                                       f"target_temp and resi {resi} and name CA+N+C+O")
            
            # Calculate minimum RMSD considering symmetry
            rmsd_min = rmsd_all
            used_symmetry = False
            
            if resname in symmetric_residues:
                try:
                    flipped_res = flipAtomName(f"target_temp and resi {resi}")
                    rmsd_flipped = cmd.rms_cur(f"ref_temp and resi {resi}", flipped_res)
                    
                    if rmsd_flipped < rmsd_all:
                        rmsd_min = rmsd_flipped
                        used_symmetry = True
                    
                    cmd.delete(flipped_res)
                except:
                    pass  # Skip symmetry correction if it fails
            
            # Determine if residue is in RGD motif
            is_motif = motifStart <= int(resi) <= motifEnd
            
            # Store results
            result = {
                'target': targetStructure,
                'residue_name': resname,
                'residue_id': resi,
                'rmsd_all': rmsd_all,
                'rmsd_ca': rmsd_ca,
                'rmsd_backbone': rmsd_backbone,
                'rmsd_min': rmsd_min,
                'used_symmetry': used_symmetry,
                'is_rgd_motif': is_motif
            }
            results.append(result)
            
            # Print progress for important residues
            if is_motif:
                print(f"  Motif residue {resname}{resi}: RMSD = {rmsd_min:.3f} Å {'(symmetry corrected)' if used_symmetry else ''}")
    
    # Calculate summary statistics
    motif_rmsds = [r['rmsd_min'] for r in results if r['is_rgd_motif']]
    overall_rmsd = sum(r['rmsd_min'] for r in results) / len(results) if results else 0
    motif_rmsd = sum(motif_rmsds) / len(motif_rmsds) if motif_rmsds else 0
    
    print(f"\nSUMMARY:")
    print(f"Overall RMSD: {overall_rmsd:.3f} Å")
    print(f"RGD Motif RMSD: {motif_rmsd:.3f} Å")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{outputPrefix}peptide_rmsd_{targetStructure}_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['target', 'residue_name', 'residue_id', 'rmsd_all', 'rmsd_ca', 
                     'rmsd_backbone', 'rmsd_min', 'used_symmetry', 'is_rgd_motif']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Save summary
    summary_filename = f"{outputPrefix}rmsd_summary_{timestamp}.csv"
    with open(summary_filename, 'a', newline='') as summaryfile:
        if not is_non_zero_file(summary_filename):
            summaryfile.write("target,overall_rmsd,motif_rmsd,num_residues,timestamp\n")
        summaryfile.write(f"{targetStructure},{overall_rmsd:.3f},{motif_rmsd:.3f},{len(results)},{timestamp}\n")
    
    # Cleanup
    cmd.delete("ref_temp target_temp")
    
    print(f"\nDetailed results: {csv_filename}")
    print(f"Summary results: {summary_filename}")
    
    return {
        'overall_rmsd': overall_rmsd,
        'motif_rmsd': motif_rmsd,
        'results': results
    }

def batchPeptideRMSD(referenceStructure, targetPattern="docked_*.pdb", outputPrefix="batch_"):
    """
    Batch process multiple docked structures
    """
    import glob
    
    target_files = glob.glob(targetPattern)
    results_summary = []
    
    for target_file in target_files:
        try:
            # Load structure
            target_name = os.path.splitext(os.path.basename(target_file))[0]
            cmd.load(target_file, target_name)
            
            # Calculate RMSD
            result = calculatePeptideRMSD(referenceStructure, target_name, outputPrefix=outputPrefix)
            results_summary.append({
                'target': target_name,
                'overall_rmsd': result['overall_rmsd'],
                'motif_rmsd': result['motif_rmsd']
            })
            
            # Clean up
            cmd.delete(target_name)
            
        except Exception as e:
            print(f"Error processing {target_file}: {e}")
    
    # Sort by RMSD
    results_summary.sort(key=lambda x: x['motif_rmsd'])
    
    print(f"\nBATCH SUMMARY (sorted by motif RMSD):")
    for result in results_summary[:10]:  # Top 10
        print(f"{result['target']}: {result['motif_rmsd']:.3f} Å (motif), {result['overall_rmsd']:.3f} Å (overall)")
    
    return results_summary

# Register PyMOL commands
cmd.extend("calculatePeptideRMSD", calculatePeptideRMSD)
cmd.extend("batchPeptideRMSD", batchPeptideRMSD)

print("RGD Peptide RMSD Calculator loaded successfully!")
print("Usage:")
print("  calculatePeptideRMSD reference_structure, target_structure [, outputPrefix] [, motifStart] [, motifEnd]")
print("  batchPeptideRMSD reference_structure [, targetPattern] [, outputPrefix]")