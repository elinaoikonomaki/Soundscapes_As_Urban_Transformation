import re
import csv
import glob
import json
import argparse
import pandas as pd

from parse_gpx import GPXObj as gpxobj

# 1. Paths to:
#   a. gpx file                 -- duration,lat,lon
#   b. allData_clusters.csv     -- cluster, xy_umap, filepath
#   c. phases_dates.csv         -- day/moth/date/phase


# 2. Loop through allData_clusters.csv file

# X. activedays.json needs to be updated after geojson is generated

parser = argparse.ArgumentParser()
parser.add_argument('--gpx_folder_path')
parser.add_argument('--data_clusters_csv_path')
parser.add_argument('--phases_dates_csv_path')
parser.add_argument('--phase_files_path')


args = parser.parse_args()


# {
#    'type': 'Feature',
#    'properties': {
#        # from gpx file
#        'duration': '3',
#        'phase': '2.1', # generate from matching gpx filename to phases_dates.csv
#        'chunks': [
#            # from --> allData_clusters.csv
#            {
#                'chunkFilepath': '/Users/elinaoik/Documents/MIT/THESIS-MIT/python/CLEAN/CHUNKS3/200731_001_Stereo/ChannelsTest/200731_001_Stereo_681_mono.wav',
#                'cluster': '0',
#                'xy_umap' : [1,2]
#            },
#            {
#                'chunkFilepath': '/Users/elinaoik/Documents/MIT/THESIS-MIT/python/CLEAN/CHUNKS3/200731_001_Stereo/ChannelsTest/200731_001_Stereo_681_mono.wav',
#                'cluster': '0',
#                'xy_umap' : [1,2]
#            },
#            {
#                'chunkFilepath': '/Users/elinaoik/Documents/MIT/THESIS-MIT/python/CLEAN/CHUNKS3/200731_001_Stereo/ChannelsTest/200731_001_Stereo_681_mono.wav',
#                'cluster': '0',
#                'xy_umap' : [1,2]
#            }
#        ],
#    },
#    'geometry': {
#        'type': 'LineString',
#        'coordinates': [
#            # from gpx file
#            [-122.483696, 37.833818],
#            [-122.483482, 37.833174],
#        ]
#    }
# }


def all_files_in_folder(gpx_folder_path: str, file_suffix: str) -> list:
    """ list of gpx filepaths """
    return glob.glob(f"{gpx_folder_path}/*.{file_suffix}")


def phase_url_from_phase_nr(datestr: str, phase_nr: str) -> str:
    """ 200606_PM & 3.1 --> PM_3_1 """
    am_pm = datestr.split('_')[-1]
    phase, subphase = str(phase_nr).split('.')
    return f"{am_pm}_{phase}_{subphase}"


def add_zero_to_date(date):
    """ 6 --> 06 """
    if len(str(date)) == 1:
        return f"0{date}"
    else:
        return date


if __name__ == '__main__':

    # all of the data clusters for all the days
    data_clusters = pd.read_csv(args.data_clusters_csv_path)
    # phases dates file
    phases_dates = pd.read_csv(args.phases_dates_csv_path)
    # list of files in the phase path
    phase_file_list = all_files_in_folder(args.phase_files_path, 'csv')
    # gpx fiile list
    gpx_paths = all_files_in_folder(args.gpx_folder_path, 'gpx')

    # updated filenames to match with gpx files
    # audio names set
    audio_names_updated = set()
    # get YYMMDD_AM unique filenames for matching with GPX FILES
    for idx, cluster_row in data_clusters.iterrows():
        audio_name = (cluster_row['AudioNames'])
        updated_name = '_'.join(audio_name.split('/')[-1].split('_')[:2])
        audio_names_updated.add(updated_name)

    # match phases with dates
    dates_phases = {}

    # match the audio files from the csv file
    for dates in list(audio_names_updated):
        # whith the file from the phases
        for idx, phases_dt in phases_dates.iterrows():
            date = add_zero_to_date(phases_dt['Date'])
            month = add_zero_to_date(phases_dt['Month'])
            datestr = f"20{month}{date}_{phases_dt['Part_of_the_Day']}"

            # get the right phase for the the right date
            if dates == datestr:
                phase_file = f"{phase_url_from_phase_nr(datestr, phases_dt['Phase'])}.csv"
                for phase_url in phase_file_list:
                    phase_url_short = phase_url.split('/')[-1]
                    if phase_url_short == phase_file:
                        dates_phases[dates] = {
                            'phase': phases_dt['Phase'], 'url': f"{phase_url.split('.')[0]}.json"}

    # create Objects containing all of the GPX data
    gpx_objects = []
    # create gpx file for each
    for gpx_file_name in gpx_paths:
        gpx_date = gpx_file_name.split('/')[-1].split('.')[0]
        try:
            curr_phase_f = dates_phases[gpx_date]['url']
        except KeyError as ke:
            continue
        with open(curr_phase_f) as f:
            phase_File = json.load(f)
        gpx_f = open(gpx_file_name, mode='r', encoding='utf-8-sig')
        curr_gpx_o = gpxobj(gpx_date, gpx_f, phase_File)
        curr_gpx_o.phase = curr_phase_f
        gpx_objects.append(curr_gpx_o)

    # match gpx files to wav dates
    for gpx_obj in gpx_objects:
        for idx, cluster_row in data_clusters.iterrows():
            match = re.search(r"[0-9]+_(?:AM|PM)", cluster_row['AudioNames'])
            if match:
                if match.group() == gpx_obj.gpx_date:
                    gpx_obj.add_chunk_path(cluster_row)

    for gpx_obj in gpx_objects:
        # sorting
        gpx_obj.chunk_paths = sorted(gpx_obj.chunk_paths, key=lambda x: int(
            x['AudioNames'].split('/')[-1].split('_')[-2]))
        # duration to millisec
        gpx_obj.duration_multi = [i*1000 for i in gpx_obj.duration]
        chunks_select = []

        # duration needs more than 100 points
        if len(gpx_obj.duration_multi) > 100:
            durations = iter(gpx_obj.duration_multi)
            curr_dur = next(durations)
            for i, chunk in enumerate(gpx_obj.chunk_paths):
                audio_chunk = int(chunk['AudioNames'].split(
                    '/')[-1].split('_')[-2]) * 960
                if audio_chunk + 960 <= curr_dur:
                    chunks_select.append(chunk)
                if audio_chunk > curr_dur:
                    gpx_obj.chunks_by_gps.append(chunks_select)
                    chunks_select = []
                    chunks_select.append(chunk)
                    try:
                        curr_dur = next(durations) + curr_dur
                    except StopIteration:
                        break

    for gpx_obj in gpx_objects:
        res = gpx_obj.to_geojson()

        with open(f"{gpx_obj.gpx_date}.json", "w") as outfile:
            json.dump(res, outfile)
