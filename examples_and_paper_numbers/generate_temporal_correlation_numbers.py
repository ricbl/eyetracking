# file generating the data for the graph from Figure 4, where the temporal
# correlation between the location of fixations and the mentions of 
# abnormalities.

import shapely
import shapely.geometry as geometry
from heaviside_sum import SumHeavisides
import pandas as pd
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed
from dataset_locations import reflacx_dataset_location
def create_ellipse(coords_box_):
    coords_box = []
    coords_box.append((coords_box_[0]+coords_box_[2])/2)
    coords_box.append((coords_box_[1]+coords_box_[3])/2)
    coords_box.append(abs(coords_box_[0]-coords_box_[2])/2)
    coords_box.append(abs(coords_box_[1]-coords_box_[3])/2)
    rect = coords_box
    center = (rect[0],rect[1])
    axis = (rect[2],rect[3])
    point = geometry.point.Point(center).buffer(1)
    ellipse = shapely.affinity.scale(point, int(axis[0]), int(axis[1]))
    return ellipse

def check_inside_ellipse(coords_p,ellipse):
    return geometry.Point(coords_p[0], coords_p[1]).within(ellipse)

# do linear interpolation to generate the sentence unit
# sentence unit = current sentence + timestamp/(timestamp end sentence - timestamp start sentence)
def process_output(the_tuple, current_sentence, word_end):
    return the_tuple[0]+the_tuple[1]/(the_tuple[3] - the_tuple[2])

def get_S_index(transcriptions, timestamp):
    last_was_period = True
    timestamp_found = False
    end_previous_sentence = 0.
    current_sentence = 0
    for index_word,row in transcriptions.iterrows():
        word = row['word']
        if not timestamp_found and timestamp <= row['timestamp_start_word']:
            time_in_sentence = timestamp - end_previous_sentence
            timestamp_found = True
        if last_was_period:
            if timestamp_found:
                sentence_end = row['timestamp_start_word'] 
                sentence_start = end_previous_sentence
                break
            last_was_period = False
            end_previous_sentence = row['timestamp_start_word']
            # end of pause. Starting a new sentence
            current_sentence += 1
        last_was_period = False
        #sentences are delimited by periods
        if word == '.':
            if timestamp_found:
                sentence_end = row['timestamp_start_word'] 
                sentence_start = end_previous_sentence
                break
            # end of sentence. Starting a new pause
            current_sentence += 1
            last_was_period = True
            end_previous_sentence = row['timestamp_start_word']
    return current_sentence, time_in_sentence, sentence_start, sentence_end

# for each case
def get_sampled_heavisides(labels_chars_table, sampled_indices, n_bins_t, n_bins_s, limit_graph_x_t = None, limit_graph_x_s = None):
    data_folder = reflacx_dataset_location + '/main_data/'
    list_label = {"fracture": "acute fracture & fracture",
                  "acute fracture": "acute fracture & fracture",
                  "airway wall thickening": "airway wall thickening",
                  "atelectasis":"atelectasis",
                  "consolidation":"consolidation",
                  "enlarged cardiac silhouette":"enlarged cardiac silhouette",
                  "enlarged hilum":"enlarged hilum",
                  "groundglass opacity":"groundglass opacity",
                  "hiatal hernia":"hiatal hernia",
                  "high lung volume / emphysema":"high lung volume - emphysema & emphysema",
                  "emphysema":"high lung volume - emphysema & emphysema",
                  "interstitial lung disease":"interstitial lung disease & fibrosis",
                  "fibrosis":"interstitial lung disease & fibrosis",
                  "lung nodule or mass":"lung nodule or mass",
                  "mass":"mass",
                  "nodule":"nodule",
                  "pleural abnormality":"pleural abnormality",
                  "pleural effusion":"pleural effusion",
                  "pleural thickening":"pleural thickening",
                  "pneumothorax":"pneumothorax",
                  "pulmonary edema":"pulmonary edema",
                  "abnormal mediastinal contour":"wide mediastinum & abnormal mediastinum contour",
                  "wide mediastinum":"wide mediastinum & abnormal mediastinum contour"}
    list_label = {"acute fracture","airway wall thickening","atelectasis",
                  "consolidation","enlarged cardiac silhouette",
                  "enlarged hilum","groundglass opacity","hiatal hernia",
                  "high lung volume / emphysema",
                  "interstitial lung disease","lung nodule or mass",
                  "pleural abnormality","pleural effusion","pleural thickening",
                  "pneumothorax","pulmonary edema",
                  "abnormal mediastinal contour"}
    # stores fixations inside ellipses using units of time (s)
    heavisides_Ti0 = SumHeavisides()
    
    # stores fixations inside ellipses using sentence units
    heavisides_Si0 = SumHeavisides()
    
    # stores all fixations using units of time (s)
    heavisides_all_fixations_Ti0 = SumHeavisides()
    
    # stores all fixations using sentence units
    heavisides_all_fixations_Si0 = SumHeavisides()
    
    for index_case in sampled_indices:
        case = labels_chars_table.iloc[index_case]
        # print(index_case)
        heavisides_this_case_Ti0 = SumHeavisides()
        heavisides_this_case_Si0 = SumHeavisides()
        heavisides_this_case_all_fixations_Ti0 = SumHeavisides()
        heavisides_this_case_all_fixations_Si0 = SumHeavisides()
        transcription = pd.read_csv(f'{data_folder}/{case["IDs"]}/timestamps_transcription.csv')
        fixations = pd.read_csv(f'{data_folder}/{case["IDs"]}/fixations.csv')
        ellipses_df = pd.read_csv(f'{data_folder}/{case["IDs"]}/anomaly_location_ellipses.csv')
        with open(f'{data_folder}/{case["IDs"]}/transcription.txt', 'r') as f:
            report_original = f.readlines()[0].strip()
        ellipses_df.columns= ellipses_df.columns.str.lower()
        row_chexpert = labels_chars_table.iloc[index_case]
        indices_stop = [index_char for index_char, char in enumerate(report_original) if char == '.']
        indices_stop_by_word = [index_word for index_word, row in transcription.iterrows() if row['word'] == '.']
        
        #find the timestamps and locations of each mention of presence of a label in the report
        positive_vocalizations = defaultdict(list)
        total_labels = 0
        for et_label in list_label:
            if f'{et_label.lower()}_location' in row_chexpert:
                total_labels+=1
                if len(row_chexpert[f'{et_label.lower()}_location'])>2:
                    for current_range in row_chexpert[f'{et_label.lower()}_location'].strip('][').replace('], [', '],[').split('],['):
                        current_range = current_range.split(',')
                        current_range = [int(item) for item in current_range]
                        for index_sentence, index_stop in enumerate(indices_stop):
                            if current_range[0]<index_stop:
                                current_sentence = index_sentence
                                break
                        assert(current_range[1]<=indices_stop[current_sentence])
                        if current_sentence>0:
                            assert(current_range[0]>indices_stop[current_sentence-1])
                        total_characters = 0.
                        vocalization_started = False
                        for index_word,row in transcription.iterrows():
                            word = row['word']
                            total_characters += len(word) + 1
                            if word == '.' or word == ',' or word == ':':
                                total_characters-=1
                            if not vocalization_started and total_characters-len(word)-1>=current_range[0]:
                                start_word = row['timestamp_start_word']
                                vocalization_started = True
                            if vocalization_started and total_characters-1>=current_range[1]:
                                end_word = row['timestamp_end_word']
                                break
                        end_sentence = transcription.iloc[indices_stop_by_word[current_sentence]]['timestamp_end_word']
                        start_sentence = transcription.iloc[(indices_stop_by_word[current_sentence-1] if current_sentence > 0 else -1)+1]['timestamp_start_word']
                        assert(end_sentence>=end_word)
                        assert(start_sentence<=start_word)
                        positive_vocalizations[et_label].append([start_word, end_word, current_sentence, start_sentence, end_sentence])
            
            if len(positive_vocalizations[et_label])>0:
                heavisides_this_label_Ti0 = SumHeavisides()
                heavisides_this_label_Si0 = SumHeavisides()
                heavisides_this_label_all_fixations_Ti0 = SumHeavisides()
                heavisides_this_label_all_fixations_Si0 = SumHeavisides()
                ellipses_df_this_label = ellipses_df[ellipses_df[et_label]]
                assert(len(ellipses_df_this_label)>0)
                ellipses = []
                for index_ellipse, ellipse in ellipses_df_this_label.iterrows():
                    ellipses.append(create_ellipse([ellipse['xmin'], ellipse['ymin'], ellipse['xmax'], ellipse['ymax']]))
                # for each occurrence of the positive label
                for positive_vocalization in positive_vocalizations[et_label]:
                    timestamp_end_word = positive_vocalization[1]
                    current_sentence = positive_vocalization[2]
                    processed_timestamp_end_word = process_output(get_S_index(transcription, timestamp_end_word), current_sentence, timestamp_end_word)
                    total_fixations = 0
                    # for each fixation
                    for index_fixation, row in fixations.iterrows():
                        timestamp_start_fixations = row['timestamp_start_fixation']
                        if timestamp_start_fixations>timestamp_end_word:
                            break
                        processed_timestamp_start_fixations = process_output(get_S_index(transcription, timestamp_start_fixations), current_sentence, timestamp_end_word)
                        timestamp_end_fixations = row['timestamp_end_fixation']
                        timestamp_end_fixations = min(timestamp_end_fixations,timestamp_end_word)
                        S_index_end_fixations = get_S_index(transcription, timestamp_end_fixations)
                        processed_timestamp_end_fixations = process_output(S_index_end_fixations, current_sentence, timestamp_end_word) 
                        x_fixation = row['x_position']
                        y_fixation = row['y_position']
                        
                        inside_ellipses = False
                        for ellipse in ellipses:
                            if check_inside_ellipse([x_fixation,y_fixation],ellipse):
                                inside_ellipses = True
                        amplitude = 1.
                        
                        # word mention in interval from a to b
                        # calculate heaviside interval and total time for Ti0
                        b = (timestamp_end_word - timestamp_start_fixations)
                        a = (timestamp_end_word - timestamp_end_fixations)
                        if inside_ellipses:
                            heavisides_this_label_Ti0.add_heaviside(a,b,amplitude)
                        heavisides_this_label_all_fixations_Ti0.add_heaviside(a,b,amplitude)
                        
                        if S_index_end_fixations[0]>-1:
                            # calculate heaviside interval and total time for Si0
                            b = processed_timestamp_end_word - processed_timestamp_start_fixations
                            a = processed_timestamp_end_word - processed_timestamp_end_fixations
                            if inside_ellipses:
                                heavisides_this_label_Si0.add_heaviside(a,b,amplitude)
                            heavisides_this_label_all_fixations_Si0.add_heaviside(a,b,amplitude)
                        total_fixations += 1
                if total_fixations>0:
                    # add to heaviside
                    heavisides_this_case_Ti0.join_heaviside(heavisides_this_label_Ti0)
                    heavisides_this_case_Si0.join_heaviside(heavisides_this_label_Si0)
                    heavisides_this_case_all_fixations_Ti0.join_heaviside(heavisides_this_label_all_fixations_Ti0)
                    heavisides_this_case_all_fixations_Si0.join_heaviside(heavisides_this_label_all_fixations_Si0)
        assert(total_labels==14)
        heavisides_Ti0.join_heaviside(heavisides_this_case_Ti0)
        heavisides_Si0.join_heaviside(heavisides_this_case_Si0)
        heavisides_all_fixations_Ti0.join_heaviside(heavisides_this_case_all_fixations_Ti0)
        heavisides_all_fixations_Si0.join_heaviside(heavisides_this_case_all_fixations_Si0)
    
    #sample the data into bins
    if limit_graph_x_t is None:
        interval_width = (heavisides_Ti0.interval_limits[-1])/n_bins_t
    else:
        interval_width = (limit_graph_x_t)/n_bins_t
    xt = []
    yt = []
    ntp = []
    nta = []
    for i in range(n_bins_t):
        x = interval_width*(i+0.5)
        yt.append(heavisides_Ti0.get_fn_at_interval(x, interval_width)[0]/heavisides_all_fixations_Ti0.get_fn_at_interval(x, interval_width)[0])
        ntp.append(heavisides_Ti0.get_fn_at_interval(x, interval_width)[1])
        nta.append(heavisides_all_fixations_Ti0.get_fn_at_interval(x, interval_width)[1])
        
        xt.append(x)
    xs = []
    ys = []
    nsp = []
    nsa = []
    if limit_graph_x_s is None:
        interval_width = (heavisides_Si0.interval_limits[-1])/n_bins_s
    else:
        interval_width = (limit_graph_x_s)/n_bins_s
    for i in range(n_bins_s):
        x = interval_width*(i+0.5)
        ys.append(heavisides_Si0.get_fn_at_interval(x, interval_width)[0]/heavisides_all_fixations_Si0.get_fn_at_interval(x, interval_width)[0])
        nsp.append(heavisides_Si0.get_fn_at_interval(x, interval_width)[1])
        nsa.append(heavisides_all_fixations_Si0.get_fn_at_interval(x, interval_width)[1])
        xs.append(x)
    return xt, yt, nta, ntp, xs, ys, nsa, nsp

def parallel_fn(i,n_bins_t, n_bins_s, limit_xt, limit_xs):
    print(i)
    labels_chars_table = pd.read_csv(f'./manually_labeled_reports_3.csv')
    #samples from images with replacement
    new_indices = np.random.choice(range(len(labels_chars_table)), size=len(labels_chars_table), replace=True)
    _, yt_, _, _, _, ys_, _, _ = get_sampled_heavisides(labels_chars_table, new_indices, n_bins_t, n_bins_s, limit_xt, limit_xs)
    return yt_, ys_

if __name__=='__main__':
    labels_chars_table = pd.read_csv(f'./manually_labeled_reports_3.csv')
    
    #get an analysis with 75 bins over the full length of data
    xt, yt, nta, ntp, xs, ys, nsa, nsp = get_sampled_heavisides(labels_chars_table, range(len(labels_chars_table)),75, 75)
    
    #find which bins were the first to have less than 11 positive samples to 
    # limit the data to before that point
    for index_t in range(len(ntp)):
        if ntp[index_t]<=10:
            n_bins_t = index_t
            limit_xt = xt[n_bins_t-1]+xt[0]
            break
    for index_s in range(len(nsp)):
        if nsp[index_s]<=10:
            n_bins_s = index_s
            limit_xs = xs[n_bins_s-1]+xs[0]
            break
    
    xt, yt, nta, ntp, xs, ys, nsa, nsp = get_sampled_heavisides(labels_chars_table, range(len(labels_chars_table)), n_bins_t, n_bins_s, limit_xt, limit_xs)
    
    with open('xt.npy', 'wb') as f:
        np.save(f, np.array(xt))
    with open('yt.npy', 'wb') as f:
        np.save(f, np.array(yt))
    with open('nta.npy', 'wb') as f:
        np.save(f, np.array(nta))
    with open('ntp.npy', 'wb') as f:
        np.save(f, np.array(ntp))
    with open('xs.npy', 'wb') as f:
        np.save(f, np.array(xs))
    with open('ys.npy', 'wb') as f:
        np.save(f, np.array(ys))
    with open('nsa.npy', 'wb') as f:
        np.save(f, np.array(nsa))
    with open('nsp.npy', 'wb') as f:
        np.save(f, np.array(nsp))
    
    bootstrapping_output = Parallel(n_jobs=25)(delayed(parallel_fn)(i, n_bins_t, n_bins_s, limit_xt, limit_xs) for i in range(800))
    yts, yss = list(map(list, zip(*bootstrapping_output)))
    
    with open('yts.npy', 'wb') as f:
        np.save(f, np.array(yts))
    with open('yss.npy', 'wb') as f:
        np.save(f, np.array(yss))
    
    plt.plot(xt, yt)
    plt.plot(xt, np.percentile(np.array(yts), 2.5, axis = 0))
    plt.plot(xt, np.percentile(np.array(yts), 97.5, axis = 0))
    plt.savefig('./Ti0.png', bbox_inches='tight', pad_inches = 0)
    plt.cla()
    
    plt.plot(xs, ys)
    plt.plot(xs, np.percentile(np.array(yss), 2.5, axis = 0))
    plt.plot(xs, np.percentile(np.array(yss), 97.5, axis = 0))
    plt.savefig('./Si0.png', bbox_inches='tight', pad_inches = 0)
    plt.cla()
