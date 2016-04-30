import csv

first_row = True
intakeoutput = "SELECT * FROM EICU_ADM.INTAKEOUTPUT WHERE CELLLABEL IN ("
infusion_drug = "SELECT * FROM EICU_ADM.INFUSIONDRUG WHERE DRUGNAME IN ("
medication = "SELECT * FROM EICU_ADM.MEDICATION WHERE DRUGNAME IN ("
"SELECT * FROM EICU_ADM.MEDICATION WHERE DRUGNAME IN ("
with open('FINAL_AA_drugs_CSV.csv', 'rb') as f:
	reader = csv.reader(f)
	for row in reader:
		if first_row:
			first_row = False
			continue
		if len(row[0]) >=2:
			intakeoutput += "'" + row[0] + "'," 
		if len(row[1]) >= 2:
			infusion_drug += "'" + row[1] + "'," 
		if len(row[2]) >=2:
			medication += "'" + row[2] + "'," 
intakeoutput = intakeoutput[:-1] + ")"
infusion_drug = infusion_drug[:-1] + ")"
medication = medication[:-1] + ")"
print intakeoutput #asks for value for Diltiazem
print infusion_drug
print medication #asks for value for DR

##why do these queries ask me for a value for medications?
# for i in xrange(len(intakeoutput)):
# 	if intakeoutput[i:i+9]=="Diltiazem":
# 		print intakeoutput[(i-20):(i+20)]



