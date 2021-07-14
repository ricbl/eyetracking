import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "../../credentials/current_key-46cf5362d42b.json"
from pydub import AudioSegment
import io
import os
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import wave
from google.cloud import storage
from google.cloud import speech
from google.cloud import speech_v1p1beta1
import pickle
import librosa
import pyrubberband
import soundfile as sf
import argparse
import pickle
import shutil
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--file_name', type=str, nargs='+',
                    help='name of the audio file, without the .wav extension.')
parser.add_argument('--stretch_constant', type=float, nargs='?', default = 1.,
                    help='if >1, it will slow audio proportionally')
parser.add_argument('--boost', type=float, nargs='+', default = [0.],
                    help='')
args = parser.parse_args()

#vocab = pd.read_csv('../../vocabularies/vocabulary.csv', names = ['expression','countings']).expression.to_list()[:5000]
vocab = pd.read_csv('../../vocabularies/vocab_mimicV2.csv', names = ['expression','countings']).expression.to_list()[:4150]
boosts = np.floor(np.log(np.array(pd.read_csv('../../vocabularies/vocab_mimicV2.csv', names = ['expression','countings']).countings.to_list()[:4150]))/np.log(600)) #np.ones_like(vocab).astype(int) # np.floor(np.log(np.array(pd.read_csv('../../vocabularies/vocabulary.csv', names = ['expression','countings']).countings.to_list()[:5000]))/np.log(10))

list_frequent_expressions = ['within normal limits',
                            'airway wall',
                            'satisfactory position',
                            'lines and tubes',
                            'lung volumes',
                            'mediastinal contours and heart size',
                            'no pneumothorax',
                            'intact sternotomy',
                            'multisegmental atelectasis',
                            'subsegmental atelectasis']
list_frequent_expressions_not_found = []

# for expression in list_frequent_expressions:
#     try:
#         pass
#         index_expression = vocab.index(expression)
#         print(expression)
#         boosts[index_expression] = 20
#     except ValueError:
#         pass
#         list_frequent_expressions_not_found.append(expression)

to_group = pd.DataFrame(
    {'vocab': list_frequent_expressions_not_found+vocab,
     'boosts': np.concatenate([np.array([20]*len(list_frequent_expressions_not_found)),boosts])})
to_group = to_group.groupby('boosts')['vocab'].apply(list)
speech_contexts = [{
  "phrases": to_group.iloc[boost_index],
  'boost':
   to_group.index[boost_index]
} for boost_index in range(len(to_group))]
#['angle is','in the visualized','lucency', 'cavoatrial','lung volumes','lung volumes are within normal limits','pulmonary', 'fibrosis'] + list(modelw2v.wv.vocab.keys())

for file_name in args.file_name:
    for boost in args.boost:
        audio_file_name = file_name + '.wav'
        shutil.copyfile(audio_file_name, audio_file_name + '.back')
        bucketname = "medical_transcripts_2"
        bucket_name = bucketname
        def to_wav(audio_file_name):
            audio = AudioSegment.from_file(audio_file_name)
            audio_file_name = audio_file_name.split('.')[0] + '.wav'
            sound.export(audio_file_name, format="wav")

        def stereo_to_mono(audio_file_name):
            sound = AudioSegment.from_wav(audio_file_name)
            sound = sound.set_channels(1)
            sound.export(audio_file_name, format="wav")

        def frame_rate_channel(audio_file_name):
            with wave.open(audio_file_name, "rb") as wave_file:
                frame_rate = wave_file.getframerate()
                channels = wave_file.getnchannels()
                return frame_rate,channels

        def upload_blob(bucket_name, source_file_name, destination_blob_name):
            """Uploads a file to the bucket."""
            storage_client = storage.Client.from_service_account_json(
                "../../credentials/current_key-46cf5362d42b.json")
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)

        def delete_blob(bucket_name, blob_name):
            """Deletes a blob from the bucket."""
            storage_client = storage.Client.from_service_account_json(
                    "../../credentials/current_key-46cf5362d42b.json")
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()

        def stretch_audio(filepath):
            y, sr = librosa.load(filepath, sr=None)
            y_stretched = pyrubberband.time_stretch(y, sr, args.stretch_constant)
            sf.write(filepath + str(args.stretch_constant) + '.wav' , y_stretched, sr, format='wav')
            sf.write(filepath, y_stretched, sr, format='wav')

        def denoise_audio(filepath):
            from scipy.io import wavfile
            import noisereduce as nr
            # load data
            data, sr = librosa.load(filepath, sr=None)
            # select section of data that is noise
            print(data)
            print(len(data))
            1/0
            noisy_part = data[10000:49800]
            # perform noise reduction
            reduced_noise = nr.reduce_noise(audio_clip=data, noise_clip=noisy_part, verbose=True)
            sf.write(filepath, reduced_noise, sr, format='wav')

        config = speech_v1p1beta1.types.RecognitionConfig(
          encoding= enums.RecognitionConfig.AudioEncoding.LINEAR16,
          sample_rate_hertz = 48000,
          audio_channel_count = 1,
          enable_separate_recognition_per_channel=  False,
          language_code = 'en-US',
          max_alternatives = 5,
          profanity_filter = False,
          speech_contexts = speech_contexts,
          enable_word_time_offsets = True,
          enable_automatic_punctuation = False,
          metadata = speech_v1p1beta1.types.RecognitionMetadata(
              interaction_type = enums.RecognitionMetadata.InteractionType.DICTATION,
              industry_naics_code_of_audio =621512,
              microphone_distance =enums.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
              original_media_type =enums.RecognitionMetadata.OriginalMediaType.AUDIO,
              recording_device_type =enums.RecognitionMetadata.RecordingDeviceType.PC,
               recording_device_name = '',
              original_mime_type = 'audio/x-wav',
             audio_topic = "Dictation of radiologist report for open chest x-ray dataset."
         ),
         model= 'default',
         use_enhanced = False
        )

        frame_rate, channels = frame_rate_channel(audio_file_name)

        if channels > 1:
            stereo_to_mono(audio_file_name)

        source_file_name = audio_file_name
        #denoise_audio(audio_file_name)
        if  args.stretch_constant!=1:
            stretch_audio(audio_file_name)
        destination_blob_name = audio_file_name
        upload_blob(bucket_name, source_file_name, destination_blob_name)
        gcs_uri = 'gs://' + bucketname + '/' + audio_file_name
        audio = {"uri": gcs_uri}
        client = speech_v1p1beta1.SpeechClient()
        audio = speech_v1p1beta1.types.RecognitionAudio(uri=gcs_uri)

        response_5 = speech_v1p1beta1.SpeechClient().long_running_recognize(config, audio).result()
        for i, result in enumerate(response_5.results):
            for j in range(len(result.alternatives)):
                alternative = result.alternatives[j]
                print("-" * 20)
                print("First alternative of result {}".format(i))
                print("Transcript: {}".format(alternative.transcript))
        with open(file_name + '_' + str(args.stretch_constant) +'.pkl', 'wb') as f:
            pickle.dump(response_5, f)
        complete_string = ''
        for i in range(len(response_5.results)):
            complete_string += response_5.results[i].alternatives[0].transcript


        # complete_string = 'testing lala'
        # import time
        # time.sleep(30)
        #print(complete_string)
        text_file = open(file_name + '_' + str(args.stretch_constant) + ".txt", "w")
        text_file.write(complete_string)
        text_file.close()

        shutil.copyfile(audio_file_name + '.back', audio_file_name)
