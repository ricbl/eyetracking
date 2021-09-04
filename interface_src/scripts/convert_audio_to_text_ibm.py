# -*- coding: utf-8 -*-
import requests
import json
import codecs
import os, sys, time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import pickle
import librosa
import shutil
import soundfile as sf
import pyrubberband
import numpy as np
from pydub import AudioSegment
import re
from collections import OrderedDict

def detect_leading_silence(sound):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    from skimage.filters import threshold_otsu
    trim_ms = 0
    chunk_size = 500
    values_histogram = []
    while trim_ms < len(sound):
         values_histogram.append(sound[trim_ms:trim_ms+chunk_size].dBFS)
         trim_ms += chunk_size
    threshold = threshold_otsu(np.array(values_histogram))
    
    trim_ms = 0
    while sound[trim_ms:trim_ms+chunk_size].dBFS < threshold and trim_ms < len(sound):
        trim_ms += chunk_size
    return max(trim_ms-chunk_size, 0)

def trim_silence_start(path_to_wav):
    sound = AudioSegment.from_file(path_to_wav, format="wav")
    previous_db = sound[:1000].max_dBFS
    start_trim = detect_leading_silence(sound)
    end_trim = detect_leading_silence(sound.reverse())
    
    duration = len(sound)    
    trimmed_sound = sound[start_trim:duration-end_trim]
    
    trimmed_sound.export(path_to_wav, format="wav")
    return start_trim, end_trim

# def stretch_audio(filepath):
#     y, sr = librosa.load(filepath, sr=None)
#     y_stretched = pyrubberband.time_stretch(y, sr, 1.1)
#     sf.write(filepath + str(1.1) + '.wav' , y_stretched, sr, format='wav')
#     sf.write(filepath, y_stretched, sr, format='wav')
# 
# def denoise_audio(filepath):
#     from scipy.io import wavfile
#     import noisereduce as nr
#     # load data
#     data, sr = librosa.load(filepath, sr=None)
#     # select section of data that is noise
#     print(data)
#     print(len(data))
#     noisy_part = data[10000:49800]
#     # perform noise reduction
#     reduced_noise = nr.reduce_noise(audio_clip=data, noise_clip=noisy_part, verbose=True)
#     sf.write(filepath, reduced_noise, sr, format='wav')
            
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--file_name', type=str, nargs='?',
                        help='name of the audio file, without the .wav extension.')
    parser.add_argument('--ibm_credentials', type=str, nargs='?', default = '../../credentials/ibm_credentials_sci_all_radiologists_mt.json',
                        help='')
    args = parser.parse_args()
    transcribe_function(args.file_name, args.ibm_credentials)

def transcribe_function(file_name, ibm_credentials, suffix = '', background_audio_suppression = 0.1, speech_detector_sensitivity = 0.9):
    audio_file = file_name + '.wav'
    shutil.copyfile(audio_file, audio_file + '.back')
    try:
        start_trim, end_trim = trim_silence_start(audio_file)
        # 1/0
        # shutil.copyfile(audio_file + '.back', audio_file)
        # os.remove(audio_file + '.back')
        # return ''
        with open(ibm_credentials) as json_file:
            credentials = json.load(json_file)

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        headers = {'Content-Type' : "audio/wav"}

        try:
            language_id = "&language_customization_id="+credentials['LANGUAGE_ID']
        except:
            language_id = ""

        try:
            acoustic_id = "&acoustic_customization_id="+credentials['ACOUSTIC_ID']
        except:
            acoustic_id = ""
        
        uri = credentials['STT_ENDPOINT'] + "/v1/recognize?inactivity_timeout=60&timestamps=true&profanity_filter=false&smart_formatting=true&max_alternatives=5&speech_detector_sensitivity="+str(speech_detector_sensitivity)+"&background_audio_suppression="+str(background_audio_suppression)+"&model=en-US_BroadbandModel"+language_id+acoustic_id
        with open(audio_file, 'rb') as f:
            r = requests.post(uri, auth=(credentials['USERNAME'],credentials['PASSWORD']), verify=False, headers=headers, data=f)

        transcript = ""

        with open(file_name + '_' + str(1.) +suffix+'.pkl', 'wb') as f:
            pickle.dump(r.json(), f)
        with open(file_name + '_' + str(1.) +suffix+'.json', 'w') as f:
            json.dump(r.json(), f)
        with open(file_name + suffix+'_trim.json', 'w') as f:
            json.dump({'start_trim': start_trim, 'end_trim': end_trim}, f)
        # print(r.json())
        for result in r.json()['results']:
            for alternative in result['alternatives']:
                if 'confidence' in alternative.keys():
                    transcript += alternative['transcript']
                    break

        with open(file_name + '_' + str(1.) +suffix+ ".txt", "w") as text_file:
            
            replace_dict = OrderedDict()
            replace_dict[' period']='.'
            replace_dict[' comma']=','
            replace_dict[r'\bmulti segmental\b']='multisegmental'
            replace_dict[r'\bslot\b']='slight'
            replace_dict[r'\bcritic silhouette\b']='cardiac silhouette'
            replace_dict[r'\bcritics\b']='cardiac'
            replace_dict[r'\bof isis\b']='devices'
            replace_dict['\. i ']='. '
            replace_dict['^i ']= ''
            replace_dict[r'\bi\b']= ''
            replace_dict[r'\bthey are\b']= 'there are'
            replace_dict[r"\bthey're\b"]= 'there are'
            replace_dict[r'\bto to\b']= 'due to'
            replace_dict[r'\bhardest\b']= 'heart is'
            replace_dict[r'\bhiler\b']= 'hilar'
            replace_dict[r'\btyler\b']= 'hilar'
            replace_dict[r'\bperio\.']= '.'
            replace_dict[r'\band g\b']= 'ng'
            replace_dict['\. of the ng']= '. tip of the ng'
            replace_dict[r'\bto the ng\b']= 'tip of the ng'
            replace_dict[r"\bto what's\b"]= 'towards'
            replace_dict[r"\bnew paragraph\b"]= ''
            replace_dict[r"\bnigel's\b"]= 'nodules'
            replace_dict[r"\bnigels\b"]= 'nodules'
            replace_dict[r"\bnigel\b"]= 'nodule'
            replace_dict[r'\bfusion plate\b']= 'fusion_plate'
            replace_dict[r'\bfusion hardware\b']= 'fusion_hardware'
            replace_dict[r'\bspinal fusion\b']= 'spinal_fusion'
            replace_dict[r'\bcervical fusion\b']= 'cervical_fusion'
            replace_dict[r'\blumbar fusion\b']= 'lumbar_fusion'
            replace_dict[r'\bdisk fusion\b']= 'disk_fusion'
            replace_dict[r'\bfusion cage\b']= 'fusion_cage'
            replace_dict[r'\bfusion\b']= 'effusion'
            replace_dict[r'\bfusions\b']= 'effusions'
            replace_dict[r'\bfusion_plate\b']= 'fusion plate'
            replace_dict[r'\bfusion_hardware\b']= 'fusion hardware'
            replace_dict[r'\bspinal_fusion\b']= 'spinal fusion'
            replace_dict[r'\bcervical_fusion\b']= 'cervical fusion'
            replace_dict[r'\blumbar_fusion\b']= 'lumbar fusion'
            replace_dict[r'\bdisk_fusion\b']= 'disk fusion'
            replace_dict[r'\bfusion_cage\b']= 'fusion cage'
            replace_dict[r'\bread\b']= '.'
            replace_dict[r'\bbasalar\b']= 'basilar'
            replace_dict[r'\bdeac\b']= 'cardiac'
            replace_dict[r'\bslash\b']= '/'
            replace_dict[r'\bno all\b']= 'normal'
            replace_dict[r'\bacc\b']= 'svc'
            replace_dict[r'\bevery wall\b']= 'airway wall'
            replace_dict[r'\bevery way wall\b']= 'airway wall'
            replace_dict[r'\bc\. segment\b']= 'sup. segment'
            replace_dict[r'\bintro tube\b']= 'enteral tube'
            replace_dict[r'\bs. shaped\b']= 's shaped'
            replace_dict[r'\bcabbage\b']= 'CABG'
            replace_dict[r'\bcost different\b']= 'costophrenic'
            replace_dict[r'\bcost frank\b']= 'costophrenic'
            replace_dict[r'\bbecause different\b']= 'costophrenic'
            replace_dict[r'\bcuster frank\b']= 'costophrenic'
            replace_dict[r'\bcustomer neck\b']= 'costophrenic'
            replace_dict[r'\bpick\b']= 'picc'
            replace_dict[r'\bminnesota\b']= 'mediastinal'
            replace_dict[r'\bcrt d\.']= 'crt-d'
            replace_dict['^crt d\.']= 'crt-d'
            replace_dict[r'\bt. 1\.\b']= 'T1'
            replace_dict[r'\bt. 2\.\b']= 'T2'
            replace_dict[r'\bfavorite\b']= 'favored to'
            replace_dict[r'^s\. ']= ''
            replace_dict[r'^yes\b']= ''
            replace_dict[r'\bno no no\b']= 'no'
            replace_dict[r'\bno no\b']= 'no'
            replace_dict[r'\. is the\b']= 'hazy'
            replace_dict['^is the ']= 'hazy '
            replace_dict[r"\bhe's\b"]= 'hazy '
            replace_dict[r"\bapc's\b"]= 'apices'
            replace_dict[r"\b52\b"]= 'feeding tube'
            replace_dict["^52 "]= 'feeding tube'
            replace_dict[r'\bslack\b']= 'slight'
            replace_dict[r'\becstatic\b']= 'ectatic'
            replace_dict[r'\beven duration\b']= 'eventration'
            replace_dict[r'\beffusion hardware\b']= 'of fusion hardware'
            replace_dict['\.\.']= '.'
            replace_dict['\. \.']= '.'
            
            transcript = transcript.lower()
            for key,value in replace_dict.items():
                transcript = re.sub(key, value, transcript)
            text_file.write(transcript)
        
        with open(file_name + '_' + str(1.) +suffix+ "_trim.txt", "w") as text_file:
            text_file.write(str(start_trim)+'\n')
            text_file.write(str(end_trim))
    except Exception as e:
        shutil.copyfile(audio_file + '.back', audio_file)
        os.remove(audio_file + '.back')
        raise e
    shutil.copyfile(audio_file + '.back', audio_file)
    os.remove(audio_file + '.back')
    return transcript, start_trim, end_trim
    # # print("Transcription: ")
    # # print(transcript)
    #
    # output_file.write(transcript)
    # output_file.close()

if __name__ == "__main__":
    main()
