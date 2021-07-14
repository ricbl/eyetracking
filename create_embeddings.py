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
import skimage
import math

length_embedding = 128

class XRayResizerAR(object):
    def __init__(self, size, fn):
        self.size = size
        self.fn = fn
    
    def __call__(self, img):
        old_size = img.shape[1:]
        ratio = float(self.size)/self.fn(old_size)
        new_size = tuple([round(x*ratio) for x in old_size])
        return skimage.transform.resize(img, (1, new_size[0], new_size[1]), mode='constant', preserve_range=True).astype(np.float32)

class XRayResizerPad(object):
    def __init__(self, size, fn):
        self.resizer = XRayResizerAR(size, fn)
    
    def __call__(self, img):
        img = self.resizer(img)
        pad_width = (-np.array(img.shape[1:])+max(np.array(img.shape[1:])))/2
        #print(pad_width)
        return np.pad(img, ((0,0),(math.ceil(pad_width[0]),math.floor(pad_width[0])),(math.ceil(pad_width[1]),math.floor(pad_width[1]))))

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


def get_model_embeddings(dicom_id, preprocess=''):
    # if preprocess=='center':
        # transforms = torchvision.transforms.Compose([xrv.datasets.XRayCenterCrop(),xrv.datasets.XRayResizer(224)])
    # elif preprocess=='pad_max':
        # transforms = torchvision.transforms.Compose([XRayResizerPad(224, max)])
    # elif preprocess=='pad_min':
        # transforms = torchvision.transforms.Compose([XRayResizerPad(224, min)])
    # elif preprocess=='ar_max':
        # transforms = torchvision.transforms.Compose([XRayResizerAR(224, max)])
    # elif preprocess=='ar_min':
        # transforms = torchvision.transforms.Compose([XRayResizerAR(224, min)])
    transforms = torchvision.transforms.Compose([XRayResizerPadRound32(224, min)])
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
    # print(sample['lab'])
    # print(out.size())
    # # print(dir(model))
    # # print(model.classifier)
    # # print(list(model.modules()))
    # # print(list(model.named_buffers()))
    # 1/0

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
    #print(np.sum(to_return))
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

def create_heatmap(sequence_table, size_x, size_y):
    img = np.zeros((size_y, size_x), dtype=np.float32)
    for index, row in sequence_table.iterrows():
        # angle_circle = 2.5
        angle_circle = 0.98 #1.9 #0.98
        shown_rects_image_space = [round(row['source_rect_dimension_1']) ,round(row['source_rect_dimension_2']),round(row['source_rect_dimension_3']),round(row['source_rect_dimension_4'])]
        # shown_rects_image_space = [row['source_rect_dimension_1']) ,row['source_rect_dimension_2']),row['source_rect_dimension_3'],row['source_rect_dimension_4']]
        # print(shown_rects_image_space)
        gaussian = get_gaussian(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle, size_y,size_x, shown_rects_image_space)
        img += gaussian*(row['time_linux']-row['time_start_linux'])
        # print(np.min(gaussian[gaussian>0]))
        # rr, cc = ellipse(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle)
        # len_rr_before_invalid = len(rr)
        # invalid_indexs  = np.logical_or(np.logical_or(rr<shown_rects_image_space[1], cc<shown_rects_image_space[0]), np.logical_or(rr>=shown_rects_image_space[3], cc>=shown_rects_image_space[2]))
        # rr = rr[~invalid_indexs]
        # cc = cc[~invalid_indexs]
        # if len(rr)>0:
        #     img[rr, cc] += 1/len_rr_before_invalid*(row['time_linux']-row['time_start_linux'])
    return img/np.max(img)

def create_embedding(sequence_table, dicom_id, start_audio):
    embedding, img_shape = get_model_embeddings(dicom_id)
    size_y, size_x = img_shape
    all_fixations = []
    all_timestamps = []
    all_probabilities = []
    for index, row in sequence_table.iterrows():
        angle_circle = 0.98
        shown_rects_image_space = [round(row['source_rect_dimension_1']) ,round(row['source_rect_dimension_2']),round(row['source_rect_dimension_3']),round(row['source_rect_dimension_4'])]
        gaussian = get_gaussian(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle, size_y
        ,size_x, shown_rects_image_space)
        gaussian_old_shape = gaussian.shape
        p_fixation = np.sum(gaussian)
        gaussian = transforms(gaussian[None,...])
        gaussian = gaussian*(max(gaussian_old_shape[0],gaussian_old_shape[1])/get_32_size(gaussian_old_shape))**2
        gaussian = torch.nn.functional.avg_pool2d(torch.tensor(gaussian).unsqueeze(0), 32).numpy()[0,0,...]*32*32
        
        
        #print('oi1')
        all_fixations.append(weight_embedding(embedding, gaussian))
        # all_fixations.append(weight_embedding(torch.tensor(embedding).half().cuda(), gaussian))
        #print('oi2')
        all_timestamps.append([(row['time_start_linux']-start_audio)*24*60*60,(row['time_linux']-start_audio)*24*60*60])
        all_probabilities.append(p_fixation)
    #print(np.array(all_fixations).shape)
    #print(np.array(all_timestamps).shape)
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

def create_embedding(sequence_table, dicom_id, start_audio):
    d_mimic_chex_original = xrv.datasets.MIMIC_Dataset(#datadir="/lustre03/project/6008064/jpcohen/MIMICCXR-2.0/files",
          imgpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-jpg/mimic-cxr-jpg-2.0.0.physionet.org/files",
          csvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-chexpert.csv",
          metacsvpath="/usr/sci/scratch/ricbl/mimic-cxr/mimic-cxr-2.0.0-metadata.csv",
          views=["PA","AP"], unique_patients=False)
    img_shape = get_img_size(dicom_id, d_mimic_chex_original)
    size_y, size_x = img_shape
    all_timestamps = []
    distance_to_buttons = []
    distance_to_image_angle = []
    distance_to_image = []
    position_x = []
    position_y = []
    for index, row in sequence_table.iterrows():
        shown_rects_image_space = [round(row['source_rect_dimension_1']) ,round(row['source_rect_dimension_2']),round(row['source_rect_dimension_3']),round(row['source_rect_dimension_4'])]
        shown_rects_screen_space = [round(row['dest_rect_dimension_1']) ,round(row['dest_rect_dimension_2']),round(row['dest_rect_dimension_3']),round(row['dest_rect_dimension_4'])]
        #buttons_rectangle = np.array([10,1038,650, 1122]) 933, 1017
        buttons_rectangle = np.array([0,923,660, 1132])
        all_timestamps.append([(row['time_start_linux']-start_audio)*24*60*60,(row['time_linux']-start_audio)*24*60*60])
        
        image_pixels_per_screen_pixel_x = (shown_rects_image_space[2]-shown_rects_image_space[0])/(shown_rects_screen_space[2]-shown_rects_screen_space[0])
        image_pixels_per_screen_pixel_y = (shown_rects_image_space[3]-shown_rects_image_space[1])/(shown_rects_screen_space[3]-shown_rects_screen_space[1])
        
        x_screen, y_screen = convert_image_to_screen_coordinates(row['position_x'], row['position_y'], shown_rects_screen_space, shown_rects_image_space)
        distance_to_image.append(distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space))
        distance_to_buttons.append(distance_point_rectangle([x_screen, y_screen],buttons_rectangle))
        distance_to_image_angle.append(distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space, image_pixels_per_screen_pixel_x/row['angular_resolution_x'], image_pixels_per_screen_pixel_y/row['angular_resolution_y']))
        position_x.append(x_screen)
        position_y.append(y_screen)
        
        
    return np.array(all_timestamps),np.array(distance_to_image),np.array(distance_to_buttons),np.array(distance_to_image_angle),np.array(position_x), np.array(position_y)
    
# def create_embedding(sequence_table, img, start_audio):
    # size_y, size_x = img.shape
    # all_fixations = []
    # all_timestamps = []
    # for index, row in sequence_table.iterrows():
        # angle_circle = 0.98
        # shown_rects_image_space = [row['source_rect_dimension_1'] ,row['source_rect_dimension_2'],row['source_rect_dimension_3'],row['source_rect_dimension_4']]
        # rr, cc = ellipse(row['position_y'],row['position_x'], row['angular_resolution_y']*angle_circle, row['angular_resolution_x']*angle_circle)
        # len_rr_before_invalid = len(rr)
        # invalid_indexs  = np.logical_or(np.logical_or(rr<shown_rects_image_space[1], cc<shown_rects_image_space[0]), np.logical_or(rr>=shown_rects_image_space[3], cc>=shown_rects_image_space[2]))
        # rr = rr[~invalid_indexs]
        # cc = cc[~invalid_indexs]
        # if len(rr)>0:
            # # all_fixations.append(img[rr, cc][np.random.randint(len(rr), size=[length_embedding])])
            # all_fixations.append(img[rr, cc][np.random.randint(len(rr), size=[length_embedding])])
            # all_timestamps.append([(row['time_start_linux']-start_audio)*24*60*60,(row['time_linux']-start_audio)*24*60*60])
    # print(np.array(all_fixations).shape)
    # print(np.array(all_timestamps).shape)
    # return np.array(all_fixations),np.array(all_timestamps)

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
                dicom_id = filpath_image_this_trial.split('/')[-1].split('.')[0]
                # image = open_dicom(filpath_image_this_trial)
                start_audio = float(df_this_trial_this_user[df_this_trial_this_user['type']=='start_audio_recording']['value'].values[0])
                # fixations, timestamp, probability = create_embedding(df_this_trial_this_user[df_this_trial_this_user['type']=='fixation'],dicom_id, start_audio)
                # h5_f.create_dataset('embedding_'+f'{h5_index:06}', data=fixations)
                # h5_f.create_dataset('probability_'+f'{h5_index:06}', data=probability)
                # h5_f.create_dataset('timestamp_start_'+f'{h5_index:06}', data=timestamp[:,0])
                # h5_f.create_dataset('timestamp_end_'+f'{h5_index:06}', data=timestamp[:,1])
                # h5_f.create_dataset('user_'+f'{h5_index:06}', data=np.array([list_of_users.index(user)]))
                # h5_f.create_dataset('trial_n_'+f'{h5_index:06}', data=np.array([trial]))
                timestamp, distance_to_image, distance_to_buttons, distance_to_image_angle, position_x, position_y = create_embedding(df_this_trial_this_user[df_this_trial_this_user['type']=='fixation'],dicom_id, start_audio)
                h5_f.create_dataset('distance_to_image_'+f'{h5_index:06}', data=distance_to_image)
                h5_f.create_dataset('distance_to_image_angle_'+f'{h5_index:06}', data=distance_to_image_angle)
                h5_f.create_dataset('distance_to_buttons_'+f'{h5_index:06}', data=distance_to_buttons)
                h5_f.create_dataset('timestamp_start_'+f'{h5_index:06}', data=timestamp[:,0])
                h5_f.create_dataset('timestamp_end_'+f'{h5_index:06}', data=timestamp[:,1])
                h5_f.create_dataset('user_'+f'{h5_index:06}', data=np.array([list_of_users.index(user)]))
                h5_f.create_dataset('trial_n_'+f'{h5_index:06}', data=np.array([trial]))
                h5_f.create_dataset('position_x_'+f'{h5_index:06}', data=position_x)
                h5_f.create_dataset('position_y_'+f'{h5_index:06}', data=position_y)
                h5_index += 1

def get_embeddings_phase_2():
    all_trials = {}
    all_trials['user1'] = [x for x in range(1,51) if x not in {6,40,47,48}]
    all_trials['user2'] = [x for x in range(1,51) if x not in {4,14,15}]
    all_trials['user3'] = [x for x in range(1,51) if x not in {1,46}]
    all_trials['user4'] = [x for x in range(1,51) if x not in {}]
    all_trials['user5'] = [x for x in range(1,51) if x not in {1}]
    
    
    create_embeddings('./summary_edf_phase_2.csv', 
    './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',
    "embeddings_phase_2_distances.hdf5", all_trials)

def get_embeddings_phase_1():
    all_trials = {}
    all_trials['user1'] = [x for x in range(2,61) if x not in {1,6,7,8,41}]
    all_trials['user2'] = [x for x in range(2,61) if x not in {15,27,32}]
    all_trials['user3'] = [x for x in range(2,61) if x not in {14,44}]
    all_trials['user4'] = [x for x in range(2,61) if x not in {7}]
    all_trials['user5'] = [x for x in range(2,61) if x not in {}]
    
    create_embeddings('./summary_edf_phase_1.csv',
     './anonymous_collected_data/image_paths_preexperiment_3.txt',
     "embeddings_phase_1_distances.hdf5", all_trials)

def weight_embedding(embedding, weights):
    sum_weigths = np.sum(weights[None,...])
    this_embedding = np.sum(np.sum(embedding*weights[None,...]/sum_weigths, axis = 2), axis=1)
    return this_embedding

# def weight_embedding(embedding, weights):
    
    
    
    # sum_weigths = np.sum(weights[None,...])
    # embedding.mul_(torch.tensor(weights[None,...]/sum_weigths).half().cuda())
    # this_embedding = embedding.sum(dim = [1,2])
    # # this_embedding = np.sum(np.sum(embedding*weights[None,...]/sum_weigths, axis = 2), axis=1)
    # # final_embedding = []
    # # for i in range(embedding.shape[0]):
        
        # # resized_embedding_i = skimage.transform.resize(embedding[i], (1,new_size[0], new_size[1]), mode='constant', preserve_range=True).astype(np.float32)
        # # final_embedding.append(np.sum(resized_embedding_i*weights[None,...]/sum_weigths))
        # # print(np.sum(weights[None,...]))
    # # resized_embedding = np.stack(final_embedding)
    # #print(this_embedding.size())
    # return this_embedding.detach().cpu().numpy()

import argparse
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--preprocess', type=str, nargs='?',
                        help='')
    args = parser.parse_args()

    # get_model_embeddings('',args.preprocess)
    # create_heatmaps('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',60, 9, './results_phase_2.csv',folder_name='heatmaps_phase_2_0.98')
    # create_heatmaps('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',60, folder_name='heatmaps_gaussian_phase_2_0.98')
    # create_heatmaps('./summary_edf_phase_1.csv', './anonymous_collected_data/phase_1/image_paths_preexperiment_3.txt',60, folder_name='heatmaps_phase_1_0.98')
    
    get_embeddings_phase_1()
    get_embeddings_phase_2()
    # create_embeddings('./summary_edf_phase_2.csv', './anonymous_collected_data/phase_2/image_paths_preexperiment_4.txt',"embeddings_phase_2.hdf5", 50)