"""Ververst cams.js met de streams die nu live zijn op YouTube.

- Bestaande streams behouden hun naam en plaats. Een stream verdwijnt pas als hij
  twee verversingen op rij aantoonbaar niet live is.
- Nieuwe streams van bekende kanalen komen er automatisch bij.
- Streams van onbekende kanalen met een Nederlandse aanwijzing komen in
  nieuwe-kanalen.txt. Staat zo'n kanaal echt in Nederland? Kopieer de regel dan naar
  kanalen.txt; de volgende verversing neemt zijn streams mee.
- Eén verzoek tegelijk. Weigert YouTube (bijvoorbeeld fout 429), dan stopt het script
  en blijft de lijst bewaard, zonder iets te verwijderen.

Gebruik: python ververs-streams.py [--proef]   (--proef schrijft niets weg)
"""
import datetime
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CAMS = os.path.join(HERE, 'cams.js')
TRUSTED_FILE = os.path.join(HERE, 'kanalen.txt')
REVIEW_FILE = os.path.join(HERE, 'nieuwe-kanalen.txt')
DELAY = 4  # seconden tussen verzoeken
REMOVE_AFTER = 2  # aantal verversingen op rij zonder live-beeld

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9',
    'Cookie': 'CONSENT=YES+1',
}
PLACES = ['Amsterdam', 'Rotterdam', 'Den Haag', 'Scheveningen', 'Utrecht', 'Eindhoven', 'Groningen', 'Maastricht',
          'Tilburg', 'Breda', 'Nijmegen', 'Arnhem', 'Zwolle', 'Leeuwarden', 'Haarlem', 'Zandvoort', 'Texel',
          'Terschelling', 'Ameland', 'Vlieland', 'Schiermonnikoog', 'Volendam', 'Giethoorn', 'Hoek van Holland',
          'IJmuiden', 'Den Helder', 'Harlingen', 'Vlissingen', 'Zeeland', 'Domburg', 'Noordwijk', 'Katwijk', 'Egmond',
          'Bergen aan Zee', 'Schiphol', 'Amersfoort', 'Apeldoorn', 'Deventer', 'Enschede', 'Assen', 'Venlo',
          'Lelystad', 'Almere', 'Friesland', 'Limburg', 'Drenthe', 'Veluwe', 'Dordrecht', 'Delft', 'Leiden', 'Gouda',
          'Alkmaar', 'Hoorn', 'Enkhuizen', 'Urk', 'Lauwersoog', 'Maasvlakte', 'Waalhaven']
GENERIC = ['webcam nederland', 'live webcam netherlands', 'holland live cam', 'livestream webcam strand nederland',
           'treinen live webcam nederland', 'train cam netherlands live', 'spoorwegovergang live webcam',
           'ship spotting netherlands live', 'schepen live webcam', 'nieuwe waterweg live', 'haven webcam live',
           'vogel webcam nederland live', 'ooievaar webcam live', 'wadden webcam live', 'Dutch live webcam 4K',
           'planespotting schiphol live', 'weer webcam live nederland', 'snelweg webcam live nederland',
           'dierentuin live webcam nederland']
NOT_A_WEBCAM = re.compile(r'\b(backup|dashboard|dordrecht nu)\b', re.I)  # zulke titels zijn geen echt webcambeeld
NL_HINT = re.compile(r'\b(nederland|netherlands|holland|dutch|' + '|'.join(map(re.escape, PLACES)) + r')\b', re.I)


class Refused(Exception):
    """YouTube weigert verzoeken; verder gaan maakt het alleen erger."""


def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
            return r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise Refused(f'fout {e.code}')
        raise


def unquote(s):
    try:
        return json.loads(f'"{s}"')
    except ValueError:
        return s


def parse_search(html):
    """Geeft de live streams uit een YouTube-zoekpagina terug."""
    found = {}
    for chunk in html.split('"videoRenderer":{"videoId":"')[1:]:
        if 'BADGE_STYLE_TYPE_LIVE_NOW' not in chunk and 'LIVE_NOW' not in chunk:
            continue
        title = re.search(r'"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', chunk)
        owner = re.search(r'"ownerText":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', chunk)
        channel = re.search(r'"ownerText":.*?"browseId":"(UC[\w-]+)"', chunk)
        if title and owner and channel:
            found[chunk[:11]] = dict(id=chunk[:11], title=unquote(title.group(1)),
                                     channel=unquote(owner.group(1)), channelId=channel.group(1))
    return found


def check_watch(video_id):
    """Geeft (live, insluitbaar) terug, of None als de pagina niets zegt."""
    html = fetch(f'https://www.youtube.com/watch?v={video_id}&hl=nl&gl=NL')
    if '"playabilityStatus"' not in html:
        return None
    return '"isLiveNow":true' in html, '"playableInEmbed":true' in html


def read_cams():
    text = open(CAMS, encoding='utf-8').read()
    return json.loads(text[text.index('['):text.rindex(']') + 1])


def write_cams(cams):
    cams.sort(key=lambda c: (c['place'], c['name']))
    body = ',\n'.join(json.dumps(c, ensure_ascii=False) for c in cams)
    today = datetime.date.today().isoformat()
    tmp = CAMS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(f'// Live op YouTube gevonden, ververst op {today}. Een stream die niet (meer) speelt, slaat de pagina vanzelf over.\n')
        f.write('const CAMS = [\n' + body + '\n];\n')
    shutil.copyfile(CAMS, CAMS + '.bak')
    os.replace(tmp, CAMS)


def clean_title(title, channel):
    t = re.sub(r'[^\w\s,.&\'()/|-]', ' ', title)
    t = re.sub(r'(?i)\b(webcam\.nl|live\s*stream|livestream|live\s*webcam|webcam|live|24/7|4k|hd)\b', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip(' |-,.')
    return (t or channel)[:60]


def guess_place(title, channel_cams):
    m = re.search(r'\b(' + '|'.join(map(re.escape, PLACES)) + r')\b', title, re.I)
    if m:
        return next(p for p in PLACES if p.lower() == m.group(1).lower())
    if channel_cams:
        return Counter(c['place'] for c in channel_cams).most_common(1)[0][0]
    return 'Nederland'


def read_trusted():
    if not os.path.exists(TRUSTED_FILE):
        return set()
    return set(re.findall(r'^\s*(UC[\w-]+)', open(TRUSTED_FILE, encoding='utf-8').read(), re.M))


def main():
    dry = '--proef' in sys.argv
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    cams = read_cams()
    by_id = {c['id']: c for c in cams}
    queries = GENERIC + [f'{p} webcam live' for p in PLACES]
    live, complete = {}, True

    print(f'{len(cams)} streams in de lijst. Zoeken met {len(queries)} zoekopdrachten (duurt enkele minuten)...')
    try:
        for i, q in enumerate(queries, 1):
            url = ('https://www.youtube.com/results?sp=EgJAAQ%253D%253D&hl=nl&gl=NL&search_query='
                   + urllib.parse.quote(q))
            live.update(parse_search(fetch(url)))
            if i % 10 == 0:
                print(f'  {i}/{len(queries)}: {len(live)} live streams gevonden')
            time.sleep(DELAY)
    except Refused as e:
        complete = False
        print(f'YouTube weigert verzoeken ({e}). Probeer het later nog eens; er wordt niets verwijderd.')
    except urllib.error.URLError as e:
        complete = False
        print(f'Geen verbinding met YouTube ({e}). Er wordt niets verwijderd.')

    # Kanaalgegevens bijwerken, zodat bekende kanalen herkend worden.
    for vid, s in live.items():
        if vid in by_id:
            by_id[vid]['channelId'] = s['channelId']
            by_id[vid].pop('miss', None)
    trusted = read_trusted() | {c['channelId'] for c in cams if c.get('channelId')}

    added, removed, review = [], [], {}
    try:
        for vid, s in live.items():
            if vid in by_id or NOT_A_WEBCAM.search(s['title']):
                continue
            if s['channelId'] not in trusted:
                if NL_HINT.search(s['title'] + ' ' + s['channel']):
                    review[vid] = s
                continue
            if not complete:
                continue
            time.sleep(DELAY)
            state = check_watch(vid)
            if state and state[0] and state[1]:
                same = [c for c in cams if c.get('channelId') == s['channelId']]
                cat = Counter(c['cat'] for c in same).most_common(1)[0][0] if same else 'stad'
                cam = dict(id=vid, place=guess_place(s['title'], same), name=clean_title(s['title'], s['channel']),
                           cat=cat, channelId=s['channelId'])
                cams.append(cam)
                by_id[vid] = cam
                added.append(cam)

        # Niet gevonden in de zoekresultaten zegt nog niets: kijk op de pagina van de stream zelf.
        if complete:
            for cam in list(cams):
                if cam['id'] in live:
                    continue
                time.sleep(DELAY)
                state = check_watch(cam['id'])
                if state is None:
                    continue
                if state[0]:
                    cam.pop('miss', None)
                else:
                    cam['miss'] = cam.get('miss', 0) + 1
                    if cam['miss'] >= REMOVE_AFTER:
                        cams.remove(cam)
                        removed.append(cam)
    except Refused as e:
        complete = False
        print(f'YouTube weigert verzoeken ({e}). Wat al bekend is, wordt bewaard.')

    print(f'\nToegevoegd: {len(added)}')
    for c in added:
        print(f"  + {c['place']}: {c['name']}")
    print(f'Verwijderd: {len(removed)}')
    for c in removed:
        print(f"  - {c['place']}: {c['name']}")
    waiting = sum(1 for c in cams if c.get('miss'))
    print(f'Nu niet live, krijgt nog een kans: {waiting}')
    print(f'Onbekende kanalen om te beoordelen: {len({s["channelId"] for s in review.values()})}')
    print(f'Totaal: {len(cams)} streams' + ('' if complete else ' (verversing was niet volledig)'))

    if dry:
        print('Proefrun: niets weggeschreven.')
        return
    if not live and not complete:
        print('Niets gevonden; cams.js is ongewijzigd.')
        return
    write_cams(cams)
    if review:
        with open(REVIEW_FILE, 'w', encoding='utf-8') as f:
            f.write('# Kopieer de regel van een kanaal dat echt in Nederland staat naar kanalen.txt.\n')
            for s in sorted(review.values(), key=lambda x: x['channel'].lower()):
                f.write(f"{s['channelId']}  # {s['channel']}: {s['title']}  https://www.youtube.com/watch?v={s['id']}\n")
        print(f'Te beoordelen kanalen staan in {os.path.basename(REVIEW_FILE)}.')
    print('Klaar. Ververs de pagina om de nieuwe lijst te gebruiken.')


if __name__ == '__main__':
    main()
