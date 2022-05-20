import io
import csv
import os
import re
import gpxpy
import gpxpy.gpx
import math
import json
import requests
import subprocess
import bisect

from math import cos, asin, sqrt

import matplotlib.pyplot as plt

import numpy as np
from pydub import AudioSegment

import dropbox

import librosa
import librosa as lr
import librosa.display

import mpu
from datetime import datetime as dt

import sys
sys.path.append('..')
from yamnet.classifyAudio import classifyWav


WAV_FOLDER = os.environ.get('WAV_FOLDER')

# we temporarily store the chunks until we run the segmentation
WAVCHUNKS_FOLDER = os.environ.get('WAVCHUNKS_FOLDER')
PHASE_FOLDER = os.environ.get('PHASE_FOLDER')
GPX_FOLDER = os.environ.get('GPX_FOLDER')
DROPBOX_KEY = os.environ.get('DROPBOX_KEY')

# TODO: find from a set folder the right json - match timestamps and load urls


class GPXObj:

    def __init__(self, gpx_filePath, phase_filePath, wav_filePath):

        self.geoJson = None
        self.gpx_filePath = gpx_filePath

        with open(phase_filePath) as f:
            self.phase_File = json.load(f)
        self.wav_filePath = wav_filePath

        # we save the sound urls as a list
        self.sound_urls_lis = []

        # best points to a location
        self.best_points = []

        self.lat = None
        self.lon = None
        self.ele = None
        self.time = []
        self.speed = []
        self.bearing = []
        self.distance = []
        self.duration = []

        self.audio_chunk_splits = []

        # analysis part
        self.change_tempo_time = []
        self.change_tempo = []

        # we store the audio chunks here
        self.audio_chunks = []

        # we store the temp wavs here for segmentation
        self.tmp_wav_seg = []

        # parsing gpx
        self._parse_gpx(gpx_filePath)

        # gets the closest points
        self.assignClosestPhasePoint()

        # populate the analysis
        self.r_analysis()

        # upload the files to dropbox
        self.segment_sound_url()

        # craete geojson
        self.createGeoJson()

    def _calculate_initial_compass_bearing(self, pointA, pointB):
        """
            calculates the compass bearing  relative to north from 0-360 degrees
        """
        if (type(pointA) != tuple) or (type(pointB) != tuple):
            raise TypeError("Only tuples are supported as arguments")
        lat1 = math.radians(pointA[0])
        lat2 = math.radians(pointB[0])
        diffLong = math.radians(pointB[1] - pointA[1])
        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                * math.cos(lat2) * math.cos(diffLong))
        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing

    def _parse_gpx(self, gpx_filePath):
            """
                parses the gpx
            """

            gpx_file = open(gpx_filePath, 'r')
            gpx = gpxpy.parse(gpx_file)
            gpx = gpx.to_xml()

            reLat = r'lat="[-+]?[0-9]{2,3}(?:(?:\.[0-9]+)|(?:[0-9]+))"'
            reLon = r'lon="[-+]?[0-9]{2,3}(?:(?:\.[0-9]+)|(?:[0-9]+))"'
            eleV = r"<ele>[0-9]\d*.[0-9]+"
            reTime = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'

            all_lat = [float(latval[5:-1]) for latval in re.findall( reLat, gpx )]
            all_lon = [float(lonval[5:-1]) for lonval in re.findall( reLon, gpx )]

            all_time = [dt.strptime(timeval, "%Y-%m-%dT%H:%M:%S") for timeval in re.findall( reTime, gpx)[1:]]
            all_ele = [float(elval[5:]) for elval in re.findall( eleV, gpx )]

            self.lat = all_lat
            self.lon = all_lon
            self.ele = all_ele

            for i in range(0, len(all_lat)-1):

                pt_1 = (all_lat[i], all_lon[i])
                pt_2 = (all_lat[i+1], all_lon[i+1])

                curr_breaing = int(self._calculate_initial_compass_bearing(pt_1, pt_2))
                self.bearing.append(curr_breaing)

                curr_duration = (all_time[i+1] - all_time[i]).total_seconds()
                self.duration.append(int(curr_duration))

                curr_distance = round(mpu.haversine_distance(pt_1, pt_2)*1000, 2)
                self.distance.append(curr_distance)

                if curr_distance == 0 or curr_duration == 0:
                    self.speed.append(0.0)
                else:
                    self.speed.append(round(curr_distance/curr_duration, 3))

                self.time.append(all_time[i].strftime("%m/%d/%Y-%H:%M:%S"))

            # we remove the last point from lat/lon/ele
            self.lat = self.lat[:-1]
            self.lon = self.lon[:-1]
            self.ele = self.ele[:-1]



    def assignClosestPhasePoint(self):
        all_latlon = list(zip(self.lat, self.lon))
        phaseLoc = self.phase_File['phase']

        def distance(lat1, lon1, lat2, lon2):
            p = 0.017453292519943295
            a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
            return 12742 * asin(sqrt(a))

        all_dist = {}
        for phloc in phaseLoc:
            res = []
            for ll in all_latlon:
                res.append((distance(ll[1], ll[0], float(phloc['lat']), float(phloc['lon'])), ll, (phloc['lat'], phloc['lon'])))
            all_dist[phloc['name']] = sorted(res, key=lambda x: x[0])[:1]

        best_vals = []
        for phloc in phaseLoc:
            c = [top[1] for top in all_dist[phloc['name']]]
            c.append(phloc)
            best_vals.append(c)
        self.best_points = best_vals



    def createGeoJson(self):
        """
            creates a geoJSON as object paramenter
        """
        features = []

        # loop through all of the files
        for i in range(0, len(self.lat)):
            curr_row = { 'type': 'Feature',
                         'properties': {'time' : '',
                                        'speed': '',
                                        'bearing' : '',
                                        'elevation' : '',
                                        'distance': '',
                                        'duration':'',
                                        'sound':'',
                                        'phase':'',
                                        'image':'',
                                        },
                         'geometry':{'type':'Point',
                                      'coordinates':[]}
                       }

            curr_row['properties']['time'] = self.time[i]
            curr_row['properties']['speed'] = self.speed[i]
            curr_row['properties']['bearing'] = self.bearing[i]

            try:
                curr_row['properties']['elevation'] = self.ele[i]
            except:
                pass

            curr_row['properties']['distance'] = self.distance[i]
            curr_row['properties']['duration'] = self.duration[i]

            soundtmp = {
                        'url':'',
                        'semantic':'',
                        'analytic':''
                    }


            # loop through the sound urls
            # loop through the audio chunks

            # filter change tempo time
            # filter change tempo

            # feed the audio part

            start, end = self.audio_chunk_splits[i]
            st_idx = bisect.bisect(self.change_tempo_time, start)
            ed_idx = bisect.bisect(self.change_tempo_time, end)

            curr_ctt = self.change_tempo_time[st_idx:ed_idx]
            curr_ct = self.change_tempo[st_idx:ed_idx]
            url = self.sound_urls_lis[i]

            semantic = classifyWav(self.tmp_wav_seg[i], 3)

            soundtmp['url'] = url
            soundtmp['semantic'] = semantic
            soundtmp['analytic'] = {'change_tt':curr_ctt, 'change_t': curr_ct}
            curr_row['properties']['sound'] = soundtmp
            curr_row['geometry']['coordinates'] = [self.lon[i], self.lat[i]]

            for vals in self.best_points:
                for val in vals[:-1]:
                    if val[0] == self.lat[i] and val[1] == self.lon[i]:
                        curr_row['properties']['phase'] = vals[-1]

            print('soundtmp')
            print(soundtmp)
            #curr_row['properties']['sound'] = row['pic 1']
            features.append(curr_row)

        self.geoJson = { 'type': 'FeatureCollection', 'features': features }


    def saveGeoJson(self, outfilename):
        """
            saves the geojson to a folder
        """
        with open(outfilename, 'w') as outfile:
            json.dump({'type':'geojson', 'data': self.geoJson}, outfile)

    def parse_datename_to_json_name(self) -> str:
        """
            eg. Afternoon_Aug_1st.gpx --> 08012020_AM.json
        """

        filestr = ""
        file_name_gpx = self.gpx_filePath.split('/')[-1]
        month = {"Jun": "06", "Jul": "07", "Aug" : "08", "Sep":"09" }
        times = {"Afternoon":"AM", "Evening":"PM"}
        day = str(re.search(r"\d+", file_name_gpx).group())

        # the month
        filestr += str([month[m] for m in month.keys() if m in file_name_gpx][0])
        # the day
        if len(day) == 1: day = '0' + day
        filestr += day
        # the year
        filestr += "2020_"
        # the time
        filestr += str([times[t] for t in times.keys() if t in file_name_gpx][0])
        return filestr

    def parse_datename_to_dropbox_date(self) -> str:
        """
            eg. Afternoon_Aug_1st.gpx --> 0108
        """

        filestr = ""
        file_name_gpx = self.gpx_filePath.split('/')[-1]
        month = {"Jun": "06", "Jul": "07", "Aug" : "08", "Sep":"09" }
        times = {"Afternoon":"Aft", "Evening":"Eve"}
        day = str(re.search(r"\d+", file_name_gpx).group())

        # the day
        if len(day) == 1: day = '0' + day
        filestr += day

        # the month
        filestr += str([month[m] for m in month.keys() if m in file_name_gpx][0])

        ampm = str([times[t] for t in times.keys() if t in file_name_gpx][0])
        return (filestr, ampm)


    def segment_sound_url(self):

        try:
            subprocess.call(f"rm {WAVCHUNKS_FOLDER}*.wav", shell=True)
        except:
            pass


        dbx = dropbox.Dropbox(DROPBOX_KEY)
        dbx.users_get_current_account()

        # self. wavfile

        assert self.duration != None, 'calculate the duration first thrugh gpx'

        tot_dur = 0
        all_dur = []
        for i, dur in enumerate(self.duration):
            tot_dur += dur
            try:
                next_dur = tot_dur + self.duration[i+1]
                all_dur.append((tot_dur, next_dur))
            except:
                pass

        stereo_audio = AudioSegment.from_wav(self.wav_filePath)

        all_dur.insert(0, (0, all_dur[0][0]))

        print(all_dur)

        # here we need to upload to the right folder
        filedate, ampm = self.parse_datename_to_dropbox_date()
        naming = self.parse_datename_to_json_name()

        #---Creating Audio chunks 
        audio_chunks = []
        audio_paths = []

        for  idx,t in enumerate(all_dur):
            start, end = t

            self.audio_chunk_splits.append((start, end))
            start *= 1000
            end *= 1000
            #break loop if at last element of list
            if idx == len(all_dur):
                break
            print ("split at [ {}:{}] ms".format(start, end))
            audio_chunk=stereo_audio[start:end]
            audio_chunks.append(audio_chunk)

            curr_dbx_url = f"/Website_Repo/{filedate}/{ampm}/audio/{naming}_{str(end)}.mp3"

            buf = io.BytesIO()
            audio_chunk.export(buf, format='mp3', codec='mp3')

            # exporting for the segmentation
            audio_chunk.export(WAVCHUNKS_FOLDER + f'{naming}_{str(end)}.wav', format='WAV')
            self.tmp_wav_seg.append(WAVCHUNKS_FOLDER + f'{naming}_{str(end)}.wav')

            dbx.files_upload(buf.read(), curr_dbx_url, mode=dropbox.files.WriteMode('overwrite'))

            path_audio = curr_dbx_url
            shared_link = dbx.sharing_create_shared_link(path_audio,short_url=False,pending_upload=None)
            metaLink =shared_link.url.replace("https://www.dropbox.com","https://dl.dropboxusercontent.com").replace("dl=0","raw=1") # raw=1 for force render in browser
            audio_paths.append([metaLink])

            print(metaLink)


        self.sound_urls_lis = audio_paths
        self.audio_chunks = audio_chunks



    def r_analysis(self):

        """
            BPM analysis
        """
        y, sr = librosa.load(self.wav_filePath)

        # calculate onset of amplitude
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # calculate dynamic tempo estimation
        dtempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr,
                                aggregate=None)
        # get timestamps
        time_dtempo = librosa.frames_to_time(np.arange(len(dtempo)))
        change_tempo =[]
        change_tempo_time =[]

        ls_time_dtempo = time_dtempo.tolist()
        ls_dtempo = dtempo.tolist()

        for i in range(len(ls_dtempo)-1):
            if i==0:
                    change_tempo.append(round(ls_dtempo[i],3))
                    change_tempo_time.append(round(ls_time_dtempo[i],3))

            if ls_dtempo[i] != ls_dtempo[i+1]:
                    change_tempo.append(round(ls_dtempo[i+1],3))
                    change_tempo_time.append(round(ls_time_dtempo[i+1],3))

        #  Predominant local pulse --changing beats
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)

        # PLP local maxima can be used as estimates of beat positions.
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env)
        beats_plp = np.flatnonzero(librosa.util.localmax(pulse))
        times = librosa.times_like(onset_env, sr=sr)

        self.change_tempo_time = [round(val) for val in change_tempo_time]
        self.change_tempo = [round(val) for val in change_tempo]


    def __str__(self):
        return(f"numLat: {len(self.lat) or ''},\
                 numLon: {len(self.lon) or ''},\
                 numEle: {len(self.ele) or ''},\
                 numTime: {len(self.time) or ''},\
                 numSpeed: {len(self.speed) or ''},\
                 numBearing: {len(self.bearing) or ''},\
                 numDistance: {len(self.distance) or ''},\
                 numDuration: {len(self.duration) or ''}")

if __name__ == '__main__':

    testobj = GPXObj(GPX_FOLDER + "Afternoon_Jul_31st.gpx", PHASE_FOLDER + "Aft_PH3.json", WAV_FOLDER + "Aft_0731.wav")
    testobj.saveGeoJson("./geoJson_OUT/Afternoon_Jul_31st.json")

