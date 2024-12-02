from __future__ import print_function
import optparse

from rosetta.protocols.scoring import Interface
from rosetta import *
from pyrosetta import *

init(extra_options = "-constant_seed") #replace -constant_seed with?
import os; os.chdir('.test.output')

def scanning(rgdfm1.pdb, partners, mutant_aa = 'A',
        interface_cutoff = 8.0, output = False,
        trials = 1, trial_output = ''):
    

    pose = Pose()
    pose_from_file(pose, rgdfm1.pdb) #Will this one or the other pose function below work?

############
#Adding extra comment to show dil how command line git works
#ANother line cause why not

# Import necessary PyRosetta modules
from pyrosetta import pose_from_pdb, Pose
from pyrosetta.rosetta.core.scoring import ScoreFunction
from pyrosetta.rosetta.protocols.moves import PyMOLMover

def main():
    # Initialize PyRosetta 
    # WARNING: Remove -constant_seed for production runs!
    pyrosetta.init(extra_options="-constant_seed")

    # Change to output directory (common in scientific computing)
    os.chdir('.test.output')

    # Create a pose from a PDB file
    pose = pose_from_pdb('input_protein.pdb')

    # Save modified pose
    pose.dump_pdb('output_protein.pdb')

if __name__ == "__main__":
    main()                
################
        
    dock_jump = 1
    movable_jumps = Vector1([dock_jump])
    protocols.docking.setup_foldtree(pose, partners, movable_jumps)


    scorefxn = get_fa_scorefxn() #  create_score_function('standard')
    scorefxn(pose)    # needed for proper Interface calculation

    ddG_scorefxn = ScoreFunction()
    ddG_scorefxn.set_weight(core.scoring.fa_atr, 0.44)
    ddG_scorefxn.set_weight(core.scoring.fa_rep, 0.07)
    ddG_scorefxn.set_weight(core.scoring.fa_sol, 1.0)
    ddG_scorefxn.set_weight(core.scoring.hbond_bb_sc, 0.5)
    ddG_scorefxn.set_weight(core.scoring.hbond_sc, 1.0)


    interface = Interface(dock_jump)
    interface.distance(interface_cutoff)
    interface.calculate(pose)


    pymover = PyMOLMover()
    pymover.keep_history(True)    # for multiple trajectories
    pymover.apply(pose)
    pymover.send_energy(pose)


    for trial in range( trials ):

        ddG_mutants = {}
        for i in range(1, pose.total_residue() + 1): #how do I only specify 1 residue manipulation?

            if interface.is_interface(i) == True:
                filename = ''
                if output:
                    filename = pose.pdb_info().name()[:-4] + '_' + pose.sequence()[i-1] + str(pose.pdb_info().number(i)) + '->' + mutant_aa
                #What is the above line
                ddG_mutants[i] = interface_ddG(pose, i, mutant_aa,
                    movable_jumps, ddG_scorefxn, interface_cutoff, filename )

        # output results
        print( '='*80 )
        print( 'Trial', str( trial + 1 ) )
        print( 'Mutants (PDB numbered)\t\"ddG\" (interaction dependent score change)' )
        residues = list( ddG_mutants.keys() )  # list(...) conversion is for python3 compatbility
        residues.sort()    # easier to read
        display = [pose.sequence()[i - 1] +
            str(pose.pdb_info().number(i)) + mutant_aa + '\t' +
            str(ddG_mutants[i]) + '\n'
            for i in residues]
        print( ''.join(display)[:-1] )
        print( '='*80 )

        # write to file
        f = open(trial_output + '_' + str(trial + 1) + '.txt' , 'w' )
        f.writelines(display)
        f.close()


    print( 'Likely Hotspot Residues' )
    for hotspot in scanning_analysis(trial_output):
        print( hotspot )
    print( '='*80 )


def interface_ddG( pose, mutant_position, mutant_aa, movable_jumps, scorefxn = '',
        cutoff = 8.0, out_filename = ''):
    # 1. create a reference copy of the pose
    wt = Pose()    # the "wild-type"
    wt.assign(pose)

    # 2. setup a specific default ScoreFunction
    if not scorefxn:

        scorefxn = ScoreFunction()
        scorefxn.set_weight(fa_atr, 0.44)
        scorefxn.set_weight(fa_rep, 0.07)
        scorefxn.set_weight(fa_sol, 1.0)
        scorefxn.set_weight(hbond_bb_sc, 0.5)
        scorefxn.set_weight(hbond_sc, 1.0)


    mutant = Pose()
    mutant.assign(pose)


    mutant = mutate_residue(mutant, mutant_position, mutant_aa,
        0.0, scorefxn)


    wt_score = calc_binding_energy(wt, scorefxn,
        mutant_position, cutoff)
    mut_score = calc_binding_energy(mutant, scorefxn,
        mutant_position, cutoff)

    ddg = mut_score - wt_score

    mutant.pdb_info().name( pose.sequence()[mutant_position -1] +
        str( pose.pdb_info().number(mutant_position)) +
        mutant.sequence()[mutant_position - 1])
    pymover = PyMOLMover()
    scorefxn(mutant)
    pymover.apply(mutant)
    pymover.send_energy(mutant)

    if out_filename:
        mutant.dump_pdb(out_filename)

    return ddg


def mutate_residue(pose, mutant_position, mutant_aa,
        pack_radius = 0.0, pack_scorefxn = '' ):



    if pose.is_fullatom() == False:
        IOError( 'mutate_residue only works with fullatom poses' )

    test_pose = Pose()
    test_pose.assign(pose)


    if not pack_scorefxn:
        pack_scorefxn = get_fa_scorefxn() #  create_score_function('standard')

    task = standard_packer_task(test_pose)


    aa_bool = rosetta.utility.vector1_bool()
    
    mutant_aa = core.chemical.aa_from_oneletter_code(mutant_aa)

    
    for i in range(1, 21):
        
        aa_bool.append( i == int(mutant_aa) )

    task.nonconst_residue_task(mutant_position
        ).restrict_absent_canonical_aas(aa_bool)

    
    center = pose.residue(mutant_position).nbr_atom_xyz()
    for i in range(1, pose.total_residue() + 1):
        # only pack the mutating residue and any within the pack_radius
        if not i == mutant_position or center.distance_squared(
                test_pose.residue(i).nbr_atom_xyz()) > pack_radius**2:
            task.nonconst_residue_task(i).prevent_repacking()


    packer = protocols.simple_moves.PackRotamersMover(pack_scorefxn, task)
    packer.apply(test_pose)

    return test_pose

def calc_binding_energy(pose, scorefxn, center, cutoff = 8.0):
    # create a copy of the pose for manipulation
    test_pose = Pose()
    test_pose.assign(pose)

    
    tf = standard_task_factory()    # create a TaskFactory
    tf.push_back(core.pack.task.operation.RestrictToRepacking())    # restrict it to repacking


    prevent_repacking = core.pack.task.operation.PreventRepacking()

    
    center = test_pose.residue(center).nbr_atom_xyz()
    for i in range(1, test_pose.total_residue() + 1):
        
        if center.distance_squared(
                test_pose.residue(i).nbr_atom_xyz()) > cutoff**2:
            prevent_repacking.include_residue(i)

    # apply these settings to the TaskFactory
    tf.push_back(prevent_repacking)

    # setup a PackRotamersMover
    packer = protocols.simple_moves.PackRotamersMover(scorefxn)
    packer.task_factory(tf)


    packer.apply(test_pose)


    before = scorefxn(test_pose)

    xyz = rosetta.numeric.xyzVector_double_t()    # a Vector for coordinates
    xyz.x = 500.0    # arbitrary separation magnitude, in the x direction
    xyz.y = 0.0    #...I didn't have this and it defaulted to 1e251...?
    xyz.z = 0.0    #...btw thats like 1e225 light years,
                   #    over 5e245 yrs at Warp Factor 9.999 (thanks M. Pacella)

    chain2starts = len(pose.chain_sequence(1)) + 1
    for r in range(chain2starts, test_pose.total_residue() + 1):
        for a in range(1, test_pose.residue(r).natoms() + 1):
            test_pose.residue(r).set_xyz(a,
                test_pose.residue(r).xyz(a) + xyz)

    
    packer.apply(test_pose)

    # return the change in score
    return before - scorefxn(test_pose)


def scanning_analysis(trial_output):

    # extract all files
    filenames = os.listdir(os.getcwd())
    
    filenames =[i for i in filenames if trial_output in i]


    filename = filenames[0]
    f = open(filename , 'r')
    data = f.readlines()
    data = [i.strip() for i in data]    # remove "\n"
    f.close()


    mutants = [i.split('\t')[0] for i in data]
    ddg = [float(i.split('\t')[1]) for i in data]


    for filename in filenames[1:]:
        f = open( filename , 'r' )
        data = f.readlines()
        data = [i.strip() for i in data]
        f.close()

        ddg = [float(data[i].split('\t')[1])+ddg[i] for i in range(len(data))]


    ddg = [i/len(filenames) for i in ddg]


    mean = sum(ddg)/len(ddg)

    std = [(i-mean)**2 for i in ddg]
    std = (sum(std)/len(std))**.5

    significant = [i for i in range(len(ddg)) if abs(ddg[i]-mean)>std]

    hotspots = [mutants[i] for i in significant]

    return hotspots
