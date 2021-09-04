import difflib
import json
import re
import pandas as pd
from collections import defaultdict
import os
import pickle
import numpy as np
import glob
from copy import  copy
from decimal import Decimal
import syllables
from nltk.corpus import cmudict
cmudict_dict = cmudict.dict()
  
list_of_users = sorted(['user1','user2','user3','user4','user5'])

def inverse_replace_punctuation(input_string):
    if input_string=='.':
        return 'period'
    if input_string==',':
        return 'comma'
    if input_string=='/':
        return 'slash'
    return input_string

def replace_punctuation(input_string):
    if input_string=='period':
        return '.'
    if input_string=='comma':
        return ','
    if input_string=='slash':
        return '/'
    return input_string

def split_punctuation_from_words(transcription):
    # print(transcription)
    return transcription.replace('.',' .').replace(',',' ,').replace('/',' / ').replace('  ',' ').replace('  ',' ')

def get_diff(string_real, string_google):
    string_google = string_google.split(' ')
    string_real = split_punctuation_from_words(string_real).split(' ')
    return list(difflib.ndiff(string_google,string_real))
    
def ge(x,y):
    return x>=y

def le(x,y):
    return x<=y

def g(x,y):
    return x>y

def l(x,y):
    return x<y

def get_timestamp_from_float_index(list_words, float_index, stick_following):
    current_index = 0
    next_index = 0
    if stick_following:
        compare_next = g
        compare_current = le 
    else:
        compare_next = ge
        compare_current = l
    for word in list_words:
        num_sylables = get_n_syllables(word[0])
        next_index += num_sylables
        if compare_current(current_index,float_index) and compare_next(next_index, float_index):
            return round((word[2]-word[1])/(next_index-current_index)*(float_index-current_index) + word[1], 2)
        current_index = next_index
    print(current_index)
    print(list_words)
    print(float_index)
    print(stick_following)
    assert(False)

def get_n_syllables(word):
    word = inverse_replace_punctuation(word)
    word = word.lower()
    if word in cmudict_dict.keys():
        return sum(map(lambda x : x[-1].isdigit(), cmudict_dict[word][0]))
    else:
        return syllables.estimate(word)
    # return len(instance.syllabify_en(word)) - len(word)-1

from fractions import Fraction
def get_ratio_syllables_removed_vs_added(added_words,removed_words):
    total_sylables_removed = 0
    for removed_word in removed_words:
        num_sylables = get_n_syllables(removed_word[0])
        total_sylables_removed += num_sylables
    total_sylables_added = 0
    for added_word in added_words:
        num_sylables = get_n_syllables(added_word)
        total_sylables_added += num_sylables
    return Fraction(total_sylables_removed,total_sylables_added)

def adjust_timestamps_form_removed_to_added(added_words,removed_words,result_timestamps,json_ibm,index_ibm):
    if len(removed_words)==0:
        if index_ibm>len(json_ibm)-1:
            removed_words = [["dummy",json_ibm[index_ibm-1][2],json_ibm[index_ibm-1][2]]]
        elif index_ibm==0:
            removed_words = [["dummy",json_ibm[0][1],json_ibm[0][1]]]
        else:
            removed_words = [["dummy",json_ibm[index_ibm-1][2],json_ibm[index_ibm][1]]]
    if len(added_words) == 1:
        result_timestamps.append([added_words[0],removed_words[0][1],removed_words[-1][2]])
    elif len(added_words) == 0:
        pass
    else:
        ratio_sylables = get_ratio_syllables_removed_vs_added(added_words,removed_words)
        added_words_index = 0
        removed_words_index = 0
        result_timestamps_2 = copy(result_timestamps)
        for added_word in added_words:
            num_sylables = get_n_syllables(added_word)
            timestamp_start = get_timestamp_from_float_index(removed_words, removed_words_index, True)
            removed_words_index +=num_sylables*ratio_sylables
            added_words_index+=1
            timestamp_end = get_timestamp_from_float_index(removed_words, removed_words_index, False)
            assert(timestamp_end is not None)
            result_timestamps.append([added_word,timestamp_start,timestamp_end])
        # index_removed_word = 0
        # count_syllables_added = 0
        # for word in added_words:
        #     this_removed_word = removed_words[index_removed_word]
        #     this_removed_word_n_syllables = Fraction(get_n_syllables(this_removed_word[0]),ratio_sylables)
        #     timestamp_start = (this_removed_word[2]-this_removed_word[1])*count_syllables_added/this_removed_word_n_syllables+this_removed_word[1]
        #     count_syllables_added += get_n_syllables(word)
        #     while count_syllables_added > this_removed_word_n_syllables:
        #         count_syllables_added -= this_removed_word_n_syllables
        #         index_removed_word += 1
        #         this_removed_word_n_syllables = Fraction(get_n_syllables(removed_words[index_removed_word][0]),ratio_sylables)
        #     this_removed_word = removed_words[index_removed_word]
        #     timestamp_end = (this_removed_word[2]-this_removed_word[1])*count_syllables_added/this_removed_word_n_syllables+this_removed_word[1]
        #     result_timestamps_2.append([word,round(timestamp_start,2),round(timestamp_end,2)])
        # 
        #     # so that if words from both list are ending, you get the timestamp of the start of the following word
        #     if count_syllables_added == this_removed_word_n_syllables:
        #         count_syllables_added -= this_removed_word_n_syllables
        #         index_removed_word += 1
        # print(result_timestamps_2)
        # print(result_timestamps)
        # assert(result_timestamps_2==result_timestamps)
    return result_timestamps

def open_transcription_json_ibm(json_filename):
    with open(json_filename) as f:
        b = json.load(f)
        json_ibm = [[replace_punctuation(item[0].lower()), Fraction(round(item[1]*100),100), Fraction(round(item[2]*100),100)] for sublist in [b['results'][i]['alternatives'][0]['timestamps'] for i in range(len(b['results']))] for item in sublist ]
    return json_ibm

def add_delay_to_all_timestamps(timestamps, delay):
    print(delay)
    print(timestamps)
    return [[word[0],round(word[1]+delay,2),round(word[2]+delay,2)] for word in timestamps]

def align_timestamps(json_filename, string_real):
    json_ibm = open_transcription_json_ibm(json_filename)
    if len(json_ibm)==0:
        assert(len(string_real)==0)
        return []
    string_ibm = ' '.join([item[0].lower() for item in json_ibm])
    print(string_ibm)
    print(string_real)
    diff =get_diff(string_real, string_ibm)
    index_ibm = 0
    result_timestamps = []
    mid_diff = False
    added_words = []
    removed_words = []
    delta_index_ibm = 0
    
    for word in diff:
        if word[0] == '+':
            mid_diff = True
            added_words.append(word[2:])
        if word[0] == '-':
            mid_diff = True
            removed_words.append(json_ibm[index_ibm+delta_index_ibm])
            print(word[2:])
            print(json_ibm[index_ibm+delta_index_ibm][0])
            assert(word[2:] == json_ibm[index_ibm+delta_index_ibm][0])
            delta_index_ibm += 1
        if word[0] == ' ':
            if mid_diff:
                result_timestamps = adjust_timestamps_form_removed_to_added(added_words,removed_words,result_timestamps,json_ibm,index_ibm)
                added_words = []
                removed_words = []
                mid_diff = False
                index_ibm += delta_index_ibm
                delta_index_ibm = 0
            result_timestamps.append(json_ibm[index_ibm])
            assert(word[2:] == json_ibm[index_ibm][0])
            index_ibm += 1
        if word[0] == '?':
            pass
    if mid_diff: 
        result_timestamps = adjust_timestamps_form_removed_to_added(added_words,removed_words,result_timestamps,json_ibm,index_ibm)
    print(' '.join([word[0] for word in result_timestamps]))
    print(split_punctuation_from_words(string_real))
    assert(len(' '.join([word[0] for word in result_timestamps]))==len(split_punctuation_from_words(string_real)))
    print(result_timestamps)
    assert(all([word[1]<=word[2] for word in result_timestamps]))
    return result_timestamps

def get_delay(json_trim_filename):
    with open(json_trim_filename) as f:
        b = json.load(f)
    value = float(b['start_trim'])/1000
    return value

def get_timestamp_for_case(json_filename,json_trim_filename,string_real, use_trim):
    timestamps = align_timestamps(json_filename, string_real)
    if use_trim:
        delay = get_delay(json_trim_filename)
        timestamps = add_delay_to_all_timestamps(timestamps, delay)
    return {'timestamps':timestamps}

def get_joined_json_from_folder(experiment_folder, results_file, all_trials, user, use_trim):
    transcriptions_file = pd.read_csv(results_file)
    transcriptions_file = transcriptions_file[transcriptions_file['user']==user]
    
    all_timestamps = {}
    
    for trial in all_trials:
        json_filename = experiment_folder + '/' + str(trial) + '_1.0.json'
        json_trim_filename = experiment_folder + '/' + str(trial) + '_trim.json'
        print(json_filename)
        if os.path.isfile(json_filename):
            transcriptions_file_this_trial = transcriptions_file[transcriptions_file['trial'].astype(float)==trial]
            transcriptions_file_this_trial = transcriptions_file_this_trial.replace(np.nan, '', regex=True)
            assert(len(transcriptions_file_this_trial)==1)
            string_real = transcriptions_file_this_trial['transcription'].values[0].lower()
            new_timestamps = get_timestamp_for_case(json_filename,json_trim_filename,string_real,use_trim)
            print(new_timestamps)
            new_timestamps['timestamps'] = [ [item[0],float(item[1]),float(item[2])] for item in new_timestamps['timestamps']]
            with open(experiment_folder + '/' + str(trial) + '_joined.json', 'w') as outfile:
                json.dump(new_timestamps, outfile)
            new_timestamps['user'] = list_of_users.index(user)
            new_timestamps['trial'] = trial
            all_timestamps[trial] = new_timestamps
    
    return all_timestamps

def get_all_joined_json(experiment_folders, suffix,all_trials, results_file, use_trim = True):
    timestamps_by_user = defaultdict(dict)
    for experiment_folder in experiment_folders:
        user = experiment_folder.split('/')[-2].split('_')[0]
        timestamps_by_user[user].update(get_joined_json_from_folder(experiment_folder, results_file, all_trials[user], user, use_trim))
    all_timestamps = []
    for user in list_of_users:
        for trial in all_trials[user]:
            print(timestamps_by_user[user].keys())
            all_timestamps.append(timestamps_by_user[user][trial])
    with open('all_timestamps'+suffix+'.json', 'w') as outfile:
        json.dump({'all_timestamps':all_timestamps}, outfile)

def get_all_joined_json_phase_3(discard_df):
    all_trials = {}
    total_trials = {'user1':515,'user2':510,'user3':509,'user4':504,'user5':511}
    for user in list_of_users:
        all_trials[user] = [x for x in range(1,total_trials[user]+1) if x not in discard_df[discard_df['user']==user]['trial'].values]


    experiment_folders = [item for item in glob.glob('anonymized_collected_data/phase_3/*/')]
    results_file = 'anonymized_collected_data/phase_3/phase_3_transcriptions_anon.csv'
    get_all_joined_json(experiment_folders, '_phase_3',all_trials, results_file)

def get_all_joined_json_phase_2(discard_df):
    all_trials = {}
    for user in list_of_users:
        all_trials[user] = [x for x in range(1,51) if x not in discard_df[discard_df['user']==user]['trial'].values]


    experiment_folders = [item for item in glob.glob('anonymized_collected_data/phase_2/*/')]
    results_file = 'anonymized_collected_data/phase_2/phase_2_transcriptions_anon.csv'
    get_all_joined_json(experiment_folders, '_phase_2',all_trials, results_file)

def get_all_joined_json_phase_1(discard_df):
    all_trials = {}
    for user in list_of_users:
        all_trials[user] = [x for x in range(1,61) if x not in discard_df[discard_df['user']==user]['trial'].values]

    experiment_folders = [item for item in glob.glob('anonymized_collected_data/phase_1/*/')]
    print(experiment_folders)
    results_file = 'anonymized_collected_data/phase_1/phase_1_transcriptions_anon.csv'
    # convert_pickle_to_json(experiment_folders)
    get_all_joined_json(experiment_folders, '_phase_1',all_trials, results_file, use_trim=False)

def convert_return_from_google_to_ibm(x):
    converted_json_from_google ={}
    converted_json_from_google["result_index"] = 0
    converted_json_from_google["results"] = []
    for i in range(len(x.results)):
        timestamps = []
        converted_json_from_google["results"].append({})
        converted_json_from_google["results"][-1]["final"] = True
        converted_json_from_google["results"][-1]["alternatives"] = []
        for alternative_index in range(len(x.results[i].alternatives)):
            converted_json_from_google["results"][-1]["alternatives"].append({})
            converted_json_from_google["results"][-1]["alternatives"][-1]['transcript'] = x.results[i].alternatives[alternative_index].transcript
            if alternative_index==0:
                converted_json_from_google["results"][-1]["alternatives"][-1]['confidence'] = x.results[i].alternatives[alternative_index].confidence
                converted_json_from_google["results"][-1]["alternatives"][-1]["timestamps"] = []
                for word in x.results[i].alternatives[alternative_index].words:
                    print(word)
                    converted_json_from_google["results"][-1]["alternatives"][-1]["timestamps"].append([word.word, word.start_time.seconds+word.start_time.nanos/10**9, word.end_time.seconds+word.end_time.nanos/10**9])
    return converted_json_from_google

def convert_pickle_to_json(experiment_folders):
    for experiment_folder in experiment_folders:
        user = experiment_folder.split('/')[-1].split('_')[0]
        for subdir, dirs, files in os.walk(experiment_folder):
            for file in files:
                ext = os.path.splitext(file)[-1].lower()
                if ext in ('.pkl',):
                    with open(os.path.join(subdir, file), 'rb') as pkl_file:
                        x = pickle.load(pkl_file)
                        print()
                        print(os.path.join(subdir, file))
                    if user=='user5':
                        x = convert_return_from_google_to_ibm(x)
                    with open(os.path.join(subdir, file)[:-3]+'json', 'w') as outfile:
                        json.dump(x, outfile)

# json_filename = '7_1.0.json'
# json_trim_filename = '7_trim.json'
# string_real = 'the endotracheal tube is adequately positioned. tip of the ng tube is in the stomach. there are hazy opacities in the right lung and to a lesser extent in the left lung. no definite effusions or pneumothorax although the right costophrenic angle is not included on the film.'
if __name__ == '__main__':
    # json_filename = '7_1.0.json'
    # json_trim_filename = '7_trim.json'
    # string_real = 'the endotracheal tube is adequately positioned. tip of the ng tube is in the stomach. there are hazy opacities in the right lung and to a lesser extent in the left lung. no definite effusions or pneumothorax although the right costophrenic angle is not included on the film.'
    # print(get_timestamp_for_case(json_filename,json_trim_filename,string_real, use_trim=False))
    # {"timestamps": [["the", 4.97, 5.08], ["endotracheal", 5.08, 5.56], ["tube", 5.56, 5.7], ["is", 5.7, 5.8], ["adequately", 5.8, 6.19], ["positioned", 6.19, 6.55], [".", 6.55, 6.8], ["tip", 6.8, 6.8], ["of", 6.8, 6.88], ["the", 6.88, 7.03], ["ng", 7.03, 7.26], ["tube", 7.26, 7.56], ["is", 7.56, 8.01], ["in", 12.28, 12.44], ["the", 12.44, 12.53], ["stomach", 12.53, 12.97], [".", 12.97, 13.42], ["there", 17.09, 17.26], ["are", 17.26, 17.33], ["hazy", 17.33, 17.62], ["opacities", 17.62, 18.11], ["in", 18.11, 18.28], ["the", 18.28, 18.7], ["right", 20.16, 20.47], ["lung", 20.47, 21.02], ["and", 21.29, 21.48], ["to", 21.48, 21.59], ["a", 21.59, 21.65], ["lesser", 21.65, 21.89], ["extent", 21.89, 22.25], ["in", 22.25, 22.31], ["the", 22.31, 22.39], ["left", 22.39, 22.7], ["lung", 22.7, 23.06], [".", 26.76, 27.26], ["no", 29.93, 30.09], ["definite", 30.09, 30.43], ["effusions", 30.43, 30.78], ["or", 30.78, 30.86], ["pneumothorax", 30.86, 31.41], ["although", 31.41, 31.69], ["the", 31.69, 32.07], ["right", 32.55, 32.76], ["costophrenic", 32.76, 33.22], ["angle", 33.22, 33.49], ["is", 33.49, 33.68], ["not", 33.68, 33.81], ["included", 33.81, 34.24], ["on", 34.24, 34.36], ["the", 34.36, 34.43], ["film", 34.43, 34.66], [".", 34.66, 35.01]]}
    # 1/0
    discard_df = pd.read_csv('discard_cases.csv')
    get_all_joined_json_phase_1(discard_df[discard_df['phase']==1])
    get_all_joined_json_phase_2(discard_df[discard_df['phase']==2])
    get_all_joined_json_phase_3(discard_df[discard_df['phase']==3])