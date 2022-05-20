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

import mpu
from datetime import datetime as dt

import sys
sys.path.append('..')



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

        # parsing gpx
        self._parse_gpx(gpx_filePath)

        # gets the closest points
        self.assignClosestPhasePoint()

        # create geojson
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
                        'cluster':''
                        
                    }

            url = self.sound_urls_lis[i] #to get from csv file

            soundtmp['url'] = url
            # soundtmp['cluster'] = getfromcsvfile
    
            curr_row['properties']['sound'] = soundtmp
            curr_row['geometry']['coordinates'] = [self.lon[i], self.lat[i]]

            for vals in self.best_points:
                for val in vals[:-1]:
                    if val[0] == self.lat[i] and val[1] == self.lon[i]:
                        curr_row['properties']['phase'] = vals[-1]

            print('soundtmp')
            print(soundtmp)
            curr_row['properties']['sound'] = row['pic 1']
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

    #this should change to input GPX, CSV with clusters, Aft_PH, Overall Phase csv
    testobj = GPXObj(GPX_FOLDER + "Afternoon_Jul_31st.gpx", PHASE_FOLDER + "Aft_PH3.json", WAV_FOLDER + "Aft_0731.wav")
    testobj.saveGeoJson("./geoJson_OUT/Afternoon_Jul_31st.json")

