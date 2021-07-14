import difflib
from convert_audio_to_text_ibm import transcribe_function as tf
import os
import re

def get_transcription_from_txt(audio_path, path_with_txt, suffix = ''):
    import ntpath
    audio_name = ntpath.basename(audio_path)
    with open(path_with_txt + audio_name + "_1.0"+suffix+".txt", 'r') as f:
        string_old_transcription = f.read()
    return string_old_transcription

def get_diff_score(string_real, string_google):
    a = list(difflib.ndiff(string_google,string_real))
    print(a)
    return sum([1 if element[0]=='+' else 0 for element in a])/len(string_real)

def get_score(ground_truth_location, audio_location, transcription_function):
    differences = []
    for entry in sorted(os.listdir(audio_location)):
        if (entry.endswith(".wav")):
            print(entry)
            with open(ground_truth_location+entry[:-4]+'.txt', 'r') as f:
                string_real = f.read()
            string_google = transcription_function(audio_location + entry[:-4]).lower().replace('.',' period').replace(',',' comma').replace('  ',' ').split(' ')
            string_real = string_real.lower().replace('.',' period').replace(',',' comma').replace('  ',' ').split(' ')
            string_google = [word2 for word2 in [re.sub(r'\W+', '', word) for word in string_google] if len(word2)>0]
            string_real = [word2 for word2 in [re.sub(r'\W+', '', word) for word in string_real] if len(word2)>0]
            differences.append(get_diff_score(string_real, string_google))
    print(sum(differences)/len(differences))
    return sum(differences)/len(differences)

def main():
    ground_truth_location = '/home/eye/Documents/projects/eyetracking/ibm/Train-Custom-Speech-Model/data/val_documents/'
    transcription_function = lambda entry: tf(entry, '../../credentials/ibm_credentials_sci.json')[0]
    # path_with_txt = '/home/eye/Documents/projects/eyetracking/ibm/Train-Custom-Speech-Model/data/val_audio/language_only/'
    #transcription_function = lambda x: get_transcription_from_txt(x, path_with_txt)
    audio_location = '/home/eye/Documents/projects/eyetracking/ibm/Train-Custom-Speech-Model/data/val_audio/'
    get_score(ground_truth_location, audio_location, transcription_function)

if __name__ == '__main__':
    main()