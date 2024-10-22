-- Búa til töfluna 'hlaup'
DROP TABLE IF EXISTS hlaup;
CREATE TABLE hlaup (
    id INTEGER PRIMARY KEY,
    nafn TEXT,
    start_time TIME,
    est_finish_time TIME,
    "started" INTEGER,
    "finished" INTEGER,
    percent_completed INTEGER,
    upphaf DATETIME,
    fjoldi INTEGER
);

-- Búa til töfluna 'timataka'
DROP TABLE IF EXISTS timataka;
CREATE TABLE timataka (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hlaup_id INTEGER,
    "Rank" INTEGER,
    BIB INTEGER,
    "Name" TEXT,
    "Year" INTEGER,
    Club TEXT,
    Split TEXT,
    "Time" TIME,
    Chiptime TIME,  -- Bætti við Chiptime sem var ekki notað áður
    Behind TEXT,
    FOREIGN KEY (hlaup_id) REFERENCES hlaup(id)
);

-- Slökkva á viðskiptum til að auka innlestrarhraða
PRAGMA synchronous = OFF;
BEGIN TRANSACTION;

-- Lesa inn gögn í 'hlaup' töfluna
.mode csv
.separator ","
.import data/hlaup_info.csv hlaup_temp

-- Færa gögnin úr hlaup_temp yfir í hlaup (til að tryggja rétta dálkaröð)
INSERT INTO hlaup (id, nafn, start_time, est_finish_time, "started", "finished", percent_completed, upphaf, fjoldi)
SELECT id, nafn, start_time, est_finish_time, "started", "finished", percent_completed, upphaf, fjoldi FROM hlaup_temp;

DROP TABLE hlaup_temp;

-- Lesa inn gögn í 'timataka' töfluna
.mode csv
.separator ","
.import data/hlaup.csv timataka_temp

-- Eyða hausalínunni úr timataka_temp
DELETE FROM timataka_temp WHERE hlaup_id = 'hlaup_id';  -- Þetta tryggir að fyrsta línan sé fjarlægð

-- Færa gögnin úr timataka_temp yfir í timataka
INSERT INTO timataka (hlaup_id,"Rank",BIB, "Name","Year", Club, Split, "Time", Chiptime, Behind)
SELECT hlaup_id,"Rank",BIB, "Name","Year", Club, Split, "Time", Chiptime, Behind FROM timataka_temp;

DROP TABLE timataka_temp;

COMMIT;
PRAGMA synchronous = ON;

-- Sannreyna fjölda þátttakenda í hverju hlaupi
SELECT
    h.id,
    h.nafn,
    h.fjoldi AS Fjoldi_ut_fra_hlaup_toflu,
    COUNT(r.id) AS Fjoldi_ut_fra_timataka_toflu
FROM
    hlaup h
LEFT JOIN
    timataka r ON h.id = r.hlaup_id
GROUP BY
    h.id, h.nafn, h.fjoldi;

-- Athuga hvort fjöldi úr 'hlaup' töflunni stemmi við fjölda úr 'timataka' töflunni
SELECT
    CASE
        WHEN h.fjoldi = COUNT(r.id) THEN 'Fjöldi stemmir fyrir hlaup ' || h.nafn
        ELSE 'Fjöldi stemmir EKKI fyrir hlaup ' || h.nafn || ' (hlaup_tafla: ' || h.fjoldi || ', timataka_tafla: ' || COUNT(r.id) || ')'
    END AS Niðurstaða
FROM
    hlaup h
LEFT JOIN
    timataka r ON h.id = r.hlaup_id
GROUP BY
    h.id, h.nafn, h.fjoldi;