import h5py
import pandas as pd
import numpy as np

e1 = h5py.File('embeddings_phase_1.hdf5', 'r')
e2 = h5py.File('embeddings_phase_2.hdf5', 'r')
d1 = h5py.File('embeddings_phase_1_distances.hdf5', 'r')
d2 = h5py.File('embeddings_phase_2_distances.hdf5', 'r')

n1 = int(len(e1.keys())/6)
n2 = int(len(e2.keys())/6)
emb_filename_prefix = 'filtered_embeddings_phase_'
for current_phase in [0,1]:
    current_n = [n1,n2][current_phase]
    current_d = [d1,d2][current_phase]
    current_e = [e1,e2][current_phase]
    emb_filename = emb_filename_prefix +str(current_phase+1) + '.hdf5'
    with h5py.File(emb_filename, "w") as h5_f:
        for h5_index in range(current_n):
            all_timestamps_end = []
            all_timestamps_start = []
            all_embeddings = []
            user = current_d['user_'+f'{h5_index:06}'][0]
            trial_n = current_d['trial_n_'+f'{h5_index:06}'][0]
            for index_fix in range(len(current_d['distance_to_image_'+f'{h5_index:06}'])):
                if current_d['distance_to_image_'+f'{h5_index:06}'][index_fix]==0 or (current_d['distance_to_buttons_'+f'{h5_index:06}'][index_fix]>50 and current_d['distance_to_image_angle_'+f'{h5_index:06}'][index_fix]<0.5):
                    all_timestamps_start.append(current_e['timestamp_start_'+f'{h5_index:06}'][index_fix])
                    all_timestamps_end.append(current_e['timestamp_end_'+f'{h5_index:06}'][index_fix])
                    all_embeddings.append(current_e['embedding_'+f'{h5_index:06}'][index_fix])
            
            h5_f.create_dataset('embedding_'+f'{h5_index:06}', data=np.array(all_embeddings))
            h5_f.create_dataset('timestamp_start_'+f'{h5_index:06}', data=np.array(all_timestamps_start))
            h5_f.create_dataset('timestamp_end_'+f'{h5_index:06}', data=np.array(all_timestamps_end))
            h5_f.create_dataset('user_'+f'{h5_index:06}', data=np.array([user]))
            h5_f.create_dataset('trial_n_'+f'{h5_index:06}', data=np.array([trial_n]))
