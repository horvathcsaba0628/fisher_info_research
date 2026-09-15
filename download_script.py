import cdsapi
import calendar
from pathlib import Path
import time

START = (2007, 1)
END =   (2007, 2)

OUT_DIRECTORY = Path("tigge_data")
OUT_DIRECTORY.mkdir(exist_ok=True) # ha még nincs output mappa létrehozunk egyet, ebbe fognak kerülni a grib fájlok

client = cdsapi.Client()

def month_breakdown(start, end):
    """A függvény paraméterként megkapja a kezdő és a végső évet és hónapot,
    majd sorban visszaadja a kezdő és a végső hónap közötti hónapokat.
    """
    year, month = start
    while (year, month) <= end:
        yield year, month

        month += 1
        if month > 12:
            month = 1
            year += 1

def days_of_month(year, month):
    ''' A függvény paraméterként megkap egy hónapot egy évben, és visszaad egy listát a 
    hónapban szereplő napokról két karakter hosszű string formában
    '''
    n = calendar.monthrange(year, month)[1]
    days = []

    for d in range(1, n + 1):
        days.append(f"{d:02d}")

    return days

def download_one_month(year, month, forecast_type, tag):
    "A függvény az out mappába letölt egy hónapnyi adatot"
    fname = OUT_DIRECTORY / f"{tag}_{year}-{month:02d}.grib"

    request = {
        "origin": "ecmwf",  # melyik állomás méréseit kérjuk
        "year": str(year),
        "month": f"{month:02d}",
        "day": days_of_month(year,month),
        "time": "12:00",
        "level_type": "single_level",                       # egy magassági szintű mérés
        "variable": [                                       # milyen paraméterek kellenek?
            "maximum_2_m_temperature_in_the_last_6_hours",  # max napi
            "minimum_2_m_temperature_in_the_last_6_hours",  # min napi
            "2_m_temperature",
            "total_precipitation"                           # csapadék
        ],
        "forecast_type": forecast_type,
        "leadtime_hour": ["24"],
        "data_format": "grib",
        "area": [49, 15.5, 45.5, 23] # kapott értékek a terület leszűkítésére
    }

    for attempt in range(2):
        try:
            print(f" - [API REQUEST SENT] {tag}_{year}-{month:02d} (2/{attempt+1} try)")
            client.retrieve("tigge-forecasts", request).download(str(fname))
            return

        except Exception as error:
            print(f"[HIBA] {tag}_{year}-{month:02d}: {error}")

# FŐCIKLUS - Letöltés
'''for year, month in month_breakdown(START, END):
    download_one_month(year, month, "control_forecast", "cf")'''