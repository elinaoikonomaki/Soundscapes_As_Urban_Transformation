import json
import csv
import os.path


file = 'sites_selected.csv'


features = []
with open(os.path.abspath(file), newline='') as csvfile:

    # change the delimiter from \t to , and vice versa
    reader = csv.DictReader(csvfile, delimiter=',')
    for row in reader:
        curr_row = { 'type': 'Feature',
                     'properties': {'time' : '',
                                    'speed': '',
                                    'bearing' : '',
                                    'distance': '',
                                    'duration':'',
                                    'sound': {  'url':'',
                                                'semantic': {},
                                                'analytic': {}
                                              },
                                    'image': {
                                        'url':''
                                              }
                                    },
                     'geometry':{'type':'Point',
                                  'cooridnates':[]}
                   }

        curr_row['properties']['name'] = row['name']
        curr_row['properties']['lotnr'] = row['lot number']
        curr_row['properties']['address'] = row['address']
        curr_row['properties']['description'] = row['description']

        curr_row['properties']['occupation'] = row['occupation']
        curr_row['properties']['pic1'] = row['pic 1']
        curr_row['properties']['pic2'] = row['pic 2']
        curr_row['properties']['pic3'] = row['pic 3']

        curr_row['properties']['streetview'] = row['streetview link']
        curr_row['properties']['linkurl'] = row['linkurl']

        curr_row['geometry']['coordinates'] = [row['longitude'], row['latitude']]

        features.append(curr_row)

print(features)


with open('sites_selected.json', 'w') as outfile:
    json.dump({'type' : 'geojson', 'data' : { 'type': 'FeatureCollection', 'features': features }}, outfile)

