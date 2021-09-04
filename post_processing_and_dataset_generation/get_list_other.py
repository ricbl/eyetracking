import pandas as pd
from collections import defaultdict, OrderedDict
import numpy
import numpy as np
from nltk import agreement
import csv
from sklearn.metrics import roc_auc_score, confusion_matrix
import re

def filter_by_timestamp(table, begin_timestamp, end_timestamp):
    table = table[table['timestamp']>=begin_timestamp]
    table = table[table['timestamp']<=end_timestamp]
    return table

def get_last_saved_screen(table, trial, screen, title_start = 'index_start_screen_trial', class_start = 'MainWindow'):
    table = table[table['trial'] == trial]
    table = table[table['screen'] == screen]
    table_filter_start = table[table['messenger'] == class_start]
    begin_timestamp = table_filter_start[table_filter_start['title'] == title_start]['timestamp'].values.tolist()[-1]
    table_filter_end = table[table['messenger'] == 'MainWindow']
    end_timestamp = table_filter_end[table_filter_end['title'] == 'end_screen_trial']['timestamp'].values.tolist()[-1]
    return filter_by_timestamp(table, begin_timestamp, end_timestamp)

def get_classes_from_csv(csv_file, results_csv, user, data_folder, original_transcriptions_csv, title_start, class_start):
    data_table = pd.read_csv(csv_file)
    
    all_trials = list(OrderedDict.fromkeys(data_table['trial']))
    
    all_trials = all_trials[1:-1]
    for trial in all_trials:
        print(user+str(trial))
        data_table_this_trial = data_table[data_table['trial'] == trial]
        if len(data_table_this_trial[data_table_this_trial['screen']==5])==0:
            continue
        #get labels (from screens 4 and 7 combined)
        data_table_transcription_this_trial = get_last_saved_screen(data_table_this_trial, trial, 5,title_start = title_start, class_start = class_start)
        transcription = str(data_table_transcription_this_trial[data_table_transcription_this_trial['messenger'] == 'TextBox']['value'].values[0])
        new_row = {'user':user, 'trial':trial, 'transcription':transcription.strip()}
        results_csv = results_csv.append(new_row, ignore_index=True)
        
    return results_csv

import glob

def analyze_interrater_reliability():
    phase = 'phase_3'
    title_start = 'index_start_screen_trial'
    class_start = 'MainWindow'
    
    data_folders = glob.glob(f"anonymized_collected_data/{phase}/*/")
    results_csv = pd.DataFrame()
    original_transcriptions_csv = pd.DataFrame()
    for index_data_folder,data_folder in enumerate(sorted(data_folders)):
        print(data_folder)
        user = data_folder.split('/')[-2].split('_')[0]
        results_csv = get_classes_from_csv(data_folder +'/structured_output.csv', results_csv, user, data_folder, original_transcriptions_csv, title_start, class_start)
    
    results_csv.to_csv(f'other_phase_{phase}.csv')

analyze_interrater_reliability()
