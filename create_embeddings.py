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
import torch
import sklearn, sklearn.metrics
import torchvision
import skimage.transform
import math
import os

length_embedding = 128

os.environ['CUDA_VISIBLE_DEVICES'] = '1'

class XRayResizerAR(object):
    def __init__(self, size, fn):
        self.size = size
        self.fn = fn
    
    def __call__(self, img):
        old_size = img.shape[1:]
        ratio = float(self.size)/self.fn(old_size)
        new_size = tuple([round(x*ratio) for x in old_size])
        return skimage.transform.resize(img, (1, new_size[0], new_size[1]), mode='constant', preserve_range=True).astype(np.float32)

def get_32_size(shape):
    projected_max_size = 224/min(np.array(shape))*max(np.array(shape))
    return round(projected_max_size/32)*32

class XRayResizerPadRound32(object):
    def __init__(self, size, fn):
        self.size = size
    
    def __call__(self, img):
        self.resizer = XRayResizerAR(get_32_size(img.shape[1:]), max)
        img = self.resizer(img)
        pad_width = (-np.array(img.shape[1:])+max(np.array(img.shape[1:])))/2
        #print(pad_width)
        return np.pad(img, ((0,0),(math.floor(pad_width[0]),math.ceil(pad_width[0])),(math.floor(pad_width[1]),math.ceil(pad_width[1]))))

def get_img_size(dicom_id, d_mimic_chex_original, preprocess=''):    
    
    iloc_index = np.argwhere((d_mimic_chex_original.csv['dicom_id']==dicom_id).values).flatten()[-1]
    assert(d_mimic_chex_original.csv.iloc[iloc_index]['dicom_id']==dicom_id)
    return d_mimic_chex_original[iloc_index]["img"].shape[1:]

transforms = torchvision.transforms.Compose([XRayResizerPadRound32(224, min)])

def get_model_embeddings(dicom_id, preprocess=''):

    d_mimic_chex = xrv.datasets.MIMIC_Dataset(#datadir="/lustre03/project/6008064/jpcohen/MIMICCXR-2.0/files",
          imgpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-jpg/mimic-cxr-jpg-2.0.0.physionet.org/files",
          csvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-chexpert.csv",
          metacsvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-metadata.csv",
          views=["PA","AP"], transform= transforms, unique_patients=False)
    d_mimic_chex_original = xrv.datasets.MIMIC_Dataset(#datadir="/lustre03/project/6008064/jpcohen/MIMICCXR-2.0/files",
          imgpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-jpg/mimic-cxr-jpg-2.0.0.physionet.org/files",
          csvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-chexpert.csv",
          metacsvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-metadata.csv",
          views=["PA","AP"], unique_patients=False)
    model = xrv.models.DenseNet(weights="all").cuda()
    xrv.datasets.relabel_dataset(model.pathologies, d_mimic_chex)
    
    # outs = []
    # labs = []
    # with torch.no_grad():
        # loader = torch.utils.data.DataLoader(d_mimic_chex,
                                           # batch_size=1,
                                           # shuffle=False,
                                           # num_workers=0, pin_memory=True)
        # for i in np.random.RandomState(0).randint(0,len(d_mimic_chex), 1000): #,sample in enumerate(loader):
            # print(i)
            # sample = d_mimic_chex[i]
            # labs.append(np.nan_to_num(sample["lab"]))
            # out = model(torch.from_numpy(sample["img"]).cuda().unsqueeze(0)).cpu()
            # outs.append(out.detach().numpy()[0])
    
    # for i in range(14):
        # if len(np.unique(np.asarray(labs)[:,i])) > 1:
            # auc = sklearn.metrics.roc_auc_score(np.asarray(labs)[:,i], np.asarray(outs)[:,i])
        # else:
            # auc = "(Only one class observed)"
        # print(xrv.datasets.default_pathologies[i], auc)
    
    iloc_index = np.argwhere((d_mimic_chex.csv['dicom_id']==dicom_id).values).flatten()[-1]

    assert(d_mimic_chex.csv.iloc[iloc_index]['dicom_id']==dicom_id)
    assert(d_mimic_chex_original.csv.iloc[iloc_index]['dicom_id']==dicom_id)
    sample = d_mimic_chex[iloc_index]
    # sample = d_mimic_chex[0]
    #print(sample["img"].shape)
    out = model.features(torch.from_numpy(sample["img"]).cuda().unsqueeze(0)).cpu()
    #print(out.size())
    return out.squeeze(0).detach().numpy(),d_mimic_chex_original[iloc_index]["img"].shape[1:]

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

def create_embedding(sequence_table, dicom_id):
    embedding, img_shape = get_model_embeddings(dicom_id)
    size_y, size_x = img_shape
    all_fixations = []
    all_timestamps = []
    all_probabilities = []
    for index, row in sequence_table.iterrows():
        angle_circle = 1
        shown_rects_image_space = [round(row['xmin_shown_from_image']) ,round(row['ymin_shown_from_image']),round(row['xmax_shown_from_image']),round(row['ymax_shown_from_image'])]
        
        shown_rects_screen_space = [round(row['xmin_in_screen_coordinates']) ,round(row['ymin_in_screen_coordinates']),round(row['xmax_in_screen_coordinates']),round(row['ymax_in_screen_coordinates'])]
        #buttons_rectangle = np.array([10,1038,650, 1122]) 933, 1017
        buttons_rectangle = np.array([0,923,660, 1132])

        image_pixels_per_screen_pixel_x = (shown_rects_image_space[2]-shown_rects_image_space[0])/(shown_rects_screen_space[2]-shown_rects_screen_space[0])
        image_pixels_per_screen_pixel_y = (shown_rects_image_space[3]-shown_rects_image_space[1])/(shown_rects_screen_space[3]-shown_rects_screen_space[1])

        x_screen, y_screen = convert_image_to_screen_coordinates(row['average_x_position'], row['average_y_position'], shown_rects_screen_space, shown_rects_image_space)
        distance_to_image = distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space)
        distance_to_buttons = distance_point_rectangle([x_screen, y_screen],buttons_rectangle)
        distance_to_image_angle = distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space, image_pixels_per_screen_pixel_x/row['angular_resolution_x_pixels_per_degree'], image_pixels_per_screen_pixel_y/row['angular_resolution_y_pixels_per_degree'])
        if distance_to_image==0 or (distance_to_buttons>50 and distance_to_image_angle<0.5):
        
            gaussian = get_gaussian(row['average_y_position'],row['average_x_position'], row['angular_resolution_y_pixels_per_degree']*angle_circle, row['angular_resolution_x_pixels_per_degree']*angle_circle, size_y
            ,size_x, shown_rects_image_space)
            gaussian_old_shape = gaussian.shape
            p_fixation = np.sum(gaussian)
            gaussian = transforms(gaussian[None,...])
            gaussian = gaussian*(max(gaussian_old_shape[0],gaussian_old_shape[1])/get_32_size(gaussian_old_shape))**2
            gaussian = torch.nn.functional.avg_pool2d(torch.tensor(gaussian).unsqueeze(0), 32).numpy()[0,0,...]*32*32
            
            all_fixations.append(weight_embedding(embedding, gaussian))
            all_timestamps.append([row['timestamp_start_fixation'],row['timestamp_end_fixation']])
            all_probabilities.append(p_fixation)
    return np.array(all_fixations),np.array(all_timestamps), np.array(all_probabilities)

def convert_screen_to_image_coordinates(x, y, dest_rect, source_rect):
    return interpolate_2d(dest_rect, source_rect, x,y);

def convert_image_to_screen_coordinates(x, y, dest_rect, source_rect):
    return interpolate_2d(source_rect,dest_rect,x,y);

def interpolate_2d(source_rect, dest_rect, x,y):
    x_scale = (dest_rect[2]-dest_rect[0])/(source_rect[2]-source_rect[0]);
    y_scale = (dest_rect[3]-dest_rect[1])/(source_rect[3]-source_rect[1]);
    return_x = x_scale*(x-source_rect[0])+dest_rect[0];
    return_y = y_scale*(y-source_rect[1])+dest_rect[1];
    return return_x,return_y

def check_inside_rect(p, rect):
    return p[0]>=rect[0] and p[0]<=rect[2] and p[1]>=rect[1] and p[1]<=rect[3]

def distance_point_rectangle(p, rect,multiplier_x = 1, multiplier_y = 1):
    if check_inside_rect(p, rect):
        return 0
    return  nearest_distance(rect, p,multiplier_x, multiplier_y)

def nearest_distance(rectangle, point,multiplier_x = 1, multiplier_y = 1):
    if point[0]>=rectangle[0] and point[0]<=rectangle[2]:
        d_top = abs(rectangle[1] - point[1])*multiplier_y
        d_bottom = abs(rectangle[3] - point[1])*multiplier_y
    else:
        d_top =float('inf')
        d_bottom=float('inf')
    corner_y = rectangle[1] if d_top < d_bottom else rectangle[3]
    if point[1]>=rectangle[1] and point[1]<=rectangle[3]:
        d_left = abs(rectangle[0] - point[0])*multiplier_x
        d_right = abs(rectangle[2] - point[0])*multiplier_x
    else:
        d_left = float('inf')
        d_right = float('inf')
    corner_x = rectangle[0] if d_left < d_right else rectangle[2]
    d_cx = corner_x - point[0]
    d_cy = corner_y - point[1]
    d_corner = ((d_cx*multiplier_x)**2 + (d_cy*multiplier_x)**2)**0.5
    return min(d_top, d_bottom, d_left, d_right, d_corner)

def create_embeddings(path_dataset,filename_edf, emb_filename):
    h5_index = 0
    with h5py.File(emb_filename, "w") as h5_f:
        df = pd.read_csv(f'{path_dataset}/{filename_edf}')
        df = df[df['eye_tracking_data_discarded']==False]
        all_images = df['image'].unique()
        for trial, image_name in enumerate(sorted(all_images)):
            df_this_trial = df[df['image']==image_name]
            for _, row in df_this_trial.iterrows():
                id = row['id']
                fixations_df = pd.read_csv(f'{path_dataset}/{id}/fixations.csv')
                print(trial)
                filpath_image_this_trial = row['image']
                dicom_id = filpath_image_this_trial.split('/')[-1].split('.')[0]
                fixations, timestamp, probability = create_embedding(fixations_df,dicom_id)
                h5_f.create_dataset('embedding_'+f'{h5_index:06}', data=fixations)
                h5_f.create_dataset('probability_'+f'{h5_index:06}', data=probability)
                h5_f.create_dataset('timestamp_start_'+f'{h5_index:06}', data=timestamp[:,0])
                h5_f.create_dataset('timestamp_end_'+f'{h5_index:06}', data=timestamp[:,1])
                h5_f.create_dataset('trial_n_'+f'{h5_index:06}', data=np.array([trial]))
                h5_index += 1

def get_embeddings_phase_2():
    create_embeddings('./dataset/','metadata_phase_2.csv',"embeddings_phase_2_v3.hdf5")

def get_embeddings_phase_1():
    create_embeddings('./dataset/','metadata_phase_1.csv',"embeddings_phase_1_v3.hdf5")

def weight_embedding(embedding, weights):
    sum_weigths = np.sum(weights[None,...])
    this_embedding = np.sum(np.sum(embedding*weights[None,...]/sum_weigths, axis = 2), axis=1)
    return this_embedding

import argparse
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--preprocess', type=str, nargs='?',
                        help='')
    args = parser.parse_args()
    
    get_embeddings_phase_1()
    get_embeddings_phase_2()