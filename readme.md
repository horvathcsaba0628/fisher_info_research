1: pip install ecmwf-datastores-client

2: pip install cdsapi

3: Regisztrálni kell az oldalon és kimásolni a felhasználó home könyvtárába (windows: C:\Users\felhasznalo) ".cdsapirc" fájlnéven a profil alatt található api url-t és api key-t.


Feljött kérdések:
- A letöltött adatok pontosítása:
    - A TIGGE-nek 13 különböző központja van, amiknek az adatai külön letölthetőek. Hány központ adatait akarjuk vizsgálni? Mind a 13 központ felhasználása lehetségesen kezelhetetlen mennyiség lenne. Kezdetileg egyedül az ECMWF központ előrejelzésivel kísérleteztem mert azt olvastam, hogy ez a leghosszabb, legjobban dokumentált archívum.

    - Time: Naponta két mérés is elérhető. 00:00 és 12:00 órakor. Szükségünk van a napi két mérésre, vagy elég a napi egy, ezzel csökkentve a vizsgálandó adatmennyiséget?

    - Leadtime (előrejelzési táv): ez azt jelenti, hány órával/nappal az indítás után nézzük az adott előrejelzést (pl. "mit jósolt a modell 3 nappal előre" vagy "10 nappal előre" ugyanabból az indításból) — minél messzebb nézünk előre, jellemzően annál bizonytalanabb az előrejelzés. Mennyi legyen ez az érték? 

    - Milyen paramétereket akarunk letölteni? (hőmérséklet, csapadék stb)

    - Ensemble tagok száma: a control forecast (1 futtatás) mellett a perturbed forecast tagokat is tervezem letölteni, mert a bizonytalanság/szórás csak ezekből számolható. Az ECMWF-nél 50 tag van — mind az 50 kelljen, vagy elég egy kisebb, reprezentatív részhalmaz (pl. 10-20) egy első, feltáró elemzéshez? Ha mind az 50-t használnánk az jelentősen megnövelné a letöltött fájlok méretét.

A PERTURBED FORECAST LETÖLTÉS EGY HÓNAPRA 30 PERCET VETT IGÉNYBE

.venv\Scripts\Activate.ps1