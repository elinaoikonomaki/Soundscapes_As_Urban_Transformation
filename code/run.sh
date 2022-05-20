#!/bin/sh

python3 generate_geojson.py \
	--gpx_folder_path '/Users/elinaoik/Documents/MIT/THESIS-MIT/analysis/01_Structure/data/GPX_files' \
	--data_clusters_csv_path '//Users/elinaoik/Documents/MIT/THESIS-MIT/analysis/01_Structure/data/allData_clusters0508.csv' \
	--phases_dates_csv_path '/Users/elinaoik/Documents/MIT/THESIS-MIT/analysis/01_Structure/data/phases_dates.csv' \
	--phase_files_path '/Users/elinaoik/Documents/MIT/THESIS-MIT/analysis/01_Structure/data/phaseFiles'
