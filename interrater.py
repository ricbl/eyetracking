import pandas as pd
from collections import defaultdict, OrderedDict
import numpy
import numpy as np
from nltk import agreement
# import matlab.engine
import csv
from sklearn.metrics import roc_auc_score, confusion_matrix
from statsmodels.stats import inter_rater
import math

dataset_location = 'built_dataset/main_data/'

eng = []
import shapely
import shapely.geometry as geometry
def create_ellipse(coords_box_):
    coords_box = []
    coords_box.append((coords_box_[0]+coords_box_[2])/2)
    coords_box.append((coords_box_[1]+coords_box_[3])/2)
    coords_box.append(abs(coords_box_[0]-coords_box_[2])/2)
    coords_box.append(abs(coords_box_[1]-coords_box_[3])/2)
    rect = coords_box
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

def convert_center_axis_to_corners(rect):
    return [rect[0]-rect[2], rect[1]-rect[3],rect[0]+rect[2],rect[1]+rect[3]]

def convert_to_stats_table(array, total_raters):
    array = np.transpose(array)
    array_to_return = np.zeros([array.shape[0], 2])
    array_to_return[:,0] = array.sum(axis = 1)
    array_to_return[:,1] = total_raters - array.sum(axis = 1)
    return array_to_return

def fleiss_kappa_standard_error(table):
    n_raters = np.sum(table[0,:])
    n_categories = table.shape[1]
    n_cases = table.shape[0]
    p = np.sum(table, axis = 0)/n_raters/n_cases
    sum_p2 = np.sum(p**2)
    sum_p3 = np.sum(p**3)
    var_k = 2/n_cases/n_raters/(n_raters-1)*(sum_p2-(2*n_raters-3)*sum_p2**2+2*(n_raters-2)*sum_p3)/(1-sum_p2)**2
    return math.sqrt(var_k)

def analyze_interrater_reliability(phase, labels):
    results_csv = pd.DataFrame()
    labels_list = labels
    metadata_phase = pd.read_csv(f'{dataset_location}/metadata_phase_{phase}.csv')
    all_images = metadata_phase['image'].unique()
    full_array = np.full([5,len(all_images),len(labels)], True)
    for i,image in enumerate(all_images):
        j = 0
        for _, row in metadata_phase[metadata_phase['image']==image].iterrows():
            for k, label in enumerate(labels):
                if label.lower() in ['support devices', 'quality issue']:
                    full_array[j,i,k] = row[label]
                else:
                    full_array[j,i,k] = row[label]>=3
            j += 1
        assert(j==5)
    
    for k in range(len(labels)):
        array_to_use = full_array
        # print(np.sum(array_to_use[:,:,k]))
        # print(np.sum(array_to_use[:,:,k], 1))
        # print(np.sum(array_to_use[:,:,k], 0))
        
        
        # numpy.savetxt(f"rating_{labels[k].replace('/','_').replace(' ','_').lower()}_phase_{phase}.csv", convert_to_stats_table(array_to_use[:,:,k], 5), delimiter=",")
        # numpy.savetxt(f"rating_2_{labels[k].replace('/','_').replace(' ','_').lower()}_phase_{phase}.csv", array_to_use[:,:,k], delimiter=",")
        table_answers = convert_to_stats_table(array_to_use[:,:,k], 5)
        value = inter_rater.fleiss_kappa(table_answers, method='fleiss')
        
        se = fleiss_kappa_standard_error(table_answers)
        
        
        # formatted_codes = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1]) for j in range(array_to_use.shape[0])]
        # 
        # # i -> trial
        # # j -> user
        # ratingtask = agreement.AnnotationTask(data=formatted_codes)
        # try:
        #     value = ratingtask.multi_kappa()
        # except ZeroDivisionError:
        #     value = None
        # print(labels[k])
        # print(value)
        # 1/0
        new_row = {'label':labels_list[k], 'title':'Fleiss Kappa', 'value':value}
        results_csv = results_csv.append(new_row, ignore_index=True)
        new_row = {'label':labels_list[k], 'title':'Fleiss Kappa standard error', 'value':se}
        results_csv = results_csv.append(new_row, ignore_index=True)
    
        for trial_index,_ in enumerate(all_images):
            # formatted_codes_except = [[j,i,array_to_use[j,i,k]] for i in range(array_to_use.shape[1])  for j in range(total_cases_image[i]) if i!=trial_index]
            # ratingtask = agreement.AnnotationTask(data=formatted_codes_except)
            # try:
            #     value = ratingtask.multi_kappa()
            # except ZeroDivisionError:
            #     value = None
            value = inter_rater.fleiss_kappa(convert_to_stats_table(np.delete(array_to_use[:,:,k], trial_index, axis = 1), 5), method='fleiss')
            new_row = {'label':labels_list[k], 'trial':trial_index, 'title':'Fleiss Kappa (except trial)', 'value':value}
            results_csv = results_csv.append(new_row, ignore_index=True)
    
    for user_index in range(full_array.shape[0]):
        for k in range(len(labels_list)):
            array_to_use = full_array
            formatted_codes = [[0,i,array_to_use[user_index,i,k]*1.] for i in range(array_to_use.shape[1])]
    
            formatted_codes_atleast1 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=1)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast1',results_csv, formatted_codes, formatted_codes_atleast1, labels_list[k])
    
            formatted_codes_atleast2 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=2)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast2',results_csv, formatted_codes, formatted_codes_atleast2, labels_list[k])
    
            formatted_codes_atleast3 = [[1,i,(sum(numpy.delete(array_to_use[:,i,k], user_index, 0))>=3)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('atleast3',results_csv, formatted_codes, formatted_codes_atleast3, labels_list[k])
    
            for user_index_pair in range(full_array.shape[0]):
                if user_index_pair != user_index:
                    formatted_codes_pair = [[1,i,array_to_use[user_index_pair,i,k]*1.] for i in range(array_to_use.shape[1])]
                    results_csv = calculate_per_user('pair',results_csv, formatted_codes, formatted_codes_pair, labels_list[k])
    
            formatted_codes_majority = [[1,i,((array_to_use[:,i,k]).sum()>2.5)*1.] for i in range(array_to_use.shape[1])]
            results_csv = calculate_per_user('majority',results_csv, formatted_codes, formatted_codes_majority, labels_list[k])
    
    # chest_boxes_iou = []
    
    for image_index,image in enumerate(all_images):
        this_case = metadata_phase[metadata_phase['image']==image]
        all_chest_boxes = []
        for id in this_case['id'].values:
            chest_box_table = pd.read_csv(f'{dataset_location}/{id}/chest_bounding_box.csv')
            chest_box_coordinates = chest_box_table.values[0]
            assert(len(chest_box_coordinates)==4)
            all_chest_boxes.append(chest_box_coordinates)
        for index_1 in range(len(all_chest_boxes)):
            for index_2 in range(len(all_chest_boxes)):
                if index_1!=index_2:
                    value = get_iou([all_chest_boxes[index_1]],[all_chest_boxes[index_2]],create_box)
                    new_row = {'trial':image_index, 'title':'Chest Box IoU', 'value':value}
                    results_csv = results_csv.append(new_row, ignore_index=True)
                        
    # ellipses_iou = []
    for k in range(len(labels_list)):
        print(labels_list[k])
        for image_index,image in enumerate(all_images):
            ellipses_iou_k = []
            this_case = metadata_phase[metadata_phase['image']==image]
            ellipses = []
            for id in this_case['id'].values:
                
                ellipse_table = pd.read_csv(f'{dataset_location}/{id}/anomaly_location_ellipses.csv')
                if labels_list[k]=='Enlarged cardiac silhouette':
                    print(ellipse_table['Enlarged cardiac silhouette'])
                    print(ellipse_table['certainty'])
                    
                ellipse_table = ellipse_table[ellipse_table['certainty']>2]
                ellipse_table = ellipse_table[ellipse_table[labels_list[k]]]
                if labels_list[k]=='Enlarged cardiac silhouette':
                    print(image_index)
                    print(len(ellipse_table))
                if len(ellipse_table)>0:
                    ellipses.append(ellipse_table[['xmin','ymin','xmax','ymax']].values)
                else:
                    ellipses.append([])
            for user_index in range(len(ellipses)):
                # do IoU for label BBox for every pairs of users
                for user_index_2 in range(len(ellipses)):
                    if user_index_2!=user_index:
                        if len(ellipses[user_index])>0 and len(ellipses[user_index_2])>0:
                            # print(ellipses[user_index])
                            # print(ellipses[user_index_2])
                            value = get_iou(ellipses[user_index],ellipses[user_index_2],create_ellipse)
                            ellipses_iou_k.append(value)
            if len(ellipses_iou_k)>0:
                average_iou = np.mean(ellipses_iou_k)
                new_row = {'label':labels_list[k],'trial':image_index, 'title':'Ellipse IoU', 'value':average_iou}
                results_csv = results_csv.append(new_row, ignore_index=True)



    
    results_csv.to_csv(f'interrater_phase_{phase}.csv', index=False)
    
def calculate_per_user(name, results_csv, formatted_codes, formatted_codes_other, label):
    try:
        value_roc = roc_auc_score(np.array([row[2] for row in formatted_codes_other]), np.array([row[2] for row in formatted_codes]))
    except ValueError:
        value_roc = None
    new_row = {'label':label, 'title':'AUC ('+name+')', 'value':value_roc}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    arg_1 = np.array([row[2] for row in formatted_codes_other])
    arg_2 = np.array([row[2] for row in formatted_codes])
    if sum(arg_1)==0 and sum(arg_2)==0:
        tn = len(arg_1)
        tp = 0
        fp = 0
        fn = 0
    elif sum(arg_1)==len(arg_1) and sum(arg_2)==len(arg_2):
        tn = 1
        tp = len(arg_1)
        fp = 0
        fn = 0
    else:
        tn, fp, fn, tp = confusion_matrix(arg_1, arg_2).ravel()
    
    if tn+fp!=0:
        specificity = tn / (tn+fp)
    else:
        specificity = None
    new_row = {'label':label, 'title':'Specificity ('+name+')', 'value':specificity}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    if tp+fn!=0:
        recall = tp / (tp+fn)
    else:
        recall = None
    new_row = {'label':label,'title':'Recall ('+name+')', 'value':recall}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    if tp+fp!=0:
        precision = tp / (tp+fp)
    else:
        precision = None
    new_row = { 'label':label, 'title':'Precision ('+name+')', 'value':precision}
    results_csv = results_csv.append(new_row, ignore_index=True)
    
    return results_csv

labels = sorted(['Atelectasis','Consolidation','Pulmonary edema','Airway wall thickening','Groundglass opacity','Mass','Nodule','Pneumothorax','Pleural effusion','Pleural thickening','Emphysema','Fibrosis','Wide mediastinum','Enlarged cardiac silhouette','Support devices','Fracture','Quality issue'])
analyze_interrater_reliability(1, labels)
labels = sorted(['Support devices', 'Abnormal mediastinal contour', 'Enlarged cardiac silhouette', 'Enlarged hilum', 'Hiatal hernia', 'Pneumothorax', 'Pleural abnormality', 'Consolidation','Groundglass opacity','Atelectasis', 'Lung nodule or mass', 'Pulmonary edema', 'High lung volume / emphysema','Interstitial lung disease', 'Acute fracture'])
analyze_interrater_reliability(2, labels)
