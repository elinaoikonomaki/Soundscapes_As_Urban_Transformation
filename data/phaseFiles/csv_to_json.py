import csv
import json
import glob

# Function to convert a CSV to JSON
# Takes the file paths as arguments
def make_json(csvFilePath, jsonFilePath):
    # create a dictionary
    phase = []
    # Open a csv reader called DictReader
    print(csvFilePath)
    with open(csvFilePath, encoding='utf-8-sig') as csvf:
        csvReader = csv.DictReader(csvf)
        # Convert each row into a dictionary
        # and add it to data
        for rows in csvReader:
            curr_data = {}

            print(rows)
            curr_data['lat'] = rows['Langtitude']
            curr_data['lon'] = rows['Longtitude']

            curr_data['name'] = rows['Name']
            curr_data['status'] = rows['Status']

            curr_data['bst'] = rows['BSt']
            curr_data['bb'] = rows['BB']

            curr_data['bb_or'] = rows['BB_Or']
            curr_data['bst_or'] = rows['BSt_Or']

            phase.append(curr_data)

 
    # Open a json writer, and use the json.dumps()
    # function to dump data
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps({"phase" : phase }, indent=2))


if __name__ == '__main__':
    csv_files = glob.glob("./*.csv")
    for file in csv_files:
        filename = file.split('/')[-1]
        make_json(file, f"{filename.split('.')[0]}.json")

