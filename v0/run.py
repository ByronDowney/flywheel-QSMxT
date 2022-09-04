#!/usr/bin/env python3

# The file that will be initially run by Flywheel. This should run any scripts, QSMxT or otherwise
print("run.py has started...")

import subprocess
from subprocess import call
import glob
from zipfile import ZipFile
import os
from os.path import basename
import json

#takes config and input from config.json
with open('config.json') as config:
    config = json.load(config)

qsm_iterations = int(config["config"]["TGV_QSM_Iterations"])
with ZipFile('/flywheel/v0/input/magnitude/mag.zip', 'r') as zipObj:
    zipObj.extractall('/flywheel/v0/input/magnitude/')

with ZipFile('/flywheel/v0/input/phase/phs.zip', 'r') as zipObj:
    zipObj.extractall('/flywheel/v0/input/phase/')

print("Environment variables:")
result = subprocess.run(["printenv"], stdout=subprocess.PIPE)
print("Number of QSM iterations:  ", qsm_iterations)

print("Sorting DICOM data...")
call([
    "python3",
    "/opt/QSMxT/run_0_dicomSort.py",
    "/flywheel/v0/input",  # input - this should be in the Flywheel input folder!
    "/00_dicom"
    ])

ima_files = glob.glob("/00_dicom/**/*.IMA", recursive=True)
print('found ' + str(len(ima_files)) + ' ima_files after Sorting DICOM data in /00_dicom')
print("Converting DICOM data...")

try:
    retcode = call([
        "python3",
        "/opt/QSMxT/run_1_dicomToBids.py",
        "/00_dicom/",
        "/01_bids"
    ])
    if retcode < 0:
        print("Converting DICOM data was terminated by signal" + str(retcode))
    else:
        print("Converting DICOM data returned " + str(retcode))
except Exception as e:
    print("Converting DICOM data failed:" + e)
    raise

nii_files = glob.glob("/01_bids/**/*.nii.gz", recursive=True)
print('found ' + str(len(nii_files)) + ' nii_files after Converting DICOM data in /01_bids')

print('Run QSM pipeline ...')

CompletedProcess = subprocess.run([
    "python3",
    "/opt/QSMxT/run_2_qsm.py",
    "--qsm_iterations",
    str(qsm_iterations),
    "--two_pass",
    "/01_bids",
    "/02_qsm_output"
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print('QSM pipeline stdout: ' + CompletedProcess.stdout)
print('QSM pipeline stderr: ' + CompletedProcess.stderr)

output_file = glob.glob("/02_qsm_output/qsm_final/_run_run-1/*.nii")
print('outputfile is ... ' + output_file[0])
print('Zipping and moving files to the output directory...')

# create a ZipFile object
# code taken from https://thispointer.com/python-how-to-create-a-zip-archive-from-multiple-files-or-directory/
with ZipFile('/flywheel/v0/output/QSM_output.zip', 'w') as zipObj:
   # Iterate over all the files in directory
   for folderName, subfolders, filenames in os.walk("/02_qsm_output/qsm_final/_run_run-1/"):
       for filename in filenames:
           #create complete filepath of file in directory
           filePath = os.path.join(folderName, filename)
           # Add file to zip
           zipObj.write(filePath, basename(filePath))

print('The QSMxT gear has finished analysing the input. Exiting...')

exit(0)