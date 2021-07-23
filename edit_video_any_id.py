import moviepy.editor as mpe
from moviepy.video.VideoClip import ImageClip
from collections import defaultdict
import re
import pandas as pd
import math
from skimage import draw
import os
import numpy as np
from PIL import Image,ImageDraw
from pydub import AudioSegment
from pydicom import dcmread

fps = 30.
scale_video = 1

def scroll(get_frame, t,table_et):
    frame = get_frame(t)
    frame = frame.copy()
    frame.setflags(write=1)
    
    fixations = table_et
    fixations = fixations[t<=(fixations['timestamp_end_fixation'])]
    fixations = fixations[t>=(fixations['timestamp_start_fixation'])]
    if len(fixations)>0:
        frame = draw_circle(frame,fixations['average_x_position'].values[0]*scale_video, fixations['average_y_position'].values[0]*scale_video, fixations['angular_resolution_x_pixels_per_degree'].values[0]*scale_video,fixations['angular_resolution_y_pixels_per_degree'].values[0]*scale_video, (255,0,0))
    
    return frame

def draw_circle(image, x,y,radius_x,radius_y,color):
    foreground = Image.new('RGB', (image.shape[1], image.shape[0]), color)
    background = Image.fromarray(image[:,:,0])
    mask = Image.new('L', (image.shape[1], image.shape[0]), 255)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((x-radius_x,y-radius_y, x+radius_x, y+radius_y), fill=(200))
    result = Image.composite(background, foreground, mask)
    return np.array(result)

import copy
def fl(clip, fun):
    calculated_frames = []
    i = 0
    print(len(list(clip.iter_frames())))
    for frame in clip.iter_frames():
        calculated_frames.append(frame.copy())
        break
    
    def my_get_frame(t):
        return calculated_frames[0]
    print('oi1')
    clip = clip.set_make_frame(lambda t: fun(my_get_frame, t))
    return clip

def apply_windowing(x,level,width):
    return np.minimum(np.maximum(((x.astype(float)-level)/width+0.5),0),1);

def find_nearest(a, n):
    return np.argmin(np.abs(a.astype(float)-n))

def open_dicom(filpath_image_this_trial):
    with dcmread(filpath_image_this_trial) as header:
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
                lut_center = float(header.VOILUTSequence[0].LUTDescriptor[0])/2
                window_center = find_nearest(np.array(header.VOILUTSequence[0].LUTData), lut_center)
                deltas = []
                for i in range(10,31):
                    deltas.append((float(header.VOILUTSequence[0].LUTData[window_center+i]) - float(header.VOILUTSequence[0].LUTData[window_center-i]))/2/i)
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

def main():
    et_dataset_location = 'built_dataset'
    mimic_dataset_location = 'datasets/mimic/'
    id = 'U5E301T500'
    audio_file = f'./{int(id[-3:])}.wav'
    audio_background = mpe.AudioFileClip(audio_file)
    table_et_pt1 = pd.read_csv(f'{et_dataset_location}/{id}/fixations.csv')
    main_table = pd.read_csv(f'{et_dataset_location}/metadata_phase_3.csv')
    image_filepath = main_table[main_table['id']==id]['image'].values
    assert(len(image_filepath)==1)
    
    dicom_array = open_dicom(f'{mimic_dataset_location}/{image_filepath[0]}')*255
    from skimage.transform import resize
    dicom_array = resize(dicom_array, (int(dicom_array.shape[0] *scale_video), int(dicom_array.shape[1] *scale_video)),
                       anti_aliasing=True)
    dicom_array = dicom_array.astype(np.uint8)
    my_clip = ImageClip(np.stack((dicom_array,)*3, axis=-1) ).set_duration(audio_background.duration).set_fps(fps)
    
    print(my_clip)
    my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_pt1))
    
    my_clip = my_clip.set_audio(audio_background)
    my_clip.write_videofile(f"movie_{id}.mp4",audio_codec='aac', codec="libx264",temp_audiofile='temp-audio.m4a', 
                     remove_temp=True,fps=30, bitrate = "5000k")
if __name__ == '__main__':
    main()