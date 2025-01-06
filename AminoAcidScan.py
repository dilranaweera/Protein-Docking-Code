from __future__ import print_function
import optparse

from rosetta import *
from rosetta.protocols.scoring import Interface
from pyrosetta import *
from pyrosetta.rosetta.protocols import docking
from pyrosetta import protocols
from pyrosetta.rosetta.protocols.minimization_packing import PackRotamersMover
# importing in programs needed for amino acid scanning

init() # (extra options = "-seed ####") also an option
import os; os.chdir('.test.output')
## if needed, need to mkdir .test.output

def scanning(pdb_filename, partners, mutant_aa = 'A', 
        interface_cutoff = 8.0, output = False,
        trials = 1, trial_output = ''):
    

    pose = Pose()
    pose_from_file(pose, pdb_filename)
        
    dock_jump = 1
    movable_jumps = Vector1([dock_jump])
    ## protocols.docking.setup_foldtree(pose, partners, movable_jumps) (could be wrong command)
    docking.setup_foldtree(pose, partners, movable_jumps)


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
                #What is the above line mean
                ddG_mutants[i] = interface_ddG(pose, i, mutant_aa,
                    movable_jumps, scorefxn, interface_cutoff, filename )

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


def interface_ddG( pose, mutant_position, mutant_aa, movable_jumps, scorefxn = None,
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
        mutant_position, cutoff, pack_scorefxn)
    mut_score = calc_binding_energy(mutant, scorefxn,
        mutant_position, cutoff, pack_scorefxn)

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
        pack_radius = 0.0, pack_scorefxn = None):



    if pose.is_fullatom() == False:
        IOError( 'mutate_residue only works with fullatom poses' )

    test_pose = Pose()
    test_pose.assign(pose)


    ##if not pack_scorefxn:
        ## pack_scorefxn = get_fa_scorefxn() #  create_score_function('standard') (these two lines in original script)
    if pack_scorefxn is None:
        pack_scorefxn = get_fa_scorefxn()



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


    ## packer = protocols.simple_moves.PackRotamersMover(pack_scorefxn, task) from original script
    packer = PackRotamersMover(pack_scorefxn, task)
    packer.apply(test_pose)

    return test_pose

def calc_binding_energy(pose, scorefxn, center, cutoff = 8.0):
    # create a copy of the pose for manipulation
    if pack_scorefxn is None: 
        pack_scorefxn = get_fa_scorefxn()

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
    ## packer = protocols.simple_moves.PackRotamersMover(scorefxn) (in original script)
    packer = PackRotamersMover(pack_scorefxn)
    packer.task_factory(tf)


    packer.apply(test_pose)


    before = scorefxn(test_pose)

    xyz = rosetta.numeric.xyzVector_double_t()    # a Vector for coordinates
    xyz.x = 500.0    # arbitrary separation magnitude, in the x direction; may need to be adjusted?
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

## Averages ddg values gives mutations >1 Std away from the mean
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

parser = optparse.OptionParser()
parser.add_option('--pdb_filename', dest = 'pdb_filename',
    default = '../test/data/test_dock.pdb',    # default example PDB
    help = 'the PDB file containing the protein to refine')

parser.add_option('--partners', dest = 'partners',
    default = 'A_B',    # default for the example test_dock.pdb
    help = 'the relative chain partners for docking')
# scanning options
parser.add_option('--mutant_aa', dest = 'mutant_aa',
    default = 'A',    # default to alanine, A
    help = 'the amino acid to mutate all residues to')
parser.add_option('--interface_cutoff', dest = 'interface_cutoff',
    default = '8.0',    # default to 8.0 Angstroms
    help = 'the distance (in Angstroms) to detect residues for repacking\
        near the interface')
parser.add_option('--output', dest = 'output',
    default = '',    # default off, do now write to file
    help = 'if True, mutant structures are written to PDB files')
# trials options
parser.add_option('--trials', dest='trials',
    default = '1',    # default to single trial for speed
    help = 'the number of trials to perform')
parser.add_option('--trial_output', dest = 'trial_output',
    default = 'ddG_out',    # if a specific output name is desired
    help = 'the name preceding all output files')
(options,args) = parser.parse_args()

# PDB file option
pdb_filename = options.pdb_filename
partners = options.partners
# scanning options
mutant_aa = options.mutant_aa
interface_cutoff = float(options.interface_cutoff)
output = bool(options.output)
# trials options
trials = int(options.trials)
trial_output = options.trial_output

scanning(pdb_filename, partners, mutant_aa,
    interface_cutoff, output, trials, trial_output)

####

## Example: pyscript_name.py --pdb_filename my_protein.pdb --mutant_aa V --trials 3
## This would analyze 'my_protein.pdb', mutate residues to valine, and perform 3 trials.

###

### Input into command line:

### >python alascan.py --pdb_filename=1l5g.pdb --partners=A_B --mutant_aa=A --interface_cutoff=8.0 --trials=3 --trial_output=pdb_ddG --PyMOLMover_ip=off

########