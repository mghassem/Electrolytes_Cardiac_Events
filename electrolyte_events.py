
'''
for each day and for each hostpital admission:
	be sure to line up patients' times on the first day
	find out the last electrolyte reading he had before midnight
	ignore them if they have a reading between midnight and 4am
	ignore them if they had lasix between midnight and 4am 
	over the course of the next day, find out how many events they have

approach:
	make a dictionary
	every time you find a new hadm_id, hash it
	every time you come across a new electrolyte reading, add it to the hadm_id's list

	now for each hadm_id:
		date = the first date you see
		find the last reading before midnight
		if they have a reading between 3am and 5am, ignore
		otherwise, find the number of events they had the following day 
'''
#first save then show
#copy into variable, then save variable

import pandas as pd 
import numpy as np 
import datetime
import pylab

Lasix=[1035, 1686, 2244, 2526, 4789, 5416, 12979, 15471]

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
		list_of_drug_names.append(drug)
	return list_of_drug_names

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
	list_of_drugs = generate_list_of_drug_names()
	misspelled_dictionary = {}

	#insert all correctly spelled words into dictionary
	for drug in list_of_drugs:
		misspelled_dictionary[drug.lower()] = True
		misspelled_dictionary[drug.upper()] = True
		misspelled_dictionary[drug.capitalize()] = True 

	#insert all edit-distance-1 omissions into dictionary
	for drug in list_of_drugs:
		for word in omit_letter(drug):
			misspelled_dictionary[word.lower()] = True 
			misspelled_dictionary[word.upper()] = True 
			misspelled_dictionary[word.capitalize()] = True 

	#insert all edit-distance-1 insertions into dictionary
	for drug in list_of_drugs:
		for word in add_letter(drug):
			misspelled_dictionary[word.lower()] = True 
			misspelled_dictionary[word.upper()] = True 
			misspelled_dictionary[word.capitalize()] = True 

	#insert all distance-1 transpositions (e.g.  hello --> hlelo, not hello --> ohell)
	for drug in list_of_drugs:
		for word in switch_letters(drug):
			misspelled_dictionary[word.lower()] = True 
			misspelled_dictionary[word.upper()] = True 
			misspelled_dictionary[word.upper()] = True 

	return misspelled_dictionary 

#returns the nurse note for that patient as a string
def get_note_text(hadm_id):
	with open('nursenotes.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[1]==str(hadm_id):
				return row[2]


#searches collection of nurses notes for mention of an anti-arrhythmia drug from 3-5 am on a particular day
def nurse_note(icustay_id, date):  
	#example date: date = "2682-10-3"
	#example of a timestamp: [**2830-3-12**] 10:45AM
	drug_dictionary = make_spell_check_dictionary()
	hadm_id = get_hadm_id_from_icustay_id(icustay_id)
	note_text = get_note_text(hadm_id)
	words_in_note_text= note_text.split()
	for word_index in xrange(len(words_in_note_text)):
		if words_in_note_text[word_index] == '[**' + str(date) + '**] ':
			check_for_drug_administration = True
		if check_for_drug_administration==True:
			if '[**' in words_in_note_text[word_index] and words_in_note_text[word_index] != '[**' + str(date) + '**] ':
				check_for_drug_administration = False
				break
			else: 
				if drug_dictionary.get(words_in_note_text[word_index]) != None:
					 return True 
	return False 

#takes in an icustay_id, outputs the admission time of that patient
def get_admission_time(icustay_id): 
	hadm_id = get_hadm_id_from_icustay_id(icustay_id)
	subject_id = get_subject_id_from_hadm_id(hadm_id) 
	with open('admissions.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if str(subject_id) == row[0]:
				return row[1]

#takes in an icustay_id, outputs the hadm_id associated with it
def get_hadm_id_from_icustay_id(icustay_id):
	with open('all_chartevents.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[2]==icustay_id:
				return row[1]

#takes in 
def blood_pressure_event(hadm_id, measurement_date): #speed this up later
	admit_time = get_admission_time(hadm_id)
	admit_time = pd.Timestamp(admit_time)
	time_since_admission = pd.Timestamp(measurement_date) - admit_time
	hours_since_admission = time_since_admission.hours()
	days_since_admission = time_since_admission.days()
	#time_index is the x index in the 3D matrix that indicates the heart rate at midnight on measurement_date
	time_index = 24*days_since_admission + hours_since_admission

#this relies on the assumption that all_chartevents.csv and big_matrix.npy have the same subject_id ordering
#query for big_matrix.npy: "select * from chartevents where ITEMID = " + str(ITEMID) # + " and SUBJECT_ID<200" #and SUBJECT_ID < 15000"
#by looking at it, both appear to be ordered by increasing subject_id
	count = 0
	with open('all_chartevents.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if str(row[0])==subject_id: 
				y_index = count
			count += 1
	for window_hours in xrange(3):
		if matrix[0][y_index][time_index + window_hours] >= 150:
			return True
		return False 

def drug_event(hadm_id, date):
	with open('drug_events.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[1]==str(hadm_id) and pd.Timestamp(row[3]).date() == pd.Timestamp(date).date():
				try:
					if int(row[2]) in generate_list_of_drug_itemids():
						return True
				except ValueError:
					print "Error Checking for Drug Event: empty or non-integer column in csv"
		return False

#takes in an icustay_id and date, returns whether or not a patient received lasix on that date between midnight and 4am. 
def lasix(icustay_id, date):
	with open('drug_events.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			#if a particular patient received lasix
			if row[2]==str(icustay_id) and row[3] in lasix:
				#if the lasix was recieved on the same date between midnight and 4am
				if  pd.Timestamp(row[4]).date()==date and (datetime.time(0)>pd.Timestamp(row[4]).time()>datetime.time(4)):
					return True
	return False

#checks if a particular patient had a clinical event between midnight and 4am on a particular day.
def check_for_event(icustay_id, date):
	event = False
	hadm_id = get_hadm_id_from_icustay_id(icustay_id)
	if blood_pressure_event(hadm_id) and drug_event(icustay_id, date):  
		event = True
	elif nurse_note(hadm_id, date):
		event = True
	if lasix(icustay_id, date):
		event = False
	return event

def get_icustay_id_from_subject_id(subject_id, icu):
	icustay_ids = []
	with open('transfers.csv', 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			if row[4] == icu:
				icustay_ids.append(row[2])
	if len(icustay_ids)==0:
		return None
	else:
		return icustay_ids 


#go through all patients and check if 
def generate_assorted_data():
	list_of_dictionary_tuples = []
	for electrolyte in ['magnesium', 'potassium']:
		filename = electrolyte + '.csv'
		for icu in ['CCU', 'CSRU', 'MICU', 'NICU', 'NWARD', 'SICU', 'TSICU']:
			events_dictionary = {}
			patient_counter = 0
			#look over each patient in electrolyte csv
			with open(filename, 'rb') as f:
				reader = csv.reader(f)
				for row in reader:
					#get all valid icustay_ids for a patient
					icustay_ids =  get_icustay_id_from_subject_id(row[0], icu) 
					if icustay_ids == None:
						continue
					for icustayid in icustay_ids:
						cut_off = None
						list_of_results = []
						#find last reading before 4am each day
						for row in reader:
							if row[2]==icustayid:
								timestamp = pd.Timestamp(row[4])
								electrolyte_level = row[3]
								try:
									if datetime.time(3) > timestamp.time() > datetime.time(5) and (timestamp.date() == time_frame_date):
										continue
								except NameError:
									pass
								if datetime.time(3) > timestamp.time() > datetime.time(5):   
									time_frame_date = timestamp.date()
									event_status = check_for_event(icustay_id, timestamp.date())
									list_of_results.append(electrolyte_level, event_status)
						(events_dictionary[icustayid], patient_counter) = list_of_results
						patient_counter+=1
			list_of_dictionary_tuples.append(events_dictionary, icu, electrolyte)

def plot_data():
	assorted_data = generate_assorted_data()
	#sort by alphabetically electrolyte, then by icu 
	sorted_by_icu_and_electrolyte = sorted(list_of_dictionary_tuples.items(),  key=lambda x: (x[2], x[1]))
	for data_tuple in sorted_by_icu_and_electrolyte:
		icu = data_tuple[1]
		electrolyte = data_tuple[2]
		dictionary = data_tuple[0]
		plotting_data
		for reading_tuple in dictionary.values():
			if reading_tuple[1] == True:
				plotting_data.append(reading_tuple[0])
		save_hist(electrolyte, icu, plotting_data)


def save_hist(electrolyte, icu, events_data):
	pylab.figure(0)
	title = electrolyte.capitalize() + 'Levels in ' + icu + ' vs. Number of Clinical Events'
	pylab.title(title)
	pylab.xlabel("Electrolyte Levels")
	pylab.ylabel("Number of Events")
	bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
	pylab.hist(events_data,bins)
	filename = icu + '_' + electrolyte + '_hist'
	pylab.savefig(filename)
	# pylab.plot()

print "unpacking matrix"
matrix = np.load('big_matrix.npy')
z,y,x = matrix.shape()
print "Done unpacking matrix"

plot_data()






	# first_row = True
	# hadm_id=None
	# data_dictionary = {}
	# with open('magnesium.csv', 'rb') as f:
	# 	reader = csv.reader(f)
	# 	for row in reader:
	# 		#ignores the top row
	# 		if first_row:
	# 			first_row = False
	# 			continue
	# 		#handles first case
	# 		if hadm_id==None:
	# 			hadm_id = row[1]
	# 		#handles hadm_id's not previously seen
	# 		if data_dictionary.get(hadm_id)==None:
	# 			data_dictionary[hadm_id] = [(row[3],row[4])]
	# 		#handles hadm_id's previously seen
	# 		else:
	# 			data_dictionary[hadm_id].append((row[3],row[4]))

	# total_events=[]
	# for hadm_id in data_dictionary.keys():
	# 	skip_day = False
	# 	new_day = False
	# 	time, date = None, None
	# 	for data_tuple in data_dictionary[hadm_id]:
	# 		timestamp = pd.Timestamp(data_tuple[1])
	# 		time = timestamp.time()
	# 		date = timestamp.date()
	# 		#handles first reading for a patient
	# 		if date == None or time == None:
	# 			current_date = date 
	# 			last_time = time 

	# 		#identify patients' last reading of the day

	# 		#conditionif it's the current day or before 3am the next day
	# 		if date == current_date: #or (date = (current_date + pd.Timedelta('1 day')) and time < datetime.time(3)):
	# 			last_time = time
	# 		elif datetime.time(0)>time>datetime.time(3):
	# 			skip_day = True
	# 			continue
	# 		elif time>datetime.time(3) and not skip_day:
	# 			subject_id = get_subject_id_from_hadm_id(hadm_id)
	# 			admission_time = get_admission_time(subject_id)
	# 			time_index = (timestamp - admission_time)/pd.Timedelta('1 hour')
	# 			event_bool = check_for_event(hadm_id, time_index)
	# 			if event_bool:
	# 				total_events.append(data_tuple[0])
	# 		elif time>datetime.time(3) and skip_day: 
	# 			skip_day = False









# pylab.figure(0)
# pylab.title("Magnesium Levels vs. Number of Clinical Events")
# pylab.xlabel("Magnesium Levels")
# pylab.ylabel("Number of Events")
# bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
# pylab.hist(total_events,bins)
# pylab.plot()













