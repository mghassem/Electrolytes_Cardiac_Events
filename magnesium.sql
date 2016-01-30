DROP TABLE MAGNESIUM;


	CREATE TABLE MAGNESIUM
	("SUBJECT_ID" NUMERIC(7,0), 
	"ICUSTAY_ID" NUMERIC(7,0), 
	"HADM_ID" NUMERIC(7,0),
	"CHARTTIME" TIMESTAMP (9) WITH TIME ZONE 
	);

	WITH
	subject_and_icustay_ids AS
	(
	  SELECT DISTINCT
	    subject_id,
	    icustay_id,
		charttime
	  FROM 
		mimiciii.chartevents
	  WHERE itemid IN ('1532', '40645', '44088', '220635')
	  AND icustay_id IS NOT NULL
	  ORDER BY 
		icustay_id,
		charttime

	)
	,
		icustay_and_hadm_ids AS
		(SELECT DISTINCT 
			hadm_id,
			icustay_id
		FROM 
			mimiciii.transfers
		WHERE icustay_id IS NOT NULL
		ORDER BY
			icustay_id
		)
	,
		final_table AS
		(SELECT subject_id, icustay_id 
			FROM subject_and_icustay_ids
			INNER JOIN icustay_and_hadm_ids
			ON icustay_and_hadm_ids.icustay_id = subject_and_icustay_ids.icustay_id
			)

		INSERT INTO MAGNESIUM ("SUBJECT_ID", "ICUSTAY_ID","HADM_ID", "CHARTTIME" )
		SELECT subject_id, icustay_id, hadm_id, charttime FROM final_table


		--magnesium item_id's are 1532, 40645, 44088, 220635