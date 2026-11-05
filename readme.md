# TIGGE előrejelzések és met.hu mérések összevetése

A projekt a Fisher-információs (FI) kutatás része: az ECMWF TIGGE archívumának historikus előrejelzéseit
összekapcsoljuk a hosszú magyarországi napi mérési adatsorral, és megnézzük, **mekkora a napi eltérés az előrejelzés
és a mérés között**, illetve hogy ez **mely hónapokban nagyobb**.

Ez a repó a következőket tartalmazza: a TIGGE-adatok automatizált letöltése, feldolgozása (GRIB → napi értékek öt
városra), a met.hu adatok előkészítése, a kettő összevetése és a napi hibametrika (`delta`) számítása.
Az FI számítása a projekt másik részében történik, nem ebben a repóban.

## Tartalom

1. [Háttér](#1-háttér)
2. [Áttekintés](#2-áttekintés)
3. [Gyors indulás](#3-gyors-indulás)
4. [Fájlok és mappák](#4-fájlok-és-mappák)
5. [Telepítés és beállítás](#5-telepítés-és-beállítás)
6. [Futtatás lépésről lépésre](#6-futtatás-lépésről-lépésre)
7. [Módszertani döntések és indoklások](#7-módszertani-döntések-és-indoklások)
8. [Fájlformátumok](#8-fájlformátumok)
9. [Előzetes megfigyelések](#9-előzetes-megfigyelések)
10. [Ismert korlátok](#10-ismert-korlátok)
11. [Nyitott kérdések a csoportnak](#11-nyitott-kérdések-a-csoportnak)
12. [Hibaelhárítás](#12-hibaelhárítás)
13. [Git és adatkezelés](#13-git-és-adatkezelés)

---

## 1. Háttér

A kutatásban hosszú távú meteorológiai adatsorok segítségével azt vizsgáljuk, hogy a klímarendszerben bekövetkező
változások kimutathatók-e a Fisher-információ (FI) változásán keresztül. Több magyarországi mérőállomás mintegy
120 éves napi adatsorán az FI-t időablakokra, illetve hónapokra számoljuk, és azt találtuk, hogy az értéke
időben nem állandó: vannak hónapok és időszakok, amikor számottevően alacsonyabb.

**Hipotézis:** az alacsonyabb FI-jű időszakokban a légköri állapot kevésbé „meghatározott”, ezért az
időjárás-előrejelzések bizonytalansága, illetve hibája is nagyobb lehet.

Ennek teszteléséhez a mérési adatsort össze kell kapcsolni historikus előrejelzésekkel. Erre az ECMWF **TIGGE**
(THORPEX Interactive Grand Global Ensemble) adatbázisát használjuk, amely 2006 októbere óta tartalmaz előrejelzéseket.
A két adathalmaz közös időszaka ezért **2006 október – 2025 december** (a mérések 2025 végéig, a letöltött TIGGE-hónapok a
tényleges lefedettségtől függően).


Vizsgált városok: **Budapest, Debrecen, Pécs, Szeged, Szombathely**.

## 2. Áttekintés

```
ECMWF TIGGE (ECDS API)
        │  download_script.py   (havi kérések, újrapróbálkozással)
        ▼
tigge_data/YYYY-MM_cf.grib      (nyers GRIB, 6 órás értékek)
        │  txt_output_script.py (város pontja, met.hu-napi aggregálás)
        ▼
out_txt/<Város>_final.txt       (napi TIGGE: d_ta, d_tx, d_tn, d_rs)
                                              │
met.hu CSV-k ─► extending_data.py ─► methu_txt/<kód>_d.txt   (napi mérés, 2025-ig kiegészítve)
                                              │
                         összevetés (notebook): merge → normalizálás → delta
                                              ▼
                         havi statisztika, boxplotok
```

**Fontos:** a met.hu-ról letöltött napi fájlok (`methu_txt/`) eredetileg csak **2020 decemberéig** tartanak. A
2021–2025-ös szakaszt az **`extending_data.py`** fűzi hozzá a nyers CSV-kből, ezt a scriptet az összevetés
előtt le kell futtatni (lásd: 6. fejezet, 3. lépés).

A két napi adatsor szándékosan **ugyanabban a formátumban** van (`#datum;d_ta;d_tx;d_tn;d_rs`), és a TIGGE-oldali
napi értékeket a **met.hu saját napi definíciói** szerint számoljuk, hogy közvetlenül összehasonlíthatók legyenek.

## 3. Gyors indulás

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python -m cfgrib selfcheck        # az ecCodes ellenőrzése
# .cdsapirc létrehozása és a TIGGE-licenc elfogadása: lásd az 5. fejezetet
python download_script.py         # 1. TIGGE letöltés (hosszú futás)
python txt_output_script.py       # 2. GRIB -> napi txt városonként
python extending_data.py          # 3. met.hu adatok kiegészítése 2025-ig (az eredeti fájlok 2020-ig tartanak)
# 4. összevetés és delta: lásd a 6. fejezetet és a notebookot
```

## 4. Fájlok és mappák

A fájlnevek a projektben használt elnevezések. Ha a te példányodban mások, igazítsd.

```
.
├── download_script.py          # TIGGE letöltés az ECDS API-n keresztül 
├── txt_output_script.py        # GRIB -> napi txt, városonként
├── extending_data.py           # a met.hu napi txt-k kiegészítése 2021–2025-tel a nyers CSV-kből
├── data_analyzing.ipynb        # felderítő notebook (GRIB megnyitása, függvények tesztelése)
├── delta_calculating.py        # merge, normalizálás, delta, havi statisztika, ábrák
├── requirements.txt
├── .gitignore
├── tigge_data/                 # letöltött GRIB-ek          (NEM kerül gitbe)
├── out_txt/                    # feldolgozott napi TIGGE txt-k
├── methu_txt/                  # met.hu napi txt-k (BP_d.txt, DE_d.txt, PE_d.txt, SZE_d.txt, SZO_d.txt)
└── 2020-2025/                  # nyers met.hu CSV-k változónként: ta/, tx/, tn/, rs/ (városonként egy fájl)
```

| Fájl / mappa | Mit tartalmaz |
|---|---|
| `tigge_data/YYYY-MM_cf.grib` | egy hónap TIGGE-adata (kontroll előrejelzés, a Kárpát-medence doboza) |
| `out_txt/<Város>_final.txt` | a város napi TIGGE-értékei (`d_ta`, `d_tx`, `d_tn`, `d_rs`) |
| `methu_txt/<kód>_d.txt` | a város napi mért értékei, ugyanebben a formátumban (a letöltött eredeti fájlok 2020 decemberéig tartanak, az `extending_data.py` futtatása után 2025-ig) |
| `2020-2025/<ta,tx,tn,rs>/` | nyers met.hu CSV-k, változónként külön mappa, városonként egy fájl |

Városkódok a met.hu fájlokhoz: Budapest `BP`, Debrecen `DE`, Pécs `PE`, Szeged `SZE`, Szombathely `SZO`.

### A feldolgozó script függvényei (`txt_output_script.py`)

| Függvény | Feladata |
|---|---|
| `month_breakdown(start, end)` | végigmegy a hónapokon `(év, hónap)` párokként |
| `scan_grib_grids(fname)` | egy GRIB fájl üzeneteinek fejlécét olvassa (ecCodes), megmondja, milyen rácsok vannak benne |
| `open_grib_all_grids(fname)` | a fájlt rácsonként külön Datasetként nyitja meg |
| `nearest_point(ds, lat, lon)` | kiválasztja a városhoz legközelebbi rácspontot |
| `open_point_all_grids(fname, city)` | rácsonként kivágja a város pontját, majd időben összefűzi |
| `get_month_point(year, month, city)` | egy hónap pont-adata az előző hónap utolsó és a következő hónap első napjával kiegészítve |
| `daily_max_min_methu(ds, i)` | napi max/min hőmérséklet a met.hu definíciója szerint |
| `daily_precipitation_methu(ds, i)` | napi csapadékösszeg a met.hu definíciója szerint |
| `daily_aggregation_methu(ds, év, hónap)` | egy hónap napi táblázata (`datum, d_ta, d_tx, d_tn, d_rs`) |
| `output_multiple_months(start, end, city)` | a hónapokon végigmegy, és kiírja a város txt fájlját |

## 5. Telepítés és beállítás

### Python és csomagok

Python 3.10 vagy újabb (a fejlesztés Windows alatt, virtuális környezetben, Python 3.12-vel történt).

Telepítés: `pip install -r requirements.txt`. A reprodukálhatóság kedvéért érdemes a működő környezet verzióit
rögzíteni (`pip freeze > requirements.txt`).

A `cfgrib` csak egy Python-wrapper, a GRIB-ek dekódolásához az **ecCodes** natív könyvtár kell. Ellenőrzés:

```bash
python -m cfgrib selfcheck
```

Ha ez hibát ad (Windowson előfordul), a legegyszerűbb a conda:
`conda install -c conda-forge eccodes cfgrib`.

### ECDS-fiók, API-kulcs, licenc

A TIGGE hozzáférése az **ECMWF Data Store (ECDS)** rendszerén keresztül működik (`ecds.ecmwf.int`).

1. Regisztrálj az ECDS-en, és másold ki az API-kulcsodat a profil oldalról.
2. Hozd létre a saját home könyvtáradban a `.cdsapirc` fájlt
   (Windows: `C:\Users\<felhasználónév>\.cdsapirc`), két sorral:
   ```
   url: https://ecds.ecmwf.int/api
   key: A-TE-SAJAT-KULCSOD
   ```
   Idézőjelek és `<` `>` jelek **nélkül**. Az URL-t és a kulcsot a profil oldalról másold, ne gépeld át.
3. Az ECDS-en a `tigge-forecasts` dataset oldalán fogadd el a licencfeltételeket (a Download fülön).
   Ez kézi, egyszeri lépés, enélkül a letöltés hibát dob.
4. A kulcsot **soha ne töltsd fel gitbe**. Mindenki a saját fiókját és kulcsát használja.

## 6. Futtatás lépésről lépésre

### 1. lépés – TIGGE letöltés (`download_script.py`)

A script havi bontásban, **egymás után** (szekvenciálisan) kéri le az adatokat, és hiba esetén exponenciális
várakozással újrapróbálkozik. A kimenet: `tigge_data/YYYY-MM_cf.grib`.

- Az időszak a script elején állítható (`START`, `END`).
- A letöltés hosszú (órák–napok, az ECDS sorától függően, mennyi request van már a queue-ban).
- Ha egy hónap tartósan hibázik (lásd: sérült szalag a 7.10 pontban), a script feladja, és a hónap kimarad.

### 2. lépés – GRIB → napi txt (`txt_output_script.py`)

```bash
python txt_output_script.py
```

Beállítások a script elején: `START`, `END`, a városok koordinátái (`cities`). Minden városra és hónapra kiszámolja a
napi értékeket, és kiírja az `out_txt/<Város>_final.txt` fájlba. Futás közben `tqdm` folyamatjelző látszik, a végén a
script kiírja a **kihagyott (hiányzó) hónapokat**. Hosszú futásnál a `debug=False` beállítás ajánlott, mert a
figyelmeztető kiírások szétszaggatják a folyamatjelzőt.

### 3. lépés – met.hu adatok kiegészítése 2025-ig (`extending_data.py`)

A met.hu-ról letöltött napi adatok (`methu_txt/<kód>_d.txt`, a TIGGE-kimenettel azonos formátumban) **csak 2020
decemberéig** tartanak. A TIGGE-adat viszont ennél később is tart, ezért az összevetés előtt a mért adatokat ki kell
egészíteni a 2021–2025-ös szakasszal. Ezt végzi az `extending_data.py`:

```bash
python extending_data.py
```

A script a nyers CSV-kből dolgozik (változónként külön mappa: `ta/`, `tx/`, `tn/`, `rs/`, városonként egy fájl):

1. A négy változó fájlja dátum szerint egy táblába kerül (`Time` oszlop → dátum, az `EOR` oszlop eldobva).
2. Csak a meglévő fájl utolsó napja utáni sorok kerülnek hozzáfűzésre, és az eredmény a `methu_txt` mappába
   mentődik.

Ha a script a meglévő fájlokat írja felül, érdemes előtte **biztonsági másolatot** készíteni az eredeti, 2020-ig tartó
fájlokról. Ha kihagyod ezt a lépést, az összevetésben a 2021 utáni napokhoz nem lesz mért érték, és az `inner` merge
miatt ezek a napok hibaüzenet nélkül kimaradnak.

### 4. lépés – összevetés és `delta` (notebook)

1. Mindkét adatsor beolvasása, `varos` oszloppal.
2. `merge` a `datum` és a `varos` kulcson (`inner`: csak a közös napok maradnak).
3. Normalizálás és a napi `delta` kiszámítása (lásd: 7.12).
4. Havi csoportosítás a naptári hónap szerint: átlag, medián, szórás, napok száma.
5. Boxplotok hónaponként.

## 7. Módszertani döntések és indoklások

### 7.1 Miért az ECMWF kontroll előrejelzés, és miért nincs ensemble-szórás?

A TIGGE 13 központ ensemble-előrejelzéseit tartalmazza. Az **ECMWF**-et választottuk, mert a leghosszabb, legjobban
dokumentált archívum, és egy központtal az adatmennyiség kezelhető marad.

A **kontroll** előrejelzés (`control_forecast`) egyetlen, perturbáció nélküli futtatás. Ebből az előrejelzés **hibája**
számolható (előrejelzés − mérés). A **bizonytalanság** (az ensemble-tagok szórása) csak a perturbált tagokból
(ECMWF: 50 tag) kapható meg. A perturbált tagokat egyelőre **nem** töltöttük le, mert:

- az ECDS letöltési űrlapján a perturbált tagok csak együtt (`all members`) kérhetők, részhalmaz nem választható,
- az adatmennyiség és a sorban állási idő a kontrollhoz képest nagyságrendekkel nagyobb.

Következmény: a jelenlegi eredmény a hipotézis „hiba” felét tudja vizsgálni, a „bizonytalanság” felét nem
(lásd: 11. fejezet).

### 7.2 Letöltési paraméterek

| Paraméter | Érték | Indoklás |
|---|---|---|
| `origin` | `ecmwf` | lásd 7.1 |
| `forecast_type` | `control_forecast` | lásd 7.1 |
| `time` | `00:00` | a 6/12/18/24 órás lépések így az indítás napjának 00–24 UTC szakaszát fedik le; 12 UTC-s indításnál az ablakok két naptári napra szóródnának szét |
| `leadtime_hour` | `6, 12, 18, 24` | lásd 7.3 |
| `level_type` | `single_level` | felszíni mezők kellenek, légköri szintek nem |
| `variable` | `2_m_temperature`, `maximum_2_m_temperature_in_the_last_6_hours`, `minimum_2_m_temperature_in_the_last_6_hours`, `total_precipitation` | a GRIB-ben: `t2m`, `mx2t6`, `mn2t6`, `tp` |
| `area` | `[49, 15.5, 45.5, 23]` (É, Ny, D, K) | a feladatban megadott doboz, mind az öt várost lefedi |
| `data_format` | `grib` | a natív formátum |
| kérés mérete | egy hónap / kérés | hiba esetén csak az adott hónapot kell újrapróbálni |

### 7.3 Miért kell a 6, 12, 18 és 24 órás lépés (és miért nem elég a 24)?

A `mx2t6` és `mn2t6` **nem a teljes napra**, hanem az **előző 6 órára** vonatkozik. A `tp` (csapadék) az indítástól
**kumulatív**. 00 UTC-s indításnál:

| Lépés | Érvényes idő (UTC) | `mx2t6` / `mn2t6` ablaka | `tp` |
|---|---|---|---|
| 6 | 06:00 | 00–06 | 0–6 |
| 12 | 12:00 | 06–12 | 0–12 |
| 18 | 18:00 | 12–18 | 0–18 |
| 24 | másnap 00:00 | 18–24 | 0–24 |

Egyetlen 24-es lépés esetén a napi maximum csak a 18–24 UTC közti hat órát látná, a délutáni csúcs kimaradna.

### 7.4 A met.hu napi definíciói, és hogyan számoljuk ezeket a TIGGE-ből

A met.hu az észleléseket **CET** (közép-európai idő, nyári időszámítás nélkül) szerint végzi, ami egész évben
**UTC+1**. Az idősorok homogenitása érdekében a napi értékek nem éjféltől éjfélig tartanak:

| Mennyiség | met.hu definíció (CET) | UTC-ben | Számítás a TIGGE-ből |
|---|---|---|---|
| `d_tx` napi maximum | előző nap 19 CET – aznap 19 CET | előző nap 18 UTC – aznap 18 UTC | az **előző nap 24-es** lépésének `mx2t6`-ja, és a **mai nap 6, 12, 18-as** lépéseié: ezek maximuma |
| `d_tn` napi minimum | ugyanaz az ablak | ugyanaz | ugyanez, `mn2t6`-ból, minimummal |
| `d_rs` napi csapadék | 07 CET – másnap 07 CET | 06 UTC – másnap 06 UTC | `(tp[mai, 24] − tp[mai, 6]) + tp[holnapi, 6]` |
| `d_ta` napi középhőmérséklet | lásd alább | | `(d_tx + d_tn) / 2` |

A `d_ta` a met.hu-nál korszakonként más: 1901–1965 között `(t07 + t14 + 2·t21) / 4`, 1966-tól
`(t01 + t07 + t13 + t19) / 4`, az automaták óta a 10 perces adatok átlaga. A TIGGE-oldali `(max + min) / 2` ezért
nem pontosan ugyanaz a mennyiség, kis rendszeres eltérés várható. A `t2m` változót is letöltöttük, de a `d_ta`
számításában nem használjuk, mert a 4 pontos mintavétel úgyis durva közelítése a folytonos átlagnak.

### 7.5 Legközelebbi rácspont

Az ECMWF-adatok a modell **natív, redukált Gauss-rácsán** (`reduced_gg`) vannak, nem szabályos szélesség–hosszúság
rácson, és az ECDS űrlapján a rács nem választható. Emiatt az `xarray` megszokott `sel(method="nearest")` hívása nem
működik (a koordináta nem egyedi index). A `nearest_point` ehelyett az összes rácspont koordinátájából kiszámolja a
fokokban mért távolságot a célvároshoz, és a legközelebbi pontot választja.

### 7.6 Rácsváltások az archívumban

Az ECMWF az ensemble felbontását kétszer növelte, ezért az archívum három rácsgenerációt tartalmaz:

| Indítás napja (00 UTC) | Rács | Közelítő felbontás | Pont a dobozban | ECMWF modellváltás |
|---|---|---|---|---|
| 2006-10-01 – 2010-01-26 | N200 | ~50 km | 97 | |
| 2010-01-27 – 2016-03-08 | N320 | ~32 km | 232 | 2010-01-26 (T399 → T639) |
| 2016-03-09 – | O640 (oktaéderes) | ~18 km | 640 | 2016-03-08 (IFS 41r2) |

A váltás napja egy nappal későbbi az ECMWF dátumánál, mert 00 UTC-s futásokat töltöttünk le, és a modellváltás a nap
folyamán lépett életbe.

Két havi fájl (**2010-01** és **2016-03**) **mindkét rácsot** tartalmazza, ezeket a `cfgrib` egyetlen Datasetként nem
tudja megnyitni (`multiple values for key 'numberOfPoints'`). A megoldás:

1. `scan_grib_grids`: az ecCodes-szal kiolvassuk a fájl rácsait (`numberOfPoints`),
2. `open_grib_all_grids`: rácsonként külön megnyitjuk a fájlt (`filter_by_keys`),
3. `open_point_all_grids`: **rácsonként előbb** kivágjuk a város pontját, és **csak utána** fűzzük össze időben
   (a teljes rácsokat nem lehet összefűzni, mert a `values` dimenzió hossza különböző).

**Következmény:** a legközelebbi rácspont a váltásoknál máshol van, és a modell is pontosabb lett, ezért az idősor
**nem homogén**. Az előrejelzési hiba időbeli változásában a modellfejlesztés hatása is benne lehet (lásd: 10. fejezet).

### 7.7 Mértékegységek

- `t2m`, `mx2t6`, `mn2t6`: **Kelvin**, kivonjuk belőlük a 273,15-öt.
- `tp`: **kg/m²**, ami **egyenlő milliméterrel**, így nem kell átváltani. (Egy korábbi változatban tévesen
  megszoroztuk 1000-rel, ami ezerszeres csapadékot adott. Javítva.)
- A kumulatív `tp` kivonásánál apró negatív kerekítési zaj keletkezhet, ezt 0-ra vágjuk.

### 7.8 Hónaphatárok

A napi max/min-hez az **előző nap** 24-es lépése, a csapadékhoz a **következő nap** 6-os lépése kell, ami a szomszédos
hónap fájljában lehet. Ezért egy hónap feldolgozásakor hozzáfűzzük az előző hónap utolsó és a következő hónap első
napját (`get_month_point`), és a kész táblából csak a hónap saját napjait tartjuk meg.

Ha a szomszédos hónap fájlja hiányzik (az idősor két végén vagy hiányzó hónap mellett), a hónap szélső napja a
**tartalék, egyszerűsített számítással** készül (00–24 UTC ablak). Ez kevésbé pontos, mint a met.hu-definíció.

### 7.9 Napi értékek kerekítése

A napi értékek egy tizedesre kerekítve kerülnek a txt fájlba, a met.hu fájlok formátumával azonosan.

### 7.10 Hiányzó hónapok

Egyes hónapokat nem sikerült letölteni, mert az ECMWF archívumban az adatot tároló szalag sérült
(`AccessError: Requested data is on one or more damaged tape`). Ez az ECMWF oldali hiba, a kérésünkön nem múlik.
Kezelés: a hónap kimarad (a feldolgozó `None`-t kap, és felsorolja a kihagyott hónapokat), **nem pótoljuk**
becsléssel, mert egy előrejelzési hibát nem lehet kitalálni. A dátumsorban lyuk marad, az összevetésnél az `inner`
merge automatikusan kihagyja ezeket a napokat. A havi statisztikánál érdemes a napok számát (`count`) is nézni, mert
a hiányos hónapok átlaga kevésbé megbízható.

### 7.11 Hosszú met.hu sorok hozzáfűzése

A met.hu-ról letöltött napi fájlok 2020 decemberéig tartanak, ezért kell az `extending_data.py`. A 2021–2025-ös nyers CSV-k szerkezete `Time;érték;EOR` (dátum `ÉÉÉÉHHNN` alakban, az érték, és egy `EOR` sorvége-jelölő).
A beolvasó az értéket pozíció szerint veszi, így a változó betűjelétől független. Az új fájlok az egész 1901–2025
időszakot lefedik, ezért az átfedő időszakban a régi és az új adat egyezését ellenőrizzük, mielőtt hozzáfűzünk.

### 7.12 A `delta` hibametrika

A cél egy napi, **dimenzió nélküli** hibaszám, amely a hőmérséklet (°C) és a csapadék (mm) eltérését egy számba
sűríti. A témafelelőssel egyeztetett módszer:

1. **Normalizálás:** a nyolc oszlop (`d_ta`, `d_tx`, `d_tn`, `d_rs`, mindegyik TIGGE és met.hu oldalon) mindegyikét a
   **saját átlagával** osztjuk el. Az átlagot a teljes összevetett táblából (minden város, minden nap) számoljuk.
2. **Távolság:** a négy változó normalizált eltéréseiből az euklideszi távolság:

```
delta = √( (ta_tigge − ta_methu)² + (tx_tigge − tx_methu)² + (tn_tigge − tn_methu)² + (rs_tigge − rs_methu)² )
```

(a négy érték itt már a normalizált érték). Ha egy napon bármelyik hiányzik, a `delta` is hiányzik.

Amit érdemes tudni erről a módszerről:

- **A rendszeres torzítás (bias) kiesik.** Mivel a TIGGE és a met.hu oszlopot is a saját átlagával osztjuk, mindkét
  oldal átlaga 1 lesz, így az állandó eltolódás (például a TIGGE kb. 1,5–2 °C-kal hidegebb Budapesten
  2006 októberében) nem jelenik meg a deltában.
- **A csapadék dominál.** A csapadék napi átlaga kicsi (kb. 1,6 mm), ezért egy-egy esős napon elvétett csapadék
  nagyon nagy normalizált hibát ad (a kiugró értékek a 60-at is elérik), míg a hőmérsékleti hibák 0,2 körüliek.
  A kombinált delta ezért nagyrészt csapadékhiba-mérő. A hőmérséklet-delta (csak a három hőmérséklet) külön
  kiszámolható.
- Alternatíva: **szórással** normalizálni átlag helyett (standardizált euklideszi távolság), így minden változó a
  saját ingadozásához mérve számít (lásd: 11. fejezet).

## 8. Fájlformátumok

### Napi txt (TIGGE és met.hu is)

```
#datum;d_ta;d_tx;d_tn;d_rs
2006-10-01;17.4;23.4;11.3;0.0
```

| Oszlop | Jelentés | Egység |
|---|---|---|
| `datum` | dátum (`ÉÉÉÉ-HH-NN`) | |
| `d_ta` | napi középhőmérséklet | °C |
| `d_tx` | napi maximumhőmérséklet | °C |
| `d_tn` | napi minimumhőmérséklet | °C |
| `d_rs` | napi csapadékösszeg | mm |

Elválasztó: `;`. A fejléc `#datum`-mal kezdődik, ezt a beolvasók átugorják.

### Nyers met.hu CSV (2021–2025 hozzáfűzéséhez)

```
    Time;     r;EOR
19010101;   1.9;EOR
```

Egy változó, egy város, a teljes 1901–2025 időszak naponta (hézag nélkül). Az `EOR` csak sorvége-jelölő.

### Összevetett tábla (notebook)

Oszlopai: `datum`, `varos`, `d_ta_tigge`, `d_ta_methu`, `d_tx_tigge`, `d_tx_methu`, `d_tn_tigge`, `d_tn_methu`,
`d_rs_tigge`, `d_rs_methu`, `delta`.

## 9. Előzetes megfigyelések

(A futtatás idején kapott értékek, a letöltött adat bővülésével frissíteni kell.)

- A kombinált napi `delta` **mediánja egész évben hasonló** (kb. 0,32–0,45 között), egy átlagos napon az előrejelzés
  hibája tehát nem függ erősen az évszaktól.
- Az **átlag nyáron magasabb** (május–augusztus kb. 1,2–1,5, a többi hónapban kb. 0,64–0,75), mert a ritka, nagy
  csapadékos napok felhúzzák. Az átlag és a medián közti nagy különbség ezt mutatja.
- A **csak hőmérsékletre** számolt `delta` mediánja egész évben kb. 0,2, a dobozok szinte egyformák. A kiugró
  értékek télen (december–február) gyakoribbak és nagyobbak.
- Budapestre, 2006 októberében a TIGGE rendszeresen hidegebb a mérésnél (medián kb. −1,5…−2 °C). Ez egyetlen hónap,
  ezért csak jelzés.

## 10. Ismert korlátok

- **Csak kontroll előrejelzés:** hibát tudunk vizsgálni, ensemble-szórás alapú bizonytalanságot nem.
- **Rövid előrejelzési táv (≤ 24 óra):** a hiba jelentős része a rácspont és az állomás különbségéből jön
  (felbontás, magasság, városi környezet), nem a légkör kiszámíthatatlanságából. Budapestnél például a 2006-os rácson
  a legközelebbi pont kb. 20–25 km-re volt a várostól.
- **Három rácsgenerációból összefűzött idősor** (lásd: 7.6): a pont helye és a modell pontossága is változik.
  A váltás napján az előző napi (régi rácsú) és a következő napi (új rácsú) érték egy napi számításban keveredhet.
- **Hiányzó hónapok** (sérült szalag): az idősorban lyukak vannak.
- **A napi középhőmérséklet definíciója** eltér a met.hu-étól (lásd: 7.4).
- **Szélső napok:** az idősor két végén és a hiányzó szomszéd melletti napok az egyszerűsített 00–24 UTC
  számítással készülnek.
- **A legközelebbi pont keresése fokokban** történik, a hosszúsági fok északi szélességen rövidebb (cos(szélesség) szorzó)
  hatását elhanyagolja. A vizsgált kis területen ez csekély hiba.
- **A `delta` csapadék-dominanciája** és a bias kiesése (lásd: 7.12).
- **A met.hu 2021–2025 szakasz** új forrásfájlokból jön, ezért az átfedés-ellenőrzés fontos.

## 11. Nyitott kérdések a csoportnak

1. Kell-e az **ensemble-szórás** (perturbált tagok) a bizonytalanság vizsgálatához? Ha igen, hány tagot töltsünk le
   (az ECDS űrlap csak az összeset kínálja)?
2. A `delta` normalizálása: **átlaggal** (jelenleg) vagy **szórással**? Külön kezeljük-e a csapadékot, vagy készüljön
   külön hőmérséklet-delta is?
3. Elfogadható-e, hogy a rendszeres torzítás (bias) kiesik a deltából, vagy külön mutatóként kell szerepeltetni?
4. A napi középhőmérséklet legyen `(tx + tn) / 2`, vagy a pillanatnyi értékek átlaga?
5. A hiányzó hónapokat kihagyjuk és dokumentáljuk, vagy van igény a pótlásukra (például napi bontású újralekérés)?
6. A rácsgenerációk közti inhomogenitást hogyan kezeljük az eredmények értelmezésében?

## 12. Hibaelhárítás

| Hibaüzenet | Ok | Megoldás |
|---|---|---|
| `Missing/incomplete configuration file: ...\.cdsapirc` | hiányzik a `.cdsapirc` | hozd létre a home könyvtárban (5. fejezet) |
| `No connection adapters were found for '<https://...>'` | a `<` `>` jelek is bekerültek az URL-be | töröld a szögletes zárójeleket a `.cdsapirc`-ből |
| a letöltés licenc-hibával áll meg | a TIGGE-licenc nincs elfogadva | fogadd el a dataset oldalán (Download fül) |
| `MarsRuntimeError ... damaged tape` | az ECMWF archívum szalagja sérült | nem a kérésed hibája, a hónap kimarad; jelezheted az ECMWF supportnak |
| `Maximum number queued requests for this dataset has been reached` | túl sok sorban álló kérés az ECDS-en | a kérések menjenek egymás után, ne párhuzamosan; az ECDS fiókod kéréseinél töröld a régi, függőben lévő kéréseket; várj, és próbáld újra |
| `unrecognized engine 'cfgrib'` | a `cfgrib` nincs telepítve az aktív környezetben | `pip install cfgrib` az aktív `.venv`-ben |
| `ecCodes library not found` | hiányzik a natív ecCodes | `python -m cfgrib selfcheck`, szükség esetén `conda install -c conda-forge eccodes cfgrib` |
| `multiple values for key 'numberOfPoints'` | a fájlban két rács van (2010-01, 2016-03) | használd a `get_month_point` láncot (7.6) |
| `Reindexing only valid with uniquely valued Index objects` | `sel(method="nearest")` a redukált Gauss-rácson | használd a `nearest_point` függvényt (7.5) |
| `FileNotFoundError ... .idx` / hiányzó GRIB | az adott hónap fájlja nincs meg | a feldolgozó kihagyja a hónapot; ellenőrizd a letöltést |
| `TypeError: unsupported operand type(s) for -: 'str' and 'str'` | a beolvasás után az oszlopok szövegek | `pd.to_numeric(..., errors="coerce")` a beolvasáskor |
| irreálisan nagy csapadék (több ezer mm) | a `tp` hibásan meg lett szorozva 1000-rel | a `tp` már mm-ben van (7.7) |

## 13. Git és adatkezelés

A nyers adatok nagyok, binárisak, és az ECMWF licenc alá esnek, ezért **nem kerülnek gitbe**. A repó a
**reprodukálhatóságot** szolgálja: a szkriptekből bárki újra elő tudja állítani az adatot a saját ECDS-fiókjával.

Javasolt `.gitignore`:

```gitignore
# nyers adat
tigge_data/
2020-2025/
*.grib
*.grb
*.nc
*.idx

# naplók
download_log.json
*.log

# Python
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/

# API-kulcs
.cdsapirc
*.key
```

- A kicsi, származtatott eredmények (`out_txt/`, `methu_txt/`) gitbe tehetők, ha a csoport úgy dönt.
- A notebookok **kimenetét** commit előtt érdemes törölni (`Kernel → Restart & Clear Output`), különben a fájl
  nagy és olvashatatlan lesz a diffekben.
- A TIGGE-adat licencét (a központtól függően CC BY 4.0 vagy CC BY-NC 4.0) az ECDS dataset oldalán ellenőrizd,
  mielőtt bármilyen adatot publikálsz.