import requests
import pandas as pd
import argparse
import re
from datetime import datetime
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='Vinna með úrslit af tímataka.net.')
    parser.add_argument('--url', help='Slóð að vefsíðu með úrslitum.')
    parser.add_argument('--output_dir', default='data',
                        help='Mappa til að vista niðurstöðurnar.')
    parser.add_argument('--debug', action='store_true',
                        help='Vistar html í skrá til að skoða.')
    return parser.parse_args()

def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Tókst ekki að sækja gögn af {url}")
        return None

def parse_html(html):
    """
    Vinnur úr HTML gögnum og skilar lista af niðurstöðum og upplýsingum um hlaupið.
    """
    # Finna töfluna sem inniheldur úrslitin
    table_pattern = r"<table[^>]*>(.*?)</table>"
    tables = re.findall(table_pattern, html, re.DOTALL)

    if not tables:
        print("Engin tafla fannst í HTML gögnunum.")
        return [], {}

    # Leita að töflu sem inniheldur bæði <thead> og <tbody>
    results_table = None
    for table_html in tables:
        if '<thead' in table_html and '<tbody' in table_html:
            results_table = table_html
            break

    if not results_table:
        print("Engin úrslitatöflu fannst í HTML gögnunum.")
        return [], {}

    # Finna hausana úr thead
    thead_pattern = r"<thead.*?>(.*?)</thead>"
    thead_match = re.search(thead_pattern, results_table, re.DOTALL)
    headers = []
    if thead_match:
        thead_html = thead_match.group(1)
        th_pattern = r"<th[^>]*>(.*?)</th>"
        headers = re.findall(th_pattern, thead_html, re.DOTALL)
        # Hreinsa headers
        headers = [re.sub(r"<.*?>", "", h).strip() for h in headers]
    else:
        print("Engir hausar fundust í úrslitatöflunni.")
        return [], {}

    # Finna allar raðir í tbody
    tbody_pattern = r"<tbody.*?>(.*?)</tbody>"
    tbody_match = re.search(tbody_pattern, results_table, re.DOTALL)
    if not tbody_match:
        print("Engin gögn fundust í úrslitatöflunni.")
        return [], {}

    tbody_html = tbody_match.group(1)
    row_pattern = r"<tr[^>]*>(.*?)</tr>"
    rows = re.findall(row_pattern, tbody_html, re.DOTALL)

    data = []

    for row_html in rows:
        # Sækja gögn úr <td> elementum
        td_pattern = r"<td[^>]*>(.*?)</td>"
        tds = re.findall(td_pattern, row_html, re.DOTALL)
        if tds:
            # Hreinsa HTML tags úr gögnunum
            cells = [re.sub(r"<.*?>", "", td).strip() for td in tds]
            # Búa til orðabók með hausum sem lykla ef þeir eru til
            if headers and len(headers) == len(cells):
                result = dict(zip(headers, cells))
            else:
                # Ef hausar eru ekki til staðar eða fjöldi reita passar ekki
                result = {f"Column_{idx}": cell for idx, cell in enumerate(cells)}
            data.append(result)

    # Bæta við viðbótarupplýsingum um hlaupið
    race_info = {}

    # 1. Sækja heiti hlaupsins úr mismunandi hlutum
    race_name_parts = []

    # Úr <title> taginu
    title_match = re.search(r"<title>(?:TÍMATAKA:)?(.*?)<\/title>", html, re.DOTALL)
    if title_match:
        title_text = re.sub(r"<.*?>", "", title_match.group(1)).strip()
        race_name_parts.append(title_text)

    # Úr <h2> taginu
    h2_match = re.search(r"<h2>(.*?)</h2>", html, re.DOTALL)
    if h2_match:
        h2_text = re.sub(r"<.*?>", "", h2_match.group(1)).strip()
        race_name_parts.append(h2_text)

    # Úr valinni <option> (ef til staðar)
    option_match = re.search(
        r"<option[^>]*selected[^>]*>(.*?)</option>", html, re.DOTALL)
    if option_match:
        option_text = re.sub(r"<.*?>", "", option_match.group(1)).strip()
        race_name_parts.append(option_text)

    # Úr <h3> taginu
    h3_match = re.search(r"<h3>(.*?)</h3>", html, re.DOTALL)
    if h3_match:
        h3_text = re.sub(r"<.*?>", "", h3_match.group(1)).strip()
        race_name_parts.append(h3_text)

    # Sameina heiti hlaupsins
    race_name = ' - '.join(race_name_parts)
    race_info['nafn'] = race_name if race_name else 'Óþekkt hlaup'

    # 2. Sækja viðbótarupplýsingar úr <div> elementum
    # Finna öll div með class "col-xs-4 col-md-3" eða "hidden-xs col-md-3"
    div_pattern = r'<div class="(col-xs-4 col-md-3|hidden-xs col-md-3)">\s*' \
                  r'<small class="stats-label">(.*?)</small>\s*' \
                  r'<h4>(.*?)</h4>\s*</div>'
    divs = re.findall(div_pattern, html, re.DOTALL)

    details = {}
    for _, label, value in divs:
        label = label.strip()
        value = value.strip()
        details[label] = value

    # Bæta upplýsingum við race_info
    race_info['start_time'] = details.get('Start time')
    race_info['started_finished'] = details.get('Started / Finished')
    race_info['percent_completed'] = details.get('% completed')
    race_info['est_finish_time'] = details.get('Est. finish time')

    # 3. Aðskilja 'started' og 'finished' úr 'Started / Finished'
    if 'started_finished' in race_info:
        started_finished = race_info['started_finished']
        started_finished_match = re.match(r'(\d+)\s*/\s*(\d+)', started_finished)
        if started_finished_match:
            race_info['started'] = int(started_finished_match.group(1))
            race_info['finished'] = int(started_finished_match.group(2))
        else:
            race_info['started'] = None
            race_info['finished'] = None
        del race_info['started_finished']

    # 4. Reikna 'upphaf' með því að sameina dagsetningu og 'start_time'
    if race_info.get('start_time'):
        try:
            # Reyna að lesa tíma
            time_str = race_info['start_time']
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            # Finna dagsetningu úr HTML
            date_pattern = r"(\d{1,2}\.\s+\w+\s+\d{4})"
            date_match = re.search(date_pattern, html)
            if date_match:
                date_str = date_match.group(1)
                try:
                    date_obj = datetime.strptime(date_str, "%d. %B %Y")
                except ValueError:
                    date_obj = datetime.now()
            else:
                date_obj = datetime.now()
            # Sameina dagsetningu og tíma
            datetime_obj = datetime.combine(date_obj.date(), time_obj)
            race_info['upphaf'] = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            race_info['upphaf'] = None
    else:
        race_info['upphaf'] = None

    # 5. Fjöldi þátttakenda
    race_info['fjoldi'] = race_info.get('started') or len(data)

    # 6. Setja 'id' fyrir hlaupið
    race_info_file = os.path.join('data', 'hlaup_info.csv')
    if os.path.exists(race_info_file):
        existing_races = pd.read_csv(race_info_file)
        max_id = existing_races['id'].max()
        race_info['id'] = max_id + 1
    else:
        race_info['id'] = 1  # Fyrsta hlaupið

    # 7. Bæta 'hlaup_id' við gögnin í 'data'
    for result in data:
        result['hlaup_id'] = race_info['id']

    return data, race_info

def skrifa_nidurstodur(data, race_info, output_dir):
    """
    Skrifar niðurstöður í úttaksskrár.
    :param data:        (list) Listi af línum
    :param race_info:   (dict) Upplýsingar um hlaupið
    :param output_dir:  (str) Mappa til að vista úttaksskrárnar
    :return:            None
    """
    if not data:
        print("Engar niðurstöður til að skrifa.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Vista þátttakendagögn í hlaup.csv
    hlaup_file = os.path.join(output_dir, 'hlaup.csv')
    df = pd.DataFrame(data)
    # Athuga hvort skráin er til; ef hún er til, bætum við við hana
    if os.path.exists(hlaup_file):
        df_existing = pd.read_csv(hlaup_file)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_csv(hlaup_file, sep=',', index=False)
    print(f"Niðurstöður vistaðar í '{hlaup_file}'.")

    # Vista upplýsingar um hlaupið í hlaup_info.csv
    race_info_file = os.path.join(output_dir, 'hlaup_info.csv')
    df_info = pd.DataFrame([race_info])
    # Athuga hvort skráin er til; ef hún er til, bætum við við hana
    if os.path.exists(race_info_file):
        existing_df = pd.read_csv(race_info_file)
        df_info = pd.concat([existing_df, df_info], ignore_index=True)
    df_info.to_csv(race_info_file, sep=',', index=False)
    print(f"Upplýsingar um hlaupið vistaðar í '{race_info_file}'.")

def main():
    args = parse_arguments()

    # Uppfæra if-skilyrðið til að nota reglulega segð sem passar við rétta slóð
    url_pattern = r"^https?://(www\.)?timataka\.net/.+/urslit/\?race=\d+(&cat=\w+)?(\&age=\d+)?(\&age\_from\=\d+\&age\_to\=\d+)?(\&laps\=\d+)?(\&division\=\w+)?$"
    if not re.match(url_pattern, args.url):
        print("Slóðin er ekki í réttu formi frá timataka.net")
        return

    html = fetch_html(args.url)
    if not html:
        raise Exception("Ekki tókst að sækja HTML gögn, athugið URL.")

    if args.debug:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        html_file = os.path.join(args.output_dir, 'debug.html')
        with open(html_file, 'w') as file:
            file.write(html)
        print(f"HTML fyrir {args.url} vistað í {html_file}")

    results, race_info = parse_html(html)
    skrifa_nidurstodur(results, race_info, args.output_dir)

if __name__ == "__main__":
    main()