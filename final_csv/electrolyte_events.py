import pandas as pd 
import datetime
import pylab #analyze free form intake and medications
import math
import csv
#QUESTION: do I have to handle edge case: serum reading recorded twice, same timestamp
#procedure after this?
#test suite or not? testing without suite
#list_of_distinct_valid_icustay_ids = [list of icustay_ids that are adult w/first icu admission]
#queued: IV analysis, clinical fill-ins, paragraph for Leo

def generate_list_of_lasix_itemids():
	lasix=[1035, 1686, 2244, 2526, 4789, 5416, 12979, 15471]
	return lasix

# generates full list of all anti-arrhythmia drug itemids 
def generate_list_of_drug_itemids():
	drug_dictionary = {'metoprolol':[225974], 'esmolol':[221429, 2953, 30117], 'amiodarone': [2478, 7158, 30112, 42342, 221347, 228339], 'procainamide': [30052, 45853, 222151], 'Lidocaine':[30048, 225945], 'Diltiazem':[30115, 221468], 'Adenosine': [4649, 221282]}
	list_of_drug_itemids = []
	for drug in drug_dictionary.values():
		list_of_drug_itemids.extend(drug)
	return list_of_drug_itemids

#generates full list of all anti-arrhythmia drug names 
def generate_list_of_drug_names():
	drug_dictionary = {'metoprolol':[225974], 'esmolol':[221429, 2953, 30117], 'amiodarone': [2478, 7158, 30112, 42342, 221347, 228339], 'procainamide': [30052, 45853, 222151], 'Lidocaine':[30048, 225945], 'Diltiazem':[30115, 221468], 'Adenosine': [4649, 221282]}
	list_of_drug_names = []
	for drug in drug_dictionary.keys():
		list_of_drug_names.a(drug)
	return list_of_drug_names

#get a list of all the valid icustay ids (i.e. adult, first icu_stay)
def list_of_distinct_valid_icustay_ids():
	first_row = True
	icustay_id_set = []
	with open('valid_icustay_ids.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if first_row:
				first_row = False
			else:
				icustay_id_set.append(row[0])
	return icustay_id_set

#generates edit-distance-1 omission permutations
def omit_letter(drug_name):
	count = 0
	omissions_list = []
	for letter in drug_name:
		if count == 0:
			drug_name_copy = drug_name
			omissions_list.append(drug_name_copy[1:])
		else:
			omissions_list.append(drug_name_copy[:count] + drug_name_copy[count+1:])
		count+=1
	return omissions_list

#generates edit-distance-1 insertion permutations
def add_letter(drug_name):
	alphabet = 'qwertyuiopasdfghjklzxcvbnm'
	count = 0
	insertions_list = []
	for letter in drug_name:
		drug_name_copy = drug_name 
		#handles insertions before the first letter in the word
		if count == 0:
			for letter in alphabet:
				insertion = letter
				insertions_list.append(letter + drug_name_copy)
		#handles insertions in the middle of the word
		else:
			for letter in alphabet:
				insertion = letter
				insertions_list.append(drug_name_copy[:count] + insertion + drug_name_copy[count:])
		count+=1
	#handles insertions after the last letter of a word
	for letter in alphabet:
		insertion = letter
		insertions_list.append(drug_name_copy + letter)
	return insertions_list

#generates edit-distance-1 transposition
def switch_letters(drug_name):
	transpositions_list = []
	for letter_index in xrange(len(drug_name)):
		if letter_index == len(drug_name) - 1:
			break
		drug_name_copy = drug_name 
		first_letter = drug_name_copy[letter_index]
		second_letter = drug_name_copy[letter_index + 1]
		if letter_index == 0:
			transposed_word = second_letter + first_letter + drug_name_copy[2:]
		else:
			transposed_word = drug_name_copy[:letter_index] + second_letter + first_letter + drug_name_copy[letter_index+2:]
		transpositions_list.append(transposed_word)
	return transpositions_list 

#generate dictionary of words and words 1-edit-distance away
def make_spell_check_dictionary():
	alphabet = 'abcdefghijklmnopqrstuvwxyz'
	# list_of_drugs = generate_list_of_drug_names()
	list_of_drugs = ['hi']
	misspelled_dictionary = set()

	#insert all correctly spelled words into dictionary
	for drug in list_of_drugs:
		misspelled_dictionary.add(drug.lower()) 
		misspelled_dictionary.add(drug.upper()) 
		misspelled_dictionary.add(drug.capitalize()) 

	#insert all edit-distance-1 omissions into dictionary
	for drug in list_of_drugs:
		for word in omit_letter(drug):
			misspelled_dictionary.add(word.lower()) 
			misspelled_dictionary.add(word.upper()) 
			misspelled_dictionary.add(word.capitalize()) 

	#insert all edit-distance-1 insertions into dictionary
	for drug in list_of_drugs:
		for word in add_letter(drug):
			misspelled_dictionary.add(word.lower())
			misspelled_dictionary.add(word.upper())
			misspelled_dictionary.add(word.capitalize())  

	#insert all distance-1 transpositions (e.g.  hello --> hlelo, NOT hello --> ohell)
	for drug in list_of_drugs:
		for word in switch_letters(drug):
			misspelled_dictionary.add(word.lower()) 
			misspelled_dictionary.add(word.upper()) 
			misspelled_dictionary.add(word.capitalize())

	return misspelled_dictionary 


#takes in the desired electrolyte
#takes in icustay_id of desired patient
#returns an ordered list of all serium draw timestamps from that patient's icu stay
def get_date_range(electrolyte, icustay_id):
	icustay_id_column = 0
	charttime_column = 1
	valuenum_column = 2
	itemid_column = 3
	list_of_timestamps = []
	filename = electrolyte + "_final.csv"
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column]==str(icustay_id):
				timestamp_of_reading = pd.Timestamp(row[charttime_column])
				if len(list_of_timestamps) == 0:
					list_of_timestamps.append(timestamp_of_reading)
					set_of_timestamps = Set([timestamp_of_reading])
				else:
					if timestamp_of_reading not in set_of_timestamps:
						list_of_timestamps = binary_search_insertion(list_of_timestamps, timestamp_of_reading)
						set_of_timestamps.add(timestamp_of_reading)
	return list_of_timestamps


#takes in list of serum draw timestamps 
#takes in a timestamp to insert into the list of timestamps
#utilizes binary search to find correct index, inserts timestamp into list of timestamps
#returns mutated list
def binary_search_insertion(list_of_timestamps, timestamp_of_reading):
	lower_bound = 0
	upper_bound = len(list_of_timestamps)
	if timestamp_of_reading < list_of_timestamps[lower_bound]:
		list_of_timestamps.insert(0, timestamp_of_reading)
		return list_of_timestamps
	elif timestamp_of_reading > list_of_timestamps[upper_bound]:
		list_of_timestamps.append(timestamp_of_reading)
		return list_of_timestamps
	else:
		while upper_bound - lower_bound > 1:
			middle_bound = math.floor((upper_bound+lower_bound)*1.0/2)
			if timestamp_of_reading > list_of_timestamps[middle_bound]:
				lower_bound = middle_bound
			elif timestamp_of_reading < list_of_timestamps[middle_bound]:
				upper_bound = middle_bound
		list_of_timestamps.insert(upper_bound, timestamp_of_reading)
	return list_of_timestamps



#takes in icustay_id of desired patient
#takes in a desired date to check for anti-arrhythmia drug and lasix administration between 12-3am
#returns boolean, whether or not the patient received lasix or anti-arrhythmia drugs between 12-3am
def lasix_aadrug_administration(icustay_id, date):
	icustay_id_column = 0
	itemid_column = 1
	charttime_column = 2
	valuenum_column = 3
	with open('complete_drug_table_final.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column] == str(icustay_id):
				time_of_drug_admin = pd.Timestamp(row[charttime_column])
				if time_of_drug_admin.date()==date and (datetime.time(0) < time_of_drug_admin.time() < datetime.time(3)):
					return True 
	return False

#takes in the desired electrolyte
#takes in the desired date to check
#takes in the desired icu_id of a patient
#returns boolean, whether or not that patient had a serum draw on that day between 12-3 am
def invalidating_serum_measurement(electrolyte, icustay_id, date):
	icustay_id_column = 0
	charttime_column = 1
	valunum_column = 2
	itemid_column = 3
	filename = electrolyte + "_final.csv"
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column]==str(icustay_id):
				timestamp_of_reading = pd.Timestamp(row[charttime_column])
				if timestamp_of_reading.date() == date and (datetime.time(0) < timestamp_of_reading.time() < datetime.time(3)):
					return True
	return False


#takes in the desired electrolyte
#takes in the desired date to check
#takes in the desired icu_id of a patient
#returns boolean, whether or not that patient received only one serum measurement between 3-5am
def sole_valid_measurement(electrolyte, icustay_id, date):
	icustay_id_column = 0
	charttime_column = 1
	valunum_column = 2
	itemid_column = 3
	list_of_timestamps = []
	filename = electrolyte + "_final.csv"
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column]==str(icustay_id):
				timestamp_of_reading = pd.Timestamp(row[charttime_column])
				if timestamp_of_reading.date() == date and (datetime.time(3) < timestamp_of_reading.time() < datetime.time(5)):
					list_of_timestamps.append(timestamp_of_reading)
	if len(list_of_timestamps) != 1:
		return False
	return list_of_timestamps[0]


#takes in the icustay_id of a patient
#takes in the desired date of nurse's note (in pd.Timestamp.date()) format
#return the nurse's note for the designated patient on the designated day as a string
def get_nurse_note(icusay_id, date):
	icustay_id_column = 0
	charttime_column = 1
	note_column = 2
	with open('nurse_note_final.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column] == str(icustay_id):
				timestamp_of_event = pd.Timestamp(row[charttime_column])
				if timestamp_of_event.date() == date:
					return row[note_column]


#takes in the icustay_id of patient
#takes in the desired date of nurse's note (in pd.Timestamp.date()) format
#returns a boolean, whether or not nurse's note contains the name of an anti-arrhythmia drug in distance_1_drug_dictionary
def scan_nurse_note(icustay_id, date):
	distance_1_drug_dictionary = make_spell_check_dictionary()
	nurse_note = get_nurse_note(icustay_id, date)
	nurse_note_split = nurse_note.split()
	for word in nurse_note_split:
		if word in distance_1_drug_dictionary:
			return True 
	return False


#takes in icustay_id of desired patient
#takes in a desired date to check for heart rate event
#returns a boolean, whether or not the patient's heart rate reached or exceeded 150bpm between 12-4am that day
def heart_rate_event(icustay_id, date): 
	valid_readings = []
	icustay_id_column = 0
	charttime_column = 1
	valuenum_column = 2
	itemid_column = 3
	with open('heart_rate_final.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column] == str(icustay_id):
				timestamp_of_reading = pd.Timestamp(row[charttime_column])
				if timestamp_of_reading.date() == date:
					if datetime.time(0)<timestamp_of_reading.time()<datetime.time(4):
						valid_readings.append(row[valuenum_column])
	if len(valid_readings) != 1:
		return False
	if valid_readings[0] >= 150:
		return True 
	return False 




#takes in icustay_id of desired patient
#takes in a desired date to check for anti-arrhythmia drug administration
#returns boolean, whether or not the patient was given anti-arrhythmia drugs between 12-4 am on the desired day
def anti_arrhythmia_drug_event(icustay_id, date):
	icustay_id_column = 0
	itemid_column = 1
	charttime_column = 2
	valuenum_column = 3
	with open('complete_drug_table_final.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[icustay_id_column] == str(icustay_id):
				if row[itemid_column] in generate_list_of_drug_itemids():
					timestamp_of_event = pd.Timestamp(row[charttime])
					if timestamp_of_event.date() == date and (datetime.time(0) < timestamp_of_event.time()< datetime.time(4)):
						return True 
	return False



#takes in an icustay_id for a particular patient
#takes in a desired date
#returns a boolean, whether or not that patient had a clinical event between 12-4am that day
def event_check(icustay_id, date):
	return scan_nurse_note(icustay_id, date) or (anti_arrhythmia_drug_event(icustay_id, date) and heart_rate_event(icustay_id, date))

#generates a python dictionary with keys in the format (electrolyte, icustay_id, icu, day_number)
#and values in the format (reading_value, event_boolean)
#allows for easy histogram plotting
def generate_histogram_hash_table():
	histogram_hash_table = {}
	for electrolyte in ['magnesium', 'potassium']:
		for icu in ['CCU', 'CSRU', 'MICU', 'NICU', 'NWARD', 'SICU', 'TSICU']:
			for icustay_id in list_of_distinct_valid_icustay_ids():
				timestamp_index_counter = -1
				for timestamp in get_date_range(electrolyte, icustay_id):
					timestamp_index_counter+=1
					if lasix_aadrug_administration(icustay_id, timestamp.date()):
						continue
					if invalidating_serum_measurement(electrolyte, icustay_id, timestamp.date()):
						continue
					if sole_valid_measurement(electrolyte, icustay_id, timestamp.date())==False:
						continue
					if sole_valid_measurement(electrolyte, icustay_id, timestamp.date()) != False:
						reading = sole_valid_measurement(electrolyte, icustay_id, timestamp.date())
					event = event_check(icustay_id, date)
					tuple_to_hash = (electrolyte, icustay_id, icu, timestamp_index_counter)
					value_to_hash = (reading, event)
					histogram_hash_table[tuple_to_hash] = value_to_hash
	return histogram_hash_table

#generates and saves histograms for both Magnesium and Potassium
#plots data unseparated data, data separated by day and by icu
def generate_histograms():
	potassium_unfiltered_list = []
	magnesium_unfiltered_list = []
	potassium_day_filtered_hash = {}
	magnesium_day_filtered_hash = {}
	potassium_icu_filtered_hash = {}
	magnesium_icu_filtered_hash = {}

	electrolyte_dictionary = generate_histogram_hash_table()
	for ((electrolyte, icustay_id, icu, day_number), (reading, event)) in electrolyte_dictionary.items():
		if electrolyte=='magnesium' and event:
			magnesium_unfiltered_list.append(reading)
			if magnesium_icu_filtered_hash.get()==None:
				magnesium_icu_filtered_hash[icu] = [reading]
			else:
				magnesium_icu_filtered_hash[icu].append(reading)
			if magnesium_day_filtered_hash.get()==None:
				magnesium_day_filtered_hash[day_number] = [reading]
			else:
				magnesium_day_filtered_hash.append(reading)

		if electrolyte=='potassium' and event:
			potassium_unfiltered_list.append(reading)
			if potassium_icu_filtered_hash.get()==None:
				potassium_icu_filtered_hash[icu] = [reading]
			else:
				potassium_icu_filtered_hash[icu].append(reading)
			if potassium_day_filtered_hash.get()==None:
				potassium_day_filtered_hash[day] = [reading]
			else:
				potassium_day_filtered_hash[day].append(reading)

	#question: when to call pylab.figure()?

	for (icu, list_of_readings) in magnesium_icu_filtered_hash.items():
		 title = "Magnesium Levels in " + icu + "vs. Number of Clinical Events"
		 pylab.title(title)
		 pylab.xlabel("Electrolyte Levels")
		 pylab.ylabel("Number of Events")
		 bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
		 filename = icu + "_magnesium_hist_hist"
		 pylab.hist(list_of_readings, bins)
		 pylab.savefig(filename)

	for (icu, list_of_readings) in potassium_icu_filtered_hash.items():
		title = "Potassium Levels in " + icu + "vs Number of Clinical Events"
		pylab.title(title)
		pylab.xlabel("Electrolyte Levels")
		pylab.ylabel("Number of Events")
		bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
		filename = icu + "_potassium_icu_hist"
		pylab.hist(list_of_readings, bins)
		pylab.savefig(filename)

	for (day_number, list_of_readings) in magnesium_day_filtered_hash.items():
		title = "Magnesium Levels of Day " + day_number + "in ICU"
		pylab.title(title)
		pylab.xlabel("Electrolyte Levels")
		pylab.ylabel("Number of Events")
		bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
		filename = "magnesium_day_hist"
		pylab.hist(list_of_readings, bins)
		pylab.savefig(filename)

	for (day_number, list_of_readings) in potassium_day_filtered_hash.items():
		title = "Potassium Levels of Day " + day_number + "in ICU"
		pylab.title(title)
		pylab.xlabel("Electrolyte Levels")
		pylab.ylabel("Number of Events")
		bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
		filename = "potassium_day_hist"
		pylab.hist(list_of_readings, bins)
		pylab.savefig(filename)	


	list_of_readings = magnesium_unfiltered_list
	title = "Magnesium Levels vs Number of Events in ICU" 
	pylab.title(title)
	pylab.xlabel("Electrolyte Levels")
	pylab.ylabel("Number of Events")
	bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
	filename = "magnesium_hist"
	pylab.hist(list_of_readings, bins)
	pylab.savefig(filename)	


	list_of_readings = potassium_unfiltered_list
	title = "Potassium Levels vs Number of Events in ICU" 
	pylab.title(title)
	pylab.xlabel("Electrolyte Levels")
	pylab.ylabel("Number of Events")
	bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
	filename = "potassium_hist"
	pylab.hist(list_of_readings, bins)
	pylab.savefig(filename)	

print type(list_of_distinct_valid_icustay_ids())
