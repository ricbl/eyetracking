#change these to the folders where the datasets are located on your machine
# works for all of the scripts located in this folder
reflacx_dataset_location = '../built_dataset/' # main_data should be a subfolder in this location
mimic_iv_dataset_location = '../datasets/mimic/tables/' # patients.csv should be a file in this location. This is only used for the get_sex_statistics_dataset script
mimiccxr_images_location = '../datasets/mimic/' # the ssubfolder structure physionet.org/files/mimic-cxr/2.0.0/files/p.../p.../s.../....dcm should be in this folder
mimiccxr_tables_location = '../datasets/mimic/tables/' # cxr-record-list.csv, mimic-cxr-2.0.0-chexpert.csv, mimic-cxr-2.0.0-split.csv should be a file in this location.