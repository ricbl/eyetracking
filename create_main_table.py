import pandas as pd
from pathlib import Path
import shutil
import json
import glob
from collections import defaultdict
import os
from copy import deepcopy
import re
import random
import time

list_of_users = sorted(['user1','user2','user3','user4','user5'])

def get_main_table(experiment_folders, phase, all_trials):
    transcriptions_table = pd.read_csv(f'anonymized_collected_data/phase_{phase}/phase_{phase}_transcriptions_anon.csv')
    others_table = pd.read_csv(f'anonymized_collected_data/phase_{phase}/other_phase_{phase}.csv')
    fixations_table = pd.read_csv(f'summary_edf_phase_{phase}.csv')
    results_table = pd.read_csv(f'results_phase_{phase}.csv')
    discard_table = pd.read_csv('discard_cases.csv')
    discard_table = discard_table[discard_table['phase']==phase]
    
    total_folders = defaultdict(lambda: 0)
    main_table = []
    for experiment_folder in experiment_folders:
        experiment = experiment_folder.split('/')[-2].split('_')[1]
        so_table = pd.read_csv(f'{experiment_folder}/structured_output.csv')
        user = experiment_folder.split('/')[-2].split('_')[0]
        for trial in all_trials[user]:
            
            json_filename = f'{experiment_folder}/{trial}_joined.json'
            # if os.path.isfile(json_filename):
            if len(so_table[(so_table['trial']==trial) & (so_table['screen']==2)]['trial'].values)>0 or os.path.isfile(json_filename):
                print(trial)
                print(experiment_folder)
                print(user)
                #assert it is not in the discard table

                discarded_case = discard_table[(discard_table['trial']==trial) & (discard_table['user']==user)]
                assert(phase!=3 or len(discarded_case)==0)
                discarded = len(discarded_case)>0
                so_table_this_id = so_table[(so_table['trial']==trial) & (so_table['screen']==2) ]
                timestamp_start_eye = so_table_this_id[so_table_this_id['title']=='start_eye_recording']['timestamp'].values
                assert(len(timestamp_start_eye)==1)
                timestamp_start_eye = timestamp_start_eye[0]
                timestamp_start_audio= so_table_this_id[so_table_this_id['title']=='start_audio_recording']['timestamp'].values
                assert(len(timestamp_start_audio)==1)
                timestamp_start_audio = timestamp_start_audio[0]
                
                count = 0
                while count<10000:
                    r = random.randint(0,999999)
                    if phase < 3:
                        id = f"P{phase}{trial:02}R{r:06}"
                    else:
                        id = f"P{phase}00R{r:06}"
                    if not os.path.isdir(f'built_dataset/{id}'):
                        break
                    count += 1
                    assert(count<9999)
                Path(f'built_dataset/{id}').mkdir(parents=True, exist_ok=True)
                total_folders[user] +=1
                
                if not discarded:
                    #transcription
                    f = open(json_filename,'r')
                    data = json.load(f)
                    f.close()
                    pd.DataFrame(data['timestamps'], columns = ['word', 'timestamp_start_word', 'timestamp_end_word']).to_csv(f'built_dataset/{id}/timestamps_transcription.csv', index = False)
                    # shutil.copyfile(json_filename, f'built_dataset/{id}/timestamps_transcription.json')
                    transcription = transcriptions_table[(transcriptions_table['user']==user) & (transcriptions_table['trial']==trial)]['transcription'].values
                    assert(len(transcription)==1)
                    f = open(json_filename,)
                    json_transcription=json.load(f)
                    f.close()
                    assert(transcription[0].replace('.',' .').replace(',', ' ,')==' '.join([item[0] for item in json_transcription['timestamps']]))
                    text_file = open(f'built_dataset/{id}/transcription.txt', "w")
                    text_file.write(transcription[0])
                    text_file.close()
                
                #chest box
                results_this_id = results_table[results_table['trial']!='all']
                results_this_id = results_this_id[(results_this_id['trial'].astype(float)==trial) & (results_this_id['user']==user)]
                coordinates_names = ['xmin','ymin','xmax','ymax']
                coordinates = {}
                for i in range(4):
                    chest_box_coordinate = results_this_id[results_this_id['title']==f'ChestBox (Rectangle) coord {i}']['value'].values
                    assert(len(chest_box_coordinate)==1)
                    coordinates[coordinates_names[i]] = chest_box_coordinate[0]
                pd.DataFrame([coordinates], columns = coordinates_names).to_csv(f'built_dataset/{id}/chest_bounding_box.csv', index = False)
                # f = open(f'built_dataset/{id}/chest_bounding_box.json','w')
                # json_transcription=json.dump(coordinates, f, indent = 2)
                # f.close()
                
                #fixations
                fixations_table_this_id = fixations_table[(fixations_table['screen']==2) & (fixations_table['user']==user) & (fixations_table['trial']==trial)]
                if not discarded:
                    fixations = fixations_table_this_id[fixations_table_this_id['type']=='fixation']
                    columns_fixations = {'time_start_linux': 'timestamp_start_fixation',
                    'time_linux':'timestamp_end_fixation', 
                    'position_x':'average_x_position', 
                    'position_y':'average_y_position', 
                    'pupil_size': 'pupil_area',
                    'pupil_size_normalization': 'pupil_area_normalization_constant', 
                    'angular_resolution_x':'angular_resolution_x_pixels_per_degree',
                    'angular_resolution_y':'angular_resolution_y_pixels_per_degree',
                    # 'window_width':,
                    # 'window_level':,
                    'source_rect_dimension_1':'xmin_shown_from_image',
                    'source_rect_dimension_2':'ymin_shown_from_image',
                    'source_rect_dimension_3':'xmax_shown_from_image',
                    'source_rect_dimension_4':'ymax_shown_from_image',
                    'dest_rect_dimension_1':'xmin_in_screen_coordinates',
                    'dest_rect_dimension_2':'ymin_in_screen_coordinates',
                    'dest_rect_dimension_3':'xmax_in_screen_coordinates',
                    'dest_rect_dimension_4':'ymax_in_screen_coordinates'}
                    fixations = fixations[columns_fixations.keys()].rename(columns = columns_fixations)
                    
                    fixations.loc[:,'timestamp_start_fixation'] = (fixations['timestamp_start_fixation']-timestamp_start_audio)*60*60*24
                    fixations.loc[:,'timestamp_end_fixation'] = (fixations['timestamp_end_fixation']-timestamp_start_audio)*60*60*24
                    assert(len(fixations)>0)
                    fixations.to_csv(f'built_dataset/{id}/fixations.csv',index = False)
                
                #window, zoom
                if not discarded:
                    columns_windows = {'level':'window_level',
                    'width':'window_width',
                    'zoom':'zoom_multiplier',
                    'source_rect_dimension_1':'xmin_shown_from_image',
                    'source_rect_dimension_2':'ymin_shown_from_image',
                    'source_rect_dimension_3':'xmax_shown_from_image',
                    'source_rect_dimension_4':'ymax_shown_from_image',
                    'dest_rect_dimension_1':'xmin_in_screen_coordinates',
                    'dest_rect_dimension_2':'ymin_in_screen_coordinates',
                    'dest_rect_dimension_3':'xmax_in_screen_coordinates',
                    'dest_rect_dimension_4':'ymax_in_screen_coordinates'}
                    
                    image_exhibition_values = so_table_this_id[so_table_this_id['title'].isin(columns_windows.keys())]
                    current_values = {}
                    
                    previous_timestamp = 0
                    current_values['timestamp'] = 0
                    for column_name  in columns_windows.keys():
                        if column_name =='zoom':
                            continue
                        first_value = image_exhibition_values[image_exhibition_values['title']==column_name]['value'].values[0]
                        current_values[column_name] = first_value
                    current_values['zoom'] = 1
                    all_values = []
                    started_writing = False
                    started_zoom = False
                    for _,row in image_exhibition_values.iterrows():
                        if started_writing and row['title'] in ['zoom','level']:
                            started_zoom = True
                            current_values['timestamp'] = (row['timestamp']-timestamp_start_audio)*60*60*24
                            assert(current_values['timestamp']>previous_timestamp)
                            assert(current_values['timestamp']<60*4)
                            previous_timestamp = current_values['timestamp']
                            
                        if started_zoom:
                            current_values[row['title']] = row['value']
                        
                        if (not started_writing and row['title']=='width') or (started_zoom and row['title'] in ['dest_rect_dimension_4', 'width']):
                            all_values.append(deepcopy(current_values))
                            started_zoom = False
                            started_writing = True
                    # pd.DataFrame(all_values).rename(columns = columns_windows).to_csv(f'built_dataset/{id}/image_exhibition_window_zoom.csv',index = False)
                
                #labels and main table
                answers = results_this_id[results_this_id['title']=='trial_answer']
                row = dict(zip([item[:1].upper() + item[1:].lower() for item in answers['label'].values],answers['value'].values))
                del row['Skip']
                row['Support devices'] = float(row['Support devices'])==-1
                labels_list = sorted(row.keys())
                # others = results_this_id[results_this_id['title']=='Other label']['value'].values
                others = others_table[(others_table['trial']==trial) & (others_table['user']==user)]['transcription'].values
                if len(others)>0:
                    assert(len(others)==1)
                    print(others)
                    others = re.split(r'\@\$|\@\!|\@\£|\@\Â\£',others[0])
                    print(others)
                    row['Other'] = '|'.join(others)
                else:
                    row['Other'] = ''
                if 'Quality issue' in row.keys():
                    row['Quality issue'] = float(row['Quality issue'])==-1
                image_filepath = fixations_table_this_id[fixations_table_this_id['type']=='filepath']['value'].values
                assert(len(image_filepath)==1)
                image_x = fixations_table_this_id[fixations_table_this_id['type']=='image_size_x']['value'].values
                assert(len(image_x)==1)
                image_x = int(float(image_x[0]))
                image_y = fixations_table_this_id[fixations_table_this_id['type']=='image_size_y']['value'].values
                assert(len(image_y)==1)
                image_y = int(float(image_y[0]))
                dicom_id = image_filepath[0].split('/')[-1].split('.')[0]
                splits = pd.read_csv(f'datasets/mimic/tables/mimic-cxr-2.0.0-split.csv')
                split = splits[splits['dicom_id']==dicom_id]['split'].values
                assert(len(split)==1)
                check_image_filepath = results_this_id[results_this_id['title']=='filepath']['value'].values
                assert(len(check_image_filepath)==1)
                print(image_filepath[0].split('/')[-1])
                print(check_image_filepath[0].split('/')[-1])
                assert(image_filepath[0].split('/')[-1]==check_image_filepath[0].split('/')[-1])
                check_image_x = so_table_this_id[so_table_this_id['title']=='image_size_x']['value'].values
                assert(len(check_image_x)==1)
                check_image_x = int(float(check_image_x[0]))
                
                assert(check_image_x==image_x)
                check_image_y = so_table_this_id[so_table_this_id['title']=='image_size_y']['value'].values
                assert(len(check_image_y)==1)
                check_image_y = int(float(check_image_y[0]))
                assert(check_image_y==image_y)
                row_= {'id':id,'split':split[0],'eye_tracking_data_discarded':discarded,'image':image_filepath[0],'subject_id':image_filepath[0].split('/')[-3][1:],'image_size_x':image_x, 'image_size_y':image_y}
                row_.update(row)
                main_table.append(row_)
                
                #ellipses
                labels_check = results_this_id[results_this_id['title']=='BBox (Ellipse) certainty']['extra_info'].unique()
                labels_check = [int(item) for item in labels_check]
                total_ellipses = len(labels_check)
                ellipses = []
                ellipses_json = []
                for index, ellipse_index in enumerate(labels_check):
                    ellipses.append({})
                    ellipses_json.append({})
                    coordinates = {}
                    for i in range(4):
                        ellipse_coordinate = results_this_id[(results_this_id['title']==f'BBox (Ellipse) coord {i}')]
                        ellipse_coordinate = ellipse_coordinate[(ellipse_coordinate['extra_info'].astype(float)==ellipse_index)]['value'].values
                        assert((ellipse_coordinate==ellipse_coordinate[0]).all())
                        coordinates[coordinates_names[i]] = ellipse_coordinate[0]
                    ellipses_json[index]['coordinates'] = coordinates
                    ellipses[index].update(coordinates)
                    ellipse_certainties = results_this_id[(results_this_id['title']==f'BBox (Ellipse) certainty')]
                    ellipse_certainties = ellipse_certainties[(ellipse_certainties['extra_info'].astype(float)==ellipse_index)][['label','value']]
                    labels_json = []
                    labels = {item:False for item in labels_list}
                    for _, row in ellipse_certainties.iterrows():
                        labels_json.append(row['label'])
                        labels[row['label']] = True
                        certainty = row['value']
                    ellipses_json[index]['labels'] = labels_json
                    ellipses[index].update(labels)
                    ellipses[index]['certainty'] = certainty
                    ellipses_json[index]['certainty'] = certainty
                pd.DataFrame(ellipses, columns = coordinates_names + ['certainty'] + labels_list).to_csv(f'built_dataset/{id}/anomaly_location_ellipses.csv', index = False)
                # f = open(f'built_dataset/{id}/anomaly_location_ellipses.json','w')
                # json_transcription=json.dump(ellipses_json, f, indent = 2)
                # f.close()

    for user in all_trials.keys():
        print(total_folders[user])
        print(all_trials[user])
        assert(total_folders[user]==len(all_trials[user]))
    main_table = pd.DataFrame(main_table)
    if phase < 3:
        main_table = main_table.sort_values(by=['id'])
    else:
        main_table = main_table.sort_values(by=['image'])
    main_table.to_csv(f'built_dataset/metadata_phase_{phase}.csv',index=False, columns = ['id','split','eye_tracking_data_discarded','image','subject_id','image_size_x', 'image_size_y'] + labels_list)
    access_time = time.time()
    pathlist = list(Path('./built_dataset/').glob('**/*')) + list(Path('./built_dataset/').glob('**'))
    print(len(pathlist))
    for path_to_file in pathlist:
        os.utime(path_to_file, (access_time, access_time))

def generate_df_phase_3(discard_df):
    all_trials = {}
    total_trials = {'user1':515,'user2':510,'user3':509,'user4':504,'user5':511}
    for user in list_of_users:
        all_trials[user] = [x for x in range(1,total_trials[user]+1) if x not in discard_df[discard_df['user']==user]['trial'].values]
    experiment_folders = [item for item in glob.glob('anonymized_collected_data/phase_3/*/')]
    get_main_table(experiment_folders, 3,all_trials)

def generate_df_phase_2(discard_df):
    all_trials = {}
    phase = 2
    for user in list_of_users:
        all_trials[user] = [x for x in range(1,51)]
        
    experiment_folders = [item for item in glob.glob(f'anonymized_collected_data/phase_{phase}/*/')]
    get_main_table(experiment_folders, phase,all_trials)

def generate_df_phase_1(discard_df):
    all_trials = {}
    for user in list_of_users:
        all_trials[user] = [x for x in range(2,61)]
        
    experiment_folders = [item for item in glob.glob('anonymized_collected_data/phase_1/*/')]
    # convert_pickle_to_json(experiment_folders)
    get_main_table(experiment_folders, 1,all_trials)

discard_df = pd.read_csv('discard_cases.csv')
generate_df_phase_1(discard_df[discard_df['phase']==1])
generate_df_phase_2(discard_df[discard_df['phase']==2])
generate_df_phase_3(discard_df[discard_df['phase']==3])
