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



import pandas as pd 
import numpy as np 
import datetime
import pylab

drug_dictionary = {'metoprolol':[225974], 'esmolol':[221429, 2953, 30117], 'amiodarone': [2478, 7158, 30112, 42342, 221347, 228339], 'procainamide': [30052, 45853, 222151], 'Lidocaine':[30048, 225945], 'Diltiazem':[30115, 221468], 'Adenosine': [4649, 221282]}
Lasix=[1035, 1686, 2244, 2526, 4789, 5416, 12979, 15471]
result = []
for drug in drug_dictionary.values():
	result.extend(drug)
#result is full list of all anti-arrhythmia drug itemids 




matrix = np.load('big_matrix.npy')
z,y,x = matrix.shape()
print "Done opening matrix"

def omit_letter(drug_name):
	count = 0
	final_list = []
	for letter in drug name:
		if count == 0:
			final_list.append(drug_name[1:])
		else:
			final_list.append(drug_name[:count - 1] + drug_name[count+1:])
	return final_list




def get_subject_id_from_hadm_id(hadm_id):
	with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if row[1]==hadm_id:
			subject_id = row[0]
	return subject_id

def get_admission_time(subject_id):
	with open('admissions.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		subject_id = row[0]:
		return row[1]

def blood_pressure_event(hadm_id, time_index):
	subject_id = get_subject_id_from_hadm_id(hadm_id)
	for potential_subject_id in xrange(y):
		if matrix[0][potential_subject_id][0]==int(subject_id):
			subject_id_index = potential_subject_id
			break
	for elt in xrange(3):
		if matrix[0][subject_id_index][time_index+elt] > 150:
			return True
	return False  


def drug_event(subject_id, time_index):
	time = time_index*pd.Timedelta('1 hour') + get_admission_time(subject_id)
	date = time.date()
	with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if row[0]==subject_id and row[4].date()==date
			return True
	return False 

def make_spell_check_dictionary(list_of_words):
	alphabet = 'qwertyuiopasdfghjklzxcvbnm'
	dictionary={}
	list_of_drugs = ['metoprolol', 'esmolol','amiodarone','digoxin','procainamide','lidocaine','diltiazem']
	misspelled_dictionary = {}
	for drug in list_of_drugs:
		misspelled_dictionary[drug] = True 
		for word in omit_letter(drug):
			misspelled_dictionary[word] = True 
		for letter in drug:
			for elt in alphabet:
				temp_drug = drug
				temp_drug[letter] = elt
				misspelled_dictionary[temp_drug] = True 
				temp_drug[]


def nurse_note(subject_id, date, note):
	with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		note = row[3]
		if check_text(date, list_of_words, note):
			return True
	return False
#[**2830-3-12**] 10:45AM

	for index in note:
		if note[index + 15] == '[**' + str(date) + '**] ': ##update this number later - 10
			starting_index = index 
	for character_index in note:
		pass
time = time_index*pd.Timedelta('1 hour') + get_admission_time(subject_id)
	date = time.date()
	

def check_for_event(hadm_id, time_index):
	event = False
	if blood_pressure_event(hadm_id) and drug_event(hadm_id, time_index):
		event = True
	if nurse_note(hadm_id):
		event = True
	return event

	#convert hadm_id to subject_id
	#find that subject_id's admission time/date
	#match up hadm_id's time with subject_id's time
	#look up subject_id in 3D matrix and check blood pressure at apprpriate time
	#check notes for administration of drug
	#check nurse's notes
	# return true for false




first_row = True
hadm_id=None
data_dictionary = {}
with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		#ignores the top row
		if first_row:
			first_row = False
			continue
		#handles first case
		if hadm_id=None:
			hadm_id = row[1]
		#handles hadm_id's not previously seen
		if data_dictionary.get(hadm_id)==None:
			data_dictionary[hadm_id] = [(row[3],row[4])]
		#handles hadm_id's previously seen
		else:
			data_dictionary[hadm_id].append((row[3],row[4]))

total_events=[]
for hadm_id in data_dictionary.keys():
	skip_day = False
	new_day = False
	time, date = None, None
	for data_tuple in data_dictionary[hadm_id]:
		timestamp = pd.Timestamp(data_tuple[1])
		time = timestamp.time()
		date = timestamp.date()
		#handles first reading for a patient
		if date = None or time = None:
			current_date = date 
			last_time = time 

		#identify patients' last reading of the day

		#conditionif it's the current day or before 3am the next day
		if date == current_date #or (date = (current_date + pd.Timedelta('1 day')) and time < datetime.time(3)):
			last_time = time
		elif datetime.time(0)>time>datetime.time(3):
			skip_day = True
			continue
		elif time>datetime.time(3) and not skip_day:
			subject_id = get_subject_id_from_hadm_id(hadm_id)
			admission_time = get_admission_time(subject_id)
			time_index = (timestamp - admission_time)/pd.Timedelta('1 hour')
			event_bool = check_for_event(hadm_id, time_index)
			if event_bool:
				total_events.append(data_tuple[0])
		elif time>datetime.time(3) and skip_day: 
			skip_day = False



pylab.figure(0)
pylab.title("Magnesium Levels vs. Number of Clinical Events")
pylab.xlabel("Magnesium Levels")
pylab.ylabel("Number of Events")
bins = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
pylab.hist(total_events,bins)
pylab.plot()













