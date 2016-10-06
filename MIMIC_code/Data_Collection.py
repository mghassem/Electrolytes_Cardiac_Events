import pandas as pd
import sqlalchemy
import numpy as np
# import logging


# access mimic 3 data
engine=sqlalchemy.create_engine("mysql+pymysql://mimic3:password@safar.csail.mit.edu/mimiciii")

##Produces Dictionary with Subject_ID keyed to list of static values
def static_data(engine):
	#obtaining ages data
	ages_dictionary={}
	ages_data=pd.read_sql_query('select * from patients where DOD and SUBJECT_ID<100',engine)
	ages=ages_data['DOD']-ages_data['DOB']
	counter=0
	for elt in ages_data['SUBJECT_ID']:
		ages_dictionary[elt]=ages[counter]
		counter+=1
	for key in ages_dictionary.keys():
		value=str(ages_dictionary[key])
		value=value[:5]
		ages_dictionary[key]=[int(value)]

	#Gender Data
	gender_data=pd.read_sql_query("select * from patients where DOD and SUBJECT_ID<100",engine)
	counter=0
	for elt in ages_dictionary.keys():
		ages_dictionary[elt].append(gender_data['GENDER'][counter])
		counter+=1

	#Service Unit Data
	service_dictionary=ages_dictionary
	services_data=pd.read_sql_query('select * from services where SUBJECT_ID<100',engine)
	service_ids=[]
	for elt in services_data['SUBJECT_ID']:
		service_ids.append(elt)
	service_units=[]
	for elt in services_data['CURR_SERVICE']:
		service_units.append(elt)
	list_of_service_tuples=[]
	for elt in service_ids:
		a=elt
		b=service_units[service_ids.index(elt)]
		list_of_service_tuples.append((a,b))
	for elt in list_of_service_tuples:
		if service_dictionary.get(elt[0]) != None and len(service_dictionary[elt[0]])!=3:
			service_dictionary[elt[0]].append(elt[1])
	static_dictionary=service_dictionary
	return static_dictionary

#Produces Dictionary with Subject_ID keyed to list of (Value, Timestamp) tuples
def dynamic_data(ITEMID):
	dictionary={}
	patient_list=[]
	patient_data_list=[]
	time_stamps=[]
	print "running query"
	query="select * from chartevents where ITEMID = " + str(ITEMID) # + " and SUBJECT_ID<200" #and SUBJECT_ID < 15000"
	patient_data=pd.read_sql_query(query,engine)
	print "query complete"
	for patient in patient_data['SUBJECT_ID']:
		patient_list.append(patient)
	for value in patient_data['VALUENUM']:
		patient_data_list.append(value)
	for time in patient_data['CHARTTIME']:
		time_stamps.append(time)
	counter=0
	for patient in patient_list:
		if dictionary.get(patient)==None:
			dictionary[int(patient)]=[(int(patient_data_list[counter]),time_stamps[counter])]
		else:
			dictionary[int(patient)].append((int(patient_data_list[counter]),time_stamps[counter]) )	
		counter+=1
	for elt in dictionary.keys():
		dictionary[elt]=np.asarray(dictionary[elt])
	return dictionary

#Produces Dictionary with Subject_ID keyed to list of (Value, Timestamp) tuples, Blood Pressures only
def dynamic_data_bp(ITEMID):
	dictionary={}
	patient_list=[]
	patient_data_list=[]
	timestamp_list=[]
	query="select * from chartevents where ITEMID = " + str(ITEMID) + " and SUBJECT_ID<200"
	print "running query..."
	patient_data=pd.read_sql_query(query,engine)
	print "query complete. Processing Data..."
	for patient in patient_data['SUBJECT_ID']:
		patient_list.append(patient)
	for value in patient_data['VALUENUM']:
		patient_data_list.append(value)
	for time in patient_data['CHARTTIME']:
		timestamp_list.append(time)
	counter=0
	for patient in patient_list:
		if dictionary.get(patient)==None:
			dictionary[int(patient)]=[(int(patient_data_list[counter]), timestamp_list[counter])]
		else:
			dictionary[int(patient)].append((int(patient_data_list[counter]), timestamp_list[counter]))	
		counter+=1
	for elt in dictionary.keys():
		dictionary[elt]=np.asarray(dictionary[elt])
	print "finished extracting dynamic data"
	np.save('dynamic_data_bp_test',dictionary)
	return dictionary

#Produces Dictionary with Subject_ID keyed to list of (Value, Timestamp) tuples, Average Blood Pressure
def ABP():
	systolic=dynamic_data_bp(220051)
	diastolic=dynamic_data_bp(220050)
	subject_id_list=[]
	for subject_id in systolic.keys():
		if subject_id not in diastolic.keys():
			del systolic[subject_id]
	counter=0
	for subject_id in systolic.keys():
		while counter < min(len(systolic[subject_id]), len(diastolic[subject_id])):
			if systolic[subject_id][counter][1] != diastolic[subject_id][counter][1]:
				if systolic[subject_id][counter][1] < diastolic[subject_id][counter][1]:
					systolic = np.delete(systolic[subject_id], systolic[subject_id][counter]) #[1] just within ')'
				else:
					diastolic = np.delete(diastolic[subject_id], diastolic[subject_id][counter]) #[1] just within ')'
			else:
				systolic[subject_id][counter][0]=(float(systolic[subject_id][counter][0]) + diastolic[subject_id][counter][0])/2
				counter+=1
	abp_dictionary = systolic
	return abp_dictionary

#Equivelent of the .index() function in a list, but for numpy arrays
def get_numpy_index(item,array):
	counter=0
	for elt in array:
		if elt[1]==item[1]:
				return counter 
		counter+=1

#takes in dictionary from dynamic_data or dynamic_data_bp
#puts data into 1-hour "bins" and converts data into a 2D matrix. Saves matrix as .npy file
def make_bins(data_dict):
	print "executing make_bins function"
	## prepare data for use
	dictionary = data_dict
	hour = pd.Timedelta('1 hours')
	dataframe = pd.DataFrame(dictionary.items(),columns=['Subject_ID','Data'])
	which_patient_counter=0
	##determine the min/max times in all the data, find time span, prep for final matrix 
	matrix=None
	time_span = pd.Timedelta('0 hours')
	minimum=dataframe['Data'][0][0][1]
	maximum=dataframe['Data'][0][0][1]
	patient_counter=0
	print "determining size of matrix"
	for elt in dataframe['Data']:
		maximum = dataframe['Data'][patient_counter][0][1]
		minimum = maximum 
		for ele in elt:
			if ele[1]<minimum:
				minimum=ele[1]
			if ele[1]>maximum:
				maximum=ele[1]
		if (maximum-minimum)>time_span:
			time_span = maximum-minimum
		patient_counter+=1
	starting_index=int(str(time_span).index('s')+2)
	hours = int(str(time_span)[starting_index:starting_index+2])
	time_span = time_span.days*24 + hours
	print "putting data into bins"
	for patient in dataframe['Data']:
		##pivot = first timestamp in hour block
		pivot = dataframe['Data'][which_patient_counter][0][1]
		##prev_index = index of first data reading in that 1 hour block
		prev_index=0
		##index = index of first data reading after the 1 hour block
		data_avg=0
		index=0
		for reading in patient:	
			if abs(reading[1] - pivot) >= hour: 
				index = get_numpy_index(reading, patient)
				patient[prev_index][0]=round(data_avg/(float(index-prev_index)),2) 
				prev_index = index 
				pivot=patient[prev_index][1]
				data_avg = patient[prev_index][0]
			##for end-case
			if abs(reading[1]-patient[-1][1])<hour:
				data_avg=0
				try:
					for i in xrange(prev_index,patient.size):
						data_avg+=patient[i][0]
						patient[i][0]=0
				except IndexError:
					patient[prev_index][0]=data_avg/(patient.size/2.0-prev_index)
					break
			else: 
				data_avg+=reading[0] 
				reading[0]=0
			index+=1
		final_array=np.empty(time_span+1, dtype=tuple)
		# print "producing matrix"
		for reading in dataframe['Data'][which_patient_counter]:
			if reading[0]!=0:
				patient_time_icu=reading[1]-dataframe['Data'][which_patient_counter][0][1]
				starting_index=int(str(patient_time_icu).index('s')+2)
				patient_hours = int(str(patient_time_icu)[starting_index:starting_index+2])
				patient_time_icu=patient_time_icu.days*24 + patient_hours
				final_array[patient_time_icu]=(reading[0], reading[1])
		counter=0
		for elt in final_array:
			if elt==None:
				final_array[counter]=np.nan
			counter+=1
		try:
			matrix=np.vstack((matrix,final_array))
		except ValueError:
			matrix = final_array 
		which_patient_counter+=1 
	try:
		print "saving file"
		file_name = "data_for_itemid_" + str(ITEMID) 
		np.save(file_name,matrix)
		return matrix
	except:
		print "Error Trying to Save File"
		return True 


# ITEMID=220045 #Heart Rate
# make_bins(dynamic_data(ITEMID))

# ITEMID=220277 #SPO2
# make_bins(dynamic_data(ITEMID))

# ITEMID=223761 #Temperature
# make_bins(dynamic_data(ITEMID))

# ITEMID=220210 #Respiratory Rate
# make_bins(dynamic_data(ITEMID))

# ITEMID=220051 #Systolic Blood Pressure (Arterial)
# make_bins(dynamic_data(ITEMID))

# ITEMID="ABP" # "Average Blood Pressure"
# make_bins(ABP())

# ITEMID=220050 #Diastolic Blood Pressure (Arterial)

#Loads all 2D matrices produced by make_bins and concatenates them into a 3D matrix. Saves Matrix.
#z axis is the variables
#y axis is the patients
# x axis is the time
def concatenate_matrices():
	print "concatenating matrices"
	list_of_matrices = []
	set_of_matrices = ["data_for_itemid_220045.npy","data_for_itemid_220210.npy", 'data_for_itemid_220277.npy','data_for_itemid_223761.npy','data_for_itemid_ABP.npy','data_for_itemid_220051.npy']
	for matrix in set_of_matrices:
		list_of_matrices.append(np.load(matrix))
	max_x,max_y = 1,1
	for matrix in list_of_matrices:
		y,x = matrix.shape 
		if x>max_x:
			max_x = x
		if y >max_y:
			max_y = y
	z=len(list_of_matrices)
	mat_3d = np.empty((z,max_y, max_x))
	z_counter = 0
	print mat_3d.shape, "Matrix Dimensions"
	for matrix in list_of_matrices:
		y_counter=0
		for j in matrix:
			x_counter=0
			for i in j:
				if str(matrix[y_counter][x_counter])=='nan':
					mat_3d[z_counter][y_counter][x_counter]=np.nan
				else:
					mat_3d[z_counter][y_counter][x_counter] = matrix[y_counter][x_counter][0]
				if x_counter<(max_x-1):
					x_counter+=1
				else:
					break
			for elt in xrange(x_counter,max_x):		
				mat_3d[z_counter][y_counter][elt] = np.nan
			y_counter+=1
		for elt in xrange(y_counter,max_y):
			for value in xrange(max_x):
				mat_3d[z_counter][elt][value] = np.nan
		z_counter+=1
	np.save('big_matrix',mat_3d)
	print np.load('big_matrix.npy')
	
concatenate_matrices()
