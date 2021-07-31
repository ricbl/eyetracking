import pandas as pd
import os.path
from collections import defaultdict
import re
import numpy as np
import glob
import math

def time_edf_to_time_linux_scale(time_edf):
    return float(time_edf)/1000/60/60/24

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

columns_csv = ['type','value','time_linux','trial','screen', 'time_start_linux',
'position_x','position_y','pupil_size','pupil_size_normalization','angular_resolution_x','angular_resolution_y',
'window_width','window_level','zoom_level','center_screen_x','center_screen_y','eye', 'source_rect_dimension_1', 
'source_rect_dimension_2','source_rect_dimension_3', 'source_rect_dimension_4', 'dest_rect_dimension_1', 
'dest_rect_dimension_2', 'dest_rect_dimension_3', 'dest_rect_dimension_4']

next_rect = np.array([10,1035,650, 1120])
center_next = [330, 1077.5]

def distance(p1, p2):
    return ((p2[0]-p1[0])**2+(p2[1]-p1[1])**2)**0.5

def check_inside_rect(p, rect):
    return p[0]>=rect[0] and p[0]<=rect[2] and p[1]>=rect[1] and p[1]<=rect[3]

def distance_point_rectangle(p, rect):
    if check_inside_rect(p, rect):
        return 0
    return  nearest_distance(rect, p)

def nearest_distance(rectangle, point):
    if point[0]>=rectangle[0] and point[0]<=rectangle[2]:
        d_top = abs(rectangle[1] - point[1])
        d_bottom = abs(rectangle[3] - point[1])
    else:
        d_top =float('inf')
        d_bottom=float('inf')
    corner_y = rectangle[1] if d_top < d_bottom else rectangle[3]
    if point[1]>=rectangle[1] and point[1]<=rectangle[3]:
        d_left = abs(rectangle[0] - point[0])
        d_right = abs(rectangle[2] - point[0])
    else:
        d_left = float('inf')
        d_right = float('inf')
    corner_x = rectangle[0] if d_left < d_right else rectangle[2]
    d_cx = corner_x - point[0]
    d_cy = corner_y - point[1]
    d_corner = (d_cx**2 + d_cy**2)**0.5
    return min(d_top, d_bottom, d_left, d_right, d_corner)

def ASC2CSV(fname, user, pupil_normalization,screen_dictation=[2, 4, 7, 9], screen_pupil_calibration=14, correct_trial_0 = False, skip_after_pupil = False, chest_box_image=None, image_filepath = '', discard = False):
    print(fname)
    current_sorce_rect = [0,0,0,0]
    current_dest_rect = [0,0,0,0]
    current_window_width = 1
    current_window_level = 0.5
    current_zoom = 1
    if fname.split('/')[-1][:2]=='et':
        if fname[-7:-4]=='pt2':
            trial = int(fname.split('/')[-1][2:-7])
        else:
            trial = int(fname.split('/')[-1][2:-4])
        if correct_trial_0:
            trial = trial + 1;
    else:
        trial = 0
    current_screen = 0
    current_delta_time = 0
    current_image_size_x = 0
    current_image_size_y = 0
    screen_fixations_by_screen = defaultdict(list)
    image_fixations_by_screen = defaultdict(list)
    state_edf = 'not_started'
    filepath = ''
    if pupil_normalization is None:
        current_pupil_normalization = []
        current_pupil_normalization_times = []
    else:
        current_pupil_normalization  = pupil_normalization
        current_pupil_normalization_times = 1
    dfs = defaultdict(lambda: pd.DataFrame(columns=columns_csv))
    with open(fname, 'r', encoding="utf8", errors='ignore') as ascfile:
        for current_line in ascfile:
            split_line = re.split('\t| ',current_line.rstrip())
            split_line = [i for i in split_line if i] 
            if len(split_line)>0:
                if split_line[0] == 'MSG':
                    time_edf = time_edf_to_time_linux_scale(split_line[1])
                    if len(split_line)>=11 and split_line[2]=='!CAL' and split_line[3]=='VALIDATION' and split_line[5]!='ABORTED':
                        # print(current_line)
                        # print(split_line)
                        # MSG	8204406 !CAL VALIDATION HV13 L LEFT  GOOD ERROR 0.26 avg. 0.83 max  OFFSET 0.03 deg. -0.2,-2.6 pix.
                        # MSG	8204406 VALIDATE L POINT 0  LEFT  at 1920,1080  OFFSET 0.08 deg.  -3.2,7.0 pix.
                        # MSG	8204406 VALIDATE L POINT 1  LEFT  at 1920,184  OFFSET 0.12 deg.  -10.1,4.8 pix.
                        # MSG	8204406 VALIDATE L POINT 2  LEFT  at 1920,1975  OFFSET 0.83 deg.  5.2,-74.9 pix.
                        # MSG	8204406 VALIDATE L POINT 3  LEFT  at 230,1080  OFFSET 0.19 deg.  1.3,-16.9 pix.
                        # MSG	8204406 VALIDATE L POINT 4  LEFT  at 3609,1080  OFFSET 0.25 deg.  18.7,13.1 pix.
                        # MSG	8204406 VALIDATE L POINT 5  LEFT  at 433,291  OFFSET 0.57 deg.  52.9,-2.2 pix.
                        # MSG	8204406 VALIDATE L POINT 6  LEFT  at 3406,291  OFFSET 0.58 deg.  -44.8,29.0 pix.
                        # MSG	8204406 VALIDATE L POINT 7  LEFT  at 433,1868  OFFSET 0.68 deg.  48.1,-39.4 pix.
                        # MSG	8204406 VALIDATE L POINT 8  LEFT  at 3406,1868  OFFSET 0.21 deg.  -8.0,-17.3 pix.
                        # MSG	8204406 VALIDATE L POINT 9  LEFT  at 1075,632  OFFSET 0.67 deg.  61.3,-8.9 pix.
                        # MSG	8204406 VALIDATE L POINT 10  LEFT  at 2764,632  OFFSET 0.33 deg.  26.2,-15.9 pix.
                        # MSG	8204406 VALIDATE L POINT 11  LEFT  at 1075,1527  OFFSET 0.53 deg.  13.9,-46.0 pix.
                        # MSG	8204406 VALIDATE L POINT 12  LEFT  at 2764,1527  OFFSET 0.48 deg.  42.9,-12.7 pix.
                        #TODO: get expected mistake from position on the screen? probably not
                        #TODO write these values in every row, and return them and accept them as inputs
                        new_row = {'user':user, 'type':'avg_calibration_error',
                        'value':float(split_line[9]),
                        'time_linux':time_edf+current_delta_time,
                        'trial':trial,
                        'screen':-1}
                        dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                        
                        new_row = {'user':user, 'type':'max_calibration_error',
                        'value':split_line[11],
                        'time_linux':time_edf+current_delta_time,
                        'trial':trial,
                        'screen':-1}
                        dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                    elif split_line[2]=='SOM953':
                        split_message = ' '.join(split_line[3:]).split(';$')
                        writer_name = split_message[0]
                        message_title = split_message[2]
                        message_value = split_message[3]
                        time_linux = float(split_message[1])
                        if message_title == 'filepath':
                            filepath += message_value
                        current_delta_time = time_linux - time_edf
                        if writer_name=='MainWindow' and (message_title == 'index_start_screen_trial' or message_title=='index_start_screen_initialize'):
                            current_screen = int(message_value)
                            if current_screen==screen_pupil_calibration:
                                current_pupil_normalization = []
                                current_pupil_normalization_times = []
                            current_sorce_rect = [0,0,0,0]
                            current_dest_rect = [0,0,0,0]
                            current_window_width = 1
                            current_window_level = 0.5
                            #TODO: find somewhere where these are not 1
                            #TODO: check where I get the window and level from the dicom to see if it is correct that most are 1;0.5
                            current_zoom = 1
                            dfs[current_screen] = dfs[current_screen][0:0]
                        elif current_screen in screen_dictation:
                            if writer_name=='ImageLoading':
                                if message_title == 'window_width':
                                    current_window_width = float(message_value)
                                elif message_title == 'window_center':
                                    current_window_level = float(message_value)
                            elif writer_name=='InteractiveDictation':
                                if message_title == 'start_audio_recording':
                                    new_row = {'user':user,'type':'start_audio_recording',
                                    'value':time_edf+current_delta_time,
                                    'time_linux':time_edf+current_delta_time,
                                    'trial':trial,
                                    'screen':current_screen}
                                    dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            elif writer_name=='InteractiveImageWithZoom' or writer_name=='InteractiveImage':
                                if message_title == 'zoom':
                                    current_zoom = float(message_value)
                                elif message_title == 'source_rect_dimension_1':
                                    current_sorce_rect[0] = float(message_value)
                                elif message_title == 'source_rect_dimension_2':
                                    current_sorce_rect[1] = float(message_value)
                                elif message_title == 'source_rect_dimension_3':
                                    current_sorce_rect[2] = float(message_value)
                                elif message_title == 'source_rect_dimension_4':
                                    current_sorce_rect[3] = float(message_value)
                                elif message_title == 'dest_rect_dimension_1':
                                    current_dest_rect[0] = float(message_value)
                                elif message_title == 'dest_rect_dimension_2':
                                    current_dest_rect[1] = float(message_value)
                                elif message_title == 'dest_rect_dimension_3':
                                    current_dest_rect[2] = float(message_value)
                                elif message_title == 'dest_rect_dimension_4':
                                    current_dest_rect[3] = float(message_value)
                                elif message_title == 'image_size_x':
                                    new_row = {'user':user,'type':'image_size_x',
                                    'value':float(message_value),
                                    'time_linux':time_edf+current_delta_time,
                                    'trial':trial,
                                    'screen':current_screen}
                                    dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                                    current_image_size_x = float(message_value)
                                elif message_title == 'image_size_y':
                                    new_row = {'user':user,'type':'image_size_y',
                                    'value':float(message_value),
                                    'time_linux':time_edf+current_delta_time,
                                    'trial':trial,
                                    'screen':current_screen}
                                    dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                                    current_image_size_y = float(message_value)
                                elif message_title == 'set_scale':
                                    new_row = {'user':user,'type':'set_scale',
                                    'value':float(message_value),
                                    'time_linux':time_edf+current_delta_time,
                                    'trial':trial,
                                    'screen':current_screen}
                                    dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                    elif split_line[2]=='THRESHOLDS' and current_screen in screen_dictation:
                        new_row = {'user':user,'type':'pupil_threshold',
                        'value':int(split_line[4]),
                        'time_linux':time_edf+current_delta_time,
                        'trial':trial,
                        'screen':current_screen}
                        dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                        new_row = {'user':user,'type':'cornea_threshold',
                        'value':int(split_line[5]),
                        'time_linux':time_edf+current_delta_time,
                        'trial':trial,
                        'screen':current_screen}
                        dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                elif current_screen in screen_dictation or current_screen==screen_pupil_calibration:
                    if state_edf=='not_started':
                        if split_line[0] == 'START':
                            time_edf = time_edf_to_time_linux_scale(split_line[1])
                            state_edf = 'started'
                            total_time_fixation = 0
                            total_time_blink = 0
                            longest_blink = 0
                            new_row = {'user':user,'type':'filepath',
                            'value':image_filepath,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            new_row = {'user':user,'type':'discard',
                            'value':1 if discard else 0,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            print(current_sorce_rect)
                            print(trial)
                            print(current_screen)
                            assert(current_screen==screen_pupil_calibration or sum(current_sorce_rect)>0 or (correct_trial_0 and trial in [1, 7, 9]))
                            source_rect_while_starting_fixation = current_sorce_rect
                            
                            time_start_capture = time_edf+current_delta_time
                            if current_screen==9:
                                c1,c2 = convert_image_to_screen_coordinates(chest_box_image[0], chest_box_image[1], current_dest_rect, current_sorce_rect)
                                c3,c4 = convert_image_to_screen_coordinates(chest_box_image[2], chest_box_image[3], current_dest_rect, current_sorce_rect)
                                chest_box_screen = [c1,c2,c3,c4]
                    elif state_edf=='started':
                        if split_line[0] == 'END':
                            time_edf = time_edf_to_time_linux_scale(split_line[1])
                            state_edf = 'not_started'
                            new_row = {'user':user,'type':'total_time_fixation',
                            'value':total_time_fixation,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            new_row = {'user':user,'type':'total_time_blink',
                            'value':total_time_blink,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            new_row = {'user':user,'type':'total_time_capture',
                            'value':(time_edf+current_delta_time)-time_start_capture,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            new_row = {'user':user,'type':'longest_blink',
                            'value':longest_blink,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            if total_time_fixation>0:
                                ratio_blink_fixation = total_time_blink/total_time_fixation
                            else:
                                ratio_blink_fixation = None
                                
                            new_row = {'user':user,'type':'ratio_blink_fixation',
                            'value':ratio_blink_fixation,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            if ((time_edf+current_delta_time)-time_start_capture)>0:
                                ratio_blink_total = total_time_blink/((time_edf+current_delta_time)-time_start_capture)
                            else:
                                ratio_blink_total = None
                            new_row = {'user':user,'type':'ratio_blink_total',
                            'value':ratio_blink_total,
                            'time_linux':time_edf+current_delta_time,
                            'trial':trial,
                            'screen':current_screen}
                            dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                            
                            if skip_after_pupil:
                                print(current_pupil_normalization)
                                pupil_normalization = np.sum(np.array(current_pupil_normalization)*np.array(current_pupil_normalization_times)/np.sum(current_pupil_normalization_times))
                                assert(pupil_normalization>0)
                                return pupil_normalization, dfs
                        elif current_screen in screen_dictation:
                            if split_line[0] == 'SFIX':
                                assert(current_screen==screen_pupil_calibration or sum(current_sorce_rect)>0 or (correct_trial_0 and trial in [1, 7, 9]))
                                source_rect_while_starting_fixation = current_sorce_rect
                            if split_line[0] == 'EFIX':
                                if not ((sum(source_rect_while_starting_fixation)==0 or sum(current_dest_rect)==0) and correct_trial_0):
                                    eye = split_line[1]
                                    time_start = time_edf_to_time_linux_scale(split_line[2])+current_delta_time
                                    time_end = time_edf_to_time_linux_scale(split_line[3])+current_delta_time
                                    pupil_size = float(split_line[7])
                                    position_x_screen = float(split_line[5])
                                    position_y_screen = float(split_line[6])
                                    angular_resolution_x_screen = float(split_line[8])
                                    angular_resolution_y_screen = float(split_line[9])
                                    total_time_fixation = total_time_fixation + (time_end - time_start)
                                    position_x, position_y = convert_screen_to_image_coordinates(position_x_screen, position_y_screen, current_dest_rect, source_rect_while_starting_fixation)
                                    image_pixels_per_screen_pixel_x = (source_rect_while_starting_fixation[2]-source_rect_while_starting_fixation[0])/(current_dest_rect[2]-current_dest_rect[0])
                                    image_pixels_per_screen_pixel_y = (source_rect_while_starting_fixation[3]-source_rect_while_starting_fixation[1])/(current_dest_rect[3]-current_dest_rect[1])
                                    assert(type(current_pupil_normalization)==type(np.mean([0.0])))
                                    
                                    new_row = {'user':user,'type':'fixation',
                                    'value':None,
                                    'time_linux':time_end,
                                    'trial':trial,
                                    'screen':current_screen,
                                    'time_start_linux':time_start,
                                    'position_x':position_x,
                                    'position_y':position_y,
                                    'pupil_size':pupil_size,
                                    'pupil_size_normalization':current_pupil_normalization,
                                    'angular_resolution_x':angular_resolution_x_screen*image_pixels_per_screen_pixel_x, #screen pixels per visual degree, *image pixels per screen pixels
                                    'angular_resolution_y':angular_resolution_y_screen*image_pixels_per_screen_pixel_y,
                                    'window_width':current_window_width,
                                    'window_level':current_window_level,
                                    'zoom_level':current_zoom,
                                    'center_screen_x':(source_rect_while_starting_fixation[0]+source_rect_while_starting_fixation[2])/2,
                                    'center_screen_y':(source_rect_while_starting_fixation[1]+source_rect_while_starting_fixation[3])/2,
                                    'eye':eye, 
                                    'source_rect_dimension_1':source_rect_while_starting_fixation[0], 
                                    'source_rect_dimension_2':source_rect_while_starting_fixation[1],
                                    'source_rect_dimension_3':source_rect_while_starting_fixation[2], 
                                    'source_rect_dimension_4':source_rect_while_starting_fixation[3], 
                                    'dest_rect_dimension_1':current_dest_rect[0], 
                                    'dest_rect_dimension_2':current_dest_rect[1],
                                    'dest_rect_dimension_3':current_dest_rect[2],
                                    'dest_rect_dimension_4':current_dest_rect[3]}
                                    
                                    dfs[current_screen] = dfs[current_screen].append(new_row, ignore_index=True)
                                    
                                    screen_fixations_by_screen[current_screen].append([position_x_screen, position_y_screen, time_end])
                                    image_fixations_by_screen[current_screen].append([position_x,position_y, time_end])
                                    source_rect_while_starting_fixation = None
                            elif split_line[0] == 'EBLINK':
                                time_start = time_edf_to_time_linux_scale(split_line[2])+current_delta_time
                                time_end = time_edf_to_time_linux_scale(split_line[3])+current_delta_time
                                total_time_blink = total_time_blink + (time_end - time_start)
                                longest_blink = max(longest_blink, (time_end - time_start))
                        elif current_screen==screen_pupil_calibration:
                            if split_line[0] == 'EFIX':
                                position_x_screen = float(split_line[5])
                                position_y_screen = float(split_line[6])
                                angular_resolution_x_screen = float(split_line[8])
                                angular_resolution_y_screen = float(split_line[9])
                                time_start = time_edf_to_time_linux_scale(split_line[2])+current_delta_time
                                time_end = time_edf_to_time_linux_scale(split_line[3])+current_delta_time
                                print(angular_resolution_x_screen)
                                print(angular_resolution_y_screen)
                                print(math.sqrt(((position_x_screen-1920)/angular_resolution_x_screen)**2+((position_y_screen-1080)/angular_resolution_y_screen)**2))
                                if math.sqrt(((position_x_screen-1920)/angular_resolution_x_screen)**2+((position_y_screen-1080)/angular_resolution_y_screen)**2)<=2:
                                    current_pupil_normalization_times.append(time_end-time_start)
                                    current_pupil_normalization.append(float(split_line[7]))
    
    for screen in screen_fixations_by_screen.keys():
        screen_fixations = screen_fixations_by_screen[screen]
        image_fixations = image_fixations_by_screen[screen]
        if screen in [2,7,9]:
            last_fixation_in_margin  =None
            best_fixation_in_margin = None
            time_last_fixation = screen_fixations[-1][-1]
            for fixation in screen_fixations:
                px,py, timestamp = fixation
                if px<660:
                    last_fixation_in_margin = [px,py]
                    if time_last_fixation-timestamp<3/60/60/24:
                        current_distance_to_center = distance([px,py],center_next)
                        if (best_fixation_in_margin is None or current_distance_to_center<best_distance_to_center):
                            best_fixation_in_margin = [px,py]
                            best_distance_to_center = current_distance_to_center
            for key_, value_ in {'last':last_fixation_in_margin, 'best':best_fixation_in_margin}.items():
                if value_ is not None:
                    value = distance_point_rectangle(value_,next_rect)
                else: 
                    value = None
                new_row = {'user':user, 'type':key_+ '_distance_to_next_rect',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                
                if value_ is not None:
                    value = distance_point_rectangle([value_[0],center_next[1]],next_rect)
                else:
                    value=None
                new_row = {'user':user, 'type':key_ + '_distance_to_next_rect_x',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                
                if value_ is not None:
                    value = distance_point_rectangle([center_next[0],value_[1]],next_rect)
                else: 
                    value = None
                new_row = {'user':user, 'type':key_ + '_distance_to_next_rect_y',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                
                if value_ is not None:
                    value = distance([value_[0],center_next[1]],center_next)
                else: 
                    value = None
                new_row = {'user':user, 'type': key_ + '_distance_to_next_center_x',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                
                if value_ is not None:
                    value = distance([center_next[0],value_[1]],center_next)
                else: 
                    value = None
                new_row = {'user':user, 'type':key_ + '_distance_to_next_center_y',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
                
                if value_ is not None:
                    value = distance(value_,center_next)
                else: 
                    value = None
                new_row = {'user':user, 'type':key_ + '_distance_to_next_center',
                'value':value,
                'time_linux':None,
                'trial':trial,
                'screen':screen}
                dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
    
        if screen==9:
            distance_fixations = []
            distance_fixations_x= []
            distance_fixations_y = []
            for fixation in screen_fixations:
                distance_fixations.append(nearest_distance(chest_box_screen,fixation[:2]))
                distance_fixations_x.append(nearest_distance(chest_box_screen,[fixation[0],chest_box_screen[1]]))
                distance_fixations_y.append(nearest_distance(chest_box_screen,[chest_box_screen[0],fixation[1]]))
                
            distance_fixations = np.array(distance_fixations)
            value = np.min(distance_fixations)
            new_row = {'user':user, 'type':'min_distance_to_chest_box',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            value = np.mean(distance_fixations)
            new_row = {'user':user, 'type':'average_distance_to_chest_box',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            
            distance_fixations_x = np.array(distance_fixations_x)
            value = np.min(distance_fixations_x)
            new_row = {'user':user, 'type':'min_distance_to_chest_box_x',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            value = np.mean(distance_fixations_x)
            new_row = {'user':user, 'type':'average_distance_to_chest_box_x',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            
            distance_fixations_y = np.array(distance_fixations_y)
            value = np.min(distance_fixations_y)
            new_row = {'user':user, 'type':'min_distance_to_chest_box_y',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            value = np.mean(distance_fixations_y)
            new_row = {'user':user, 'type':'average_distance_to_chest_box_y',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
    
        if screen==2:
            total_inside = 0
            total_inside_x = 0
            total_inside_y = 0
            total_fixations = 0
            for fixation in image_fixations:
                if check_inside_rect(fixation[:2], chest_box_image):
                    total_inside+=1
                if check_inside_rect([fixation[0],chest_box_image[1]], chest_box_image):
                    total_inside_x+=1
                if check_inside_rect([chest_box_image[0],fixation[1]], chest_box_image):
                    total_inside_y+=1
                total_fixations+=1
            value = total_inside/float(total_fixations)
            new_row = {'user':user, 'type':'percentage_inside_chest_box',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            
            value = total_inside_x/float(total_fixations)
            new_row = {'user':user, 'type':'percentage_inside_chest_box_x',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
            
            value = total_inside_y/float(total_fixations)
            new_row = {'user':user, 'type':'percentage_inside_chest_box_y',
            'value':value,
            'time_linux':None,
            'trial':trial,
            'screen':screen}
            dfs[-1] = dfs[-1].append(new_row, ignore_index=True)
    print(current_pupil_normalization)
    print(current_pupil_normalization_times)
    pupil_normalization = np.sum(np.array(current_pupil_normalization)*np.array(current_pupil_normalization_times)/np.sum(current_pupil_normalization_times))
    assert(pupil_normalization>0)
    return pupil_normalization, dfs

def create_csv_gaze_phase_2():
    root_folders = 'anonymized_collected_data/phase_2/'
    data_folders = ['user2_204_20210308-080302-9152',
    'user1_204_20210301-141046-2142',
    'user1_204_20210301-143153-9220',
    'user4_204_20210303-133107-9152',
    'user5_204_20210302-142915-8332', 
    'user5_204_20210302-145812-8332',  
    'user3_204_20210311-101017-9152',
    'user3_204_20210311-121106-2142' ]
    results_df = pd.read_csv('./results_phase_2.csv')
    discard_df = pd.read_csv('./discard_cases.csv')
    discard_df = discard_df[discard_df['phase'] == 2]
    dfs = defaultdict(lambda: pd.DataFrame(columns=columns_csv))
    for folder in data_folders:
        user = folder.split('_')[0]
        print(results_df)
        results_df_this_user = results_df[results_df['user']==user]
        print(results_df_this_user)
        discard_df_this_user = discard_df[discard_df['user']==user]
        pupil_normalization, trial_csv = ASC2CSV(root_folders+folder+'/inpupil.asc', user, None,screen_dictation=[-1], screen_pupil_calibration=2)
        for trial_csv_key in trial_csv.keys():
            dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
        for trial in range(1,51):
            results_df_this_user_this_trial = results_df_this_user[results_df_this_user['trial']!='all']
            
            results_df_this_user_this_trial = results_df_this_user_this_trial[results_df_this_user_this_trial['trial'].values.astype(float)==trial]
            
            discard_df_this_user_this_trial = discard_df_this_user[discard_df_this_user['trial'].values.astype(float)==trial]
            
            chestbox_df_this_trial = results_df_this_user_this_trial[list(map(lambda x: x.startswith('ChestBox (Rectangle) coord'), results_df_this_user_this_trial['title']))]
            
            x1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 0']['value'].values[0])
            y1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 1']['value'].values[0])
            x2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 2']['value'].values[0])
            y2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 3']['value'].values[0])
            chest_box_image = [x1,y1,x2,y2]
            if user == 'user1':
                list_of_et_suffix = ['']
            else:
                list_of_et_suffix = ['', 'pt2']
            for et_suffix in list_of_et_suffix:
                trial_filename = root_folders+folder+'/et'+str(trial)+et_suffix+'.asc'
                if os.path.isfile(trial_filename):
                    image_filepath = results_df_this_user_this_trial[results_df_this_user_this_trial['title']=='filepath']['value'].values
                    assert(len(image_filepath)==1)
                    image_filepath = '/'.join(image_filepath[0].split('/')[image_filepath[0].split('/').index('physionet.org'):])
                    print(image_filepath)
                    pupil_normalization, trial_csv = ASC2CSV(trial_filename, user, pupil_normalization, correct_trial_0 = False, chest_box_image = chest_box_image, image_filepath = image_filepath, discard = len(discard_df_this_user_this_trial)>0)
                    for trial_csv_key in trial_csv.keys():
                        dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
    df = pd.DataFrame(columns=columns_csv)
    for dfs_key in dfs.keys():
        df = df.append(dfs[dfs_key])
    df.to_csv('./summary_edf_phase_2.csv')

def create_csv_gaze_phase_3():
    root_folders = ''
    data_folders = glob.glob("anonymized_collected_data/phase_3/*/")
    results_df = pd.read_csv('./results_phase_3.csv')
    discard_df = pd.read_csv('./discard_cases.csv')
    discard_df = discard_df[discard_df['phase'] == 3]
    dfs = defaultdict(lambda: pd.DataFrame(columns=columns_csv))
    for folder in data_folders:
        user = folder.split('/')[-2].split('_')[0]
        print(user)
        results_df_this_user = results_df[results_df['user']==user]
        discard_df_this_user = discard_df[discard_df['user']==user]
        pupil_normalization, trial_csv = ASC2CSV(root_folders+folder+'/inpupil.asc', user, None,screen_dictation=[-1], screen_pupil_calibration=2)
        for trial_csv_key in trial_csv.keys():
            dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
        for trial in range(1,550):
            print(trial)
            results_df_this_user_this_trial = results_df_this_user[results_df_this_user['trial']!='all']
            results_df_this_user_this_trial = results_df_this_user_this_trial[results_df_this_user_this_trial['trial'].values.astype(float)==trial]
            discard_df_this_user_this_trial = discard_df_this_user[discard_df_this_user['trial'].values.astype(float)==trial]
            if len(results_df_this_user_this_trial)==0 and len(discard_df_this_user_this_trial)>0:
                continue
            chestbox_df_this_trial = results_df_this_user_this_trial[list(map(lambda x: x.startswith('ChestBox (Rectangle) coord'), results_df_this_user_this_trial['title']))]
            if len(chestbox_df_this_trial)==0:
                x1 = None
                y1 = None
                x2 = None
                y2 = None
            else:
                x1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 0']['value'].values[0])
                y1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 1']['value'].values[0])
                x2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 2']['value'].values[0])
                y2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 3']['value'].values[0])
            chest_box_image = [x1,y1,x2,y2]
            list_of_et_suffix = ['', 'pt2']
            for et_suffix in list_of_et_suffix:
                trial_filename = root_folders+folder+'/et'+str(trial)+et_suffix+'.asc'
                if os.path.isfile(trial_filename):
                    image_filepath = results_df_this_user_this_trial[results_df_this_user_this_trial['title']=='filepath']['value'].values
                    assert(len(image_filepath)==1)
                    image_filepath = '/'.join(image_filepath[0].split('/')[image_filepath[0].split('/').index('physionet.org'):])
                    print(image_filepath)
                    pupil_normalization, trial_csv = ASC2CSV(trial_filename, user, pupil_normalization, correct_trial_0 = False, chest_box_image = chest_box_image, image_filepath = image_filepath, discard = len(discard_df_this_user_this_trial)>0)
                    for trial_csv_key in trial_csv.keys():
                        dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
    df = pd.DataFrame(columns=columns_csv)
    for dfs_key in dfs.keys():
        df = df.append(dfs[dfs_key])
    df.to_csv('./summary_edf_phase_3.csv')

def create_csv_gaze_phase_1():
    root_folders = 'anonymized_collected_data/phase_1/'
    data_folders = [ 'user3_203_20201210-101303-6691',
    'user3_203_20201217-083511-9152', 
    'user5_203_20201113', 
    'user2_203_20201201-092234-9617', 
    'user1_203_20201216-141859-3506',
     'user1_203_20201216-142259-5921',
      'user1_203_20201218-142722-8332', 
      'user1_203_20201223-140239-9152', 
      'user4_203_20201222-150420-9152', 
      'user4_203_20210104-130049-9152']
    results_df = pd.read_csv('./results_phase_1.csv')
    discard_df = pd.read_csv('./discard_cases.csv')
    discard_df = discard_df[discard_df['phase'] == 1]
    dfs = defaultdict(lambda: pd.DataFrame(columns=columns_csv))
    for folder in data_folders:
        user = folder.split('_')[0]
        results_df_this_user = results_df[results_df['user']==user]
        discard_df_this_user = discard_df[discard_df['user']==user]
        if user == 'user5':
            pupil_normalization, trial_csv = ASC2CSV(root_folders+folder+'/et0.asc', user, None,screen_dictation=[-1], screen_pupil_calibration=2, skip_after_pupil = True )
        else:
            pupil_normalization, trial_csv = ASC2CSV(root_folders+folder+'/inpupil.asc', user, None,screen_dictation=[-1], screen_pupil_calibration=2)
        for trial_csv_key in trial_csv.keys():
            dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
        for trial in range(1,61):
            if user=='user5' and trial in [1, 7, 9]:
                pupil_normalization, trial_csv = ASC2CSV(root_folders+folder+f'/et{trial-1}.asc', user, None,screen_dictation=[-1], screen_pupil_calibration=2, skip_after_pupil = True )
            results_df_this_user_this_trial = results_df_this_user[results_df_this_user['trial']!='all']
            results_df_this_user_this_trial = results_df_this_user_this_trial[results_df_this_user_this_trial['trial'].values.astype(float)==trial]
            
            discard_df_this_user_this_trial = discard_df_this_user[discard_df_this_user['trial'].values.astype(float)==trial]
            
            if trial>1:
                chestbox_df_this_trial = results_df_this_user_this_trial[list(map(lambda x: x.startswith('ChestBox (Rectangle) coord'), results_df_this_user_this_trial['title']))]
                x1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 0']['value'].values[0])
                y1 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 1']['value'].values[0])
                x2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 2']['value'].values[0])
                y2 = float(chestbox_df_this_trial[chestbox_df_this_trial['title']=='ChestBox (Rectangle) coord 3']['value'].values[0])
                chest_box_image = [x1,y1,x2,y2]
            else:
                chest_box_image = [0,0,0,0]
            trial_filename = root_folders+folder+'/et'+str(trial - (1 if user=='user5' else 0))+'.asc'
            if os.path.isfile(trial_filename):
                image_filepath = results_df_this_user_this_trial[results_df_this_user_this_trial['title']=='filepath']['value'].values
                assert(len(image_filepath)==1)
                image_filepath = '/'.join(image_filepath[0].split('/')[image_filepath[0].split('/').index('physionet.org'):])
                print(image_filepath)
                pupil_normalization, trial_csv = ASC2CSV(trial_filename, user, pupil_normalization, correct_trial_0 = user=='user5', chest_box_image = chest_box_image, image_filepath = image_filepath, discard = len(discard_df_this_user_this_trial)>0)
                for trial_csv_key in trial_csv.keys():
                    dfs[user] = dfs[user].append(trial_csv[trial_csv_key], ignore_index=True)
    df = pd.DataFrame(columns=columns_csv)
    for dfs_key in dfs.keys():
        df = df.append(dfs[dfs_key])
    df.to_csv('./summary_edf_phase_1.csv')

if __name__ == '__main__':
    create_csv_gaze_phase_1()
    create_csv_gaze_phase_2()
    # create_csv_gaze_phase_3()