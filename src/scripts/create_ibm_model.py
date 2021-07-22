# -*- coding: utf-8 -*-
import requests
import json
import codecs
import time
import subprocess
import pandas as pd
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from convert_audio_to_text_ibm import transcribe_function as tf
from test_transcription_scores import get_score, get_transcription_from_txt
from shutil import copyfile
import time

def get_credentials():
    ibm_credentials = '../../credentials/ibm_credentials_sci.json'
    with open(ibm_credentials) as json_file:
        credentials = json.load(json_file)
    return credentials['STT_ENDPOINT'], credentials['USERNAME'], credentials['PASSWORD']

def create_language_model(model_name):
    all_models = json.loads(list_language_models())['customizations']
    for model in all_models:
        if model['name'] == model_name:
            return model['customization_id']
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    data = {"name" : model_name, "base_model_name" : "en-US_BroadbandModel", "description" : "My broadband language model"}
    uri = endpoint + "/v1/customizations/"
    jsonObject = json.dumps(data).encode('utf-8')
    r = requests.post(uri, auth=(username, password), verify=False, headers=headers, data=jsonObject)
    assert(r.status_code == 201)
    return_text = json.loads(r.text)
    with open("../../ibm_models_infos/language_model_"+model_name+"_"+time.strftime("%Y%m%d-%H%M%S")+".json", "w") as outfile: 
        json.dump({'customization_id':return_text['customization_id'],'name':model_name}, outfile) 
    
    return return_text['customization_id']

def add_corpus(corpus_file, language_id, model_name):
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    print(os.path.basename(corpus_file))
    corpus_name = os.path.basename(corpus_file).split('.')[0]
    uri = endpoint + "/v1/customizations/"+language_id+"/corpora/"+corpus_name
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    print(r.status_code)
    print(r.text)
    if r.status_code==400:
        uri = endpoint + "/v1/customizations/"+language_id+"/corpora/"+corpus_name
        print(uri)
        with open(corpus_file, 'rb') as f:
           r = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=f)
        assert(r.status_code == 201)
    time.sleep(1)
    uri = endpoint + "/v1/customizations/"+language_id+"/corpora/"+corpus_name
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    respJson = r.json()
    print(respJson)
    status = respJson['status']
    time_to_run = 10
    while (status != 'analyzed'):
        time.sleep(10)
        r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
        respJson = r.json()
        print(r.text)
        status = respJson['status']
        print("status: ", status, "(", time_to_run, ")")
        time_to_run += 10

    uri = endpoint + "/v1/customizations/"+language_id+"/words?sort=count"
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    file = codecs.open('../../ibm_models_infos/'+model_name+'_'+language_id+'_'+corpus_name+".OOVs.corpus", 'wb', 'utf-8')
    file.write(r.text)

def train_language_model(language_id):
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/customizations/"+language_id+"/train"
    r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
    assert(r.status_code==200 or r.json()["error"]=="No input data modified since last training")
    
    uri = endpoint + "/v1/customizations/" + language_id
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    respJson = r.json()
    status = respJson['status']
    time_to_run = 10
    while (status != 'available'):
        time.sleep(10)
        r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
        respJson = r.json()
        status = respJson['status']
        print("status: ", status, "(", time_to_run, ")")
        time_to_run += 10

def create_acoustic_model(model_name):
    
    all_models = json.loads(list_acoustic_models())['customizations']
    for model in all_models:
        if model['name'] == model_name:
            return model['customization_id']
    
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    data = {"name" : model_name, "base_model_name" : "en-US_BroadbandModel", "description" : "My broadband acoustic model"}
    uri = endpoint + "/v1/acoustic_customizations"
    jsonObject = json.dumps(data).encode('utf-8')
    r = requests.post(uri, auth=(username, password), verify=False, headers=headers, data=jsonObject)
    assert(r.status_code==201)
    return_text = json.loads(r.text)
    with open("../../ibm_models_infos/acoustic_model_"+model_name+"_"+time.strftime("%Y%m%d-%H%M%S")+".json", "w") as outfile: 
        json.dump({'customization_id':return_text['customization_id'],'name':model_name}, outfile) 
    return return_text['customization_id']

def add_audio(audio_filename, acoustic_id, radiologist):
    endpoint, username, password = get_credentials()
    audio_name = os.path.basename(audio_filename).split('.')[0] + radiologist
    
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/acoustic_customizations/" + acoustic_id + "/audio/"+ audio_name
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    if r.status_code == 400:
        headers = {'Content-Type' : "audio/wav"}
        uri = endpoint + "/v1/acoustic_customizations/"+acoustic_id+"/audio/"+audio_name
        with open(audio_filename, 'rb') as f:
           r = requests.post(uri, auth=(username, password), verify=False, headers=headers, data=f)
        assert(r.status_code==201)
    
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/acoustic_customizations/" + acoustic_id + "/audio/"+ audio_name
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    respJson = r.json()
    status = respJson['status']
    time_to_run = 4
    while (status != 'ok'):
        time.sleep(4)
        r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
        respJson = r.json()
        status = respJson['status']
        print("status: ", status, "(", time_to_run, ")")
        time_to_run += 4

def train_acoustic_model(acoustic_id, language_id):
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/acoustic_customizations/"+acoustic_id+"/train?custom_language_model_id="+language_id
    r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
    assert(r.status_code==200 or r.json()["error"]=="No input data modified since last training")

    uri = endpoint + "/v1/acoustic_customizations/" + acoustic_id
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    respJson = r.json()
    status = respJson['status']
    time_to_run = 10
    while (status != 'available'):
        time.sleep(10)
        r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
        respJson = r.json()
        status = respJson['status']
        print("status: ", status, "(", time_to_run, ")")
        time_to_run += 10

def sed_to_corpora(folder_documents, corpus_name):
    bashCommand = "sed -f ../../ibm/Train-Custom-Speech-Model/data/fixup_invert_period.sed " + folder_documents + "/*.txt > ../../ibm_models_infos/" + corpus_name
    os.system(bashCommand)

def complete_train_model(test_name, use_mimic, use_transcriptions, radiologists, phase_suffixes = ['']):
    print(test_name)
    language_id = create_language_model(test_name)
    print(language_id)
    if use_mimic:
        add_corpus('../../ibm_models_infos/corpus_mimic-invert_period.txt', language_id, test_name)
    if use_transcriptions:
        for phase_suffix in phase_suffixes:
            for radiologist in radiologists:
                add_corpus('../../ibm_models_infos/corpus_'+radiologist+'-invert_period'+phase_suffix+'.txt', language_id, test_name)
    train_language_model(language_id)
    acoustic_id = create_acoustic_model(test_name)
    print(acoustic_id)
    for phase_suffix in phase_suffixes:
        for radiologist in radiologists:
            audiofolder = '../../ibm/Train-Custom-Speech-Model/data/' + radiologist + '_trainaudio' + phase_suffix
            audiofiles = os.listdir(audiofolder)
            for audioindex, filename in enumerate(audiofiles):
                print('adding audio ' +str (audioindex))
                add_audio(audiofolder+'/'+filename, acoustic_id, radiologist)
    train_acoustic_model(acoustic_id, language_id)
    endpoint, username, password = get_credentials()
    with open('../../credentials/ibm_credentials_sci_'+ test_name +'.json', "w") as outfile: 
        json.dump({'USERNAME':username,'PASSWORD':password, 'STT_ENDPOINT': endpoint, "LANGUAGE_ID":language_id , "ACOUSTIC_ID":acoustic_id}, outfile) 

def test_model(test_name,radiologist, use_txt, remove_noise_level, sensitivity):
    print('test')
    print(test_name)
    print(radiologist)
    ground_truth_location = '../../ibm/Train-Custom-Speech-Model/data/' + radiologist + '_valtxt/'
    audio_location = '../../ibm/Train-Custom-Speech-Model/data/' + radiologist + '_valaudio/'
    if use_txt:
        transcription_function = lambda x: get_transcription_from_txt(x, audio_location, test_name+'_'+radiologist + str(remove_noise_level) + '_' + str(sensitivity), remove_noise_level, sensitivity)
    else:
        credentials_json = '../../credentials/ibm_credentials_sci_'+ test_name +'.json'
        transcription_function = lambda entry: tf(entry, credentials_json, test_name, remove_noise_level, sensitivity )[0]
    score = get_score(ground_truth_location, audio_location, transcription_function)
    print(score)
    with open("../../ibm_models_infos/score_"+radiologist+"_"+test_name+"_"+str(remove_noise_level) + '_' + str(sensitivity)+time.strftime("%Y%m%d-%H%M%S")+".json", "w") as outfile: 
        json.dump({'test_name':test_name,'score':score}, outfile) 
    return score

def filter_by_timestamp(table, begin_timestamp, end_timestamp):
    table = table[table['timestamp']>=begin_timestamp]
    table = table[table['timestamp']<=end_timestamp]
    return table

def get_last_saved_screen(table):
    table_filter = table[table['messenger'] == 'MainWindow']
    begin_timestamp = table_filter[table_filter['title'] == 'index_start_screen_trial']['timestamp'].values.tolist()[-1]
    end_timestamp = table_filter[table_filter['title'] == 'end_screen_trial']['timestamp'].values.tolist()[-1]
    return filter_by_timestamp(table, begin_timestamp, end_timestamp)

def convert_structured_output(so_filename, groundtruth_location, trials):
    table = pd.read_csv(so_filename)
    for trial in trials:
        table_this_trial = table[table['trial'] == trial]
        table_this_screen = table_this_trial[table_this_trial['screen'] == 11]
        if len(table_this_screen)==0:
            continue
        table_transcription_screen = get_last_saved_screen(table_this_screen)
        transcription = table_transcription_screen[table_transcription_screen['title']=='text']['value'].tolist()[-1]
        with open(groundtruth_location+'/'+str(trial)+".txt", "w") as text_file:
            text_file.write(transcription)

def list_language_models():
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/customizations"
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    return r.text

def delete_language_model(id):
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/customizations/"+id
    resp = requests.delete(uri, auth=(username,password), verify=False, headers=headers)
    if resp.status_code != 200:
       print("Failed to delete language model")
       print(resp.text)

def list_acoustic_models():
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/acoustic_customizations"
    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
    return r.text

def delete_acoustic_model(id):
    endpoint, username, password = get_credentials()
    headers = {'Content-Type' : "application/json"}
    uri = endpoint + "/v1/acoustic_customizations/"+id
    resp = requests.delete(uri, auth=(username,password), verify=False, headers=headers)
    if resp.status_code != 200:
       print("Failed to delete language model")
       print(resp.text)

def main():
    scores = {}
    # delete_language_model("0bbe2174-8f21-41cb-9ad6-e7ebdf04d42e")
    # 
    # print(list_language_models())
    # print(list_acoustic_models())
    # data_folders = [    'user1_203_20201216-141859-3506', 
    # 'user1_203_20201216-142259-5921', 
    # 'user1_203_20201218-142722-8332', 
    # 'user1_203_20201223-140239-9152', 
    # 'user2_203_20201201-092234-9617', 
    # 'user3_203_20201210-101303-6691',
    # 'user3_203_20201217-083511-9152', 
    # 'user4_203_20201222-150420-9152', 
    # 'user4_203_20210104-130049-9152',
    # 'user5_203_20201113', ]
    # for data_folder in data_folders:
    #     user = data_folder.split('_')[0]
    #     for key,value in {'train':range(1,46),'val':range(46,61)}.items():
    #         for trial in value:
    #             if os.path.exists('../../anonymized_collected_data/'+data_folder +'/'+str(trial)+'.wav'):
    #                 copyfile('../../anonymized_collected_data/'+data_folder +'/'+str(trial)+'.wav', '/../../ibm/Train-Custom-Speech-Model/data/' + user + '_'+key+'audio/'+str(trial)+'.wav')
    #         # convert_structured_output('../../anonymized_collected_data/'+data_folder +'/structured_output.csv', '../../ibm/Train-Custom-Speech-Model/data/' + user + '_'+key+'txt', value)
    # 1/0
    # for radiologist in ['user1', 'user2', 'user3', 'user4', 'user5']:
    #     sed_to_corpora('../../ibm/Train-Custom-Speech-Model/data/' + radiologist + '_traintxt_phase_2', 'corpus_'+radiologist+'-invert_period'+'_phase_2'+'.txt')
    #     sed_to_corpora('../../ibm/Train-Custom-Speech-Model/data/' + radiologist + '_traintxt', 'corpus_'+radiologist+'-invert_period.txt')
    # sed_to_corpora('../../ibm/Train-Custom-Speech-Model/data/', 'corpus_mimic-invert_period.txt')
    # 1/0
    complete_train_model('all_radiologists_mt_phase_2', False, True, radiologists = ['user1', 'user2', 'user3', 'user4', 'user5'], phase_suffixes = ['','_phase_2'])
    scores['all_radiologists_mt_phase_2_user5'] = test_model('all_radiologists_mt_phase_2','user5', False, 0.1, 0.9)
    scores['all_radiologists_mt_phase_2_user1'] = test_model('all_radiologists_mt_phase_2','user1', False, 0.1, 0.9)
    scores['all_radiologists_mt_phase_2_user3'] = test_model('all_radiologists_mt_phase_2','user3', False, 0.1, 0.9)
    scores['all_radiologists_mt_phase_2_user4'] = test_model('all_radiologists_mt_phase_2','user4', False, 0.1,0.9 )
    scores['all_radiologists_mt_phase_2_user2'] = test_model('all_radiologists_mt_phase_2','user2', False, 0.1,0.9)
    
    print(scores)

if __name__ == '__main__':
    main()