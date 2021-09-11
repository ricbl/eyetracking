# This script was used to generate the video included in the paper as a supplementary file
# the data used to generate the video was not part of the dataset and is just an example of the use of the interface

import moviepy.editor as mpe
from collections import defaultdict
import re
import pandas as pd
import math
from skimage import draw
import os
import numpy as np
from PIL import Image,ImageDraw
from pydub import AudioSegment
import json
import pyttsx3
import librosa
import pyrubberband
import soundfile as sf
from skimage.transform import resize
from skimage.util import img_as_ubyte
import time

fps = 30.
use_digital_audio = True
# reducing the resolution of the video so that it is less than the 10 MB required for Supplementary Files
scale_video = 0.175

def clean(get_frame, t):
    frame_t = t
    while frame_t>=0:
        calculated_frame = get_frame(frame_t)
        frame = calculated_frame['frame']
        all_black = calculated_frame['all_black']
        all_white = calculated_frame['all_white']
        all_green = calculated_frame['all_green']
        top_row = calculated_frame['top_row']
        bottom_row = calculated_frame['bottom_row']
        # if any of these conditions are not met, the frame is extremly likely to be a bugged one where capture failed,
        if all_white<50000 and all_green<20000 and all_black<7000000 and top_row<1500 and bottom_row<1500:
            break
        else:
            # if bad frame, go back to previous frame (keep doing this until a good frame is found)
            frame_t -= 1/fps
    return frame

def scroll(get_frame, t,table_et, delay):
    frame = clean(get_frame, t)
    frame = frame.copy()
    frame.setflags(write=1)
    
    fixations = table_et[table_et['type']=='fixation']
    fixations = fixations[t<=(fixations['time_linux']-delay)]
    fixations = fixations[t>=(fixations['time_start_linux']-delay)]
    if len(fixations)>0:
        frame = draw_circle(frame,scale_video*fixations['position_x'].values[0], scale_video*fixations['position_y'].values[0], scale_video*fixations['angular_resolution_x'].values[0],scale_video*fixations['angular_resolution_y'].values[0], (255,0,0))
    
    samples = table_et[table_et['type']=='sample']
    
    #get gaze sampled closest to the current video time
    samples = samples.iloc[abs(samples['time_start_linux']-delay-t).argsort()[:2]]
    print(len(samples))
    frame = draw_circle(frame,scale_video*samples['position_x'].values[0], scale_video*samples['position_y'].values[0], scale_video*samples['angular_resolution_x'].values[0]/5,scale_video*samples['angular_resolution_y'].values[0]/5, (0,255,255))
    return frame

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

def time_edf_to_time_linux_scale(time_edf):
    return float(time_edf)/1000/60/60/24

columns_csv = ['type','value','time_linux', 'time_start_linux',
'position_x','position_y','angular_resolution_x','angular_resolution_y']

def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

#function to read the fixation information from the asc eye-tracking datafile
def ASC2CSV(fname):
    state_edf = 'not_started'
    filepath = ''
    dfs = pd.DataFrame(columns=columns_csv)
    index_edf = 0
    samples = []
    fixations = []
    with open(fname, 'r', encoding="utf8", errors='ignore') as ascfile:
        for current_line in ascfile:
            split_line = re.split('\t| ',current_line.rstrip())
            split_line = [i for i in split_line if i] 
            if len(split_line)>0:
                if split_line[0] == 'MSG':
                    time_edf = time_edf_to_time_linux_scale(split_line[1])
                    if split_line[2]=='SOM953':
                        split_message = ' '.join(split_line[3:]).split(';$')
                        writer_name = split_message[0]
                        message_title = split_message[2]
                        message_value = split_message[3]
                        time_linux = float(split_message[1])
                        current_delta_time = time_linux - time_edf
                        if writer_name=='InteractiveDictation':
                            if message_title == 'start_audio_recording':
                                new_row = {'type':'start_audio_recording',
                                'value':time_edf+current_delta_time,
                                'time_linux':time_edf+current_delta_time}
                                dfs= dfs.append(new_row, ignore_index=True)
                        if writer_name=='MainWindow':
                            if message_title == 'start_video_recording':
                                new_row = {'type':'start_video_recording',
                                'value':time_edf+current_delta_time,
                                'time_linux':time_edf+current_delta_time}
                                dfs = dfs.append(new_row, ignore_index=True)
                elif state_edf=='not_started':
                    if split_line[0] == 'START':
                        time_edf = time_edf_to_time_linux_scale(split_line[1])
                        state_edf = 'started'
                        time_start_capture = time_edf+current_delta_time
                elif state_edf=='started':
                    if split_line[0] == 'END':
                        time_edf = time_edf_to_time_linux_scale(split_line[1])
                        state_edf = 'not_started'
                        index_edf +=1
                    elif split_line[0] == 'EFIX':
                        time_start = time_edf_to_time_linux_scale(split_line[2])+current_delta_time
                        time_end = time_edf_to_time_linux_scale(split_line[3])+current_delta_time
                        position_x_screen = float(split_line[5])
                        position_y_screen = float(split_line[6])
                        angular_resolution_x_screen = float(split_line[8])
                        angular_resolution_y_screen = float(split_line[9])
                        
                        fixations.append({'type':'fixation',
                        'value':None,
                        'time_linux':time_end,
                        'time_start_linux':time_start,
                        'position_x':position_x_screen,
                        'position_y':position_y_screen,
                        'angular_resolution_x':angular_resolution_x_screen,
                        'angular_resolution_y':angular_resolution_y_screen,
                        'index_edf':index_edf})
                    
                    else:
                        if is_number(split_line[0]) and is_number(split_line[1]):
                            time_start = time_edf_to_time_linux_scale(split_line[0])+current_delta_time
                            position_x_screen = float(split_line[1])
                            position_y_screen = float(split_line[2])
                            angular_resolution_x_screen = float(split_line[4])
                            angular_resolution_y_screen = float(split_line[5])
                            samples.append({'type':'sample',
                            'value':None,
                            'time_start_linux':time_start,
                            'position_x':position_x_screen,
                            'position_y':position_y_screen,
                            'angular_resolution_x':angular_resolution_x_screen,
                            'angular_resolution_y':angular_resolution_y_screen,
                            'index_edf':index_edf})
    dfs = dfs.append(samples, ignore_index=True)
    dfs = dfs.append(fixations, ignore_index=True)
    dfs['time_start_linux'] = dfs['time_start_linux']*24*60*60
    dfs['time_linux'] = dfs['time_linux']*24*60*60
    return dfs

import copy
def fl(clip, fun,filter_bad_frames):
    calculated_frames = []
    i = 0
    print(len(list(clip.iter_frames())))
    for frame in clip.iter_frames():
        i+=1
        if filter_bad_frames:
            #calculate number of pixels of different colors, in different positions, used to later filter frames that wree badly recorded
            top_row = (frame[0,...,2]>=60).sum()
            bottom_row = (frame[0,...,2]>=60).sum()
            all_white = (frame[...,1]>=249).sum()
            all_black = (frame[...,0]<=5)*(frame[...,2]<=5)
            all_green = ((all_black*(frame[...,1]>=110))*1).sum()
            all_black = all_black.sum()
        else:
            top_row = 0
            bottom_row = 0
            all_white = 0
            all_black = 0
            all_green = 0
            all_black = 0
        
        
        frame = resize(frame.copy(), (int(frame.shape[0] *scale_video), int(frame.shape[1] *scale_video)),
                           anti_aliasing=True)
        frame = img_as_ubyte(frame)
        # frame = frame.astype(np.uint8)
        
        calculated_frames.append({'frame':frame, 'all_black':all_black,'all_green':all_green,'all_white':all_white,'top_row':top_row,'bottom_row':bottom_row})
    
    def my_get_frame(t):
        index = round(clip.fps*t)
        
        #sometimes there is a 1 frame mismatch by the end ofthe video
        if index>=len(calculated_frames):
            index -= 1
        return calculated_frames[index]
    
    clip = clip.set_make_frame(lambda t: fun(my_get_frame, t))
    return clip

def trim_audio(path_to_wav, start_trim, end_trim):
    sound = AudioSegment.from_file(path_to_wav, format="wav")    
    duration = len(sound)    
    trimmed_sound = sound[start_trim*1000:duration-end_trim*1000]
    trimmed_sound.export(path_to_wav, format="wav")

#text-to-speech helper
class SaveTTSFile:
    def __init__(self, filename):
        self.engine = pyttsx3.init()
        self.filename = filename

    def start(self,text, start,end):
        self.engine.setProperty('rate', 60/(end-start))
        self.engine.save_to_file(text , self.filename)
        self.engine.runAndWait()

#change the audio speed to match the speed used by the radiolgist
def stretch_audio(audio, filepath, stretch_constant):
    audio.export(filepath, format="wav")
    y, sr = librosa.load(filepath, sr=None)
    y_stretched = pyrubberband.time_stretch(y, sr, stretch_constant)
    sf.write(filepath, y_stretched, sr, format='wav')
    return AudioSegment.from_file(filepath, format="wav")

def main():
    extensions= ['ogv','mov']
    trial = ['326','160']
    folders = ['../video_302_20210514-143755-6691','../video_305_20210514-141912-2142']
    filter_bad_frames = [True,False]
    for index_trial in [0,1]:
        results_df = pd.read_csv(f'{folders[index_trial]}/structured_output.csv')
        results_df = results_df[results_df['trial']==float(trial[index_trial])]
        table_et_pt1 = ASC2CSV(f'{folders[index_trial]}/et{trial[index_trial]}.asc')
        table_et_pt2 = ASC2CSV(f'{folders[index_trial]}/et{trial[index_trial]}pt2.asc')
        list_of_videos = []
        for screen in range(1,13):
            results_df_this_screen = results_df[results_df['screen']==screen]
            video_filename = f'{folders[index_trial]}/recorded_screen_{screen}_trial_{trial[index_trial]}_0001.{extensions[index_trial]}'
            if os.path.isfile(video_filename):
                my_clip = mpe.VideoFileClip(video_filename)
                if screen in [2,4,7,9]:
                    start_video = results_df_this_screen[results_df_this_screen['title']=='start_video_recording']['timestamp'].values[0]*24*60*60
                    
                    #the only screen with audio is screen 2
                    if screen==2:
                        table_et_2 = table_et_pt1.copy()
                        start_video_2 = start_video
                        my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_2, start_video_2), filter_bad_frames[index_trial])
                        delay_audio = results_df_this_screen[results_df_this_screen['title']=='start_audio_recording']['timestamp'].values[0]*24*60*60-start_video
                        
                        #generate the audio from the timestamped transcription
                        if use_digital_audio:
                            full_audio = AudioSegment.empty()
                            previous_end = 0
                            with open(f'{folders[index_trial]}/{trial[index_trial]}_joined.json','r') as f:
                                table_text = json.load(f)['timestamps']
                            with open(f'{folders[index_trial]}/{trial[index_trial]}_trim.json','r') as f:
                                b = json.load(f)
                            trim_value = float(b['start_trim'])/1000
                            for row in table_text:
                                print(row[1])
                                print(trim_value)
                                
                                #row[1] is the timestamp for the start of the word, and row[2] the timestamp for the end of the word
                                row[1] += trim_value
                                row[2] += trim_value
                                print(row[1])
                                
                                # if start and end of the word are at the same time, it was not captured by the original transcription, so we do not use it in the audio, only in subtitle
                                if row[1] == row[2]:
                                    continue
                                
                                # text to speech
                                tts = SaveTTSFile('create_video_temp.wav')
                                tts.start(row[0].replace('.', 'period').replace(',','comma').replace('/', 'slash') , row[1], row[2])
                                for i in range(10):
                                    if not os.path.exists('./create_video_temp.wav'):
                                        time.sleep(1)
                                    else:
                                        break
                                    if i>10:
                                        assert(False)
                                del(tts)
                                
                                # add silence between words if they did not end/start at the same time
                                if row[1]>previous_end:
                                    full_audio += AudioSegment.silent(duration=(row[1]-previous_end)*1000)
                                print(full_audio.duration_seconds)
                                print(row[1])
                                assert(abs(full_audio.duration_seconds - row[1])<0.002)
                                
                                #change the duration of the word sound to the duration it took for the radiologist to say it
                                word_audio = AudioSegment.from_file('create_video_temp.wav', format="wav")
                                word_audio = stretch_audio(word_audio, 'create_video_temp.wav', word_audio.duration_seconds/(row[2] - row[1]))
                                
                                full_audio += word_audio
                                assert(abs(full_audio.duration_seconds - row[2])<0.002)
                                previous_end = row[2]
                            full_audio.export("create_video_temp.wav", format="wav")
                            audio_background = mpe.AudioFileClip('create_video_temp.wav')
                            os.remove('./create_video_temp.wav')
                        else:
                            audio_background = mpe.AudioFileClip(f'{folders[index_trial]}/{trial[index_trial]}.wav')
                            # delay_audio = round(delay_audio*my_clip.fps)/my_clip.fps
                        if delay_audio>0:
                            null_audio = mpe.AudioClip(lambda t: 0, duration= delay_audio)
                            audio_background = mpe.concatenate_audioclips([null_audio,audio_background])
                            delay_audio = 0
                        delay_end_video = my_clip.duration - audio_background.duration
                        if delay_end_video>0:
                             null_audio = mpe.AudioClip(lambda t: 0, duration= delay_end_video)
                             audio_background = mpe.concatenate_audioclips([audio_background, null_audio])
                             delay_end_video = 0
                        audio_background.write_audiofile('temp_crop_audio.wav')
                        trim_audio('temp_crop_audio.wav', -delay_audio, -delay_end_video)
                        audio_background = mpe.AudioFileClip('temp_crop_audio.wav')
                        
                    else:
                        if screen==4:
                            table_et_this_screen_4 = table_et_pt2[table_et_pt2['index_edf']==0]
                            start_video_4 = start_video
                            my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_this_screen_4, start_video_4),filter_bad_frames[index_trial] )
                        if screen==7:
                            table_et_this_screen_7 = table_et_pt2[table_et_pt2['index_edf']==1]
                            start_video_7 = start_video
                            my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_this_screen_7, start_video_7),filter_bad_frames[index_trial] )
                        if screen == 9:
                            table_et_this_screen_9 = table_et_pt2[table_et_pt2['index_edf']==2]
                            start_video_9 = start_video
                            my_clip = fl(my_clip, lambda get_frame, t: scroll(get_frame, t,table_et_this_screen_9, start_video_9),filter_bad_frames[index_trial] )
                else:
                    my_clip = fl(my_clip, clean,filter_bad_frames[index_trial] )
                if screen!=2:
                    audio_background = mpe.AudioClip(lambda t: 0, duration= my_clip.duration)
                my_clip = my_clip.set_audio(audio_background)
                list_of_videos.append(my_clip)
        final = mpe.concatenate_videoclips(list_of_videos)
        final.write_videofile(f"movie_{extensions[index_trial]}.mp4",audio_codec='aac', codec="libx264",temp_audiofile='temp-audio.m4a', 
                         remove_temp=True,fps=30, bitrate = "5000k")
        os.remove('./create_video_temp.wav')
if __name__ == '__main__':
    main()