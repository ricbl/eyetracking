import os
import io
import os
import wave
import pickle
import argparse
import pickle
import shutil

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--file_name', type=str, nargs='+',
                    help='name of the audio file, without the .wav extension.')
parser.add_argument('--stretch_constant', type=float, nargs='?', default = 1.,
                    help='if >1, it will slow audio proportionally')
args = parser.parse_args()
for file_name in args.file_name:

    audio_file_name = file_name + '.wav'
    shutil.copyfile(audio_file_name, audio_file_name + '.back')

    complete_string = 'testing lala'
    import time
    time.sleep(30)

    text_file = open(file_name + '_' + str(args.stretch_constant) + ".txt", "w")
    text_file.write(complete_string)
    text_file.close()

    shutil.copyfile(audio_file_name + '.back', audio_file_name)
