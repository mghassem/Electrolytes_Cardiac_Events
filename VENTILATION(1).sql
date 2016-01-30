
SELECT  COUNT(*)  FROM VENTILATION;
SELECT  COUNT(*)  FROM VENTILATION2V26;

DROP MATERIALIZED VIEW VENTILATION;
DROP TABLE VENTILATION;

  CREATE TABLE VENTILATION
   (	"SUBJECT_ID" NUMERIC(7,0), 
	"ICUSTAY_ID" NUMERIC(7,0),  
	"BEGIN_TIME" TIMESTAMP (6) WITH TIME ZONE, 
	"END_TIME" TIMESTAMP (9) WITH TIME ZONE
   );
   --removed "SEQ" NUMERIC line from above
   
-- One change made to the CHARTEVENTS table in v3.0 is that we renamed charttime column to TIME and REALTIME column to VALIDATIONTIME
-- Takes around 115 seconds


  -- INSERT INTO VENTILATION ("SUBJECT_ID")    <-- This is super not legitimate 
  --   SELECT SUBJECT_ID                     
  --   FROM mimiciii.chartevents
  --     WHERE
  --       itemid IN ('720', '722');
  --  (
  --     SELECT 
  --       subject_id
  --     FROM
  --       mimiciii.chartevents
  --     WHERE
  --       (itemid IN ('720', '722')
  --       )

        --the end of my test code
  --)
  WITH
  ventilation_filter AS
  (
    SELECT DISTINCT
      subject_id,
      icustay_id,
      charttime  
    FROM
      mimiciii.chartevents
    WHERE
-- ITEMIDs which indicate ventilation
      itemid  IN ('720', '722', '224685', '682', '683', '224686', '684', '224684', '721')
    AND icustay_id IS NOT NULL
    ORDER BY
      icustay_id,
      charttime
  )
--Return results that is 'Y' or 'N' for new day
  ,
  ventilation_begin AS
  (
    SELECT
      vf.subject_id,
      vf.icustay_id,
      charttime,
      CASE
        WHEN EXTRACT(DAY FROM charttime - LAG(charttime) OVER (partition BY
          icustay_id ORDER BY charttime)) > 0
        THEN 'Y' --if more then a day has passed, flag as 'Y'
        WHEN LAG(charttime, 1) OVER (partition BY icustay_id ORDER BY charttime
          ) IS NULL
        THEN 'Y' --if lag is null, then > 24hrs has passed
        ELSE 'N'
      END AS new_day
    FROM
      ventilation_filter vf
  )
--select * from ventilation_begin; --504205 rows
--Return results that is 'Y' or 'N' for end_day
  ,
  ventilation_end AS
  (
    SELECT
      vf.subject_id,
      vf.icustay_id,
      charttime,
      CASE
        WHEN LEAD(new_day, 1) OVER (partition BY icustay_id ORDER BY charttime)
          = 'Y'
        THEN 'Y' --if lead is 'Y', then the current row is end
        WHEN LEAD(new_day, 1) OVER (partition BY icustay_id ORDER BY charttime)
          IS NULL
        THEN 'Y' --if lead is null, then partition is over
        ELSE 'N' --else not an end day
      END AS end_day
    FROM
      ventilation_begin vf
  )
--select * from ventilation_end; --504205 rows
--Return results that is 'Y' for new_day
  ,
  ventilation_assemble_begin AS
  (
    SELECT
      *
    FROM
      ventilation_begin
    WHERE
      new_day = 'Y'
  )
--select * from ventilation_begin_remove_no; -- 17994 rows
--Return results that is 'Y' for end_day
  ,
  ventilation_assemble_end AS
  (
    SELECT
      *
    FROM
      ventilation_end
    WHERE
      end_day = 'Y'
  )
--select * from ventilation_end_remove_no; -- 17994 rows
--Return results has a match of begin day with end day.  end_day is found by
-- min(end_day - begin_day) that has to be >= 0.
  ,
  ventilation_find_end_date AS
  (
    SELECT
      vab.subject_id,
      vab.icustay_id,
      vab.charttime, --BEGIN,
      MIN(vae.charttime - vab.charttime)
--  END
FROM
  ventilation_assemble_begin vab
JOIN ventilation_assemble_end vae
ON
  vab.icustay_id = vae.icustay_id
WHERE
  EXTRACT(DAY FROM vae.charttime - vab.charttime) >= 0
  GROUP BY
    vab.subject_id,
    vab.icustay_id,
    vab.charttime
  )


--select * from ventilation_find_end_date; -- 17994 rows
--Return results that has subject_id, icustay_id, seq, begin time, and end
-- time
  ,
  assemble AS
  (
    SELECT
      subject_id,
      icustay_id
      --row_number() over (partition BY icustay_id order by BEGIN) AS seq -- THIS DOESN'T EXIST
      -- create seq
      --BEGIN begin_time,  THIS DOESN'T EXIST
      --BEGIN + ALSO DOESN'T EXIST 
  --END end_time THIS DOESN'T EXIST
  FROM
      ventilation_find_end_date
  )
--SELECT
--  *
--FROM
-- assemble;
  ,
  final_subject_id AS
  (
    SELECT 
      subject_id
    FROM 
      assemble
  )
  ,
  final_icustay_id AS
  (
    SELECT
      icustay_id
    FROM 
    assemble
  ),


--Only one of these will work at once...  Question below

  -- INSERT INTO VENTILATION ("SUBJECT_ID")
  --   SELECT SUBJECT_ID
  --   FROM final_subject_id
  
  -- INSERT INTO VENTILATION ("ICUSTAY_ID")
  --   SELECT ICUSTAY_ID
  --   FROM final_icustay_id 


  
  -- INSERT INTO VENTILATION ("BEGIN_TIME")
  --   SELECT charttime
  --   FROM ventilation_find_end_date

  -- INSERT INTO VENTILATION ("END_TIME")
  --   SELECT charttime
  --   FROM ventilation_begin

    --INSERT INTO VENTILATION ("SUBJECT_ID", "ICUSTAY_ID")
--        select subject_id, icustay_id, 

 
TEMP AS(
  SELECT ventilation_begin.SUBJECT_ID, ventilation_begin.ICUSTAY_ID,ventilation_begin.charttime, ventilation_end.charttime as charttime_end
    FROM ventilation_begin JOIN ventilation_end ON ventilation_begin.SUBJECT_ID=ventilation_end.SUBJECT_ID AND ventilation_begin.ICUSTAY_ID=ventilation_end.ICUSTAY_ID
)
--ALTER TABLE RENAME ventilation_end COLUMN charttime to charttime2 --'VENTILATION.charttime', 'charttime2', 'COLUMN'

INSERT INTO VENTILATION ("SUBJECT_ID", "ICUSTAY_ID", "BEGIN_TIME", "END_TIME")
SELECT SUBJECT_ID, ICUSTAY_ID, charttime_end, charttime FROM TEMP;



  

SELECT  COUNT(*)  FROM VENTILATION;

-- delete patients patients younger than 18 
DELETE FROM VENTILATION
WHERE "SUBJECT_ID" IN (
SELECT PATIENTS.SUBJECT_ID
FROM MIMICiii.ADMISSIONS,  
     MIMICiii.PATIENTS  
WHERE PATIENTS.SUBJECT_ID = ADMISSIONS.SUBJECT_ID
AND (CAST(ADMISSIONS.ADMITTIME AS DATE) - CAST(PATIENTS.DOB AS DATE)) < 18 * 365 -- patients younger than 18
);

  
SELECT  COUNT(*)  FROM VENTILATION;


-- add CUID  
ALTER TABLE VENTILATION ADD CUID NUMERIC(7,0);

SELECT *  FROM VENTILATION;


--Question Below, between error comments

--ERRORS BELOW
--CUID doesn't exists, even in mimic 2



-- SELECT CENSUSEVENTS.CUID, VENTILATION.ICUSTAY_ID FROM VENTILATION, MIMIC2V30.CENSUSEVENTS --Error
--  WHERE VENTILATION.ICUSTAY_ID = CENSUSEVENTS.ICUSTAY_ID
--  AND VENTILATION.BEGIN_TIME >= CENSUSEVENTS.INTIME --Error
--  AND VENTILATION.END_TIME <= CENSUSEVENTS.OUTTIME  --Error
--  ORDER BY VENTILATION.ICUSTAY_ID ASC
-- ;  --transfers table hostp admission id maps to icustay ids


SELECT TRANSFERS.HADM_ID, VENTILATION.ICUSTAY_ID FROM VENTILATION, MIMICiii.TRANSFERS
  WHERE VENTILATION.ICUSTAY_ID = TRANSFERS.ICUSTAY_ID
  AND VENTILATION.BEGIN_TIME >= TRANSFERS.INTIME
  AND VENTILATION.END_TIME <= TRANSFERS.OUTTIME
  ORDER BY VENTILATION.ICUSTAY_ID ASC
;

-- -- runs in 500 seconds
-- UPDATE VENTILATION
-- SET VENTILATION.CUID = (SELECT DISTINCT(CENSUSEVENTS.CUID)
-- FROM MIMIC2V30.CENSUSEVENTS  --Error
--  WHERE VENTILATION.ICUSTAY_ID = CENSUSEVENTS.ICUSTAY_ID
--  AND VENTILATION.BEGIN_TIME >= CENSUSEVENTS.INTIME  
--  AND VENTILATION.END_TIME <= CENSUSEVENTS.OUTTIME 
--  )
-- ;  

--runs in 500 seconds
UPDATE VENTILATION
SET VENTILATION.HADM_ID = (SELECT DISTINCT(TRANSFERS.HADM_ID)
FROM MIMICiii.TRANSFERS
  WHERE VENTILATION.ICUSTAY_ID=TRANSFERS.ICUSTAY_ID
  AND VENTILATION.BEGIN_TIME>=TRANSFERS.INTIME
  AND VENTILATION.END_TIME<= TRANSFERS.OUTTIME
  )
;

COMMIT;

-- SELECT VENTILATION.CUID,  COUNT(*) cnt  FROM VENTILATION
-- GROUP BY VENTILATION.CUID
--  ORDER BY cnt DESC 
-- ;

SELECT VENTILATION.HADM_ID, COUNT(*) cnt FROM VENTILATION
GROUP BY VENTILATION.HADM_ID
  ORDER BY cnt DESC
;

-- SELECT VENTILATION.ICUSTAY_ID,  COUNT(*) cnt,  COUNT(DISTINCT(VENTILATION.CUID)) cnt_distinct  FROM VENTILATION
-- GROUP BY VENTILATION.ICUSTAY_ID
--  ORDER BY cnt_distinct DESC, cnt DESC; 

SELECT VENTILATION.HADM_ID, COUNT(*) cnt, COUNT(DISTINCT(VENTILATION.HADM_ID)) cnt_distinct FROM VENTILATION
GROUP BY VENTILATION.ICUSTAY_ID
  ORDER BY cnt_distinct



--ERRORS ABOVE



-- add TIDAL_VOL_SET_MEAN 
--ALTER TABLE VENTILATION DROP COLUMN TIDAL_VOL_SET_MEAN;    <-- This never existed 
ALTER TABLE VENTILATION ADD TIDAL_VOL_SET_MEAN NUMERIC(4,0);

--Question below (1 line below) on round()

SELECT ICUSTAY_ID, AVG(CHARTEVENTS.VALUENUM), CAST(AVG(CHARTEVENTS.VALUENUM) AS FLOAT(1))  FROM MIMICiii.CHARTEVENTS, VENTILATION 
WHERE ICUSTAY_ID = CHARTEVENTS.ICUSTAY_ID
AND SUBJECT_ID = CHARTEVENTS.SUBJECT_ID -- for speedup due to the (SUBJECT_ID, ICUSTAY_ID) index
AND ICUSTAY_ID = 10
AND CHARTEVENTS.ITEMID IN ('683', '224684')
--GROUP BY ICUSTAY_ID ;

-- runs in ?? seconds (took a while, maybe 1000-2000 seconds)   Question Below
UPDATE VENTILATION
SET TIDAL_VOL_SET_MEAN = 
(
  SELECT CAST(AVG(CHARTEVENTS.VALUENUM) AS FLOAT(1)) FROM MIMICiii.CHARTEVENTS --Swapped round for float cast, I expect it to return multiple rows but this caused an error
  WHERE ICUSTAY_ID = CHARTEVENTS.ICUSTAY_ID
  AND SUBJECT_ID = CHARTEVENTS.SUBJECT_ID -- for speedup due to the (SUBJECT_ID, ICUSTAY_ID) index
  AND CHARTEVENTS.ITEMID IN ('683', '224684')
  AND CHARTEVENTS.VALUENUM > 50 -- remove noise
  --GROUP BY ICUSTAY_ID
)  --ERROR:  more than one row returned by a subquery used as an expression
;

COMMIT;


SELECT  *  FROM VENTILATION;

-- add TIDAL_VOL_OBS_MEAN 
--ALTER TABLE VENTILATION DROP COLUMN TIDAL_VOL_OBS_MEAN;
ALTER TABLE VENTILATION ADD TIDAL_VOL_OBS_MEAN NUMERIC;

-- runs in 1786 seconds           Question Below
UPDATE VENTILATION
SET TIDAL_VOL_OBS_MEAN = (
  SELECT CAST((AVG(CHARTEVENTS.VALUENUM)) AS FLOAT(1))  FROM MIMICiii.CHARTEVENTS --Swapped ROUND for float cast, I expect it to return multiple rows but this caused an error
  WHERE ICUSTAY_ID = CHARTEVENTS.ICUSTAY_ID
  AND SUBJECT_ID = CHARTEVENTS.SUBJECT_ID -- for speedup due to the (SUBJECT_ID, ICUSTAY_ID) index
  AND ITEMID IN ('682', '224685') 
  AND VALUENUM > 10 -- remove noise
  --GROUP BY ICUSTAY_ID
)  --ERROR:  more than one row returned by a subquery used as an expression
;

COMMIT;


-- add DURATION_IN_SEC column 
ALTER TABLE VENTILATION ADD DURATION_IN_SEC NUMERIC;


UPDATE VENTILATION
SET DURATION_IN_SEC = 
EXTRACT (DAY FROM CAST(CAST("END_TIME" AS date) - CAST("BEGIN_TIME" AS date) AS INTEGER))*24*60*60 --this causes type errors but shouldn't once I insert all columns
--+ EXTRACT(HOUR FROM 'END_TIME' - 'BEGIN_TIME')*60*60 --potentially would follow same format as above
--+ EXTRACT(MINUTE FROM 'END_TIME' - 'BEGIN_TIME')*60 --potentially would follow same format as above
--+ EXTRACT(SECOND FROM 'END_TIME' - 'BEGIN_TIME') --potentially would follow same format as above
;


COMMIT;


-- add PERCENT_DURATION_FOR_HADM_ID column 
-- needs to have HADM_STATS.MV_TOTAL_DURATION populated first
ALTER TABLE VENTILATION ADD PERCENT_DURATION_FOR_HADM_ID NUMERIC; -- e.g. if one row contains '0.15', it means that 15% of the time the hadm_id was under MV, he was in this particular MV event

--Question below
--Errors Below

ALTER TABLE VENTILATION ADD VENTILATION_TOTAL_TIME NUMERIC;

UPDATE VENTILATION
 SET VENTILATION_TOTAL_TIME(
  select sum("END_TIME"-"BEGIN_TIME")
  from ventilation
  group by "HADM_ID";
);






-- -- runs in 331 seconds
-- UPDATE VENTILATION
-- SET VENTILATION.PERCENT_DURATION_FOR_HADM_ID = (
-- SELECT 
-- CASE
--   WHEN HADM_STATS.MV_TOTAL_DURATION = 0 THEN 0
--   ELSE VENTILATION.DURATION_IN_SEC / HADM_STATS.MV_TOTAL_DURATION
-- END 
-- FROM  HADM_ICUSTAY_MAP, HADM_STATS
-- WHERE VENTILATION.ICUSTAY_ID = HADM_ICUSTAY_MAP.ICUSTAY_ID
-- AND HADM_ICUSTAY_MAP.HADM_ID = HADM_STATS.HADM_ID
-- );

-- COMMIT;

-- -- runs in 1 seconds 
-- SELECT HADM_ICUSTAY_MAP.HADM_ID , VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME,
-- CASE
--   WHEN HADM_STATS.MV_TOTAL_DURATION = 0 THEN 0
--   ELSE VENTILATION.DURATION_IN_SEC / HADM_STATS.MV_TOTAL_DURATION
-- END 
-- FROM  HADM_ICUSTAY_MAP, HADM_STATS, VENTILATION
-- WHERE VENTILATION.ICUSTAY_ID = HADM_ICUSTAY_MAP.ICUSTAY_ID
-- AND HADM_ICUSTAY_MAP.HADM_ID = HADM_STATS.HADM_ID
--  ORDER BY  HADM_ICUSTAY_MAP.HADM_ID , VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME ASC ;


--Errors above




--throughout one hostpital admission, how long were you ventilated










-- -- everything below is for debugging purposes
-- -- runs in 1 seconds 
-- SELECT VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME, COUNT(*) cnt
-- FROM  HADM_ICUSTAY_MAP, HADM_STATS, VENTILATION
-- WHERE VENTILATION.ICUSTAY_ID = HADM_ICUSTAY_MAP.ICUSTAY_ID
-- AND HADM_ICUSTAY_MAP.HADM_ID = HADM_STATS.HADM_ID
--  GROUP BY VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME
--  ORDER BY cnt DESC 
-- ;

-- SELECT * FROM HADM_ICUSTAY_MAP
-- WHERE HADM_ICUSTAY_MAP.ICUSTAY_ID = 20174;



-- WITH t1 as (SELECT HADM_ICUSTAY_MAP.HADM_ID hdm, VENTILATION.ICUSTAY_ID iid, VENTILATION.BEGIN_TIME bt,
-- CASE
--   WHEN HADM_STATS.MV_TOTAL_DURATION = 0 THEN 0
--   ELSE VENTILATION.DURATION_IN_SEC / HADM_STATS.MV_TOTAL_DURATION
-- END 
-- FROM  HADM_ICUSTAY_MAP, HADM_STATS, VENTILATION
-- WHERE VENTILATION.ICUSTAY_ID = HADM_ICUSTAY_MAP.ICUSTAY_ID
-- AND HADM_ICUSTAY_MAP.HADM_ID = HADM_STATS.HADM_ID
-- ORDER BY  HADM_ICUSTAY_MAP.HADM_ID , VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME ASC ),

-- t2 as (SELECT HADM_ICUSTAY_MAP.HADM_ID hdm, VENTILATION.ICUSTAY_ID iid, VENTILATION.BEGIN_TIME bt,
-- CASE
--   WHEN HADM_STATS.MV_TOTAL_DURATION = 0 THEN 0
--   ELSE VENTILATION.DURATION_IN_SEC / HADM_STATS.MV_TOTAL_DURATION
-- END 
-- FROM  HADM_ICUSTAY_MAP, HADM_STATS, VENTILATION
-- WHERE VENTILATION.ICUSTAY_ID = HADM_ICUSTAY_MAP.ICUSTAY_ID
-- AND HADM_ICUSTAY_MAP.HADM_ID = HADM_STATS.HADM_ID
-- ORDER BY  HADM_ICUSTAY_MAP.HADM_ID , VENTILATION.ICUSTAY_ID, VENTILATION.BEGIN_TIME ASC )
 
--  SELECT * FROM  t1, t2
--   where t1.iid = t2.iid and t1.bt = t2.bt ;


-- SELECT * FROM  HADM_STATS
--  WHERE HADM_STATS.HADM_ID = 76;
 
 
--  SELECT * FROM  HADM_ICUSTAY_MAP
--  WHERE HADM_ICUSTAY_MAP.HADM_ID = 76;
 
  
--  SELECT * FROM  VENTILATION;
 
 

