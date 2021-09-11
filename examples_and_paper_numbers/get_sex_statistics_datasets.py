# get the numbers used for the calculation of the sex statistics present in Table 1

import pandas as pd
from dataset_locations import mimic_iv_dataset_location, mimiccxr_tables_location, reflacx_dataset_location

def get_sex_statistics(phase):
    patients = pd.read_csv(f'{mimic_iv_dataset_location}/patients.csv')
    if phase=='mimic':
        metadata_1 = pd.read_csv(f'./image_all_paths.txt', delimiter = "\t", names = ['path'])
        metadata_1['path'] = metadata_1['path'].apply(lambda x: '/'.join(x.split('/')[4:]))
        metadata_2 = pd.read_csv(f'{mimiccxr_tables_location}/cxr-record-list.csv')
        metadata = pd.merge(metadata_1, metadata_2)
    elif phase=='all':
        metadata = pd.concat([pd.read_csv(f'{reflacx_dataset_location}/main_data/metadata_phase_1.csv')[['subject_id']],pd.read_csv(f'{reflacx_dataset_location}/main_data/metadata_phase_2.csv')[['subject_id']],pd.read_csv(f'{reflacx_dataset_location}/main_data/metadata_phase_3.csv')[['subject_id']]])
    else:
        metadata = pd.read_csv(f'{reflacx_dataset_location}/main_data/metadata_phase_{phase}.csv')
    print('\n')
    print('n subjects:',len(metadata['subject_id'].unique()))
    
    joined_table = pd.merge(metadata, patients)
    
    print('n subjects with sex listed:',len(joined_table['subject_id'].unique()))
    print('Phase:', phase)
    print('Females:',len(joined_table[joined_table['gender']=='F']['subject_id'].unique()))
    print('Males:',len(joined_table[joined_table['gender']=='M']['subject_id'].unique()))
    print('\n')
    
get_sex_statistics(1)
get_sex_statistics(2)
get_sex_statistics(3)
get_sex_statistics('all')
get_sex_statistics('mimic')
