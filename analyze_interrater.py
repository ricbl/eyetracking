import pandas as pd
from collections import defaultdict, OrderedDict
import numpy
import numpy as np
from nltk import agreement
# import matlab.engine
import csv
from sklearn.metrics import roc_auc_score, confusion_matrix

labels = ['Atelectasis','Consolidation','Pulmonary Edema','Airway Wall Thickening','Groundglass Opacity','Mass','Nodule','Pneumothorax','Pleural Effusion','Pleural Thickening','Emphysema','Fibrosis','Wide Mediastinum','Enlarged Cardiac Silhouette','Support Devices','Fracture','Quality Issue','Other']
# eng = matlab.engine.start_matlab()
# eng.addpath('/usr/share/matlab/site/m/psychtoolbox-3/',nargout=0)
eng = []
import shapely
import shapely.geometry as geometry
def create_ellipse(rect):
    center = (rect[0],rect[1])
    axis = (rect[2],rect[3])
    point = geometry.point.Point(center).buffer(1)
    ellipse = shapely.affinity.scale(point, int(axis[0]), int(axis[1]))
    return ellipse

def create_box(rect):
    return geometry.box(rect[0], rect[1], rect[2], rect[3])

def get_iou(list_rect1, list_rect2, shape_function):
    ellipses = [None, None]
    for i,list_rect in enumerate([list_rect1, list_rect2]):
        for rect in list_rect:
            ellipse = shape_function(rect)
            if ellipses[i] is None:
                ellipses[i] = ellipse
            else:
                ellipses[i] = ellipses[i].union(ellipse)
    intersect = ellipses[0].intersection(ellipses[1])
    return intersect.area/(ellipses[0].area+ellipses[1].area-intersect.area)

def filter_by_timestamp(table, begin_timestamp, end_timestamp):
    table = table[table['timestamp']>=begin_timestamp]
    table = table[table['timestamp']<=end_timestamp]
    return table

def get_last_saved_screen(table, trial, screen):
    table = table[table['trial'] == trial]
    table = table[table['screen'] == screen]
    table_filter = table[table['messenger'] == 'MainWindow']
    begin_timestamp = table_filter[table_filter['title'] == 'index_start_screen_trial']['timestamp'].values.tolist()[-1]
    end_timestamp = table_filter[table_filter['title'] == 'end_screen_trial']['timestamp'].values.tolist()[-1]
    return filter_by_timestamp(table, begin_timestamp, end_timestamp)

def get_value_from_key_value_box(table, box,value):
    a =  table[table['value'] == value]['title'].values
    # print(a)
    assert(len(a)==1)
    b = table[table['title'] == ('extra_properties_value_box_'+str(box)+'_index_' +a[0].split('_')[-1])]['value'].values
    assert(len(b)==1)
    return b[0]

def get_classes_from_csv(csv_file, results_csv, user, transcriptions_csv):
    data_table = pd.read_csv(csv_file)
    transcriptions_table = pd.read_csv(transcriptions_csv)
    all_trials = list(OrderedDict.fromkeys(data_table['trial']))
    # print(all_trials)
    all_trials = all_trials[1:-1]
    answers = {}
    other_label = []
    all_coord_chest = {}
    all_coord_box = defaultdict(lambda: defaultdict(lambda: list()))
    all_certainty_box = defaultdict(lambda: defaultdict(lambda: list()))
    all_index_box = defaultdict(lambda: defaultdict(lambda: list()))
    for trial in all_trials:
        # print(trial)
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
            
            eng.append("generate_image_from_saved_data('"+filepath+"', {["+' '.join([str(coord_value) for coord_value in coords_chest])+"]}, 0, 0, 0, 0,'./results/"+user+"/chest_box_screen_"+str(trial)+".png',0,'"+user+"',0)")
            # eng.generate_image_from_saved_data(filepath, [coords_chest], 0, 0, 0, 0,'./results/'+user+/'chest_box_screen_'+str(trial)+'.png',0, nargout=0)
            
            data_table_transcription_this_trial = get_last_saved_screen(data_table_this_trial, trial, 11)
            # transcription = data_table_transcription_this_trial[data_table_transcription_this_trial['messenger'] == 'TextBox']['value'].values[0]
            transcription = transcriptions_table[transcriptions_table['user']==user]
            transcription = transcription[transcription['trial']==trial]
            assert(len(transcription)==1)
            transcription = transcription['transcription'].values[0]
            new_row = {'user':user, 'label':'', 'trial':trial, 'title':'transcription', 'value':transcription}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_transcription_this_trial = get_last_saved_screen(data_table_this_trial, trial, 2)
            transcription = data_table_transcription_this_trial[data_table_transcription_this_trial['title'] == 'start_audio_recording']['timestamp'].values[0]
            new_row = {'user':user, 'label':'', 'trial':trial, 'title':'start_audio_recording', 'value':transcription}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_answers_this_trial = get_last_saved_screen(data_table_this_trial, trial, 4)
            data_table_answers_this_trial = data_table_answers_this_trial[data_table_answers_this_trial['messenger'] == 'ButtonChoice_disease']
            
            for label in labels:
                label_selected = data_table_answers_this_trial[data_table_answers_this_trial['title'] == label]['value']
                labels_trial[label] = -int(label_selected)
            
            if labels_trial['Other']==-1:
                data_table_other_this_trial = get_last_saved_screen(data_table_this_trial, trial, 5)
                for other_ in data_table_other_this_trial[data_table_other_this_trial['title']=='text']['value'].values[0].split('@$'):
                    new_row = {'user':user, 'label':'', 'trial':trial, 'title':'Other label', 'value':other_}
                    results_csv = results_csv.append(new_row, ignore_index=True)
            
            data_table_answers_this_trial = get_last_saved_screen(data_table_this_trial, trial, 7)
            total_boxes = int(data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'total_boxes']['value'])
            rect_list = []
            label_matrix = numpy.zeros([len(labels), total_boxes])
            from_center = 0;
            for box in range(1,total_boxes+1):
                # print('oi1')
                # print(box)
                # print(data_table_answers_this_trial)
                begin_timestamp = data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'box_'+str(box)+'_from_center']['timestamp'].values.tolist()[-1]
                end_timestamp = data_table_answers_this_trial[data_table_answers_this_trial['title'] == 'box_' +str(box)+ '_deleted']['timestamp'].values.tolist()[-1]
                
                data_table_answers_this_trial_this_box = filter_by_timestamp(data_table_answers_this_trial, begin_timestamp, end_timestamp)
                
                from_center = data_table_answers_this_trial_this_box[data_table_answers_this_trial_this_box['title']=='box_'+str(box)+'_from_center']['value'].values[0]
                coords_box_ = []
                # print(data_table_answers_this_trial_this_box['title'])
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
                
                # print(begin_timestamp)
                # print(end_timestamp)
                # 
                # print(len(data_table_answers_this_trial_this_box))
                deleted_value = data_table_answers_this_trial_this_box[data_table_answers_this_trial_this_box['title'] == 'box_' +str(box)+ '_deleted']['value'].values
                assert(len(deleted_value)==1)
                if deleted_value[0] == 'false':
                    rect_list.append(coords_box_)
                    certainty = 6 - int(get_value_from_key_value_box(data_table_answers_this_trial_this_box,box,'certainty_chosen_index'))
                    list_labels_this_box = []
                    for label_index, label in enumerate(labels):
                        if label in {'Other', 'Support Devices', 'Quality Issue'}:
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
                    if len(list_labels_this_box)>1:
                        new_row = {'user':user, 'label':'', 'trial':trial, 'title':'Pair labels same box', 'value':','.join(sorted(list_labels_this_box))}
                        results_csv = results_csv.append(new_row, ignore_index=True)
                        
            eng.append("generate_image_from_saved_data('"+filepath+"', {"+','.join([('['+' '.join([str(coord_value) for coord_value in coords_this_rect])+']') for coords_this_rect in rect_list])+"}, 1, {'"+"','".join(labels)+"'},[" + \
                ';'.join(['['+' '.join([str(label_matrix[ni,nj]) for nj in range(label_matrix.shape[1])])+']'  for ni in range(label_matrix.shape[0])]) +'],'+ str(from_center)+",'./results/"+user+"/bbox_screen_"+str(trial)+".png',1,'"+user+"',["+ \
                ' '.join([str((labels_trial[label_1]!=0)*1) for label_1 in labels])+"])")
            # eng.generate_image_from_saved_data(filepath, rect_list, 1, labels, label_matrix, from_center,'./results/'+user+'/bbox_screen_'+str(trial)+'.png',1, nargout=0)
        answers[trial] = labels_trial
    return answers, results_csv, all_coord_chest, all_coord_box, all_certainty_box, all_index_box

def convert_center_axis_to_corners(rect):
    return [rect[0]-rect[2], rect[1]-rect[3],rect[0]+rect[2],rect[1]+rect[3]]

def analyze_interrater_reliability():
    data_folders = ['user1_203_20201216-141859-3506','user3_203_20201210-101303-6691','user3_203_20201217-083511-9152', 'user2_203_20201201-092234-9617',  'user1_203_20201216-142259-5921', 'user1_203_20201218-142722-8332', 'user1_203_20201223-140239-9152', 'user4_203_20201222-150420-9152', 'user5_203_20201113', 'user4_203_20210104-130049-9152']
    # data_folders = [ 'user2_203_20201201-092234-9617', 'user4_203_20201222-150420-9152', 'user4_203_20210104-130049-9152','user1_203_20201216-141859-3506','user1_203_20201216-142259-5921', 'user1_203_20201218-142722-8332', 'user1_203_20201223-140239-9152', 'user5_203_20201113','user3_203_20201210-101303-6691','user3_203_20201217-083511-9152']
    labels_table = defaultdict(dict)
    chest_table = defaultdict(dict)
    box_table = defaultdict(dict)
    certainty_box_table = defaultdict(dict)
    index_box_table = defaultdict(dict)
    results_csv = pd.DataFrame()
    for data_folder in data_folders:
        # print(data_folder)
        user = data_folder.split('_')[0]
        # print(user)
        answers, results_csv, all_coord_chest, all_coord_box, all_certainty_box,all_index_box = get_classes_from_csv('anonymized_collected_data/phase_1/'+data_folder +'/structured_output.csv', results_csv, user,'anonymized_collected_data/phase_1/phase_1_transcriptions_anon.csv')
        labels_table[user].update(answers)
        chest_table[user].update(all_coord_chest)
        box_table[user].update(all_coord_box)
        certainty_box_table[user].update(all_certainty_box)
        index_box_table[user].update(all_index_box)
    user_lists = []
    # print(eng)
    # result_file = open("lsit_of_matlabs_command.csv",'w')
    # wr = csv.writer(result_file)
    # for item in eng:
    #     wr.writerow([item,])
    # 1/0
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
        # print(user)
        # print(len(trial_lists))
        user_lists.append(trial_lists)
    full_array = numpy.asarray(user_lists)
    numpy.logical_or(full_array<0, full_array>=3)*1.
    
    
    print(full_array.shape)
    # print(((full_array==5)*1.).sum())
    # 1/0
    full_array = numpy.logical_or(full_array<0, full_array>=3)
    skip_index = labels_list.index('Skip')
    use_trials = (full_array[:,:,skip_index].sum(axis = 0)==0)
    disease_labels_array = full_array[:,use_trials,:]
    print(disease_labels_array.shape)
    import random
    for k in range(len(labels_list)):
        # print(labels_list[k])
        if labels_list[k]=='Skip':
            array_to_use = full_array
            trials_to_use = range(1,full_array.shape[1]+1)
        else:
            array_to_use = disease_labels_array
            trials_to_use = (np.array(np.where(use_trials))+1).tolist()[0]
        formatted_codes = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1])  for j in range(array_to_use.shape[0])]
        ratingtask = agreement.AnnotationTask(data=formatted_codes)
        try:
            value = ratingtask.multi_kappa()
        except ZeroDivisionError:
            value = None
        new_row = {'user':'all', 'label':labels_list[k], 'trial':'all', 'title':'Fleiss Kappa', 'value':value}
        results_csv = results_csv.append(new_row, ignore_index=True)
    
        for trial_index,trial in enumerate(trials_to_use):
            formatted_codes_except = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1])  for j in range(array_to_use.shape[0]) if i!=trial_index]
            ratingtask = agreement.AnnotationTask(data=formatted_codes_except)
            try:
                value = ratingtask.multi_kappa()
            except ZeroDivisionError:
                value = None
            new_row = {'user':'all', 'label':labels_list[k], 'trial':trial, 'title':'Fleiss Kappa (except trial)', 'value':value}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            for user_index, user in enumerate(sorted(labels_table.keys())):
                formatted_codes_except = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1])  for j in range(array_to_use.shape[0]) if i!=trial_index and j!=user_index]
                ratingtask = agreement.AnnotationTask(data=formatted_codes_except)
                try:
                    value = ratingtask.multi_kappa()
                except ZeroDivisionError:
                    value = None
                new_row = {'user':user, 'label':labels_list[k], 'trial':trial, 'title':'Fleiss Kappa (except trial and user)', 'value':value}
                results_csv = results_csv.append(new_row, ignore_index=True)
    
    for user_index, user in enumerate(sorted(labels_table.keys())):
        for k in range(len(labels_list)):
            if labels_list[k]=='Skip':
                array_to_use = full_array
            else:
                array_to_use = disease_labels_array
            formatted_codes_except = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1])  for j in range(array_to_use.shape[0]) if j!=user_index]
            formatted_codes = [[0,i,array_to_use[user_index,i,k]*1.] for i in range(array_to_use.shape[1])]
            
            ratingtask = agreement.AnnotationTask(data=formatted_codes_except)
            try:
                value = ratingtask.multi_kappa()
            except ZeroDivisionError:
                value = None
            new_row = {'user':user, 'label':labels_list[k], 'trial':'all', 'title':'Fleiss Kappa (except user)', 'value':value}
            results_csv = results_csv.append(new_row, ignore_index=True)
            
            formatted_codes_atleast1 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=1)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast1',results_csv, formatted_codes, formatted_codes_atleast1, labels_list[k], user)
            
            formatted_codes_atleast2 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=2)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast2',results_csv, formatted_codes, formatted_codes_atleast2, labels_list[k], user)
            
            formatted_codes_atleast3 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=3)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast3',results_csv, formatted_codes, formatted_codes_atleast3, labels_list[k], user)
            
            for user_index_pair, user_pair in enumerate(sorted(labels_table.keys())):
                if user_index_pair != user_index:
                    formatted_codes_pair = [[1,i,array_to_use[user_index_pair,i,k]*1.] for i in range(array_to_use.shape[1])]
                    results_csv = calculate_per_user('pair',results_csv, formatted_codes, formatted_codes_pair, labels_list[k], user, user_pair)
            
            formatted_codes_majority = [[1,i,((array_to_use[:,i,k]).sum()>2.5)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('majority',results_csv, formatted_codes, formatted_codes_majority, labels_list[k], user)
    
    ious_box = []
    for trial in trials_list:
        if use_trials[int(trial)-1]:
            for k in range(len(labels_list)):
                for user_index, user in enumerate(sorted(labels_table.keys())):
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
                    
                    # do IoU for label BBox for every pairs of users
                    for user_index_2, user_2 in enumerate(sorted(labels_table.keys())):
                        if user_index_2!=user_index:
                            if trial in box_table[user].keys() and trial in box_table[user_2].keys() :
                                # print(box_table[user][trial][labels_list[k]])
                                if len(box_table[user][trial][labels_list[k]])>0 and len(box_table[user_2][trial][labels_list[k]])>0:
                                    value = get_iou(box_table[user][trial][labels_list[k]],box_table[user_2][trial][labels_list[k]],create_ellipse)
                                    new_row = {'user':user, 'extra_info':user_2, 'label':labels_list[k], 'trial':trial, 'title':'IoU box (pair)', 'value':value}
                                    results_csv = results_csv.append(new_row, ignore_index=True)
                                    
                                    
    
    ious_chest = []
    for user_index, user in enumerate(sorted(labels_table.keys())):
        ious_this_user = []
        for trial in trials_list:
            if use_trials[int(trial)-1]:
                for coord_index, coord in enumerate(chest_table[user][trial]):
                    new_row = {'user':user, 'extra_info':'', 'label':'', 'trial':trial, 'title':'ChestBox (Rectangle) coord ' + str(coord_index), 'value':coord}
                    results_csv = results_csv.append(new_row, ignore_index=True)
                
                for user_index_2, user_2 in enumerate(sorted(labels_table.keys())):
                    if user_index_2!=user_index:
                        ious_this_user.append(get_iou([chest_table[user][trial]],[chest_table[user_2][trial]],create_box))
                        new_row = {'user':user, 'extra_info':user_2, 'label':'', 'trial':trial, 'title':'IoU chest (pair)', 'value':ious_this_user[-1]}
                        results_csv = results_csv.append(new_row, ignore_index=True)
        # new_row = {'user':user, 'label':'', 'trial':'all', 'title':'IoU chest (pair, by user)', 'value':sum(ious_this_user)/len(ious_this_user)}
        # results_csv = results_csv.append(new_row, ignore_index=True)
        # ious_chest += ious_this_user
    # new_row = {'user':'all', 'label':'', 'trial':'all', 'title':'IoU chest (pair)', 'value':sum(ious_chest)/len(ious_chest)}
    # results_csv = results_csv.append(new_row, ignore_index=True)
    
    results_csv.to_csv('results_phase_1.csv', index=False)
    
def calculate_per_user(name, results_csv, formatted_codes, formatted_codes_other, label, user,user2 = None):
    try:
        value_roc = roc_auc_score(np.array([row[2] for row in formatted_codes_other]), np.array([row[2] for row in formatted_codes]))
    except ValueError:
        value_roc = None
    new_row = {'user':user, 'extra_info':user2, 'label':label, 'trial':'all', 'title':'AUC ('+name+')', 'value':value_roc}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    arg_1 = np.array([row[2] for row in formatted_codes_other])
    arg_2 = np.array([row[2] for row in formatted_codes])
    if sum(arg_1)==0 and sum(arg_2)==0:
        tn = len(arg_1)
        tp = 0
        fp = 0
        fn = 0
    else:
        tn, fp, fn, tp = confusion_matrix(np.array([row[2] for row in formatted_codes_other]), np.array([row[2] for row in formatted_codes])).ravel()
    
    if tn+fp!=0:
        specificity = tn / (tn+fp)
    else:
        specificity = None
    new_row = {'user':user, 'extra_info':user2, 'label':label, 'trial':'all', 'title':'Specificity ('+name+')', 'value':specificity}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    if tp+fn!=0:
        recall = tp / (tp+fn)
    else:
        recall = None
    new_row = {'user':user, 'extra_info':user2, 'label':label, 'trial':'all', 'title':'Recall ('+name+')', 'value':recall}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    if tp+fp!=0:
        precision = tp / (tp+fp)
    else:
        precision = None
    new_row = {'user':user, 'extra_info':user2, 'label':label, 'trial':'all', 'title':'Precision ('+name+')', 'value':precision}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    ratingtask = agreement.AnnotationTask(data=formatted_codes_other+formatted_codes)
    try:
        value = ratingtask.multi_kappa()
    except ZeroDivisionError:
        value = None
    new_row = {'user':user, 'extra_info':user2,'label':label, 'trial':'all', 'title':'Fleiss Kappa ('+name+')', 'value':value}
    results_csv = results_csv.append(new_row, ignore_index=True)
    return results_csv

# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
analyze_interrater_reliability()