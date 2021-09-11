# example of:
# - how dicoms were loaded and modified (windowing, zooming, panning) for display
# - how to calculate the shown brightness corresponding to the chest x-ray that is being shown in the image, in fixation

from collections import defaultdict
import re
import pandas as pd
import math
from skimage import draw
from skimage.transform import resize
import os
import numpy as np
from PIL import Image,ImageDraw, ImageFont
from pydicom import dcmread
from dataset_locations import reflacx_dataset_location, mimiccxr_images_location

def get_brightness(dicom, row):
    frame = apply_windowing(dicom, row['window_level'], row['window_width'])
    shown_part_frame = frame[round(row['ymin_shown_from_image']):round(row['ymax_shown_from_image']),
                            round(row['xmin_shown_from_image']):round(row['xmax_shown_from_image'])]
    xscreensize = (round(row['xmax_in_screen_coordinates'])-round(row['xmin_in_screen_coordinates']))
    yscreensize = (round(row['ymax_in_screen_coordinates'])-round(row['ymin_in_screen_coordinates']))
    
    image_resized = resize(shown_part_frame, (yscreensize,xscreensize),
                       anti_aliasing=True)
    
    #normalize the brightness
    frame = np.sum(image_resized)/(round(2160)*round(3840-2*660))
    
    return frame

import copy

def apply_windowing(x,level,width):
    return np.minimum(np.maximum(((x.astype(float)-level)/width+0.5),0),1);

def find_nearest(a, n):
    return np.argmin(np.abs(a.astype(float)-n))

def open_dicom(filpath_image_this_trial):
    with dcmread(filpath_image_this_trial) as header:
        
        #nromalize not by the maximum intensity, but by the maximum possible intensity
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
            starting_windowing_width = wwidth/max_possible_value
            starting_windowing_level = wcenter/max_possible_value
            
            #the following conditions show that the intensities were inverted for display
            if header.PhotometricInterpretation=='MONOCHROME1' or not ('PixelIntensityRelationshipSign' in header) or header.PixelIntensityRelationshipSign==1:
                x = 1-x
                starting_windowing_level = 1 - starting_windowing_level
        else:
             #if no windowing is provided by the dicom, approximate it from the VOILUTSequence array, if available
             if 'VOILUTSequence' in header:
                # find the window level by findingthe closest index where intensity is at half
                lut_center = float(header.VOILUTSequence[0].LUTDescriptor[0])/2
                window_center = find_nearest(np.array(header.VOILUTSequence[0].LUTData), lut_center)
                deltas = []
                
                # approximate the derivative of the array values at window_center to get the window width
                for i in range(10,31):
                    deltas.append((float(header.VOILUTSequence[0].LUTData[window_center+i]) - float(header.VOILUTSequence[0].LUTData[window_center-i]))/2/i)
                window_width = lut_center/sum(deltas)*2*len(deltas)
                starting_windowing_width = window_width/max_possible_value
                starting_windowing_level = (window_center-1)/max_possible_value
                
                # a starting_windowing_width of less than zero means that the intensities were inverted for display
                if starting_windowing_width < 0:
                    starting_windowing_width = -starting_windowing_width
                    x = 1-x
                    starting_windowing_level = 1 - starting_windowing_level
             else:
                 # if no windowing information is available, assume the standard values
                starting_windowing_width = 1
                starting_windowing_level = 0.5;
                
                #the following conditions show that the intensities were inverted for display
                if header.PhotometricInterpretation=='MONOCHROME1' or not ('PixelIntensityRelationshipSign' in header) or header.PixelIntensityRelationshipSign==1:
                    x = 1-x
                    starting_windowing_level = 1 - starting_windowing_level
        return x, starting_windowing_level, starting_windowing_width

def main():
    et_dataset_location = f'{reflacx_dataset_location}/main_data/'
    mimic_dataset_location = mimiccxr_images_location
    id = 'P300R889090'
    get_brightness_one_image(et_dataset_location, mimic_dataset_location, id)

def get_brightness_one_image(et_dataset_location, mimic_dataset_location, id):
    table_et_pt1 = pd.read_csv(f'{et_dataset_location}/{id}/fixations.csv')
    main_table = pd.read_csv(f'{et_dataset_location}/metadata_phase_{id[1]}.csv')
    image_filepath = main_table[main_table['id']==id]['image'].values
    assert(len(image_filepath)==1)
    max_time_fixation = max(table_et_pt1['timestamp_end_fixation'].values)
    dicom_array, _, _ = open_dicom(f'{mimic_dataset_location}/{image_filepath[0]}')
    for _,row in table_et_pt1.iterrows():
        brightness = get_brightness(dicom_array, row)
        print(brightness)

if __name__ == '__main__':
    main()