import csv
import pylab
import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd 

count = 0
data = []
with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>1:
			if row[3]=='':
				continue
			data.append(float(row[3]))
		count+=1
pylab.figure(1)
pylab.title('Frequency of Magnesium Levels')
pylab.xlabel('Magnesium Level')
pylab.ylabel('Number of Occurrences')
bins = [0,0.5,1.,1.5,2.,2.5,3,3.5,4,4.5,5]
pylab.hist(data,bins)
pylab.show()


count = 0
data = []
with open('potassium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>1:
			if row[3]=='':
				continue
			data.append(float(row[3]))
		count+=1

pylab.figure(2)
pylab.title('Frequency of Potassium Levels')
pylab.xlabel('Potassium Level')
pylab.ylabel('Number of Occurrences')
bins = [0,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,9]
pylab.hist(data,bins)
pylab.show()


count = 0
data = []
with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>0:
			if row[4]=='':
				continue
			timestamp = pd.Timestamp(row[4])
			hour = timestamp.hour
			data.append(hour)
		count+=1

pylab.figure(3)
pylab.title('Magnesium Measuring Times')
pylab.xlabel('Hours in Day')
pylab.ylabel('Number of Readings')
bins = range(24)
pylab.hist(data,bins)
pylab.show()



count = 0
data = []
with open('potassium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>0:
			if row[4]=='':
				continue
			timestamp = pd.Timestamp(row[4])
			hour = timestamp.hour
			data.append(hour)
		count+=1

pylab.figure(3)
pylab.title('Potassium Measuring Times')
pylab.xlabel('Hours in Day')
pylab.ylabel('Number of Readings')
bins = range(24)
pylab.hist(data,bins)
pylab.show()


count = 0
data = []
data_dict = {}
subject_id = None
with open('magnesium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>0:
			if subject_id == None:
				subject_id = row[0]
			if subject_id != row[0]:
				subject_id = row[0]
			if data_dict.get(subject_id) != None:
				data_dict[subject_id]+=1
			if data_dict.get(subject_id)==None:
				data_dict[subject_id]=1
		count+=1
data = data_dict.values()


pylab.figure(4)
pylab.title('Magnesium Measurements per Patients')
pylab.xlabel('Number of Times Measured')
pylab.ylabel('Number of Patients')
bins = range(0,40,2)
pylab.hist(data, bins)
pylab.show()

count = 0
data = []
data_dict = {}
subject_id = None
with open('potassium.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if count>0:
			if subject_id == None:
				subject_id = row[0]
			if subject_id != row[0]:
				subject_id = row[0]
			if data_dict.get(subject_id) != None:
				data_dict[subject_id]+=1
			if data_dict.get(subject_id)==None:
				data_dict[subject_id]=1
		count+=1
data = data_dict.values()


pylab.figure(4)
pylab.title('Potassium Measurements per Patients')
pylab.xlabel('Number of Times Measured')
pylab.ylabel('Number of Patients')
bins = range(0,40,2)
pylab.hist(data, bins)
pylab.show()





