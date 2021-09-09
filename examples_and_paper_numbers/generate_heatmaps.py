# generates a heatmap from all the fixations of a dicatation, using gaussians to represent the uncertatiny of location of each fixation
# this script has to be run before running the get_ncc_for_localization_in_et_data script
# this script is relatively slow given the large number of high resolution gaussians being drawn
# example of
# - how to generate heatmaps

import pandas as pd
import numpy as np
from scipy.stats import multivariate_normal
import csv
import pathlib
from dataset_locations import reflacx_dataset_location

eyetracking_dataset_path = f'{reflacx_dataset_location}/main_data/'
def get_gaussian(y,x,sy,sx, sizey,sizex, shown_rects_image_space):
    
    # displace center coordinates because gaussian will be drawn to an array representing only shown parts of the image
    mu = [y-shown_rects_image_space[1],x-shown_rects_image_space[0]]
    sig = [sy**2,sx**2]
    x = np.arange(0, shown_rects_image_space[2]-shown_rects_image_space[0], 1)
    y = np.arange(0, shown_rects_image_space[3]-shown_rects_image_space[1], 1)
    X, Y = np.meshgrid(x, y)
    pos = np.empty(X.shape + (2,))
    pos[:, :, 1] = X
    pos[:, :, 0] = Y
    to_return = np.zeros([sizey,sizex])
    
    #limit the gaussian to only be drawn over shown parts of the image
    to_return[int(round(shown_rects_image_space[1])):int(round(shown_rects_image_space[3])), int(round(shown_rects_image_space[0])):int(round(shown_rects_image_space[2]))] = multivariate_normal(mu, sig).pdf(pos)
    
    return to_return

def create_heatmap(sequence_table, size_x, size_y):
    img = np.zeros((size_y, size_x), dtype=np.float32)
    for index, row in sequence_table.iterrows():
        #gaussian with 1 degree of visual angle as its standard deviation
        angle_circle = 1
        shown_rects_image_space = [round(row['xmin_shown_from_image']) ,round(row['ymin_shown_from_image']),round(row['xmax_shown_from_image']),round(row['ymax_shown_from_image'])]
        gaussian = get_gaussian(row['y_position'],row['x_position'], row['angular_resolution_y_pixels_per_degree']*angle_circle, row['angular_resolution_x_pixels_per_degree']*angle_circle, size_y,size_x, shown_rects_image_space)
        
        #give higher weight for fixations that last longer
        img += gaussian*(row['timestamp_end_fixation']-row['timestamp_start_fixation'])
    #normalize heatmap to a gaze probabitly map
    return img/np.sum(img)

def create_heatmaps(data_folder, filename_phase, folder_name='heatmaps', phase = None):
    
    pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True) 
    df = pd.read_csv(data_folder + filename_phase)
    df = df[df['eye_tracking_data_discarded']==False]
    all_images = df['image'].unique()
    for trial, image_name in enumerate(sorted(all_images)):
        df_this_trial = df[df['image']==image_name]
        index_image = 0
        for _, df_this_index_this_trial in df_this_trial.iterrows():
            
            print('trial', trial, 'index_image', index_image)
            image_size_x = int(float(df_this_index_this_trial['image_size_x']))
            image_size_y = int(float(df_this_index_this_trial['image_size_y']))
            fixations = pd.read_csv(f'{data_folder}/{df_this_index_this_trial["id"]}/fixations.csv')
            this_img = create_heatmap(fixations,image_size_x, image_size_y)

            # Saving the array in npy format
            info_dict = {'np_image': this_img, 'img_path': image_name, 'trial': trial, 'id': df_this_index_this_trial['id'], 'phase': phase }
            np.save(folder_name + '/' + str(trial) + '_' + str(index_image), info_dict)
            
            index_image += 1

# # ### Phase 1
print('Starting Phase 1...')
file_phase_1 = 'metadata_phase_1.csv'

create_heatmaps(eyetracking_dataset_path ,file_phase_1, 
                folder_name='heatmaps_phase_1', phase =  1)

# ### Phase 2
print('Starting Phase 2...')
file_phase_2 = 'metadata_phase_2.csv'

create_heatmaps(eyetracking_dataset_path, file_phase_2,
                      folder_name='heatmaps_phase_2', phase =  1)