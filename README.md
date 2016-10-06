# Electrolyte Level/Cardiac Event Modelling - Team Blood Bath	

In this project, we pull the K and Mg levels out from the Phillips database, then we look for cardiac events that occur right beforehand. This is currently done by taking small time gap and then searching for anti arythmia drugs. 

We treat all potassium lab draws as unique events and ask for each lab draw if the patient on an antiarrhythmic (AA) medicine 2 hours prior. If not, we claim that the patient had no "cardiac events". Events will be binned per potassium level.  Percentage of lab draws within each bin that result in initiation of the AA in the proceeding 2 hours will be compared across potassium levels. We are making the assumption that the AA was started due to a “clinical event”, i.e. an arrhythmia.   

This is interesting to prove with high fidelity (due to time stamping of medications and lab draws) that certain potassium values are associated with a high rate of initiation of AA medications and therefore with “clinical events”. We can repeat the evaluation magnesium (again assuming that they are independent). 

Potassium levels separated into 8 bins (<2.49, 2.50-2.99, 3.00-3.49, 3.50-3.99, 4.00-4.49, 4.50-4.99, 5.00-5.49, >5.5) and serum magnesium levels into 4 bins (<1.49, 1.50-1.99, 2.00-2.49, >2.50).

Antiarrhythmic medications include intravenous administration: (adenosine, amiodarone, digoxin, diltiazem, esmolol, lidocaine, metoprolol, procainamide, or sotalol)

## MIMIC_Code
The legacy code for analysis in MIMICII is here. 

## code
Put code to generate data and results in here.

## resources
Put resources information in here. 

## data
Code should write data to here, but there is a gitignore so that data never gets synced on Github
