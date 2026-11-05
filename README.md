# Nederland Live

Een videomuur met livewebcams uit heel Nederland, via YouTube. De schermen wisselen willekeurig en starten standaard in hoge resolutie.

**Bekijk de muur online: https://010mick010.github.io/nederland-live/**

## Natuurmuur

**Bekijk de natuurmuur online: https://010mick010.github.io/nederland-live/?natuur**

Met `?natuur` achter het adres toont de muur alleen Nederlandse natuur: vogels, zeehonden, strand en duinen, land en water. Lokaal start je die met `start-natuur.bat`. Dierentuinen, asieldieren, boulevards en havens vallen erbuiten.

Een stream hoort bij de natuurmuur als hij in `cams.js` het veld `"natuur"` heeft, met de waarde `vogels`, `zeehonden`, `kust` of `land`. Hier staat "Alleen 1080p en hoger" standaard uit, omdat veel nestcamera's lager uitzenden.

## Lokaal starten

Dubbelklik op `start-webcams.bat` (Windows, Python nodig). De muur opent op http://localhost:8377. Het bestand `index.html` los openen werkt niet, omdat YouTube dan niets afspeelt.

Op een ander systeem start je vanuit deze map:

```bash
python -m http.server 8377 --bind 127.0.0.1
```

## Bediening

- **Schermen:** 1 tot 16 tegels tegelijk.
- **Wisselen:** elke 15 seconden tot 5 minuten wisselt één willekeurige tegel. Elke stream komt aan de beurt voordat er een terugkeert.
- **Soort:** filter op stad, kust, water en haven, spoor, vliegen, natuur of dieren.
- **Kwaliteit:** 1080p, 1440p of 4K. Elke tegel toont welke kwaliteit er echt binnenkomt.
- **Alleen 1080p en hoger:** slaat streams over die geen 1080p aanbieden.
- **Per tegel:** geluid aan, vastzetten, volgende stream of openen op YouTube. Klik op een tegel om hem groot te maken; met Esc ga je terug.

## Over de resolutie

YouTube laat zich geen kwaliteit opdringen en kiest die zelf op basis van de spelergrootte en je verbinding. Daarom draait elke speler intern op volle grootte en wordt hij met CSS passend geschaald. Een nieuwe stream kan lager beginnen, en bij een trage verbinding blijft hij lager. Reken bij 6 schermen op 1080p op grofweg 30 Mbit/s.

## De lijst verversen

Stream-ID's veranderen zodra een kanaal opnieuw start. Dubbelklik op `ververs-streams.bat` of draai:

```bash
python ververs-streams.py
```

Gebruik `--proef` om niets weg te schrijven. Een run duurt ongeveer een kwartier, omdat het script bewust één verzoek per 4 seconden doet en stopt zodra YouTube weigert.

- Bestaande streams houden hun naam en plaats in `cams.js`.
- Nieuwe streams van bekende kanalen komen er automatisch bij. Hun naam en plaats zijn een schatting uit de titel of het kanaal.
- Een stream verdwijnt pas na twee verversingen op rij zonder live beeld.
- Onbekende kanalen met een Nederlandse aanwijzing komen in `nieuwe-kanalen.txt`. Kopieer de regel van een kanaal dat echt in Nederland staat naar `kanalen.txt`.

De online muur gebruikt de `cams.js` op GitHub. Upload het bestand na een verversing opnieuw, dan werkt GitHub Pages de site vanzelf bij.

## Bestanden

| Bestand | Doel |
| --- | --- |
| `index.html` | De videomuur |
| `cams.js` | De lijst met streams |
| `ververs-streams.py` | Werkt de lijst bij |
| `kanalen.txt` | Optioneel: kanalen die je zelf hebt goedgekeurd |
| `start-webcams.bat` | Start de muur met alle webcams lokaal |
| `start-natuur.bat` | Start de natuurmuur lokaal |

## Rechten

De beelden zijn van hun eigen makers en worden via de YouTube-speler getoond. Deze repository bevat alleen verwijzingen naar de streams, geen beeldmateriaal.
