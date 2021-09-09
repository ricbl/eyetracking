# generates a table summarizing some of the data collected for phase 3 from all the individual folders of data collected in phase 3

import pandas as pd
from collections import defaultdict, OrderedDict
import numpy
import numpy as np
from nltk import agreement
import csv
from sklearn.metrics import roc_auc_score, confusion_matrix
import re

labels = ['Support devices', 'Abnormal mediastinal contour', 'Enlarged cardiac silhouette', 'Enlarged hilum', 'Hiatal hernia', 'Pneumothorax', 'Pleural abnormality', 'Consolidation','Groundglass opacity','Atelectasis', 'Lung nodule or mass', 'Pulmonary edema', 'High lung volume / emphysema','Interstitial lung disease', 'Acute fracture', 'Other']

eng = []

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

def get_value_from_key_value_box(table, box,value):
    a =  table[table['value'] == value]['title'].values
    assert(len(a)==1)
    b = table[table['title'] == ('extra_properties_value_box_'+str(box)+'_index_' +a[0].split('_')[-1])]['value'].values
    assert(len(b)==1)
    return b[0]

def get_classes_from_csv(csv_file, results_csv, user, transcriptions_csv):
    data_table = pd.read_csv(csv_file)
    transcriptions_table = pd.read_csv(transcriptions_csv)
    all_trials = list(OrderedDict.fromkeys(data_table['trial']))
    
    all_trials = all_trials[1:-1]
    answers = {}
    other_label = []
    all_coord_chest = {}
    all_coord_box = defaultdict(lambda: defaultdict(lambda: list()))
    all_certainty_box = defaultdict(lambda: defaultdict(lambda: list()))
    all_index_box = defaultdict(lambda: defaultdict(lambda: list()))
    for trial in all_trials:
        print(user+str(trial))
        data_table_this_trial = data_table[data_table['trial'] == trial]
        labels_trial = {}
        labels_trial['Skip'] = 0
        
        row_image = data_table_this_trial[data_table_this_trial['title'] == 'filepath']['value'].values
        assert(len(row_image)==1)
        filepath = row_image[0][6:]
        
        new_row = {'user':user, 'label':'', 'trial':trial, 'title':'filepath', 'value':filepath}
        results_csv = results_csv.append(new_row, ignore_index=True)
        
        #get labels (from screens 4 and 7 combined)
        if len(data_table_this_trial[data_table_this_trial['title']=='skip_image']['value'].values)>0:
            labels_trial['Skip'] = -1
            for label in labels:
                labels_trial[label] = 0
        else:
            
            for screen_index in range(1,15):
                data_table_this_trial_this_screen = data_table_this_trial[data_table_this_trial['screen'] == screen_index]
                begin_timestamp = data_table_this_trial_this_screen[data_table_this_trial_this_screen['title'] == 'index_start_screen_trial']['timestamp'].values.tolist()
                end_timestamp = data_table_this_trial_this_screen[data_table_this_trial_this_screen['title'] == 'end_screen_trial']['timestamp'].values.tolist()
                total_time_spent = 0
                for index_screen_call in range(len(begin_timestamp)):
                    total_time_spent+=(end_timestamp[index_screen_call] - begin_timestamp[index_screen_call])*60*60*24
                new_row = {'user':user, 'label':screen_index, 'trial':trial, 'title':'time spent screen', 'value':total_time_spent}
                results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_chestbox_this_trial = get_last_saved_screen(data_table_this_trial, trial, 9)
            coords_chest_ = []
            for dimen in range(1,5):
                 coords_chest_.append(float(data_table_chestbox_this_trial[data_table_chestbox_this_trial['title']=='box_0_dimension_'+str(dimen)]['value'].values[0]))
            coords_chest = []
            coords_chest.append(min(coords_chest_[0],coords_chest_[2]))
            coords_chest.append(min(coords_chest_[1],coords_chest_[3]))
            coords_chest.append(max(coords_chest_[0],coords_chest_[2]))
            coords_chest.append(max(coords_chest_[1],coords_chest_[3]))
            all_coord_chest[trial] = coords_chest
            
            eng.append("generate_image_from_saved_data('../"+filepath+"', {["+' '.join([str(coord_value) for coord_value in coords_chest])+"]}, 0, 0, 0, 0,'./results_phase_3/"+user+"/chest_box_screen_"+str(trial)+".png',0,'"+user+"',0)")
            
            data_table_transcription_this_trial = get_last_saved_screen(data_table_this_trial, trial, 11,title_start = 'trim_start', class_start = 'ScreenTranscriptionEditing')
            # transcription = data_table_transcription_this_trial[data_table_transcription_this_trial['messenger'] == 'TextBox']['value'].values[0]
            transcription = transcriptions_table[transcriptions_table['user']==user]
            transcription = transcription[transcription['trial']==trial]
            assert(len(transcription)==1)
            transcription = transcription['transcription'].values[0]
            new_row = {'user':user, 'label':'', 'trial':trial, 'title':'transcription', 'value':transcription}
            results_csv = results_csv.append(new_row, ignore_index=True)
            trim_start = data_table_transcription_this_trial[data_table_transcription_this_trial['title'] == 'trim_start']['value'].values[0]
            new_row = {'user':user, 'label':'', 'trial':trial, 'title':'trim_start', 'value':trim_start}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_transcription_this_trial = get_last_saved_screen(data_table_this_trial, trial, 2)
            transcription = data_table_transcription_this_trial[data_table_transcription_this_trial['title'] == 'start_audio_recording']['timestamp'].values[0]
            new_row = {'user':user, 'label':'', 'trial':trial, 'title':'start_audio_recording', 'value':transcription}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_answers_this_trial = get_last_saved_screen(data_table_this_trial, trial, 4)
            data_table_answers_this_trial = data_table_answers_this_trial[data_table_answers_this_trial['messenger'] == 'ButtonChoice_disease']
            
            box_screen_present = False
            
            for label in labels:
                label_selected = data_table_answers_this_trial[data_table_answers_this_trial['title'] == label]['value']
                labels_trial[label] = -int(label_selected)
                if label!='Other' and label!='Support devices' and int(label_selected)==1:
                    box_screen_present = True
            
            if labels_trial['Other']==-1:
                data_table_other_this_trial = get_last_saved_screen(data_table_this_trial, trial, 5)
                
                for other_ in re.split('@$|@!|@£', data_table_other_this_trial[data_table_other_this_trial['title']=='text']['value'].values[0]):
                    new_row = {'user':user, 'label':'', 'trial':trial, 'title':'Other label', 'value':other_}
                    results_csv = results_csv.append(new_row, ignore_index=True)
            
            if box_screen_present:
                data_table_answers_this_trial = get_last_saved_screen(data_table_this_trial, trial, 7)
                total_boxes = int(data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'total_boxes']['value'])
            else:
                total_boxes = 0
            rect_list = []
            label_matrix = numpy.zeros([len(labels), total_boxes])
            from_center = 0;
            for box in range(1,total_boxes+1):
                
                begin_timestamp = data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'box_'+str(box)+'_from_center']['timestamp'].values.tolist()[-1]
                end_timestamp = data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'box_' +str(box)+ '_deleted']['timestamp'].values.tolist()[-1]
                
                data_table_answers_this_trial_this_box = filter_by_timestamp(data_table_answers_this_trial, begin_timestamp, end_timestamp)
                
                from_center = data_table_answers_this_trial_this_box[data_table_answers_this_trial_this_box['title']=='box_'+str(box)+'_from_center']['value'].values[0]
                coords_box_ = []
                
                for dimen in range(1,5):
                    
                    coords_box_.append(float(data_table_answers_this_trial_this_box[data_table_answers_this_trial_this_box['title']=='box_'+str(box)+'_dimension_'+str(dimen)]['value'].values[0]))
                coords_box = []
                if int(from_center)==0:
                    coords_box.append((coords_box_[0]+coords_box_[2])/2)
                    coords_box.append((coords_box_[1]+coords_box_[3])/2)
                    coords_box.append(abs(coords_box_[0]-coords_box_[2])/2)
                    coords_box.append(abs(coords_box_[1]-coords_box_[3])/2)
                else:
                    coords_box.append(coords_box_[0])
                    coords_box.append(coords_box_[1])
                    coords_box.append(abs(coords_box_[0]-coords_box_[2]))
                    coords_box.append(abs(coords_box_[1]-coords_box_[3]))
                
                deleted_value = data_table_answers_this_trial_this_box[data_table_answers_this_trial_this_box['title'] == 'box_' +str(box)+ '_deleted']['value'].values
                assert(len(deleted_value)==1)
                if deleted_value[0] == 'false':
                    rect_list.append(coords_box_)
                    certainty = 6 - int(get_value_from_key_value_box(data_table_answers_this_trial_this_box,box,'certainty_chosen_index'))
                    list_labels_this_box = []
                    for label_index, label in enumerate(labels):
                        if label in {'Other', 'Support devices'}:
                            button_label = '(' + label + ')'
                        else:
                            button_label = label
                        if int(get_value_from_key_value_box(data_table_answers_this_trial_this_box,box,button_label)):
                            label_matrix[label_index,box-1] = certainty
                            labels_trial[label] = max(labels_trial[label], certainty)
                            list_labels_this_box.append(label)
                            all_coord_box[trial][label].append(coords_box)
                            all_certainty_box[trial][label].append(certainty)
                            all_index_box[trial][label].append(box)
                    new_row = {'user':user, 'extra_info':box, 'label':'', 'trial':trial, 'title':'labels for box', 'value':','.join(sorted(list_labels_this_box))}
                    results_csv = results_csv.append(new_row, ignore_index=True)
            
            for label in labels:
                if label!='Other' and label!='Support devices' and labels_trial[label]==-1:
                    labels_trial[label] = 0
            
            eng.append("generate_image_from_saved_data('../"+filepath+"', {"+','.join([('['+' '.join([str(coord_value) for coord_value in coords_this_rect])+']') for coords_this_rect in rect_list])+"}, 1, {'"+"','".join(labels)+"'},[" + \
                ';'.join(['['+' '.join([str(label_matrix[ni,nj]) for nj in range(label_matrix.shape[1])])+']'  for ni in range(label_matrix.shape[0])]) +'],'+ str(from_center)+",'./results_phase_3/"+user+"/bbox_screen_"+str(trial)+".png',1,'"+user+"',["+ \
                ' '.join([str((labels_trial[label_1]!=0)*1) for label_1 in labels])+"])")
        answers[trial] = labels_trial
    return answers, results_csv, all_coord_chest, all_coord_box, all_certainty_box, all_index_box

def convert_center_axis_to_corners(rect):
    return [rect[0]-rect[2], rect[1]-rect[3],rect[0]+rect[2],rect[1]+rect[3]]

import glob

def analyze_interrater_reliability():
    data_folders = glob.glob("anonymized_collected_data/phase_3/*/")
    discard_df = pd.read_csv('./discard_cases.csv')
    labels_table = defaultdict(dict)
    chest_table = defaultdict(dict)
    box_table = defaultdict(dict)
    certainty_box_table = defaultdict(dict)
    index_box_table = defaultdict(dict)
    results_csv = pd.DataFrame()
    for index_data_folder,data_folder in enumerate(data_folders):
        print(data_folder)
        user = data_folder.split('/')[-2].split('_')[0]
        answers, results_csv, all_coord_chest, all_coord_box, all_certainty_box,all_index_box = get_classes_from_csv(data_folder +'/structured_output.csv', results_csv, user, 'anonymized_collected_data/phase_3/phase_3_transcriptions_anon.csv')
        labels_table[user].update(answers)
        chest_table[user].update(all_coord_chest)
        box_table[user].update(all_coord_box)
        certainty_box_table[user].update(all_certainty_box)
        index_box_table[user].update(all_index_box)
    user_lists = []
    
    for user in sorted(labels_table.keys()):
        trial_lists = []
        trials_list = sorted(labels_table[user].keys())
        for trial in trials_list:
            labels_list =sorted(labels_table[user][trial].keys())
            label_lists = []
            for label in labels_list:
                label_lists.append(labels_table[user][trial][label])
                new_row = {'user':user, 'label':label, 'trial':trial, 'title':'trial_answer', 'value':labels_table[user][trial][label]}
                results_csv = results_csv.append(new_row, ignore_index=True)
                new_row = {'user':user, 'label':label, 'trial':trial, 'title':'trial_answer_present', 'value':(labels_table[user][trial][label]!=0)*1}
                results_csv = results_csv.append(new_row, ignore_index=True)
                
            trial_lists.append(label_lists)
        
        user_lists.append(trial_lists)
    
    for k in range(len(labels_list)):
        for user_index, user in enumerate(sorted(labels_table.keys())):
            trials_list = sorted(labels_table[user].keys())
            for trial in trials_list:
                if trial in box_table[user].keys():
                    list_of_boxes = box_table[user][trial][labels_list[k]]
                    list_of_certainties = certainty_box_table[user][trial][labels_list[k]]
                    list_of_indexes_boxes = index_box_table[user][trial][labels_list[k]]
                    for l in range(len(list_of_boxes)):
                        new_row = {'user':user, 'extra_info':list_of_indexes_boxes[l], 'label':labels_list[k], 'trial':trial, 'title':'BBox (Ellipse) certainty', 'value':list_of_certainties[l]}
                        results_csv = results_csv.append(new_row, ignore_index=True)
                        for coord_index, coord in enumerate(convert_center_axis_to_corners(list_of_boxes[l])):
                            new_row = {'user':user, 'extra_info':list_of_indexes_boxes[l], 'label':labels_list[k], 'trial':trial, 'title':'BBox (Ellipse) coord ' + str(coord_index), 'value':coord}
                            results_csv = results_csv.append(new_row, ignore_index=True)
    
    for user_index, user in enumerate(sorted(labels_table.keys())):
        trials_list = sorted(labels_table[user].keys())
        ious_this_user = []
        for trial in trials_list:
            for coord_index, coord in enumerate(chest_table[user][trial]):
                new_row = {'user':user, 'extra_info':'', 'label':'', 'trial':trial, 'title':'ChestBox (Rectangle) coord ' + str(coord_index), 'value':coord}
                results_csv = results_csv.append(new_row, ignore_index=True)
    
    results_csv.to_csv('results_phase_3.csv', index=False)

analyze_interrater_reliability()
#add discard flag
