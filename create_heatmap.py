from skimage.draw import ellipse
from PIL import Image
import pandas as pd
import numpy as np
from pydicom import dcmread
import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.stats import multivariate_normal
import torchxrayvision as xrv

length_embedding = 128

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

#save colored difference map over original image
def plot_diff_overlay(x, diff):
    s1, s2 = x.shape
    plt.style.use('./plotstule.mplstyle')
    plt.close('all')
    fig = plt.figure(figsize=(s2/100, s1/100), dpi=100)
    fig.tight_layout(pad=0)
    fig.add_subplot(111)
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
        hspace = 0, wspace = 0)
    plt.margins(0,0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    fig.canvas.draw()
    plt.gca().invert_yaxis()
    plt.axis('off')
    
    plt.imshow(x, cmap='gray')
    
    # alphas = (diff>0)*0.2
    alphas = (diff>-1)*0.2
    
    
    #sets the color to be green and pink for negative and positive values, respectively
    cmap = plt.get_cmap('Blues')
    rgba_img = cmap(diff*0.7+(1-0.7))
    
    rgba_img[:,:,3] = alphas
    plt.imshow(rgba_img)

def save_plt(filepath):
    plt.savefig(filepath, bbox_inches = 'tight', pad_inches = 0)

def create_heatmap(sequence_table, size_x, size_y, weights = None, type='gaussian'):
    img = np.zeros((size_y, size_x), dtype=np.float32)
    if weights is None:
        weights_fn = lambda index,row: row['time_linux']-row['time_start_linux']
    else:
        weights_fn = lambda index,row: weights[index]
    for index, row in sequence_table.reset_index().iterrows():
        # angle_circle = 2.5
        angle_circle = 0.98 #1.9 #0.98
        shown_rects_image_space = [round(row['source_rect_dimension_1']) ,round(row['source_rect_dimension_2']),round(row['source_rect_dimension_3']),round(row['source_rect_dimension_4'])]
        
        if type == 'gaussian':
            gaussian = get_gaussian(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle, size_y,size_x, shown_rects_image_space)
            img += gaussian*weights_fn(index,row)
        elif type == 'circle':
            rr, cc = ellipse(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle)
            len_rr_before_invalid = len(rr)
            invalid_indexs  = np.logical_or(np.logical_or(rr<shown_rects_image_space[1], cc<shown_rects_image_space[0]), np.logical_or(rr>=shown_rects_image_space[3], cc>=shown_rects_image_space[2]))
            rr = rr[~invalid_indexs]
            cc = cc[~invalid_indexs]
            if len(rr)>0:
                img[rr, cc] += 1/len_rr_before_invalid*weights_fn(index,row)
    return img/np.max(img)

def create_embedding(sequence_table, img, start_audio):
    size_y, size_x = img.shape
    all_fixations = []
    all_timestamps = []
    for index, row in sequence_table.iterrows():
        angle_circle = 0.98
        shown_rects_image_space = [row['source_rect_dimension_1'] ,row['source_rect_dimension_2'],row['source_rect_dimension_3'],row['source_rect_dimension_4']]
        rr, cc = ellipse(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle)
        len_rr_before_invalid = len(rr)
        invalid_indexs  = np.logical_or(np.logical_or(rr<shown_rects_image_space[1], cc<shown_rects_image_space[0]), np.logical_or(rr>=shown_rects_image_space[3], cc>=shown_rects_image_space[2]))
        rr = rr[~invalid_indexs]
        cc = cc[~invalid_indexs]
        if len(rr)>0:
            all_fixations.append(img[rr, cc][np.random.randint(len(rr), size=[length_embedding])])
            all_timestamps.append([(row['time_start_linux']-start_audio)*24*60*60,(row['time_linux']-start_audio)*24*60*60])
    print(np.array(all_fixations).shape)
    print(np.array(all_timestamps).shape)
    return np.array(all_fixations),np.array(all_timestamps)

from pydicom import dcmread
def create_heatmaps(filename_edf, filename_images, total_trials, screen_heatmap=2, results_filename=None, folder_name='./heatmaps'):
    df = pd.read_csv(filename_edf)

    if screen_heatmap==9 and results_filename is not None:
        chestbox_df = pd.read_csv(results_filename)
        chestbox_df = chestbox_df[list(map(lambda x: x.startswith('ChestBox (Rectangle) coord'), chestbox_df['title']))]
    
    with open(filename_images) as f:
        df_so = f.readlines()
        df_so = [x.strip() for x in df_so] 
    df_this_trial = df[df['screen']==screen_heatmap]
    for trial in range(1,total_trials+1):
        print(trial)
        df_this_trial = df[df['trial']==trial]
        df_this_trial = df_this_trial[df_this_trial['screen']==screen_heatmap]
        filpath_image_this_trial = df_so[trial-1]
        image = open_dicom(filpath_image_this_trial)
        for user in sorted(['user1','user2','user3','user4','user5']):
            print(user)
            df_this_users = df_this_trial[df_this_trial['user']==user]
            if len(df_this_users)>0:
                image_size_x = int(float(df_this_users[df_this_users['type']=='image_size_x']['value'].values[0]))
                image_size_y = int(float(df_this_users[df_this_users['type']=='image_size_y']['value'].values[0]))
                this_img = create_heatmap(df_this_users[df_this_users['type']=='fixation'],image_size_x, image_size_y)
                
                # plot_diff_overlay(image, this_img)
                # 
                # if screen_heatmap==9 and results_filename is not None:
                #     chestbox_df_this_trial = chestbox_df[chestbox_df['trial']==str(trial)]
                #     chestbox_df_this_trial = chestbox_df_this_trial[chestbox_df_this_trial['user']==user]
                #     if len(chestbox_df_this_trial)>0:
                #         assert(len(chestbox_df_this_trial)==4)
                #         x1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 0']['value'].values[0])
                #         y1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 1']['value'].values[0])
                #         x2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 2']['value'].values[0])
                #         y2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 3']['value'].values[0])
                #         rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='r', facecolor='none')
                #         ax = plt.gca()
                #         ax.add_patch(rect)
                #         plt.show()
                # save_plt(folder_name+'/'+str(trial)  + '_'  + user + '_' + "heatmap.png")
            im = Image.fromarray(this_img*255).convert('RGB')
            im.save(folder_name+'/'+str(trial)  + '_'  + user + '_' + "heatmap.png")

def find_nearest(a, n):
    return np.minimun(np.abs(a.astype(float)-n.astype(float)))[0]

def apply_windowing(x,level,width):
    return np.minimum(np.maximum(((x.astype(float)-level)/width+0.5),0),1);

def open_dicom(filpath_image_this_trial):
    with dcmread('datasets/mimic/'+filpath_image_this_trial) as header:
        max_possible_value = (2**float(header.BitsStored)-1)
        x = header.pixel_array
        x = x.astype(float)/max_possible_value
        if 'WindowWidth' in header:
            if hasattr(header.WindowWidth, '__getitem__'):
                wwidth = header.WindowWidth[0]
            else:
                wwidth = header.WindowWidth
            if hasattr(header.WindowCenter, '__getitem__'):
                wcenter = header.WindowCenter[0]
            else:
                wcenter = header.WindowCenter
            windowing_width = wwidth/max_possible_value
            windowing_level = wcenter/max_possible_value
            if header.PhotometricInterpretation=='MONOCHROME1' or not ('PixelIntensityRelationshipSign' in header) or header.PixelIntensityRelationshipSign==1:
                x = 1-x
                windowing_level = 1 - windowing_level
        else:
             if 'VOILUTSequence' in header:
                lut_center = float(header.VOILUTSequence.Item_1.LUTDescriptor)/2
                window_center = find_nearest(header.VOILUTSequence.Item_1.LUTData, lut_center)
                deltas = []
                for i in range(10,31):
                    deltas.append((float(header.VOILUTSequence.Item_1.LUTData[window_center+i]) - float(header.VOILUTSequence.Item_1.LUTData[window_center-i]))/2/i)
                window_width = lut_center/sum(deltas)*2*len(deltas)
                windowing_width = window_width/max_possible_value
                windowing_level = (window_center-1)/max_possible_value
                if windowing_width < 0:
                    windowing_width = -windowing_width
                    x = 1-x
                    windowing_level = 1 - windowing_level
             else:
                windowing_width = 1
                windowing_level = 0.5;
                if header.PhotometricInterpretation=='MONOCHROME1' or not ('PixelIntensityRelationshipSign' in header) or header.PixelIntensityRelationshipSign==1:
                    x = 1-x
                    windowing_level = 1 - windowing_level
        return apply_windowing(x, windowing_level, windowing_width)

def create_embeddings(filename_edf, filename_images, emb_filename, all_trials):
    h5_index = 0
    list_of_users = sorted(['user1','user2','user3','user4','user5'])
    with h5py.File(emb_filename, "w") as h5_f:
        df = pd.read_csv(filename_edf)
        with open(filename_images) as f:
            df_so = f.readlines()
            df_so = [x.strip() for x in df_so] 
        df = df[df['screen']==2]
        for user in list_of_users:
            print(user)
            df_this_user = df[df['user']==user]
            for trial in all_trials[user]:
                print(trial)
                df_this_trial_this_user = df_this_user[df_this_user['trial']==trial]
                filpath_image_this_trial = df_so[trial-1]
                image = open_dicom(filpath_image_this_trial)
                start_audio = float(df_this_trial_this_user[df_this_trial_this_user['type']=='start_audio_recording']['value'].values[0])
                fixations, timestamp = create_embedding(df_this_trial_this_user[df_this_trial_this_user['type']=='fixation'],image, start_audio)
                h5_f.create_dataset('embedding_'+f'{h5_index:06}', data=fixations)
                h5_f.create_dataset('timestamp_start_'+f'{h5_index:06}', data=timestamp[:,0])
                h5_f.create_dataset('timestamp_end_'+f'{h5_index:06}', data=timestamp[:,1])
                h5_f.create_dataset('user_'+f'{h5_index:06}', data=np.array([list_of_users.index(user)]))
                h5_f.create_dataset('trial_n_'+f'{h5_index:06}', data=np.array([trial]))
                h5_index += 1

def get_embeddings_phase_2():
    all_trials = {}
    all_trials['user1'] = [x for x in range(1,51) if x not in {6,40,47,48}]
    all_trials['user2'] = [x for x in range(1,51) if x not in {4,14,15}]
    all_trials['user3'] = [x for x in range(1,51) if x not in {1,46}]
    all_trials['user4'] = [x for x in range(1,51) if x not in {}]
    all_trials['user5'] = [x for x in range(1,51) if x not in {1}]
    
    create_embeddings('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',"embeddings_phase_2.hdf5", all_trials)

def get_embeddings_phase_1():
    all_trials = {}
    all_trials['user1'] = [x for x in range(2,61) if x not in {1,6,7,8,41}]
    all_trials['user2'] = [x for x in range(2,61) if x not in {15,27,32}]
    all_trials['user3'] = [x for x in range(2,61) if x not in {14,44}]
    all_trials['user4'] = [x for x in range(2,61) if x not in {7}]
    all_trials['user5'] = [x for x in range(2,61) if x not in {}]
    
    
    create_embeddings('./summary_edf_phase_1.csv', './anonymous_collected_data/image_paths_preexperiment_3.txt',"embeddings_phase_1.hdf5", all_trials)
    
if __name__ == '__main__':
    # create_heatmaps('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',60, 9, './results_phase_2.csv',folder_name='heatmaps_phase_2_0.98')
    # create_heatmaps('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',60, folder_name='heatmaps_gaussian_phase_2_0.98')
    # create_heatmaps('./summary_edf_phase_1.csv', './anonymous_collected_data/phase_1/image_paths_preexperiment_3.txt',60, folder_name='heatmaps_phase_1_0.98')
    
    get_embeddings_phase_1()
    get_embeddings_phase_2()
    # create_embeddings('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',"embeddings_phase_2.hdf5", 50)