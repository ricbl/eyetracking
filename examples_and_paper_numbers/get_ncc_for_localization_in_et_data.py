# generates the table with values used in the calculation of NCC values reported in the Technical Validation > Eye-tracking data section
# generates_heatmap should be run before this script
# example of: 
# - how to normalize the location of heatmaps using the chest bounding box
# - how to compare a heatmap against abnormality ellipses.

import pandas as pd
import numpy as np
import cv2
import glob
from PIL import Image
import os.path
import math
from skimage.draw import ellipse
import os
from dataset_locations import reflacx_dataset_location

def get_ellipses_image(list_rect, im_size):
    img_mask = np.zeros(im_size, np.uint8)
    for rect in list_rect:
        rr, cc = ellipse((rect[0]+rect[2])/2, (rect[1]+rect[3])/2, abs(rect[0]-rect[2])/2, abs(rect[1]-rect[3])/2,imsize)
        img_mask[rr, cc] = 1
    return np.transpose(img_mask)

eyetracking_dataset_path = f'{reflacx_dataset_location}/main_data/'

def normalised_corr(a,v): 
    return np.mean((a-np.mean(a))*(v-np.mean(v)))/np.std(v)/np.std(a)

#open results file and get all bounding boxes and image sizes
tables_boxes = pd.DataFrame()
for phase in [1,2]:
    metadata_file = pd.read_csv(f'{eyetracking_dataset_path}/metadata_phase_{phase}.csv').sort_values(['image'])
    metadata_file = metadata_file[metadata_file['eye_tracking_data_discarded']==False]
    all_images = metadata_file['image'].unique()
    for index, image_filepath in enumerate(all_images):
        rows_this_image = metadata_file[metadata_file['image']==image_filepath]
        for _, row in rows_this_image.iterrows():
            chest_box_table = pd.read_csv(f'{eyetracking_dataset_path}/{row["id"]}/chest_bounding_box.csv')
            chest_box_table['xmin'].values[0]
            tables_boxes = tables_boxes.append({'trial':index, 'image_size_x': row['image_size_x'],'image_size_y': row['image_size_y'],'phase': phase, 'ChestBox (Rectangle) coord 0': chest_box_table['xmin'].values[0], 'ChestBox (Rectangle) coord 1': chest_box_table['ymin'].values[0], 'ChestBox (Rectangle) coord 2': chest_box_table['xmax'].values[0], 'ChestBox (Rectangle) coord 3': chest_box_table['ymax'].values[0] }, ignore_index=True)
            
assert(len(tables_boxes)==525)

tables_boxes = tables_boxes.groupby(['trial', 'phase']).agg({'image_size_y':['mean'], 'image_size_x':['mean'],
     'ChestBox (Rectangle) coord 0':['mean'], 'ChestBox (Rectangle) coord 1':['mean'],
       'ChestBox (Rectangle) coord 2':['mean'], 'ChestBox (Rectangle) coord 3':['mean'],})

tables_boxes.columns = ['image_size_y', 'image_size_x',
       'ChestBox (Rectangle) coord 0', 'ChestBox (Rectangle) coord 1',
       'ChestBox (Rectangle) coord 2', 'ChestBox (Rectangle) coord 3',]
for coord in range(4):
    tables_boxes[f'ChestBox (Rectangle) coord {coord}'] = tables_boxes[f'ChestBox (Rectangle) coord {coord}'].round(0).astype(int)
assert(len(tables_boxes)==59+50)
tables_boxes = tables_boxes.reset_index()

#get average bounding box coordinate for all bounding boxes
averages_boxes = []
for coord in range(4):
    averages_boxes.append(int(round(np.mean(tables_boxes[f'ChestBox (Rectangle) coord {coord}'].values))))

average_size_box_x = averages_boxes[2] - averages_boxes[0]
average_size_box_y = averages_boxes[3] - averages_boxes[1]

average_image_size_x = int(round(np.mean(tables_boxes['image_size_x'].values)))
average_image_size_y = int(round(np.mean(tables_boxes['image_size_y'].values)))
average_margin_0 = averages_boxes[0]
average_margin_1 = averages_boxes[1]

max_margins = np.array([0]*4)

def save_normalized_image(att2_np, filepath):
    im = Image.fromarray((att2_np-np.min(att2_np))/(np.max(att2_np)-np.min(att2_np))*255).convert('RGB')
    im.save(filepath)

#check image size needed around the average box in worst case, iterating through all images
for _,row in tables_boxes.iterrows():
    #check transform needed for this bounding box to get to the average box size, and check the corresponding image size
    size_box_x = row['ChestBox (Rectangle) coord 2'] - row['ChestBox (Rectangle) coord 0']
    size_box_y = row['ChestBox (Rectangle) coord 3'] - row['ChestBox (Rectangle) coord 1']
    x_multiplier = average_size_box_x/size_box_x
    y_multiplier = average_size_box_y/size_box_y
    margins = []
    margins.append(int(round(row['ChestBox (Rectangle) coord 0']*x_multiplier)))
    margins.append(int(round(row['ChestBox (Rectangle) coord 1']*y_multiplier)))
    margins.append(int(round((row['image_size_x']-row['ChestBox (Rectangle) coord 2'])*x_multiplier)))
    margins.append(int(round((row['image_size_y']-row['ChestBox (Rectangle) coord 3'])*y_multiplier)))
    
    #check margins in each of the sides around the bounding box
    #if larger than the previous maximum, override previous maximum
    max_margins = np.maximum(np.array(margins), max_margins)

#create image for accumulation including margin sizes and box size
final_shape_average = [max_margins[3]+max_margins[1]+average_size_box_y,max_margins[2]+max_margins[0]+average_size_box_x]
aggregated_heatmaps = np.zeros(final_shape_average).astype(np.float64)
total_counts_views = np.zeros(final_shape_average).astype(np.float64)

# get list of all eye-tracking heatmaps
def sorter(item):
    return f'{int(item.split("/")[-1].split("_")[0]):04}' + item.split("/")[-1].split("_")[1]
list_et = sorted(glob.glob( './heatmaps_phase_1/*npy'),key=sorter)+ sorted(glob.glob('./heatmaps_phase_2/*npy'),key=sorter)
print(len(list_et))
assert(len(list_et)==525)
import pathlib
folder_name = f'./heatmaps_subtraction_1_1'
pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True) 
folder_name = f'./heatmaps_subtraction_2_1'
pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True) 

#accumulate all the heatmaps in a single average space
for et_path in list_et:
    #get the user, trial and phase
    this_trial = float(et_path.split('/')[-1].split('_')[0])
    this_phase = float(et_path.split('/')[-2].split('_')[2])
    loaded_pickle = np.load(et_path, allow_pickle=True).item()
    et_heatmap = loaded_pickle['np_image']
    #filter the bounding box table to get this case only
    this_row = tables_boxes[(tables_boxes['trial']==this_trial) & (tables_boxes['phase']==this_phase)]
    assert(len(this_row)==1)
    
    #transform the heatmap to the average bounding box size
    size_box_x = this_row['ChestBox (Rectangle) coord 2'].values[0] - this_row['ChestBox (Rectangle) coord 0'].values[0]
    size_box_y = this_row['ChestBox (Rectangle) coord 3'].values[0] - this_row['ChestBox (Rectangle) coord 1'].values[0]
    x_multiplier = average_size_box_x/size_box_x
    y_multiplier = average_size_box_y/size_box_y
    destination_shape = (int(round(this_row['image_size_x'].values[0]*x_multiplier)), int(round(this_row['image_size_y'].values[0]*y_multiplier)))
    resized_heatmap = cv2.resize(et_heatmap, dsize = destination_shape, interpolation=cv2.INTER_LINEAR)
    assert((destination_shape[1], destination_shape[0])==resized_heatmap.shape)
    resized_heatmap = resized_heatmap/np.sum(resized_heatmap)
    
    #adjust coordinates to include max margins
    start_x = int(round(max_margins[0]-this_row['ChestBox (Rectangle) coord 0'].values[0]*x_multiplier))
    end_x = start_x + int(round(this_row['image_size_x'].values[0]*x_multiplier))
    start_y = int(round(max_margins[1]-this_row['ChestBox (Rectangle) coord 1'].values[0]*y_multiplier))
    end_y = start_y + int(round(this_row['image_size_y'].values[0]*y_multiplier))
    assert(end_y<=final_shape_average[0])
    assert(end_x<=final_shape_average[1])
    
    this_rectangle = np.zeros(final_shape_average).astype(np.float64)
    this_rectangle[start_y:end_y,start_x:end_x] += 1.
    # save_normalized_image(np.nan_to_num(this_rectangle), f'./heatmaps_subtraction_{int(this_phase)}_1' + f'/rectangle_{this_trial}.png')
    
    #sum to accumulated image
    aggregated_heatmaps[start_y:end_y,start_x:end_x] += resized_heatmap
    total_counts_views[start_y:end_y,start_x:end_x] += 1.
    
#get average heatmap
average_heatmap = aggregated_heatmaps/total_counts_views

import pathlib
folder_name = f'./heatmaps_subtraction_1_1'
pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True) 
save_normalized_image(np.nan_to_num(average_heatmap), folder_name + '/map.png')
assert(abs(max_margins[1]-average_margin_1+average_image_size_y - (final_shape_average[0]-max_margins[3]+(average_image_size_y-averages_boxes[3])))<1)
assert(abs(max_margins[0]-average_margin_0+average_image_size_x - (final_shape_average[1]-max_margins[2]+(average_image_size_x-averages_boxes[2])))<1)
save_normalized_image(np.nan_to_num(average_heatmap[round(max_margins[1]-average_margin_1):round(average_image_size_y+max_margins[1]-average_margin_1), round(max_margins[0]-average_margin_0):round(average_image_size_x+max_margins[0]-average_margin_0)]), folder_name + '/map_small.png')
save_normalized_image(np.nan_to_num(total_counts_views), folder_name + '/count.png')

folder_name = f'./heatmaps_subtraction_2_1'
pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True) 
save_normalized_image(np.nan_to_num(average_heatmap), folder_name + '/map.png')
save_normalized_image(np.nan_to_num(average_heatmap[round(max_margins[1]-average_margin_1):round(average_image_size_y+max_margins[1]-average_margin_1), round(max_margins[0]-average_margin_0):round(average_image_size_x+max_margins[0]-average_margin_0)]), folder_name + '/map_small.png')
save_normalized_image(np.nan_to_num(total_counts_views), folder_name + '/count.png')


# do all heatmap comparisons
base = []
this_et = []
base_table = []
this_et_table = []
for et_path in list_et:
    print(et_path)
    
    #get the user, trial and phase
    this_trial = int(et_path.split('/')[-1].split('_')[0])
    this_phase = int(et_path.split('/')[-2].split('_')[2])
    
    metadata_table = pd.read_csv(f'{reflacx_dataset_location}/main_data/metadata_phase_{this_phase}.csv')
    metadata_table = metadata_table[metadata_table['eye_tracking_data_discarded']==False]
    first_trial = int(metadata_table['id'].values[0][2:4])
    
    folder_name = f'./heatmaps_subtraction_{this_phase}_1'
    
    if os.path.isfile(folder_name + '/' + str(this_trial) + '.npy'):
        continue
    
    #filter the bounding box table to get this case only
    this_row = tables_boxes[(tables_boxes['trial']==this_trial) & (tables_boxes['phase']==this_phase)]
    assert(len(this_row)==1)
    
    #find coordinates of common space that correspond to the limits of the current image
    size_box_x = this_row['ChestBox (Rectangle) coord 2'].values[0] - this_row['ChestBox (Rectangle) coord 0'].values[0]
    size_box_y = this_row['ChestBox (Rectangle) coord 3'].values[0] - this_row['ChestBox (Rectangle) coord 1'].values[0]
    x_multiplier = average_size_box_x/size_box_x
    y_multiplier = average_size_box_y/size_box_y
    start_x = int(round(max_margins[0]-this_row['ChestBox (Rectangle) coord 0'].values[0]*x_multiplier))
    end_x = start_x + int(round(this_row['image_size_x'].values[0]*x_multiplier))
    start_y = int(round(max_margins[1]-this_row['ChestBox (Rectangle) coord 1'].values[0]*y_multiplier))
    end_y = start_y + int(round(this_row['image_size_y'].values[0]*y_multiplier))
    assert(end_y<=final_shape_average[0])
    assert(end_x<=final_shape_average[1])
    
    #crop the average heatmap to correspond to the field-of-view of the current image nad resize it to the same size as the image
    cropped_average = average_heatmap[start_y:end_y,start_x:end_x]
    destination_shape = (int(round(this_row['image_size_x'].values[0])), int(round(this_row['image_size_y'].values[0])))
    localized_heatmap = cv2.resize(cropped_average, dsize = destination_shape, interpolation=cv2.INTER_LINEAR)
    save_normalized_image(np.nan_to_num(localized_heatmap), f'./heatmaps_subtraction_{int(this_phase)}_1' + f'/localized_heatmap_{this_trial}.png')
    assert(localized_heatmap.shape==(this_row['image_size_y'].values[0],this_row['image_size_x'].values[0]))
    assert((localized_heatmap==localized_heatmap).all())
    assert(np.sum(localized_heatmap)>0)
    assert(not np.isnan(localized_heatmap).any())
    
    #loading the heatmap from the radiologists gaze
    index_user = int(et_path.split('/')[-1].split('_')[1].split('.')[0])
    loaded_pickle = np.load(et_path, allow_pickle=True).item()
    rows_this_trial = metadata_table[metadata_table['image']==loaded_pickle['img_path']]
    id = rows_this_trial['id'].values[index_user]
    print(id)
    assert(loaded_pickle['id']==id)
    imsize = [None, None]
    imsize[0] = rows_this_trial['image_size_x'].values[index_user]
    imsize[1] = rows_this_trial['image_size_y'].values[index_user]
    et_map = loaded_pickle['np_image']
    
    #comparing both of the heatmaps to the union of drawn ellipses
    ellipses_table= pd.read_csv(f'{reflacx_dataset_location}/main_data/{id}/anomaly_location_ellipses.csv')
    if len(ellipses_table)>0:
        ellipse_map = get_ellipses_image(ellipses_table[['xmin','ymin','xmax','ymax']].values, imsize)
        save_normalized_image(np.nan_to_num(et_map), f'./heatmaps_subtraction_{int(this_phase)}_1' + f'/et_heatmap_{this_trial}_{index_user}.png')
        save_normalized_image(np.nan_to_num(ellipse_map), f'./heatmaps_subtraction_{int(this_phase)}_1' + f'/ellipse_heatmap_{this_trial}_{index_user}.png')
        base.append(normalised_corr(localized_heatmap,ellipse_map))
        base_table.append({'value':base[-1],'trial':this_trial,'phase':this_phase,'title':'base'})
        this_et.append(normalised_corr(et_map,ellipse_map))
        this_et_table.append({'value':this_et[-1],'trial':this_trial,'phase':this_phase,'title':'this_et'})
        print(base[-1])
        print(this_et[-1])
pd.DataFrame(base_table).to_csv(f'ncc_baseline.csv')
pd.DataFrame(this_et_table).to_csv(f'ncc_et.csv')
