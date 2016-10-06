-- Extract the initial population for the study
with init_pop as 
(
SELECT i.patienthealthsystemstayid as hadm_id, 
       i.patientunitstayid as icustay_id, 
       i.hospitalid as hospital,
       i.gender, 
       (Case When i.age = '> 89' Then 300 Else to_number(i.age) End) as age,
       i.unitvisitnumber as icustay_seq, 
       (Case When i.hospitaldischargestatus = 'Expired' Then 1 Else 0 End) as hospital_expire_flag,
       (Case When i.unitdischargestatus = 'Expired' Then 1 Else 0 End) as icu_expire_flag,
       (hospitaldischargeoffset - hospitaladmitoffset) as los_hospital, 
       i.unitdischargeoffset as los_icu, 
       i.unittype as careunit,
       i.unitstaytype,
       to_timestamp(to_char(unitadmityear) || '/01/01 ' || unitadmittime24, 'YYYY/MM/DD HH24:MI:SS') as intime, 
       to_timestamp(to_char(unitdischargeyear) || '/01/01 ' || unitdischargetime24, 'YYYY/MM/DD HH24:MI:SS') as outtime --, unitadmittime24, unitadmityear
       --to_date(unitadmittime24, to_char(unitadmityear))i.outtime,      
FROM EICU_V1.patients i
WHERE i.unitvisitnumber = 1
  and i.patienthealthsystemstayid < 200 -- Filter for speed
ORDER BY hadm_id, icustay_id
)
--select * from init_pop;
,

-- Limit based on the admission age
population as 
( select * from init_pop where age > 18 )
--select count(distinct hadm_id) from population; -- 1,955,313
--select count(distinct hospital) from population; -- 330
,

-- Get all the magnesium and potassium measures that occur from midnight to 5 am
mg_k_measures as (
select p.icustay_id, 
       l.labname as label, l.labresult as valuenum, 
       to_char(p.intime + l.labresultoffset/1440, 'YYYY/MM/DD HH24:MI:SS') as charttime,
       l.labresultoffset as min_from_icu_admit
       
from eicu_v1.lab l, 
     population p 
where l.patientunitstayid = p.icustay_id
  and (lower(l.labname) = 'magnesium' or lower(l.labname) = 'potassium')
  and labresult is not NULL
  and labresultoffset >= 0 and labresultoffset <= p.los_icu
  and EXTRACT (HOUR FROM to_timestamp(l.labresulttime24, 'HH24:MI:SS')) >= 0
  and EXTRACT (HOUR FROM to_timestamp(l.labresulttime24, 'HH24:MI:SS')) < 5
)
--select * from mg_k_measures order by icustay_id, charttime;
,
-- Extract the HR measures from midnight to 4 am,
hr_measures as (
select p.icustay_id, 
       'heartrate' as label, heartrate as valuenum, 
       to_char(p.intime + l.observationoffset/1440, 'YYYY/MM/DD HH24:MI:SS') as charttime,
       l.observationoffset as min_from_icu_admit
       
from eicu_v1.vitalperiodic l, 
     population p 
where l.patientunitstayid = p.icustay_id
  and heartrate is not NULL
  and observationoffset >= 0 and observationoffset <= p.los_icu
  and EXTRACT (HOUR FROM to_timestamp(l.observationtime24, 'HH24:MI:SS')) >= 0
  and EXTRACT (HOUR FROM to_timestamp(l.observationtime24, 'HH24:MI:SS')) < 4
)
--select * from hr_measures;
,

-- Extract Lasix medications that were given from midnight to 4am 
-- create table mghassem.
eicu_lasix_events as(
  -- take all the drugs from infusionevents
  select patientunitstayid as icustayid, infusionoffset as event_offset, 
         drugamount as total, drugname as drug_label, 'infusiondrug' as db_source
  from EICU_V1.INFUSIONDRUG 
  where drugamount is not null 
    and drugamount > 0
    and lower(drugname) like '%lasix%' or lower(drugname) like '%furosemide%'
    and EXTRACT (HOUR FROM to_timestamp(infusiontime24, 'HH24:MI:SS')) >= 0
    and EXTRACT (HOUR FROM to_timestamp(infusiontime24, 'HH24:MI:SS')) < 5
    
  UNION ALL
  
  -- take all the drugs from intake output that look like they are ins/not outs
  select patientunitstayid as icustayid, intakeoutputoffset as event_offset, 
         intaketotal as total, celllabel as drug_label, 'intakeoutput' as db_source
  from EICU_V1.INTAKEOUTPUT  
  where intaketotal is not null 
    and intaketotal > 0 
    and (lower(drugname) like '%lasix%' or lower(drugname) like '%furosemide%') 
    and lower(drugname) not in ('er urine after lasix', 
                                'er void post lasix', 
                                'ms4 urine after lasix',
                                'postpartum/met call lasix urine output', 
                                'qs lasix', 
                                'u.o. in rr (after lasix 40mg)', 
                                'urine after first dose lasix on a1', 
                                'urine from 4th post lasix', 
                                'urine output from floor after lasix', 
                                'urine post lasix/tele')
    and EXTRACT (HOUR FROM to_timestamp(intakeoutputtime24, 'HH24:MI:SS')) >= 0
    and EXTRACT (HOUR FROM to_timestamp(intakeoutputtime24, 'HH24:MI:SS')) < 5                                
)

-- TODO!!!!
-- 1) Extract the IV magnesium/potassium input events

-- 2) Extract anti-arythmia medications that were checked from midnight to 4am
-- metoprolol:[225974]
-- esmolol:[221429, 2953, 30117]
-- amiodarone: [2478, 7158, 30112, 42342, 221347, 228339]
-- procainamide: [30052, 45853, 222151]
-- Lidocaine:[30048, 225945]
-- Diltiazem:[30115, 221468]
-- Adenosine: [4649, 221282]
-- sotalol
-- digoxin




-- 3) NOT DOING THIS ANYMORE --- Look through the fake notes. (atrial fibrillation, ventricular fibrillation, ventricular tachycardia, cardioversion, torsades, torsades de pointes, supraventricular tachycardia, atrial tachycardia, AVNRT, or NSVT) correct?
--    Please include the words 'cardioversion', 'cardioverted"




-- BACKGROUND
--select distinct(celllabel) 
--from EICU_V1.INTAKEOUTPUT 
--where lower(celllabel) like '%metoprolol%'
--or lower(celllabel) like '%esmolol%'
--or lower(celllabel) like '%amiodarone%'
--or lower(celllabel) like '%procainamide%'
--or lower(celllabel) like '%lidocaine%'
--or lower(celllabel) like '%diltiazem%'
--or lower(celllabel) like '%adenosine%'
--or lower(celllabel) like '%sotalol%'
--or lower(celllabel) like '%digoxin%';
--
--select distinct(drugname) 
--from EICU_V1.INFUSIONDRUG 
--where lower(drugname) like '%metoprolol%'
--or lower(drugname) like '%esmolol%'
--or lower(drugname) like '%amiodarone%'
--or lower(drugname) like '%procainamide%'
--or lower(drugname) like '%lidocaine%'
--or lower(drugname) like '%diltiazem%'
--or lower(drugname) like '%adenosine%'
--or lower(drugname) like '%sotalol%'
--or lower(drugname) like '%digoxin%';
--
--
--select distinct(drugname) 
--from EICU_V1.medication 
--where lower(drugname) like '%metoprolol%'
--or lower(drugname) like '%esmolol%'
--or lower(drugname) like '%amiodarone%'
--or lower(drugname) like '%procainamide%'
--or lower(drugname) like '%lidocaine%'
--or lower(drugname) like '%diltiazem%'
--or lower(drugname) like '%adenosine%'
--or lower(drugname) like '%sotalol%'
--or lower(drugname) like '%digoxin%';
--


--select distinct(drugname) 
--from EICU_V1.medication 
--where lower(drugname) like '%lasix%' or lower(drugname) like '%furosemide%';
--
--select distinct(celllabel) 
--from EICU_V1.INTAKEOUTPUT 
--where lower(celllabel) like '%lasix%' or lower(celllabel) like '%furosemide%';
--
--select distinct(drugname) 
--from EICU_V1.INTAKEOUTPUT 
--where lower(celllabel) like '%lasix%' or lower(celllabel) like '%furosemide%';

