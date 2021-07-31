import moviepy.editor as mpe
from moviepy.video.VideoClip import ImageClip
from collections import defaultdict
import re
import pandas as pd
import math
from skimage import draw
import os
import numpy as np
from PIL import Image,ImageDraw, ImageFont
from pydub import AudioSegment
from pydicom import dcmread
import pyttsx3
from pydub import AudioSegment
import librosa
import pyrubberband
import soundfile as sf

fps = 30.
scale_video = 0.25

def scroll(get_frame, t,table_et, table_transcription):
    frame = get_frame(t)
    frame = frame.copy()
    frame.setflags(write=1)
    
    fixations = table_et
    fixations = fixations[t<=(fixations['timestamp_end_fixation'])]
    fixations = fixations[t>=(fixations['timestamp_start_fixation'])]
    
    table_transcription = table_transcription[t>=(table_transcription['timestamp_start_word'])]
    table_transcription = table_transcription[t-5<=(table_transcription['timestamp_end_word'])]
    
    if len(fixations)>0:
        frame = draw_circle(frame,fixations['average_x_position'].values[0]*scale_video, fixations['average_y_position'].values[0]*scale_video, fixations['angular_resolution_x_pixels_per_degree'].values[0]*scale_video,fixations['angular_resolution_y_pixels_per_degree'].values[0]*scale_video, (255,0,0))
    frame = draw_text(frame, ' '.join(table_transcription['word'].values))
    return frame

def draw_text(image, text_message):
    foreground = Image.new('RGB', (image.shape[1], image.shape[0]), (128,128,0,128))
    background = Image.fromarray(image[:,:,:])
    mask = Image.new('L', (image.shape[1], image.shape[0]), 255)
    draw = ImageDraw.Draw(mask)
    fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", round(120*scale_video))
    w, h = draw.textsize(text_message, font = fnt)
    W, H = mask.size
    draw.text(((W-w)-round(30*scale_video),(H)-round(150*scale_video)), text_message, fill=(200), font = fnt)
    result = Image.composite(background, foreground, mask)
    return np.array(result)

def draw_circle(image, x,y,radius_x,radius_y,color):
    foreground = Image.new('RGB', (image.shape[1], image.shape[0]), color)
    background = Image.fromarray(image[:,:,:])
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

class SaveTTSFile:
    def __init__(self, filename):
        self.engine = pyttsx3.init()
        self.filename = filename

    def start(self,text, start,end):
        self.engine.setProperty('rate', 60/(end-start))
        self.engine.save_to_file(text , self.filename)
        self.engine.runAndWait()

def stretch_audio(audio, filepath, stretch_constant):
    audio.export(filepath, format="wav")
    y, sr = librosa.load(filepath, sr=None)
    y_stretched = pyrubberband.time_stretch(y, sr, stretch_constant)
    sf.write(filepath, y_stretched, sr, format='wav')
    return AudioSegment.from_file(filepath, format="wav")

def main():
    et_dataset_location = 'built_dataset'
    mimic_dataset_location = 'datasets/mimic/'
    id = 'P102R068770'
    table_et_pt1 = pd.read_csv(f'{et_dataset_location}/{id}/fixations.csv')
    table_text = pd.read_csv(f'{et_dataset_location}/{id}/timestamps_transcription.csv')
    main_table = pd.read_csv(f'{et_dataset_location}/metadata_phase_1.csv')
    image_filepath = main_table[main_table['id']==id]['image'].values
    assert(len(image_filepath)==1)
    max_time_fixation = max(table_et_pt1['timestamp_end_fixation'].values)
    max_time_text = max(table_text['timestamp_end_word'].values)
    dicom_array = open_dicom(f'{mimic_dataset_location}/{image_filepath[0]}')*255
    from skimage.transform import resize
    dicom_array = resize(dicom_array, (int(dicom_array.shape[0] *scale_video), int(dicom_array.shape[1] *scale_video)),
                       anti_aliasing=True)
    dicom_array = dicom_array.astype(np.uint8)
    my_clip = ImageClip(np.stack((dicom_array,)*3, axis=-1) ).set_duration(max([max_time_fixation,max_time_text])).set_fps(fps)
    
    print(my_clip)
    my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_pt1, table_text))
    
    
    full_audio = AudioSegment.empty()
    previous_end = 0
    for _,row in table_text.iterrows():
        if row['timestamp_start_word'] == row['timestamp_end_word']:
            continue
        print(row['word'])
        tts = SaveTTSFile('create_video_temp.mp3')
        tts.start(row['word'].replace('.', 'period').replace(',','comma').replace('/', 'slash') , row['timestamp_start_word'], row['timestamp_end_word'])
        del(tts)
        if row['timestamp_start_word']>previous_end:
            full_audio += AudioSegment.silent(duration=(row['timestamp_start_word']-previous_end)*1000)
        print(full_audio.duration_seconds)
        print(row['timestamp_start_word'])
        assert(abs(full_audio.duration_seconds - row['timestamp_start_word'])<0.002)
        word_audio = AudioSegment.from_file('create_video_temp.mp3', format="mp3")
        word_audio = stretch_audio(word_audio, 'create_video_temp.mp3', word_audio.duration_seconds/(row['timestamp_end_word'] - row['timestamp_start_word']))
        full_audio += word_audio
        assert(abs(full_audio.duration_seconds - row['timestamp_end_word'])<0.002)
        previous_end = row['timestamp_end_word']
    full_audio.export("create_video_temp.mp3", format="mp3")
    audio_background = mpe.AudioFileClip('create_video_temp.mp3')
    my_clip = my_clip.set_audio(audio_background)
    my_clip.write_videofile(f"movie_{id}.mp4",audio_codec='aac', codec="libx264",temp_audiofile='temp-audio.m4a', 
                     remove_temp=True,fps=30, bitrate = "5000k")
if __name__ == '__main__':
    main()