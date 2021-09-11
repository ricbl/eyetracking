#Checks which cases have synchroinization messages with nonsensical times
#This bug was not understood, but it only affected a little small part of the cases, so those were just not included in the dataset

import glob
import re
import os

for phase in range(1,4):
    data_folders = glob.glob(f"../anonymized_collected_data/phase_{phase}/*/")
    for folder in data_folders:
        timestamp_this_folder = None
        for trial in range(1,550):
            trial_filename = folder+'/et'+str(trial)+'.asc'
            if os.path.isfile(trial_filename):
                with open(trial_filename, 'r', encoding="utf8", errors='ignore') as ascfile:
                    for current_line in ascfile:
                        split_line = re.split('\t| ',current_line.rstrip())
                        split_line = [i for i in split_line if i] 
                        if len(split_line)>0:
                            if split_line[0] == 'MSG':
                                if split_line[2]=='SOM953':
                                    split_message = ' '.join(split_line[3:]).split(';$')
                                    time_linux = float(split_message[1])
                                    if timestamp_this_folder is None:
                                        timestamp_this_folder = time_linux
                                    elif int(time_linux)!=int(timestamp_this_folder):
                                        print('problem found with:')
                                        print('Folder:',folder)
                                        print('Trial:',trial)
                                        break