import os
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import sys

sys.path.append('./')

import yamnet.params as yamnet_params
import yamnet.yamnet as yamnet_model
import tensorflow as tf

import subprocess

PATH_YAMNET_CLASSES = "./yamnet/yamnet_class_map.csv"
PATH_YAMNET_WEIGHTS = "./yamnet/yamnet.h5"


def classifyWav(wavPath, topClasses):

    semanticResults = {}
    path = wavPath.split("/")
    filename = path[-1].split(".")[0]

    # this is our temp folder we read and write the channels to
    targetFolder = '/'.join(path[:-2]) + "/splitChannels/"

    channels = 2

    # we delete all of the content first in the temp folder
    try:
        subprocess.call(f"rm {targetFolder}*.wav", shell=True)
    except:
        pass

    if channels == 4:
        subprocess.call(f"ffmpeg -i '{wavPath}' -map_channel 0.0.0 {targetFolder + filename}_ch0.wav \
                                       -map_channel 0.0.1 {targetFolder + filename}_ch1.wav \
                                       -map_channel 0.0.2 {targetFolder + filename}_ch2.wav \
                                       -map_channel 0.0.3 {targetFolder + filename}_ch3.wav", shell=True)
    elif channels == 2:
        subprocess.call(f"ffmpeg -i '{wavPath}' -map_channel 0.0.0 {targetFolder + filename}_ch0.wav \
                                              -map_channel 0.0.1 {targetFolder + filename}_ch1.wav", shell=True)

    for i, wavfile in enumerate(os.scandir(targetFolder)):

        # the results of the current channel

        chResults = {}
        #print(wavfile.path)
        #print(wavfile.name)

        wav_data, sr = sf.read(wavfile.path, dtype=np.int16)
        waveform = wav_data / 32768.0

        # The graph is designed for a sampling rate of 16 kHz, but higher rates should work too.
        # We also generate scores at a 10 Hz frame rate.
        params = yamnet_params.Params(sample_rate=sr, patch_hop_seconds=1)

        # Set up the YAMNet model.
        class_names = yamnet_model.class_names(PATH_YAMNET_CLASSES)
        yamnet = yamnet_model.yamnet_frames_model(params)
        yamnet.load_weights(PATH_YAMNET_WEIGHTS)

        # Run the model.
        scores, embeddings, _ = yamnet(waveform)
        scores = scores.numpy()
        mean_scores = np.mean(scores, axis=0)

        # we take the top 3
        top_N = topClasses
        top_class_indices = np.argsort(mean_scores)[::-1][:top_N]

        # these are our scores rows = classes , cols = seconds
        top_scores = scores[:, top_class_indices].T
        yticks = range(0, top_N, 1)
        #class_names = [class_names[top_class_indices[x]] for x in yticks]

        # we need to match the classes later in the front - end
        class_names = top_class_indices

        for col in range(0, np.shape(top_scores)[-1]):
            curr_col = top_scores[:, col].flatten()
            chResults[col] = {int(cln):round(float(prct), 2) for cln, prct in zip(class_names, curr_col)}
        semanticResults[i] = chResults

        print(semanticResults)

    return semanticResults





if __name__ == '__main__':

    fourPath = "/home/lukas/99_TMP/05_Elina_Thesis/MIT_Thesis/data/wavFiles/4/200630_001.WAV"
    classifyWav(fourPath, 2)

