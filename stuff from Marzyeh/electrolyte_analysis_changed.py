# -- - Get all the adult patients on their first ICU admission (unique HADMs, not unique SIDs)
from __future__ import division
import numpy as np
from scipy.stats import norm, mstats
import pandas as pd
import matplotlib
#matplotlib.use('Qt4Agg')   question: can this be deleted?
import matplotlib.pyplot as plt
import seaborn as sns
import itertools as it
#question: remove print statements?


def mk_test(x, alpha = 0.05):
    """
    This function is derived from code originally posted by Sat Kumar Tomer (satkumartomer@gmail.com)
    See also: http://vsp.pnnl.gov/help/Vsample/Design_Trend_Mann_Kendall.htm
    
    The purpose of the Mann-Kendall (MK) test (Mann 1945, Kendall 1975, Gilbert 1987) is to statistically assess if there is a monotonic upward or downward trend of the variable of interest over time. A monotonic upward (downward) trend means that the variable consistently increases (decreases) through time, but the trend may or may not be linear. The MK test can be used in place of a parametric linear regression analysis, which can be used to test if the slope of the estimated linear regression line is different from zero. The regression analysis requires that the residuals from the fitted regression line be normally distributed; an assumption not required by the MK test, that is, the MK test is a non-parametric (distribution-free) test.
    Hirsch, Slack and Smith (1982, page 107) indicate that the MK test is best viewed as an exploratory analysis and is most appropriately used to identify stations where changes are significant or of large magnitude and to quantify these findings.
    
    Input:
        x:   a vector of data
        alpha: significance level (0.05 default)
    
    Output:
        trend: tells the trend (increasing, decreasing or no trend)
        h: True (if trend is present) or False (if trend is absence)
        p: p value of the significance test
        z: normalized test statistics 
        
    Examples
    --------
      >>> x = np.random.rand(100)
      >>> trend,h,p,z = mk_test(x,0.05) 
    """
    n = len(x)
    
    # calculate S 
    s = 0
    for k in range(n-1):
        for j in range(k+1,n):
            s += np.sign(x[j] - x[k])
    
    # calculate the unique data
    unique_x = np.unique(x)
    g = len(unique_x)
    
    # calculate the var(s)
    if n == g: # there is no tie
        var_s = (n*(n-1)*(2*n+5))/18
    else: # there are some ties in data
        tp = np.zeros(unique_x.shape)
        for i in range(len(unique_x)):
            tp[i] = sum(unique_x[i] == x)
        var_s = (n*(n-1)*(2*n+5) + np.sum(tp*(tp-1)*(2*tp+5)))/18
    
    if s>0:
        z = (s - 1)/np.sqrt(var_s)
    elif s == 0:
            z = 0
    elif s<0:
        z = (s + 1)/np.sqrt(var_s)
    
    # calculate the p_value
    p = 2*(1-norm.cdf(abs(z))) # two tail test
    h = abs(z) > norm.ppf(1-alpha/2) 
    
    if (z<0) and h:
        trend = 'decreasing'
    elif (z>0) and h:
        trend = 'increasing'
    else:
        trend = 'no trend'
        
    return trend, h, p, z



def map_bin(x, bins):
	kwargs = {}
	if x == max(bins):
		kwargs['right'] = True
	bin = bins[np.digitize([x], bins, **kwargs)[0]]
	bin_lower = bins[np.digitize([x], bins, **kwargs)[0]-1]
	return '[{0}-{1}]'.format(bin_lower, bin)


# Read in tables and assign appropriate types
population = pd.read_csv('csv_files/electrolyte_population.csv')
population['intime'] = pd.to_datetime(population['intime'])
population['outtime'] = pd.to_datetime(population['outtime'])
population['gender'] = population['gender'].astype('category')
population['careunit'] = population['careunit'].replace('TSICU', 'SICU')

measures = pd.read_csv('csv_files/electrolyte_measures.csv')
measures['charttime'] =  pd.to_datetime(measures['charttime'])
measures['label'] = measures['label'].astype('category')


measures = measures.merge(population[['icustay_id', 'intime']])
measures['day'] = measures['charttime'] - measures['intime']
measures['dayint'] = measures['day'].apply(lambda d: d / np.timedelta64(1,'D'))


# Process the notes
notes = pd.read_csv('csv_files/electrolyte_notes.csv')
notes['charttime'] =  pd.to_datetime(notes['charttime'])

proc_notes = pd.read_pickle('small_notes.pickle')
proc_notes = proc_notes.merge(population[['icustay_id', 'intime']])


# truncate the first date from the intime and then set the "time" part of it to be midnight
start_day = measures['intime'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))
start_day_notes = proc_notes['intime'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))

# look at the things we might want to exclude by
iv_k     = (measures['label'] == 'k-incv') | (measures['label'] == 'k-inmv')
iv_mg    = (measures['label'] == 'mg-incv') | (measures['label'] == 'mg-inmv')
k_meas   = (measures['label'] == 'K-chart') | (measures['label'] == 'K-lab')
mg_meas  = (measures['label'] == 'Mg-chart') | (measures['label'] == 'Mg-lab')
lasix_in = (measures['label'] == 'lasix-inmv') | (measures['label'] == 'lasix-incv')
aa_in = (measures['label'] == 'aa-inmv') | (measures['label'] == 'aa-incv') | (measures['label'] == 'aa-chart')
hr_meas  = (measures['label'] == 'hr-chart')

def data_per_icu():  
	#day = 0

	# the start window for THIS day is the start win + day
	start_win = start_day + pd.Timedelta(days=(day+1))
	start_win_notes = start_day_notes + pd.Timedelta(days=(day+1))

	# then add + 5 hours to that start_win
	end_win = start_win + pd.Timedelta(hours=5)
	end_win_notes = start_win_notes + pd.Timedelta(hours=8)

	# find the right day 
	this_day = (measures['charttime'] >= start_win) & (measures['charttime'] <= end_win)
	this_day_notes = (proc_notes['charttime'] >= start_win_notes) & (proc_notes['charttime'] <= end_win_notes)

	#####
	# -- - For Day N:
	# --    Exclude patients who:
	# --    1) receive IV potassium or magnesium between 12 and 4 AM 
	# --    2) had their potassium or magnesium checked between 12 and 3 AM 
	# --    3) recived charted diuretics between 12 and 4 AM

	badids1 = this_day & (iv_k | iv_mg | lasix_in)
	badids2 = this_day & (k_meas | mg_meas) & (measures['charttime'].apply(lambda t: t.hour) < 3)
	bad_list = measures.ix[(badids1 | badids2),'icustay_id'].unique()

	# Now get some population statistics
	include = set(measures.ix[this_day,'icustay_id'].unique()) - set(bad_list)
	include_rows = measures['icustay_id'].isin(include)	
	this_population = population[population['icustay_id'].isin(include)]

	#####
	# X patients (Y icustays) were included for day Z
	# On day 1 there were 23,966 subjects (29,254 unique icustays) that fit the inclusion criteria,
	len(this_population['subject_id'].unique()) # Number of unique patients, per day
	len(this_population['icustay_id'].unique()) # number of unqiue icustay_ids, per day

	#####
	# -- Now include patients who:
	# --    1) Had a Mg/K measurement between 3 and 5 AM, multiple measures are ok, always take the later one chronologically
	goodids_k = this_day & (k_meas) & (measures['charttime'].apply(lambda t: t.hour) >= 3)
	goodids_mg = this_day & (mg_meas) & (measures['charttime'].apply(lambda t: t.hour) >= 3)

	#####
	#####
	#####
	# For intervention = k or mg......
	#####
	## First, look at potassium
	goodids = goodids_k;
	good_list = measures.ix[(goodids), 'icustay_id'].unique()
	include = set(good_list) - set(bad_list) # get the icustay_ids (people) to include
	include_rows = measures['icustay_id'].isin(include)	# now, get all the day_this measures and events rows FOR THESE IDS

	# Make a new table from the population that we're going to join on...
	this_population = population[population['icustay_id'].isin(include)]
	len(this_population)

	# Now extract the k values per person by sorting by the charttimes 
	#    and then take the last value from each element in the gorupby
	measures_today = measures[include_rows & goodids] # used to be k_meas and adding in the time window, now using the 
	measures_today = measures_today.sort_values('charttime')
	gb = measures_today.groupby(['icustay_id'])
	gb = gb.last()
	gb['icustay_id'] = gb.index

	# concat the k measures to the population df
	this_population = this_population.merge(gb[['icustay_id', 'valuenum']])
	this_population = this_population.rename(columns = {'valuenum':'last_lab_value'})
	len(this_population)

	## Count up cardiac events as defined by:
	# You had a (HR > 150 bpm form 12 - 4 am) AND (you had a charted medication (aa-meds))
	hr_measures_today = measures[include_rows & this_day & hr_meas]
	hr_measures_today = hr_measures_today.sort_values('valuenum')
	gb = hr_measures_today.groupby(['icustay_id'])
	gb = gb.last()
	gb['max_hr'] = gb['valuenum'] # > 150
	gb['icustay_id'] = gb.index

	# concat the hr measures to the population df
	this_population = pd.merge(left=this_population,right=gb[['icustay_id', 'valuenum']], how='left', on='icustay_id')
	this_population = this_population.rename(columns = {'valuenum':'max_hr'})
	len(this_population)

	# You had a ... AND (you had a charted medication (aa-meds))
	aa_in_today = measures[include_rows & this_day & aa_in]
	gb = aa_in_today.groupby(['icustay_id'])
	gb = gb.last()	
	gb['icustay_id'] = gb.index	                   # Take any value, it doesn't actually matter
	this_population = pd.merge(left=this_population,right=gb[['icustay_id', 'label']], how='left', on='icustay_id')
	this_population = this_population.rename(columns = {'label':'aa_label'})
	len(this_population)

	# --   1) You had a nurse note from midnight - 8am ish with certain words (defined in email) 
	include_note_rows = proc_notes['icustay_id'].isin(include)
	notes_today = proc_notes[include_note_rows & this_day_notes]
	notes_today = notes_today[['icustay_id','has_word']].groupby('icustay_id').any() #notes_today['has_word'] = notes_today['medications'] | notes_today['conditions']
	notes_today['icustay_id'] = notes_today.index	 
	this_population = pd.merge(left=this_population,right=notes_today[['icustay_id', 'has_word']], how='left', on='icustay_id')
	len(this_population)

	# Replaces all of the NUlls with None... 
	#this_population = this_population.where((pd.notnull(this_population)), None)

	# Print out some dataset statistics
	print day, len(this_population['subject_id'].unique()), 'unique patients WITH a K lab measured from 3-5AM'
	print day, len(this_population['icustay_id'].unique()), 'unqiue icustay_ids'
	print day, len(this_population[ (this_population['has_word'] == True) | ((this_population['max_hr'] > 110) & (this_population['aa_label'].notnull()))]), 'positive icustay_ids'

	include_criteria = (this_population['has_word'] == True) | ((this_population['max_hr'] > 110) & (this_population['aa_label'].notnull()))
	this_population['positive'] = include_criteria


	# Bin the measurements
	# The 6 bins for potassium are: <2.5, 2.51-3.0, 3.01-3.5, 3.51-4.0, 4.01-4.5, 4.51-5.0
	freq_bins = [0, 2.5, 3.0, 3.5, 4.0, 4.5, 1000]

	# PLOT THE HISTOGRAMS
	fig = plt.figure(figsize=(10,3))	
	# fig.set_xlabel('Binned Lab Values')

	icu_list = ['MICU', 'SICU', 'CCU' 'CSRU']	
	for icu in icu_list:
		subplot = fig.add_subplot(1,4,icu_list.index(icu)+1)
		if icu=='MICU':
			ax0 = subplot 
		icu_population = this_population[this_population['careunit'] == icu]	
		icu_population['binned'] = icu_population['last_lab_value'].apply(map_bin, bins=freq_bins)
		icu_population['binned'] = icu_population['binned'].replace('[4.5-1000]', '[>4.5]')

		grouped = icu_population[['binned', 'positive']].groupby('binned').agg(['count', 'sum'])
		grouped = grouped['positive']
		grouped['ratio'] = grouped['sum'] / grouped['count'] * 100
		grouped = grouped.reindex(['[0-2.5]', '[2.5-3.0]', '[3.0-3.5]', '[3.5-4.0]', '[4.0-4.5]', '[>4.5]'], fill_value=0)
		grouped['binned'] = grouped.index
		grouped[['binned', 'ratio']].plot(kind='bar', by='binned', ax=ax0, legend=False, rot=0)

		pos = np.arange(6)
		whereitgoes = grouped['ratio'].values
		ans = mk_test(whereitgoes, alpha = 0.05)
		# print ans[0], 'MICU', day

		upperLabels = ['{0} Patients'.format(e) for e in grouped['count'].values]
		upperLabels = grouped['count'].values
		
		subplot.set_ylim(0, 100)
		for tick, label in zip(range(6), subplot.get_xticklabels()):
			k = tick % 2
			subplot.text(pos[tick], whereitgoes[tick] + 5, upperLabels[tick], horizontalalignment='center', size='x-small')
		
		subplot.set_title('icu Day {0}'.format(day))  
		subplot.set_ylabel('Proportion with Cardiac Event')
		subplot.tick_params(axis='x', labelsize=5)
			
		vals = subplot.get_yticks()
		subplot.set_yticklabels(['{}%'.format(int(x)) for x in vals])








	#####
	#####
	#####
	# For intervention = k or mg......
	#####
	## First, look at potassium
	goodids = goodids_mg;
	good_list = measures.ix[(goodids), 'icustay_id'].unique()
	include = set(good_list) - set(bad_list) # get the icustay_ids (people) to include
	include_rows = measures['icustay_id'].isin(include)	# now, get all the day_this measures and events rows FOR THESE IDS

	# Make a new table from the population that we're going to join on...
	this_population = population[population['icustay_id'].isin(include)]
	len(this_population)

	# Now extract the k values per person by sorting by the charttimes 
	#    and then take the last value from each element in the gorupby
	measures_today = measures[include_rows & goodids] # used to be k_meas and adding in the time window, now using the 
	measures_today = measures_today.sort_values('charttime')
	gb = measures_today.groupby(['icustay_id'])
	gb = gb.last()
	gb['icustay_id'] = gb.index

	# concat the k measures to the population df
	this_population = this_population.merge(gb[['icustay_id', 'valuenum']])
	this_population = this_population.rename(columns = {'valuenum':'last_lab_value'})
	len(this_population)

	## Count up cardiac events as defined by:
	# You had a (HR > 150 bpm form 12 - 4 am) AND (you had a charted medication (aa-meds))
	hr_measures_today = measures[include_rows & this_day & hr_meas]
	hr_measures_today = hr_measures_today.sort_values('valuenum')
	gb = hr_measures_today.groupby(['icustay_id'])
	gb = gb.last()
	gb['max_hr'] = gb['valuenum'] # > 150
	gb['icustay_id'] = gb.index

	# concat the hr measures to the population df
	this_population = pd.merge(left=this_population,right=gb[['icustay_id', 'valuenum']], how='left', on='icustay_id')
	this_population = this_population.rename(columns = {'valuenum':'max_hr'})
	len(this_population)

	# You had a ... AND (you had a charted medication (aa-meds))
	aa_in_today = measures[include_rows & this_day & aa_in]
	gb = aa_in_today.groupby(['icustay_id'])
	gb = gb.last()	
	gb['icustay_id'] = gb.index	                   # Take any value, it doesn't actually matter
	this_population = pd.merge(left=this_population,right=gb[['icustay_id', 'label']], how='left', on='icustay_id')
	this_population = this_population.rename(columns = {'label':'aa_label'})
	len(this_population)

	# --   1) You had a nurse note from midnight - 8am ish with certain words (defined in email) 
	include_note_rows = proc_notes['icustay_id'].isin(include)
	notes_today = proc_notes[include_note_rows & this_day_notes]
	notes_today = notes_today[['icustay_id','has_word']].groupby('icustay_id').any() #notes_today['has_word'] = notes_today['medications'] | notes_today['conditions']
	notes_today['icustay_id'] = notes_today.index	 
	this_population = pd.merge(left=this_population,right=notes_today[['icustay_id', 'has_word']], how='left', on='icustay_id')
	len(this_population)

	# Replaces all of the NUlls with None... 
	#this_population = this_population.where((pd.notnull(this_population)), None)

	# Print out some dataset statistics
	print day, len(this_population['subject_id'].unique()), 'unique patients WITH an MG lab measured from 3-5AM'
	print day, len(this_population['icustay_id'].unique()), 'unqiue icustay_ids'
	print day, len(this_population[ (this_population['has_word'] == True) | ((this_population['max_hr'] > 110) & (this_population['aa_label'].notnull()))]), 'positive icustay_ids'

	this_population['positive'] = include_criteria


	# Bin the measurements
	# The 4 bins for magnesium are:
	freq_bins = [0, 1.5, 2.0, 2.5, 1000]

	# PLOT THE HISTOGRAMS
	fig = plt.figure(figsize=(10,3))	
	# fig.set_xlabel('Binned Lab Values')


	for icu in icu_list:
		subplot = fig.add_subplot(1,4,icu_list.index(icu)+1)
		if icu_list.index(icu)==0:
			ax0 = subplot
		icu_population = this_population[this_population['careunit'] == icu]	
		icu_population['binned'] = icu_population['last_lab_value'].apply(map_bin, bins=freq_bins)
		icu_population['binned'] = icu_population['binned'].replace('[2.5-1000]', '[>2.5]')

		grouped = icu_population[['binned', 'positive']].groupby('binned').agg(['count', 'sum'])
		grouped = grouped['positive']
		grouped['ratio'] = grouped['sum'] / grouped['count'] * 100
		grouped = grouped.reindex(['[0-1.5]', '[1.5-2.0]', '[2.0-2.5]', '[>2.5]'], fill_value=0)
		grouped['binned'] = grouped.index
		grouped[['binned', 'ratio']].plot(kind='bar', by='binned', ax=ax0, legend=False, rot=0)

		pos = np.arange(6)
		whereitgoes = grouped['ratio'].values
		ans = mk_test(whereitgoes, alpha = 0.05)
		print ans[0], icu, day, 'MG'

		upperLabels = ['{0} Patients'.format(e) for e in grouped['count'].values]
		upperLabels = grouped['count'].values
		
		subplot.set_ylim(0, 100)
		for tick, label in zip(range(len(whereitgoes)), subplot.get_xticklabels()):
			k = tick % 2
			_x = pos[tick]
			_y = whereitgoes[tick] + 5
			_z = upperLabels[tick]
			subplot.text(_x, _y, _z, horizontalalignment='center', size='x-small')   #question! error here

			# subplot.text(pos[tick], whereitgoes[tick] + 5, upperLabels[tick], horizontalalignment='center', size='x-small')   #question! error here
		
		subplot.set_title(icu + ' Day {0}'.format(day))
		subplot.set_ylabel('Proportion with Cardiac Event')
		subplot.tick_params(axis='x', labelsize=5)
		vals = subplot.get_yticks()
		subplot.set_yticklabels(['{}%'.format(int(x)) for x in vals])	


for day in xrange(3):  
	data_per_icu()  








#####
## Figure 2: Trend s in the values over days across all ICUs
#####
lab = k_meas    #fix this question
num_days = 5

ks = measures[lab]
k_start_day = ks['intime'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))

# add in the per day thing
for day in range(num_days):
	start_win = k_start_day + pd.Timedelta(days=(day+1))
	end_win = start_win + pd.Timedelta(hours=5)
	fill_in = (ks['charttime'] >= start_win) & (ks['charttime'] <= end_win)
	ks.ix[fill_in, 'which_day'] = (day+1) 

ks = ks.sort_values('charttime')
gb = ks.groupby('icustay_id')
t = gb.median()
t['icustay_id'] = t.index
t = t.rename(columns = {'valuenum':'median_lab'})
gb = gb.last()
gb['icustay_id'] = gb.index
gb = gb.merge(t[['icustay_id', 'median_lab']])

plot_data = gb[['which_day', 'median_lab']].groupby('which_day').agg(['mean', 'std', 'count'])

# Error bar plt the underlying values (mu,sigma) for each grouping of which_day in the x-axis
fig = plt.figure()
ax1 = fig.add_subplot(111)
gb[['which_day', 'median_lab']].boxplot(by='which_day', ax=ax1)

ax1.set_xlabel('Days')
ax1.set_ylabel('Lab Value')

# IF LOOKING AT K
ax1.set_title('Distribution of potassium values on the first ICU stay')
ax1.set_ylim(2, 6)
top = 6

# IF LOOKING AT Mg
ax1.set_title('Distribution of magnesium values on the first ICU stay')
ax1.set_ylim(0, 4)
top = 4

pos = np.arange(num_days) + 1
upperLabels = ['{0} Readings'.format(e) for e in plot_data['median_lab']['count'].values]
for tick, label in zip(range(num_days), ax1.get_xticklabels()):
	k = tick % 2
	ax1.text(pos[tick], top - (top*0.05), upperLabels[tick], horizontalalignment='center', size='x-small')


plt.savefig('MG_Readings_Figure.png')


####
## Figure 3,4,5: Histogram of values on on day 1, 2, 3 in the values over days across all ICUs
#####
lab = k_meas
num_days = 3

ks = measures[lab]
k_start_day = ks['intime'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))

# add in the per day thing
for day in range(num_days):
	start_win = k_start_day + pd.Timedelta(days=(day+1))
	end_win = start_win + pd.Timedelta(hours=5)

	this_k = ks[(ks['charttime'] >= start_win) & (ks['charttime'] <= end_win)]
	this_k = this_k.groupby('icustay_id')
	this_k = this_k.median()

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	this_k['valuenum'].hist() #(kind='bar', ax=ax1)
	ax1.set_xlabel('Lab Value')
	ax1.set_ylabel('Count')

	ax1.set_title('Distribution of potassium values on Day {0} of the ICU stay'.format(day))
	plt.savefig('K_hist_{0}.png'.format(day))

lab = mg_meas
num_days = 3

ks = measures[lab]
k_start_day = ks['intime'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))

# add in the per day thing
for day in range(num_days):
	start_win = k_start_day + pd.Timedelta(days=(day+1))
	end_win = start_win + pd.Timedelta(hours=5)

	this_k = ks[(ks['charttime'] >= start_win) & (ks['charttime'] <= end_win)]
	this_k = this_k.groupby('icustay_id')
	this_k = this_k.median()

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	this_k['valuenum'].hist() #(kind='bar', ax=ax1)
	ax1.set_xlabel('Lab Value')
	ax1.set_ylabel('Count')

	ax1.set_title('Distribution of potassium values on Day {0} of the ICU stay'.format(day))
	plt.savefig('MG_hist_{0}.png'.format(day))	


####
## Figure 6: Histogram of values on day 1 stratified by ICU
####
 


####
## Figure 7: Histogram of values on day 1 stratified by gender
####














