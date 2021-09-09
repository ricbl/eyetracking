# calculates the statistics presented in Table 1 for the filtered MIMIC-CXR dataset

import pandas as pd
from dataset_locations import mimiccxr_tables_location

labels_mimic = ['Atelectasis',
'Cardiomegaly',
'Consolidation',
'Edema',
'Enlarged Cardiomediastinum',
'Fracture','Lung Lesion',
'Lung Opacity',
'No Finding','Pleural Effusion','Pleural Other','Pneumonia','Pneumothorax','Support Devices']

# This txt lists all the images from the MIMIC-CXR after the filtering described in the paper
with open('./image_all_paths.txt') as f:
    content = f.readlines()
content = [x.strip() for x in content] 
subject_id = [int(x.split('/')[-3][1:]) for x in content]
study_id = [int(x.split('/')[-2][1:]) for x in content]
dicom_id = [x.split('/')[-1][:-4] for x in content]
image_paths_df = pd.DataFrame(
    {'image_path': content,
     'subject_id': subject_id,
     'study_id': study_id,
     'dicom_id':dicom_id
    })
labels_df = pd.read_csv(f'{mimiccxr_tables_location}/mimic-cxr-2.0.0-chexpert.csv')
for label in labels_mimic:
    labels_df[label] = (labels_df[label] > 0) * 1.
splits_df = pd.read_csv(f'{mimiccxr_tables_location}/mimic-cxr-2.0.0-split.csv')
final_df = pd.merge(image_paths_df,labels_df,on=['study_id', 'subject_id'])
final_df = pd.merge(final_df,splits_df,on=['dicom_id'])
final_df.to_csv('mimic_metadata_count.csv')
