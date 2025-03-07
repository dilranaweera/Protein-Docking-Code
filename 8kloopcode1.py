### To generate 8k peptides in a 3-consecutive-amino-acid motif. For each space in a tripeptide motif, there are 20 possible combinations of peptides that can be generated. 
### This script automates the generation of 8k peptides by iteratively mutagenizing through each amino acid in the motif so that each of the 8k combinations of peptides that are generated are made. 
# command on mac: /usr/bin/python3 8kloopcode1.py modelname chain start_pos mid_pos end_pos
## ex: /usr/bin/python3 8kloopcode1.py rgdfm.pdb A 1 2 3
## Notes: Make sure the python version that modeller was downloaded is compatible with the version of python on your system.



import sys
import os
from modeller import *
from modeller.optimizers import MolecularDynamics, ConjugateGradients
from modeller.automodel import autosched
import shutil

def optimize(atmsel, sched):
    for step in sched:
        step.optimize(atmsel, max_iterations=200, min_atom_shift=0.001)
    refine(atmsel)
    cg = ConjugateGradients()
    cg.optimize(atmsel, max_iterations=200, min_atom_shift=0.001)

def refine(atmsel):
    md = MolecularDynamics(cap_atom_shift=0.39, md_time_step=4.0, md_return='FINAL')
    init_vel = True
    for (its, equil, temps) in ((200, 20, (150.0, 250.0, 400.0, 700.0, 1000.0)),
                                (200, 600, (1000.0, 800.0, 600.0, 500.0, 400.0, 300.0))):
        for temp in temps:
            md.optimize(atmsel, init_velocities=init_vel, temperature=temp,
                         max_iterations=its, equilibrate=equil)
            init_vel = False

def make_restraints(mdl1, aln):
    rsr = mdl1.restraints
    rsr.clear()
    s = Selection(mdl1)
    for typ in ('stereo', 'phi-psi_binormal'):
        rsr.make(s, restraint_type=typ, aln=aln, spline_on_site=True)
    for typ in ('omega', 'chi1', 'chi2', 'chi3', 'chi4'):
        rsr.make(s, restraint_type=typ+'_dihedral', spline_range=4.0,
                 spline_dx=0.3, spline_min_points=5, aln=aln, spline_on_site=True)

def mutate_residue(modelname, chain, positions):
    amino_acids = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", 
                   "HIS", "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", 
                   "THR", "TRP", "TYR", "VAL"]
    
    base_model = f"{modelname}.pdb"

    # Create directories for outputs
    mutants_dir = f"Mutants_{positions[0]}_{positions[1]}_{positions[2]}"
    os.makedirs(mutants_dir, exist_ok=True)

    # First level mutations
    for res1 in amino_acids:
        model1 = f"{modelname}_{res1}{positions[0]}"
        shutil.copy(base_model, f"{model1}.pdb")

        # Second level mutations
        for res2 in amino_acids:
            model2 = f"{model1}_{res2}{positions[1]}"
            shutil.copy(f"{model1}.pdb", f"{model2}.pdb")

            # Third level mutations
            for res3 in amino_acids:
                model3 = f"{model2}_{res3}{positions[2]}"
                output_file = os.path.join(mutants_dir, f"{model3}.pdb")
                generate_mutant(f"{model2}.pdb", positions[2], res3, chain, output_file)

                print(f"Generated: {output_file}")

def generate_mutant(input_model, respos, restyp, chain, output_file):
    env = Environ(rand_seed=-49837)
    env.io.hetatm = True
    env.edat.dynamic_sphere = False
    env.edat.dynamic_lennard = True
    env.edat.contact_shell = 4.0
    env.edat.update_dynamic = 0.39
    env.libs.topology.read(file='$(LIB)/top_heav.lib')
    env.libs.parameters.read(file='$(LIB)/par.lib')

    mdl1 = Model(env, file=input_model)
    ali = Alignment(env)
    ali.append_model(mdl1, atom_files=input_model, align_codes=input_model)

    s = Selection(mdl1.chains[chain].residues[respos])
    s.mutate(residue_type=restyp)
    ali.append_model(mdl1, align_codes=input_model)

    mdl1.clear_topology()
    mdl1.generate_topology(ali[-1])
    mdl1.transfer_xyz(ali)
    mdl1.build(initialize_xyz=False, build_method='INTERNAL_COORDINATES')

    mdl2 = Model(env, file=input_model)
    mdl1.res_num_from(mdl2, ali)

    mdl1.write(file=f"{input_model}.tmp")
    mdl1.read(file=f"{input_model}.tmp")
    make_restraints(mdl1, ali)

    mdl1.env.edat.nonbonded_sel_atoms = 1
    sched = autosched.loop.make_for_model(mdl1)
    s = Selection(mdl1.chains[chain].residues[respos])

    mdl1.restraints.unpick_all()
    mdl1.restraints.pick(s)

    s.energy()
    s.randomize_xyz(deviation=4.0)
    mdl1.env.edat.nonbonded_sel_atoms = 2
    optimize(s, sched)
    mdl1.env.edat.nonbonded_sel_atoms = 1
    optimize(s, sched)
    s.energy()

    mdl1.write(file=output_file)
    os.remove(f"{input_model}.tmp")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python script.py modelname chain start_pos mid_pos end_pos")
        sys.exit(1)

    modelname = sys.argv[1]
    chain = sys.argv[2]
    start_pos = int(sys.argv[3])
    mid_pos = int(sys.argv[4])
    end_pos = int(sys.argv[5])

    mutate_residue(modelname, chain, [start_pos, mid_pos, end_pos])
