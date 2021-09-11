# generates a video representing the reading of a chest x-ray from the information made available in the dataset
# the video shows the location of the fixations in a red ellipseand the dicatated report, syunchronied with the fixations
# the dictation is shown by a digitally generated audio and by a subtitle
# windowing, zooming and panning are also represented
# example of:
# - how dicoms were loaded and modified (windowing, zooming, panning) for display
# - a visual representation of the synchronization between gaze and speech
# - how to load the fixations and transcription tables

import moviepy.editor as mpe
from moviepy.video.VideoClip import ImageClip
from collections import defaultdict
import re
import pandas as pd
import math
from skimage import draw
from skimage.transform import resize
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
from dataset_locations import reflacx_dataset_location, mimiccxr_images_location
import time

fps = 30.
#reduce the resolution of the video by using this scaling constant
scale_video = 0.25

def scroll(get_frame, t,table_et, table_transcription):
    frame = get_frame(t)
    frame = frame.copy()
    frame.setflags(write=1)
    
    fixations = table_et
    fixations = fixations[t<=(fixations['timestamp_end_fixation'])]
    fixations = fixations[t>=(fixations['timestamp_start_fixation'])]
    
    table_transcription = table_transcription[t>=(table_transcription['timestamp_start_word'])]
    
    #in the subtitle, write all words from the last 5 seconds
    table_transcription = table_transcription[t-5<=(table_transcription['timestamp_end_word'])]
    
    if len(fixations)>0:
        frame = draw_circle(frame,fixations['x_position'].values[0]*scale_video, fixations['y_position'].values[0]*scale_video, fixations['angular_resolution_x_pixels_per_degree'].values[0]*scale_video,fixations['angular_resolution_y_pixels_per_degree'].values[0]*scale_video, (255,0,0))
    
    #if no fixation for current timestamp was found, find the latest fixation to get information about windowing, zooming and panning
    if len(fixations)==0:
        fixations = table_et[t>=(table_et['timestamp_start_fixation'])]
        
        #if there are no fixationsberfore the current timestamp, select the first fixation of the reading
        if len(fixations)==0:
            fixations = table_et.head(1)
        
        fixations = fixations.sort_values(by='timestamp_end_fixation', ascending=True)            
        if len(fixations)>1:
            assert(fixations['timestamp_end_fixation'].values[-1]>fixations['timestamp_end_fixation'].values[-2])
            assert(fixations['timestamp_end_fixation'].values[-1]>fixations['timestamp_end_fixation'].values[0])
        old_tail = fixations['timestamp_end_fixation'].values[-1]
        fixations = fixations.tail(1)
        assert(fixations['timestamp_end_fixation'].values[0]==old_tail)
    assert(len(fixations)==1)
    print(round(fixations['ymin_shown_from_image'].values[0]*scale_video),round(fixations['ymax_shown_from_image'].values[0]*scale_video),round(fixations['xmin_shown_from_image'].values[0]*scale_video),round(fixations['xmax_shown_from_image'].values[0]*scale_video))
    
    #select only the part of the image that was shown on the screen
    shown_part_frame = frame[round(fixations['ymin_shown_from_image'].values[0]*scale_video):round(fixations['ymax_shown_from_image'].values[0]*scale_video),round(fixations['xmin_shown_from_image'].values[0]*scale_video):round(fixations['xmax_shown_from_image'].values[0]*scale_video)]
    
    xscreensize = (round((fixations['xmax_in_screen_coordinates'].values[0]-660)*scale_video)-round((fixations['xmin_in_screen_coordinates'].values[0]-660)*scale_video))
    yscreensize = (round(fixations['ymax_in_screen_coordinates'].values[0]*scale_video)-round(fixations['ymin_in_screen_coordinates'].values[0]*scale_video))
    
    #resize the shown part of the x-ray to have the same size as the part of the screen where it wsas shown
    image_resized = resize(shown_part_frame, (yscreensize,xscreensize),
                       anti_aliasing=True)*255
    
    image_resized = (apply_windowing(image_resized.astype(float)/255,fixations['window_level'].values[0],fixations['window_width'].values[0])*255).astype(np.uint8)
    
    # get the full area of the screen dedicated to showing chest x-rays, and postionthe zoomed chest x-ray in it
    frame = np.zeros([round(2160*scale_video),round((3840-2*660)*scale_video),3]).astype(np.uint8)
    frame[round((fixations['ymin_in_screen_coordinates'].values[0])*scale_video):round((fixations['ymax_in_screen_coordinates'].values[0])*scale_video),round((fixations['xmin_in_screen_coordinates'].values[0]-660)*scale_video):round((fixations['xmax_in_screen_coordinates'].values[0]-660)*scale_video)] = image_resized
    
    frame = draw_text(frame, ' '.join(table_transcription['word'].values))
    
    return frame

def draw_text(image, text_message):
    #get a plain foregroun layer filled with yellow
    foreground = Image.new('RGB', (image.shape[1], image.shape[0]), (128,128,0,128))
    
    background = Image.fromarray(image[:,:,:])
    
    mask = Image.new('L', (image.shape[1], image.shape[0]), 255)
    draw = ImageDraw.Draw(mask)
    fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", round(120*scale_video))
    w, h = draw.textsize(text_message, font = fnt)
    W, H = mask.size
    
    # draw subtitle in the bottom of the frame, aligned to the right, in an alpha layer, with alpha = 200/255
    draw.text(((W-w)-round(30*scale_video),(H)-round(150*scale_video)), text_message, fill=(200), font = fnt)
    
    #draw foreground on background respecting the alpha layer
    result = Image.composite(background, foreground, mask)
    return np.array(result)

def draw_circle(image, x,y,radius_x,radius_y,color):
    #get a plain foregroun layer filled with the desired color for the circle
    foreground = Image.new('RGB', (image.shape[1], image.shape[0]), color)
    
    background = Image.fromarray(image[:,:,:])
    
    # draw a circle in the alpha layer, withalpha = 200/255
    mask = Image.new('L', (image.shape[1], image.shape[0]), 255)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((x-radius_x,y-radius_y, x+radius_x, y+radius_y), fill=(200))
    
    #draw foreground on background respecting the alpha layer
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

class SaveTTSFile:
    def __init__(self, filename):
        self.engine = pyttsx3.init('espeak')
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

def generate_video_for_id(id):
    et_dataset_location = f'{reflacx_dataset_location}/main_data/'
    mimic_dataset_location = mimiccxr_images_location
    table_et_pt1 = pd.read_csv(f'{et_dataset_location}/{id}/fixations.csv')
    table_text = pd.read_csv(f'{et_dataset_location}/{id}/timestamps_transcription.csv')
    main_table = pd.read_csv(f'{et_dataset_location}/metadata_phase_{id[1]}.csv')
    image_filepath = main_table[main_table['id']==id]['image'].values
    assert(len(image_filepath)==1)
    max_time_fixation = max(table_et_pt1['timestamp_end_fixation'].values)
    max_time_text = max(table_text['timestamp_end_word'].values)
    dicom_array,_,_ = open_dicom(f'{mimic_dataset_location}/{image_filepath[0]}')
    dicom_array = dicom_array*255
    from skimage.transform import resize
    dicom_array = resize(dicom_array, (int(dicom_array.shape[0] *scale_video), int(dicom_array.shape[1] *scale_video)),
                       anti_aliasing=True)
    dicom_array = dicom_array.astype(np.uint8)
    
    #generat ea clip with the original dicom as every frame
    my_clip = ImageClip(np.stack((dicom_array,)*3, axis=-1) ).set_duration(max([max_time_fixation,max_time_text])).set_fps(fps)
    
    #modify every frame of the video according to the fixations and transcription tables
    my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_pt1, table_text))
    
    #generate the audio from the timestamped transcription
    full_audio = AudioSegment.empty()
    previous_end = 0
    for _,row in table_text.iterrows():
        
        # if start and end of the word are at the same time, it was not captured by the original transcription, so we do not use it in the audio, only in subtitle
        if row['timestamp_start_word'] == row['timestamp_end_word']:
            continue
        
        print(row['word'])
        
        # text to speech
        tts = SaveTTSFile('./create_video_temp.wav')
        tts.start(row['word'].replace('.', 'period').replace(',','comma').replace('/', 'slash') , row['timestamp_start_word'], row['timestamp_end_word'])
        for i in range(10):
            if not os.path.exists('./create_video_temp.wav'):
                time.sleep(1)
            else:
                break
            if i>10:
                assert(False)
        del(tts)
        
        
        # add silence between words if they did not end/start at the same time
        if row['timestamp_start_word']>previous_end:
            full_audio += AudioSegment.silent(duration=(row['timestamp_start_word']-previous_end)*1000)
        print(full_audio.duration_seconds)
        print(row['timestamp_start_word'])
        assert(abs(full_audio.duration_seconds - row['timestamp_start_word'])<0.005)
        
        #change the duration of the word sound to the duration it took for the radiologist to say it
        word_audio = AudioSegment.from_file('./create_video_temp.wav', format="wav")
        word_audio = stretch_audio(word_audio, './create_video_temp.wav', word_audio.duration_seconds/(row['timestamp_end_word'] - row['timestamp_start_word']))
        
        os.remove('./create_video_temp.wav')
        
        full_audio += word_audio
        assert(abs(full_audio.duration_seconds - row['timestamp_end_word'])<0.005)
        previous_end = row['timestamp_end_word']
    full_audio.export("./create_video_temp.wav", format="wav")
    audio_background = mpe.AudioFileClip('./create_video_temp.wav')
    my_clip = my_clip.set_audio(audio_background)
    my_clip.write_videofile(f"movie_{id}.mp4",audio_codec='aac', codec="libx264",temp_audiofile='temp-audio.m4a', 
                     remove_temp=True,fps=30, bitrate = "5000k")
    os.remove('./create_video_temp.wav')

if __name__ == '__main__':
    #choose what id to generate video for
    generate_video_for_id('P300R889090')