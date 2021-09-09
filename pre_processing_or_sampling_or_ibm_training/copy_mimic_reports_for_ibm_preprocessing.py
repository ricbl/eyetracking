# generates a list of senteces from the findings or impressions sections of the mimic-cxr reports that do not make reference to previous studies

import os
from shutil import copyfile
import re
import nltk
from nltk.tokenize import sent_tokenize

list_of_unwanted_expressions = ['unchanged','prior','previous','previously',
'stable','recent','recently','now','chest radiographs','worsening', 'worsened',
'new','newly','again','improve','improvement','improved','chest views',
'earlier','day','today','this date','days','pa and lateral','remain','remains',
'ap and lateral','frontal and lateral','lateral views','hour','hours','weeks',
'continued','continue','continues','views','have increased','have decreased',
'has increased','has decreased','have slightly increased','have slightly decreased',
'has slightly increased','has slightly decreased','persists','persist','persistent','since',
'progressed','interval','siginificant change','siginificant changes',
'siginificantly changed','comparison to the study','comparison to study',
'comparison with study','comparison with the study','comparison with the next',
'compared to the study','compared to study','compared with study','compared with the study',
'compared with the next','next preceding similar study',
'preceding similar study','preceding', 'still', 'questioned', 'recommend']

folder_reports = '../datasets/mimic/reports/files/'
dst = '../ibm/'

def multiple_replace(list_of_unwanted_expressions, text):
  regex = re.compile("(%s)" % (r"\b"+r"\b|\b".join(map(re.escape, list_of_unwanted_expressions))+r"\b"))
  return regex.sub(lambda mo: ' £ ', text)
  
all_txt_files = []
for root, dirs, files in os.walk(folder_reports):
    for file in files:
        if file.endswith(".txt"):
             all_txt_files.append(os.path.join(root, file))
total_texts_files = len(all_txt_files)

import os
index = 0
root_files = folder_reports
all_sections = []
for divisive_folder in os.listdir(root_files):
    for patient_folder in os.listdir(root_files + divisive_folder):
        for report_filename in os.listdir(root_files + divisive_folder + '/' +  patient_folder):
            # if index>1000:
            #     break
            if index%100==0:
                print(str(index) + '/' + str(total_texts_files))
            with open(root_files + divisive_folder + '/' + patient_folder + '/' + report_filename,'r') as f:
                text = f.read().lower()
                do_next = False
                do_this = False
                for section in text.split('\n \n'):
                    previous_do_next = do_next
                    if section[:10]==' findings:' or section[:12]==' impression:':
                        if len(section)>14:
                            do_this = True
                            do_next = False
                        else:
                            do_next = True
                    else:
                        do_next = False
                    if previous_do_next or do_this:
                        section = section.replace('\n',' ').replace(':','.').replace(';', ',')
                        # print('oi1')
                        # print(section)
                        for sentence in sent_tokenize(section):
                            if sentence[-1] == '.':
                                sentence = sentence[:-1]
                            sentence = re.sub(r'[1-9][.]\s', '',sentence)
                            sentence = sentence.replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')
                            sentence = sentence.strip()
                            # print(sentence)
                            
                            if len(sentence)>0 and ' ' in sentence:
                                
                                original_sentence = sentence
                                sentence = sentence.replace('(',' £ ').replace(')',' £ ')
                                sentence = re.sub(r'[^\s]*[^a-zA-Z\s,-][^\s]*', ' £ ',sentence)
                                #section = re.sub(r'[\s][a-z][\s]', ' £ ',section)
                                sentence = multiple_replace(list_of_unwanted_expressions, sentence)
                                # print(sentence)
                                if sentence == original_sentence:
                                    sentence = sentence.strip()+'.'
                                    # print('accepted')
                                    all_sections.append(sentence)
                    do_this = False
            index += 1

with open(os.path.join(dst, "vocab_mimic.txt") , "w") as f:
    for item in all_sections:
        f.write("%s\n" % item)