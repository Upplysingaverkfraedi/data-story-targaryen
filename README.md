
## TL;DR

Verkefnið snýst um að safna og greina gögn frá tímataka.net um þátttöku keppenda í íslenskum hlaupum og hjólreiðakeppnum á árunum 2018 til 2024. Markmiðið er að bera saman frammistöðu tveggja keppenda, Bergdísar og Eyjólfs, með tilliti til þátttöku, tíma og sætaröðunar. Í verkefninu er byggt á sjálfvirkri gagnaöflun og gagnagreiningu með Python, R og SQLite.

## Strúktur
- timataka.py: Forrit til að sækja úrslit keppenda beint af tímataka.net.
- august.py: Forrit sem keyrir timataka.py fyrir mörg hlaup í ágúst 2018-2024.
- create_db.sql: SQL skrá sem býr til SQLite gagnagrunninn timataka.db.
- urls.txt: Textaskrá með slóðum að hlaupaúrslitum fyrir ágúst mánuð 2018-2024.
- data/: Inniheldur tvær CSV skrár, hlaup og hlaup_info með niðurstöðum hlaupa og keppenda.
- R/: Inniheldur R skrár til að hreinsa gögn og framkvæma greiningar.


## Uppsetning gagnagrunns - keyrsluuppsetning 

Forritin agust_url.py, timataka.py, create_db.sql má finna undir code möppunni í main. 
Textaskráin urls.txt og timataka.db má finn undir möppunni data í main. 

Til að sækja gagnagrunninn þarf að hlaða forritunum á viðeigandi staði til að keyrsla virki. 

1.	Keyra eftirfarandi skipun:

   ```bash
python3 agust_url.py --input_file data/urls.txt --output_dir data --debug
```

--input_file: Slóð að textaskrá sem inniheldur lista af URL-slóðum (einn á hverri línu).
--output_dir: Mappan þar sem gögnin verða vistuð (sömu og í timataka.py).
--debug: (Valfrjálst) Ef þetta flagg er sett, verður HTML skráin vistuð fyrir hvert hlaup.
Athugið að þessi keyrsla gæti tekið langan tíma, þar sem það er mikið af URL linkum í textaskránni. Einnig væri hægt að keyra þetta í nokkrum hlutum. 

2.	Keyra eftirfarandi skipun til að búa til gagnagrunninn:

   ```bash
sqlite3 timataka.db < create_db.sql
```
Eftir keyrslu er hægt að skoða töflurnar með því að opna þær í SQLite: 

   ```bash
Sqlite3 timataka.db
```

Og svo keyra eftirfarandi skipanir til að skoða töflurnar:

   ```bash
SELECT*FROM hlaup limit 10; 
```

Það er galli í create_db.sql forritinu sem gerir það að verkum að forritið nær ekki að sækja upplýsingarnar sem eiga að fara í timatöku töfluna. Þetta er hægt að laga með því að importa csv fileinu inná R. Þetta er hægt að gera með skipuninni: 

   ```bash
dat <- read.csv("path/to/your/hlaup.csv") 
head(data) # skoða fyrstu línurnar
```

Hér munuð þið taka eftir því að það eru of margir dálkar í töflunni. Það eiga aðeins að vera 10 dálkar. Þetta getið þið séð með því að keyra skipunina:

   ```bash
> colnames(dat)[1:11]
```
á console. 
Þið getið séð að seinasti dálkurinn heitir Column_0, sem bendir til þess að dálkurinn sé tómur. 
Til að eyða þessum auka dálkum er hægt að keyra skipunina: 

   ```bash
dat <- dat[,1:10]
```
Með þessu skrefi eyði ég öllum dálkum fyrir utan fyrstu 10 sem innihalda þær upplýsingar sem þörf er á. 
Næst vistum við nýja hreinsaða gagnasafnið okkar sem csv skrá. Þetta er gert með skipuninni: 

   ```bash
write.csv(dat, 'Documents/GitHub/data-story-targaryen/data/hlaup.csv')
```
Þetta visstum við á sama stað og csv taflan okkar er, hlaup_info.
Þá er gagnasafnið okkar timataka.db tilbúið til notkunar. 

Til að tengjast SQLite gagnagrunninum og lesa töflur inni á R þarf að hlaða inn bóksöfnunum: 

library(DBI) 
library(RSQLite)

Þessi bókasöfn eru notuð til að vinna með SQLite gagnagrunna í R. 
Síðan keyrum við eftirfarandi skipun til að tengjast timataka.db: 

   ```bash
con <- dbConnect(RSQLite::SQLite(), "Documents/GitHub/data-story-targaryen/data/timataka.db")
dbListTables(con) #skoða hvaða töflur eru í gagnagrunninum. 
```
Það eru nokkrar tómar raðir í timataka_data töflunni, hægt er að taka þær út með skipuninni: 

   ```bash
# Hlaup sem voru ekki með keppendur undir timataka_data
empty_names_per_hlaup <- timataka_data %>%
  group_by(hlaup_id) %>%
  summarise(Empty_Name_Count = sum(Name == "" | is.na(Name))) %>%
  filter(Empty_Name_Count > 0)  # Filter out hlaup_id with zero empty names

# Birta töfluna
empty_names_per_hlaup
```
og svo keyra:

   ```bash
# Gera timataka_data2 þar sem búið er að taka út þar sem Name er tómt og Rank er 0 líka. 
timataka_data2 <- timataka_data %>%
  filter(!(Name == "" & Rank == 0))

# Birta töfluna
head(timataka_data2)
```

Þá er komin ný tafla sem heitir timataka_data2, með viðeigandi gögnum og þá er hægt að byrja að vinna með gögnin. 

## Imports eða nauðsynleg bókasöfn til að keyra forrit:

Fyrir timtaka.py: 

   ```bash
import requests # Til að sækja HTML gögn af vefnum 
import pandas as pd # Til að vinna með gögn í DataFrames og skrifa CSV skrár 
import argparse # Til að lesa inn og meðhöndla skipanalínu valkosti
import re # Til að nota reglulegar segðir til að vinna með HTML gögn from datetime
import datetime # Til að meðhöndla dagsetningar og tíma
 import os # Til að vinna með skrár og skráarskipanir
```

Fyrir agust.py: 

   ```bash
import argparse # Til að lesa inn skipanalínu valkosti 
import subprocess # Til að keyra önnur forrit innan Python (í þessu tilfelli 'tímataka.py')
```





















