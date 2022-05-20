import pandas as pd 
import json

route_vars = ['Part_of_the_Day','Month','Date'] 

#reading only the column of Duration and removing the string 'sec'
route_df = pd.read_csv('data/Data_table.csv',sep=',',header=0,names =route_vars)
route_df['Part_of_the_Day']=route_df['Part_of_the_Day'].str.replace("Aft","_AM").replace("Eve","_PM")
route_df['Month']=route_df['Month'].str.replace("Aug","08").replace("Jun","06").replace("Jul","07").replace("Sep","09")

for  day in route_df['Date']:
	if day in range(1,10):
		newday = "0" + str(day)
		route_df["Date"]=route_df["Date"].replace([day],newday)
print(route_df)

route_df["Dates"] = route_df['Month'].astype(str) + +route_df['Date'].astype(str)+ "2020"+ route_df["Part_of_the_Day"]
print(route_df["Dates"])
months =['06','07','08','09']
allmonths_data =[]
for month in months:
	if month == "06":
		for i in range(1,31):
			if i in range(1,10):
				doubledigit = '0'+str(i) 
				dateName = month + doubledigit
				date_NamePM= month + doubledigit+"2020_PM"
				date_NameAM= month + doubledigit +"2020_AM"
				allmonths_data.append(date_NamePM)
				allmonths_data.append(date_NameAM)		
			else:
				dateName = month +str(i)
				date_NamePM= month +str(i) +"2020_PM"
				date_NameAM= month + str(i) +"2020_AM"
				allmonths_data.append(date_NamePM)
				allmonths_data.append(date_NameAM)
	elif month == "07" or month == "08":
		for i in range(1,32):
			if i in range(1,10):
				doubledigit = '0'+str(i) 
				dateName = month + doubledigit
				date_NamePM= month + doubledigit+"2020_PM"
				date_NameAM= month + doubledigit +"2020_AM"
				allmonths_data.append(date_NamePM)
				allmonths_data.append(date_NameAM)
				
			else:
				dateName = month +str(i)
				date_NamePM= month +str(i) +"2020_PM"
				date_NameAM= month + str(i) +"2020_AM"
				allmonths_data.append(date_NamePM)
				allmonths_data.append(date_NameAM)
	elif month == "09":
		for i in range(1,6):
				doubledigit = '0'+str(i) 
				dateName = month + doubledigit
				date_NamePM= month + doubledigit+"2020_PM"
				date_NameAM= month + doubledigit +"2020_AM"
				allmonths_data.append(date_NamePM)
				allmonths_data.append(date_NameAM)		

true_false_list = {}
actual_data = list(route_df["Dates"])
for i,date in enumerate(allmonths_data):
	num_date = date.replace("_PM","").replace("_AM","")

	if date in actual_data:
		true_false_list[date]= {"value":True, "url":""}

	else:
		true_false_list[date]= {"value":False, "url":""}

print('\n'*5)

with open('dates_TrueFalse.json', 'w') as outfile:
	json.dump({"days": true_false_list},outfile)

print( {"days": true_false_list})





