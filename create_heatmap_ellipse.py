from skimage.draw import ellipse
from PIL import Image
import pandas as pd
import numpy as np
from scipy.stats import multivariate_normal
from pydicom import dcmread
import pydicom

def get_gaussian(y,x,sy,sx, sizey,sizex, shown_rects_image_space):
    mu = [y-shown_rects_image_space[1],x-shown_rects_image_space[0]]
    sig = [sy**2,sx**2]
    x = np.arange(0, shown_rects_image_space[2]-shown_rects_image_space[0], 1)
    y = np.arange(0, shown_rects_image_space[3]-shown_rects_image_space[1], 1)
    X, Y = np.meshgrid(x, y)
    pos = np.empty(X.shape + (2,))
    pos[:, :, 1] = X
    pos[:, :, 0] = Y
    to_return = np.zeros([sizey,sizex])
    to_return[shown_rects_image_space[1]:shown_rects_image_space[3], shown_rects_image_space[0]:shown_rects_image_space[2]] = multivariate_normal(mu, sig).pdf(pos)
    return to_return

def create_heatmap(sequence_table, size_x, size_y):
    img = np.zeros((size_y, size_x), dtype=np.float32)
    for index, row in sequence_table.iterrows():
        angle_circle = 0.98 #1.9 #0.98
        shown_rects_image_space = [round(row['source_rect_dimension_1']) ,round(row['source_rect_dimension_2']),round(row['source_rect_dimension_3']),round(row['source_rect_dimension_4'])]
        gaussian = get_gaussian(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle, size_y,size_x, shown_rects_image_space)
        img += gaussian*(row['time_linux']-row['time_start_linux'])
    return img/np.sum(img)

def create_heatmaps(filename_edf, filename_images, total_trials, screen_heatmap=2, results_filename=None, folder_name='./heatmaps'):
    df = pd.read_csv(filename_edf, dtype={'value':str})
    
    with open(filename_images) as f:
        df_so = f.readlines()
        df_so = [x.strip() for x in df_so] 
    df_this_trial = df[df['screen']==screen_heatmap]
    for trial in range(1,total_trials+1):
        print(trial)
        df_this_trial = df[df['trial']==trial]
        df_this_trial = df_this_trial[df_this_trial['screen']==screen_heatmap]
        filpath_image_this_trial = df_so[trial-1]
        
        for user in sorted(['user1','user2','user3','user4','user5']):
            print(user)
            df_this_users = df_this_trial[df_this_trial['user']==user]
            if len(df_this_users)>0:
                
                filepath =df_this_users[df_this_users['type']=='filepath']['value'].values
                assert(len(filepath)==1)
                filepath = filepath[0]
                print('oi1')
                print(filpath_image_this_trial)
                print(filepath)
                assert(filpath_image_this_trial==filepath)
                # image_size_x = int(float(df_this_users[df_this_users['type']=='image_size_x']['value'].values[0]))
                # image_size_y = int(float(df_this_users[df_this_users['type']=='image_size_y']['value'].values[0]))
                # this_img = create_heatmap(df_this_users[df_this_users['type']=='fixation'],image_size_x, image_size_y)
                # 
                # im = Image.fromarray(this_img*255/np.max(this_img)).convert('RGB')
                # im.save(folder_name+'/'+str(trial)  + '_'  + user + '_' + "heatmap.png")

if __name__ == '__main__':
    create_heatmaps('./summary_edf_phase_2.csv', './anonymized_collected_data/phase_2/image_paths_preexperiment_4.txt',60, folder_name='heatmaps_gaussian_phase_2_0.98')
    create_heatmaps('./summary_edf_phase_1.csv', './anonymized_collected_data/phase_1/image_paths_preexperiment_3.txt',60, folder_name='heatmaps_phase_1_0.98')