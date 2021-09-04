import pandas as pd

def get_sex_statistics(phase):
    patients = pd.read_csv('datasets/mimic/tables/patients.csv')
    if phase=='mimic':
        metadata_1 = pd.read_csv(f'datasets/mimic/image_all_paths.txt', delimiter = "\t", names = ['path'])
        metadata_1['path'] = metadata_1['path'].apply(lambda x: '/'.join(x.split('/')[4:]))
        # print(len(metadata_1))
        # print(metadata_1.path)
        metadata_2 = pd.read_csv(f'datasets/mimic/tables/cxr-record-list.csv')
        # print(len(metadata_2))
        # print(metadata_2.path)
        metadata = pd.merge(metadata_1, metadata_2)
        # print(len(metadata))
    elif phase=='all':
        metadata = pd.concat([pd.read_csv(f'built_dataset/main_data/metadata_phase_1.csv')[['subject_id']],pd.read_csv(f'built_dataset/main_data/metadata_phase_2.csv')[['subject_id']],pd.read_csv(f'built_dataset/main_data/metadata_phase_3.csv')[['subject_id']]])
    else:
        metadata = pd.read_csv(f'built_dataset/main_data/metadata_phase_{phase}.csv')
    print(patients.columns)
    print(metadata.columns)
    print('Size:',len(metadata['subject_id'].unique()))
    
    # print(metadata[(~metadata.subject_id.isin(patients.subject_id))]['subject_id'])
    
    joined_table = pd.merge(metadata, patients)
    print('Size:',len(joined_table['subject_id'].unique()))
    # assert(len(joined_table)== len(metadata))
    print(joined_table.gender.unique())
    print('Phase:', phase)
    print('Females:',len(joined_table[joined_table['gender']=='F']['subject_id'].unique()))
    print('Males:',len(joined_table[joined_table['gender']=='M']['subject_id'].unique()))
    
get_sex_statistics(1)
get_sex_statistics(2)
get_sex_statistics(3)
get_sex_statistics('all')
get_sex_statistics('mimic')
