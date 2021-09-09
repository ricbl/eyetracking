# this script was used to generate the tables used to calculte the statistics of the calibrations as listed in section "Technical Validation > Eye-tracking data" of the paper
# the dataset does not provided the data needed to run this script

import pandas as pd

def create_calibration_table(phase):
    fixations_table = pd.read_csv(f'../post_processing_and_dataset_generation/summary_edf_phase_{phase}.csv')
    fixations_table['trial'] = fixations_table['trial'].astype(float)
    users = fixations_table['user'].unique()
    main_table = []
    
    for user in users:
        
        table_this_user = fixations_table[fixations_table['user']==user]
        trials = table_this_user['trial'].unique()
        
        #for every trial, find the last calibration performed before it
        for trial in trials:
            
            if trial == 0:
                continue
            table_discard = table_this_user[table_this_user['trial']==trial]
            
            table_discard = table_discard[table_discard['screen']==2]
            
            table_discard = table_discard[table_discard['type']=='discard']
            assert(len(table_discard)==1)
            discard = table_discard['value'].values[0]
            index = table_discard.index.values[0]
            
            table_this_trial_this_user = table_this_user[table_this_user.index<=index]
            
            table_max = table_this_trial_this_user[table_this_trial_this_user['type']=='max_calibration_error']
            if len(table_max.index.values)==0:
                print(trial)
                print(user)
                continue
            index_previous = table_max.index.values[-1]
            table_latest_trial = table_this_trial_this_user[table_this_trial_this_user.index==index_previous]
            
            #adjust the trial associated with each calibration to be the following trial, and not the previous
            if table_latest_trial['trial'].values[0]!= trial:
                check_next_trial_after_calibration = table_this_trial_this_user[table_this_trial_this_user.index>=index_previous]
                check_next_trial_after_calibration = check_next_trial_after_calibration[check_next_trial_after_calibration['trial']!=table_latest_trial['trial'].values[0]]
                calibration_trial = check_next_trial_after_calibration['trial'].values[0]
            else:
                calibration_trial = trial
            
            max_table = table_latest_trial[table_latest_trial['type']=='max_calibration_error']
            
            assert(len(max_table)==1)
            max_value = max_table['value'].values[0]
            
            table_avg = table_this_trial_this_user[table_this_trial_this_user['type']=='avg_calibration_error']
            index_previous = table_avg.index.values[-1]
            table_latest_trial = table_this_trial_this_user[table_this_trial_this_user.index==index_previous]
            
            avg_table = table_latest_trial[table_latest_trial['type']=='avg_calibration_error']
            assert(len(avg_table)==1)
            avg_value = avg_table['value'].values[0]
            new_row = {'user':user,'trial':trial,'avg_calibration_error':avg_value,'max_calibration_error':max_value, 'calibration_trial':calibration_trial,'discard':discard}
            main_table.append(new_row)
    pd.DataFrame(main_table).to_csv(f'calibration_table_{phase}.csv')

create_calibration_table(1)
create_calibration_table(2)
create_calibration_table(3)