## How to Run This Script:
## Save the code: Save the above script as runADCP.py
## Set the correct paths: Modify pdbqt_dir and trg_dir in the main() function to the actual paths of your directories.
## Make sure ADCP is accessible: Ensure that the adcp executable is in your system's PATH, or modify the adcp_command list in the run_adcp_on_trg function with the correct path to your adcp executable.
## Run the script: Execute the script from the command line using python runADCP.py.
## This comprehensive script will first generate .trg files from your .pdbqt files and then loop through each .trg file, running the ADCP docking simulation on each one. It provides error handling and clearer organization than previous attempts. Remember to adjust the directory paths to match your setup.
## adapted from: Michel F. SANNER https://github.com/ccsb-scripps/ADCP/blob/master/runADCP.py

import os
import sys
import subprocess
import glob
import shutil
import csv
from time import time, sleep
import argparse

class runADCP:

    def myprint(self, str, newline=True):
        sys.stdout.write(str)
        if newline:
            sys.stdout.write('\n')

    def myexit(self):
        if self.targetFile is not None:
            print "clean up unzipped map files"
            try:
                shutil.rmtree('./tmp_%s'%self.jobName)
            except OSError:
                pass        
            for element in ['C','A','SA','N','NA','OA','HD','d','e']:
                if os.path.isfile('rigidReceptor.%s.map'%element):
                    os.remove('rigidReceptor.%s.map'%element)
            if os.path.isfile('transpoints'):
                os.remove('transpoints')
            if os.path.isfile('translationPoints.npy'):
                os.remove('translationPoints.npy')
            if os.path.isfile('con'):
                os.remove('con')
        sys.exit(0)

    def __init__(self):

        import multiprocessing
        self.ncpu = multiprocessing.cpu_count()
        import platform, subprocess
        system_info = platform.uname()
        _platform = system_info[0]

        if _platform == 'Windows':
            self.shell=False
            self._argv = ['./adcp -t 2']
        else:
            self.shell=True
            self._argv = ['./adcp_Linux-x86_64 -t 2']

        # modify here
        #cmd = os.path.join(os.path.abspath(ADFR.__path__[0]), 'bin', 'adcp')
        #self._argv = ['/1tb/crankite_new/peptide -t 2']

        self.completedJobs = 0    
        self.numberOfJobs = 0
        self.outputBaseName = None # a folder with that name will be crated to store log files and ligands
                                   # a _summary.dlg file will be create with this name too
                                   # is specified using -o on the command line
        self.jobName = 'NoName'
        self.targetFile = None
     
    def __call__(self, **kw):
        #
        # run ADFR GAs using the list of command line arguments from the sysargv list
        # 
        import subprocess, datetime
        dataDict = {}
        
        seed = None
        rncpu= None
        nbRuns = 50
        numSteps = 2500000
        jobName = 'NoName'

        skip = False

        rncpu = kw.pop('maxCores')

        if rncpu is None:
            ncores = self.ncpu
            self.myprint( 'Detected %d cores, using %d cores'%(self.ncpu, ncores))
        else:
            assert rncpu > 0, "ERROR: maxCores a positive number, got %d"%rncpu
            ncores = min(self.ncpu, rncpu)
            self.myprint( 'Detected %d cores, request %d cores, using %d cores'%(self.ncpu, rncpu, ncores))

        if kw['nbRuns'] is not None:
            self.nbRuns = nbRuns = kw.pop('nbRuns')

        self.numberOfJobs = nbRuns
        self._jobStatus =  [None]*nbRuns        

        seed = kw.pop('seedValue')

        if seed is None:
            seed = str(random.randint(1,999999))

        # check ramaprob.data file
        if not os.path.isfile("ramaprob.data"):
            print "ERROR: cannot find probability data for ramachandra plot"
            self.myexit()

        if kw['jobName'] is not None:
            self.jobName = jobName = kw.pop('jobName')

        # if target is zip file unzip and replace cmdline arguments
        self.targetFile = targetFile = kw.pop('target')
        if targetFile is None and not os.path.isfile("transpoints"):
            print "ERROR: no receptor files found"
            self.myexit()
        # if transpoints file does not exists
        elif targetFile is not None:
            # unzip mapsFile
            import zipfile
            with zipfile.ZipFile(targetFile, 'r') as zip_ref:
                zip_ref.extractall('./tmp_%s/'%jobName)
            for element in ['C','A','SA','N','NA','OA','HD','d','e']:
                try:
                    shutil.copy(os.path.join('./tmp_%s/'%jobName,targetFile[:-4],'rigidReceptor.%s.map'%element),os.getcwd())
                except IOError:
                    print "WARNING: cannot locate map file for %s"%element
            shutil.copy(os.path.join('./tmp_%s/'%jobName,targetFile[:-4],'translationPoints.npy'),os.getcwd())
            ttt = numpy.load('translationPoints.npy')
            fff = open('transpoints','w+')
            fff.write('%s\n'%len(ttt))
            numpy.savetxt(fff,ttt,fmt='%7.3f')
            fff.close()
        else:
            for element in ['C','A','SA','N','NA','OA','HD','d','e']:
                if not os.path.isfile("rigidReceptor.%s.map"%element):
                    print "WARNING: cannot locate map file rigidReceptor.%s.map"%element


        fff = open('con','w+')
        fff.write('1\n')
        fff.close()

        #check overwriting files
        for i in range(nbRuns):
            if os.path.isfile('%s_%d.pdb'%(jobName,i+1)):
                if not kw['overwriteFiles']:
                    print "ERROR: output file exists %s_%d.pdb"%(jobName,i+1)
                    self.myexit()
                else:
                    print "Warning: overwriting output file %s_%d.pdb"%(jobName,i+1)

        self.dryRun = kw.pop('dryRun')

        # build cmdline args for adcp binary
        argv = self._argv

        if kw['sequence'] is None:
            if kw['input'] is None or kw['input'][-3:] != 'pdb':
                print "ERROR: no input for peptide found"
                self.myexit()
            else:
                argv.append('-f')
                argv.append('%s'%kw['input'])                
        else:
                argv.append('%s'%kw['sequence'])

        # set up the length for each run, 25M as default
        argv.append('-r')
        if kw['numSteps'] is not None:
            numSteps = kw['numSteps']        
        argv.append('1x%s'%numSteps)

        # set up other options for ADCP
        ADCPDefaultOptions = "-p Bias=NULL,external=5,con,1.0,1.0"
        if kw['cyclic']:
            ADCPDefaultOptions += ",external2=4,con14,1.0,1.0"
        if kw['cystein']:
            ADCPDefaultOptions += ",SSbond=80,2.2,20,0.5"
        ADCPDefaultOptions += ",Opt=1,0.25,0.75,0.0"
        argv.append(ADCPDefaultOptions)

        # add arguments that will be set during the loop submitting jobs
        # for seed jubNum and outputName
        argv.extend(['-s', '-1', '-o', jobName,' '])
        jobs = {} # key will be process until process.poll() is not None (i.e. finished)

        from time import time, sleep
        t0 = time()
        runStatus = [None]*(nbRuns)

        runEnergies = [999.]*(nbRuns)
        procToRun = {}
        nbStart = 0 # number of started runs
        nbDone = 0 # number of completed runs

        self.myprint( "Performing search (%d ADCP runs with %d steps each) ..."%
                      (nbRuns, numSteps))
        print "0%   10   20   30   40   50   60   70   80   90   100%"
        print "|----|----|----|----|----|----|----|----|----|----|"



        # submit the first set of jobs
        for jobNum in range(1,min(nbRuns,ncores)+1):
            # overwrite seed
            if seed == -1:
                argv[-4] = str(random.randint(1,999999))
            else:
                argv[-4] = str(seed+jobNum-1)
            # overwrite jobNum
            argv[-2] = '%s_%d.pdb'%(jobName,jobNum)
            argv[-1] = '> %s_%d.out 2>&1'%(jobName,jobNum)
            if self.dryRun:
                print '/n*************** command ***************************\n'
                print ' '.join(argv)
                print
                self.myexit()
                
            process = subprocess.Popen(' '.join(argv),
                                       stdout=subprocess.PIPE , 
                                       stderr=subprocess.PIPE, 
                                       bufsize = 1, shell=self.shell, cwd=os.getcwd())
            procToRun[process] = jobNum-1
            nbStart += 1

        # check for completion and start new runs ntil we are done
        while nbDone < nbRuns:
            # check running processes
            for proc, jnum in procToRun.items():
                #import pdb;pdb.set_trace()
                if proc.poll() is not None: # process finished
                    if proc.returncode !=0:
                        runStatus[jnum] = ('Error', '%s%04d'%(jobName, jnum+1))
                        error = '\n'.join(runStatus[jnum][1])
                        status = 'FAILED'
                        #self.myprint( jnum, 'ENDED WITH ERROR')
                        #print '%d err'%jnum
                    else:
                        status = 'OK'
                        error = ''
                        runStatus[jnum] = ('OKAY', '%s%04d'%(jobName, jnum+1))
                        #self.myprint( jnum, 'ENDED OK')
                        #print '%d ok'%jnum
                        #import pdb;pdb.set_trace()
                        f = open('%s_%d.out'%(jobName,jnum+1))
                        lines = f.readlines()
                        f.close()
                        for ln in lines:
                            if ln.startswith('best target energy'):
                                runEnergies[jnum] = float(ln.rstrip().split()[3])

                    nbDone += 1
                    # remove process
                    del procToRun[proc]

                    self._jobStatus[jobNum-1] = 2
                    self.completedJobs += 1
                    percent = float(self.completedJobs)/self.numberOfJobs
                    sys.stdout.write('%s\r' % ('*'*int(50*percent)))
                    sys.stdout.flush()

                    if nbStart < nbRuns:
                        # start new one
                        jobNum += 1
                        if seed == -1:
                            argv[-4] = str(random.randint(1,999999))
                        else:
                            argv[-4] = str(seed+jobNum-1)
                        # overwrite jobNum
                        argv[-2] = '%s_%d.pdb'%(jobName,jobNum)
                        argv[-1] = '> %s_%d.out 2>&1'%(jobName,jobNum)
                        # remove output file in case it exists
                        try:
                            os.remove(argv[-1])
                        except OSError:
                            pass

                        process = subprocess.Popen(' '.join(argv),
                                                   stdout=subprocess.PIPE , 
                                                   stderr=subprocess.PIPE, 
                                                   bufsize = 1, shell=self.shell, cwd=os.getcwd())
                        procToRun[process] = jobNum-1
                        nbStart += 1
            sleep(1)

        dt = time()-t0
        h,m,s = str(datetime.timedelta(seconds=dt)).split(':')
        self.myprint( 'Docking performed in %.2f seconds, i.e. %s hours %s minutes %s seconds '%(dt, h, m, s))
        
        #write out energy for top 5 solutions
        sort_index = numpy.argsort(runEnergies)
        for i in range(5):
            self.myprint('No. %d energy found is %3.1f kcal/mol at %s_%d.pdb '%(i+1, runEnergies[sort_index[i]]*0.59219, jobName, sort_index[i]+1))
        self.myexit()


def generate_trg_files(pdbqt_dir, trg_dir):
    pdbqt_files = glob.glob(os.path.join(pdbqt_dir, '*.pdbqt'))
    for pdbqt_file in pdbqt_files:
        base_name = os.path.splitext(os.path.basename(pdbqt_file))[0]
        receptor_file = os.path.join(pdbqt_dir, f"{base_name}_recH.pdbqt")
        ligand_file = os.path.join(pdbqt_dir, f"{base_name}_pepH.pdbqt")
        output_name = os.path.join(trg_dir, base_name)
        
        if os.path.exists(receptor_file) and os.path.exists(ligand_file):
            subprocess.run(['agfr', '-r', receptor_file, '-l', ligand_file, '-o', output_name])
        else:
            print(f"Missing files for {base_name}")

def run_adcp_on_trg(trg_file):
    base_name = os.path.splitext(os.path.basename(trg_file))[0]
    ligand_file = f"{base_name}_pepH.pdbqt"
    output_prefix = f"{base_name}_redocking"

    adcp_command = [
        'adcp',
        '-t', trg_file,
        '-s', 'sscsscplsk',
        '-N', '20',
        '-n', '500000',
        '-cyc',
        '-o', output_prefix,
        '-ref', ligand_file,
        '-nc', '0.8'
    ]
    
    subprocess.run(adcp_command) # capture_output=True, text=True) # Removed for compatability
    #if result.returncode != 0:
    #    print(f"Error running ADCP on {trg_file}: {result.stderr}")


def main():
    
    # Set directories
    pdbqt_dir = "/home/dilrana/Desktop/adcp/RGDmut/RGDpdbqt"  # Directory containing PDBQT files
    trg_dir = "/home/dilrana/Desktop/adcp/RGDmut/RGDtrg"  # Directory to store generated TRG files

    # Generate .trg files
    generate_trg_files(pdbqt_dir, trg_dir)

    # Loop through .trg files and run ADCP
    trg_files = glob.glob(os.path.join(trg_dir, "*.trg"))
    for trg_file in trg_files:
        run_adcp_on_trg(trg_file)


if __name__=='__main__':
    main()