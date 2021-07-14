import re
import nltk
from itertools import chain
from collections import Counter
import numpy as np
import os
max_n = 8
nltk.download('punkt')
acc_counter = nltk.FreqDist()
all_txt_files = []

total_expressions_keep = 6000
min_occurences_to_keep = 2
folder_reports = '/home/eye/Downloads/reports/a/files/'
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
'preceding similar study','preceding']

def multiple_replace(list_of_unwanted_expressions, text):
  regex = re.compile("(%s)" % (r"\b"+r"\b|\b".join(map(re.escape, list_of_unwanted_expressions))+r"\b"))
  return regex.sub(lambda mo: ' . ', text)

def pascal_matrix(nrows):
    to_return = np.zeros([nrows+1,nrows+1])
    to_return[0][nrows-1] = 1
    for i in range(1,nrows+1):
        for j in range(nrows-1,i-2,-1):
            to_return[i,j] = to_return[i-1,j] + to_return[i,j+1]
    return to_return[1:,:-1]

from itertools import dropwhile

def delete_below_min_count(this_counter, this_most_common, min_counts_to_keep, reference_to_original_n_grams):
    if min_counts_to_keep>1:
        counter_to_keep = nltk.FreqDist()
        index = len(this_most_common)
        total_examples = len(this_most_common)
        for key, count in reversed(this_most_common):
            if (index-total_examples)%5000==0:
                print(str(min_counts_to_keep) + ':' + str(index) +':'+str(total_examples))
            if count >=min_counts_to_keep:
                break
            if len(key)>1:
                #reference_to_original_n_grams[key] is a set
                for a in reference_to_original_n_grams[key]:
                    counter_to_keep += a[0].create_new_subdivision(a[1], a[2],reference_to_original_n_grams)
            del this_counter[key]
            index = index - 1
        if len(counter_to_keep)>0:
            new_counter = this_counter+counter_to_keep
            return delete_below_min_count(new_counter, new_counter.most_common(), min_counts_to_keep , reference_to_original_n_grams)
    return this_counter

from collections import defaultdict
class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret

class OriginalNGrams:
    def __init__(self):
        self.originals = keydefaultdict(OriginalNGram)

    def add_original(self,n_gram):
        self.originals[n_gram].add_one()
        return self.originals[n_gram]

class OriginalNGram:
    def __init__(self, ngram):
        self.original_count = 0
        self.ngram = ngram
        self.count_finds = pascal_matrix(len(ngram))

    def add_one(self):
        self.original_count+=1

    def create_new_subdivision(self, previous_start_index, previous_end_index, reference_to_original_n_grams):
        to_return = nltk.FreqDist()
        for i in range(2):
            start_index = previous_start_index + i
            end_index = previous_end_index + i - 1
            if end_index>start_index:
                self.count_finds[start_index,end_index] -= 1
                if self.count_finds[start_index,end_index] == 0:
                    a = nltk.FreqDist([self.ngram[start_index:end_index]])
                    for k in a.keys():
                        a[k] = a[k] * self.original_count
                        reference_to_original_n_grams[k].add((self,start_index,end_index))
                    to_return += a
        return to_return

reference_to_original_n_grams = defaultdict(set)
list_of_originals = OriginalNGrams()

for root, dirs, files in os.walk(folder_reports):
    for file in files:
        if file.endswith(".txt"):
             all_txt_files.append(os.path.join(root, file))
total_texts_files = len(all_txt_files)

import os
index = 0
root_files = '/home/eye/Downloads/reports/a/files/'
for divisive_folder in os.listdir(root_files):
    for patient_folder in os.listdir(root_files + divisive_folder):
        # if index>10000:
        #     break
        patient_counter = nltk.FreqDist()
        for report_filename in os.listdir(root_files + divisive_folder + '/' +  patient_folder):
            # if index>0:
            #     break
            if index%100==0:
                print(str(index) + '/' + str(total_texts_files))
            with open(root_files + divisive_folder + '/' + patient_folder + '/' + report_filename,'r') as f:
                text = f.read().lower()
                do_next = False
                do_this = False
                report_counter = nltk.FreqDist()
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
                        section = section.replace(':','.').replace('\n',' ').replace(',','.').replace('(','.').replace(')','.').replace("'",'. ').replace('.', ' .')
                        section = re.sub(r'[^\s]*[^a-zA-Z\s][^\s]*', ' . ',section)
                        section = re.sub(r'[\s][a-z][\s]', ' . ',section)
                        section = multiple_replace(list_of_unwanted_expressions, section)
                        # section = (' mediastinal and hilar contours are  unremarkable . cardiomediastinal and hilar contours are normal .   hilar contours  . ')
                        split_section = section.split('.')
                        for split_ in split_section:
                            if split_:
                                tokens = nltk.word_tokenize(split_)
                                ngram_n = len(tokens)
                                this_ngram = nltk.everygrams(tokens, ngram_n, ngram_n)
                                report_counter += nltk.FreqDist(this_ngram)
                        # break
                    do_this = False

            index += 1
            patient_counter |= report_counter
        for k in patient_counter.keys():
            reference_to_original_n_grams[k].add((list_of_originals.add_original(k), 0, len(k)-1))
        acc_counter = acc_counter + patient_counter
        # break
    # break

continue_loop = True
count_to_keep = 2
this_most_common = acc_counter.most_common()
while continue_loop or count_to_keep<=min_occurences_to_keep:
    acc_counter = delete_below_min_count(acc_counter, this_most_common, count_to_keep, reference_to_original_n_grams)
    count_to_keep = count_to_keep + 1
    this_most_common = acc_counter.most_common()
    last_count_to_keep = this_most_common[total_expressions_keep-1][1]
    last_count = this_most_common[-1][1]
    if last_count >= last_count_to_keep:
        continue_loop = False

import csv

with open("vocab_mimic.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows([(' '.join(element[0]), element[1]) for element in acc_counter.most_common()])
