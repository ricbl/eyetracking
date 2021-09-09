# calculates the scores of agreement among radiologists for their manual labeling as presented in the paper
# example of: 
#- how to load tables of manual labels in the dataset.

import pandas as pd
from collections import defaultdict, OrderedDict
import numpy
import numpy as np
from nltk import agreement
import csv
from sklearn.metrics import roc_auc_score, confusion_matrix
from statsmodels.stats import inter_rater
import math
from dataset_locations import reflacx_dataset_location
dataset_location = f'{reflacx_dataset_location}/main_data/'

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
    
    # convert metadata table information to a more compact format to use for calculations
    full_array = np.full([5,len(all_images),len(labels)], True)
    for i,image in enumerate(all_images):
        j = 0
        for _, row in metadata_phase[metadata_phase['image']==image].iterrows():
            for k, label in enumerate(labels):
                if label.lower() in ['support devices', 'quality issue']:
                    full_array[j,i,k] = row[label]
                else:
                    # for labels that had a certainty chosen, only consider as present for Possibly or higher
                    full_array[j,i,k] = row[label]>=3
            j += 1
        assert(j==5)
    
    #calculate fleiss kappa for every label, as shown in part of Table 2
    for k in range(len(labels)):
        array_to_use = full_array       
        
        # numpy.savetxt(f"rating_{labels[k].replace('/','_').replace(' ','_').lower()}_phase_{phase}.csv", convert_to_stats_table(array_to_use[:,:,k], 5), delimiter=",")
        # numpy.savetxt(f"rating_2_{labels[k].replace('/','_').replace(' ','_').lower()}_phase_{phase}.csv", array_to_use[:,:,k], delimiter=",")
        table_answers = convert_to_stats_table(array_to_use[:,:,k], 5)
        value = inter_rater.fleiss_kappa(table_answers, method='fleiss')
        
        #calculates the Fleiss Kappa standard error using the equation from the original paper (Fleiss, 1971)
        se = fleiss_kappa_standard_error(table_answers)
        
        new_row = {'label':labels_list[k], 'title':'Fleiss Kappa', 'value':value}
        results_csv = results_csv.append(new_row, ignore_index=True)
        new_row = {'label':labels_list[k], 'title':'Fleiss Kappa standard error', 'value':se}
        results_csv = results_csv.append(new_row, ignore_index=True)
        
        #calculate how much would the Fleiss Kappa be without the answers for each specific chest x-ray, for understanding what cases were the worst for that label
        for trial_index,_ in enumerate(all_images):
            value = inter_rater.fleiss_kappa(convert_to_stats_table(np.delete(array_to_use[:,:,k], trial_index, axis = 1), 5), method='fleiss')
            new_row = {'label':labels_list[k], 'trial':trial_index, 'title':'Fleiss Kappa (except trial)', 'value':value}
            results_csv = results_csv.append(new_row, ignore_index=True)
    
    #get IoU for chest bounding boxes, used to calculate the numbers presented in Technical Validation > Validation Labels > Chest bounding boxes
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
    
    #get IoU for drawn ellipses, used to calculate part of Table 2
    for k in range(len(labels_list)):
        print(labels_list[k])
        for image_index,image in enumerate(all_images):
            ellipses_iou_k = []
            this_case = metadata_phase[metadata_phase['image']==image]
            ellipses = []
            for id in this_case['id'].values:
                
                ellipse_table = pd.read_csv(f'{dataset_location}/{id}/anomaly_location_ellipses.csv')
                
                #only use labels with certainty Possibly or higher
                ellipse_table = ellipse_table[ellipse_table['certainty']>2]
                #only use the currently selected label
                ellipse_table = ellipse_table[ellipse_table[labels_list[k]]]
                
                if len(ellipse_table)>0:
                    ellipses.append(ellipse_table[['xmin','ymin','xmax','ymax']].values)
                else:
                    ellipses.append([])
            for user_index in range(len(ellipses)):
                # do IoU for label BBox for every pairs of users who drew at least one ellipse for this label
                for user_index_2 in range(len(ellipses)):
                    if user_index_2!=user_index:
                        if len(ellipses[user_index])>0 and len(ellipses[user_index_2])>0:
                            value = get_iou(ellipses[user_index],ellipses[user_index_2],create_ellipse)
                            ellipses_iou_k.append(value)
            # calculates the average IoU for all the readings of this specific chest x-ray and label
            if len(ellipses_iou_k)>0:
                average_iou = np.mean(ellipses_iou_k)
                new_row = {'label':labels_list[k],'trial':image_index, 'title':'Ellipse IoU', 'value':average_iou}
                results_csv = results_csv.append(new_row, ignore_index=True)
    
    results_csv.to_csv(f'interrater_phase_{phase}.csv', index=False)

labels = sorted(['Atelectasis','Consolidation','Pulmonary edema','Airway wall thickening','Groundglass opacity','Mass','Nodule','Pneumothorax','Pleural effusion','Pleural thickening','Emphysema','Fibrosis','Wide mediastinum','Enlarged cardiac silhouette','Support devices','Fracture','Quality issue'])
analyze_interrater_reliability(1, labels)
labels = sorted(['Support devices', 'Abnormal mediastinal contour', 'Enlarged cardiac silhouette', 'Enlarged hilum', 'Hiatal hernia', 'Pneumothorax', 'Pleural abnormality', 'Consolidation','Groundglass opacity','Atelectasis', 'Lung nodule or mass', 'Pulmonary edema', 'High lung volume / emphysema','Interstitial lung disease', 'Acute fracture'])
analyze_interrater_reliability(2, labels)
