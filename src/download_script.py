import cdsapi
import calendar
from pathlib import Path
import time
import json

START = (2021,1)
END =   (2025, 12)

PROJECT_DIRECTORY = Path.cwd()

OUT_DIRECTORY = Path(f"{PROJECT_DIRECTORY}/tigge_data")
OUT_DIRECTORY.mkdir(exist_ok=True)              # If the directory doesn't exist already, we create it

LOG_FILE = OUT_DIRECTORY / "log.json"

client = cdsapi.Client()

if LOG_FILE.exists():                           # Loading our log file
    log = json.loads(LOG_FILE.read_text())
else:
    log = {}

def save_log():
    LOG_FILE.write_text(json.dumps(log, indent=2))

def month_breakdown(start, end):
    """ 
    A függvény paraméterként megkapja a kezdő és a végső évet és hónapot,
    majd sorban visszaadja a kezdő és a végső hónap közötti hónapokat.
    -------------------------------------------------------------------------------
    The function takes the starting and ending year and month as parameters, then 
    returns the months between the starting and ending month in chronological order.
    """

    year, month = start
    while (year, month) <= end:
        yield year, month

        month += 1
        if month > 12:
            month = 1
            year += 1

def days_of_month(year, month):
    ''' 
    A függvény paraméterként megkap egy hónapot egy évben, és visszaad egy listát a 
    hónapban szereplő napokról két karakter hosszű string formában
    --------------------------------------------------------------------------------
    The function takes a month and a year as parameters and returns a list of the days in 
    that month as two-character strings.
    '''

    n = calendar.monthrange(year, month)[1]
    days = []

    for d in range(1, n + 1):
        days.append(f"{d:02d}")

    return days

def download_one_month(year, month, forecast_type = "control-forecast", tag = "cf"):
    """
    A függvény az out mappába letölt egy hónapnyi adatot
    ------------------------------------------------------------
    The function downloads one month of data into the out folder.
    """

    key = f"{year}-{month:02d}_{tag}"
    fname = OUT_DIRECTORY / f"{key}.grib"

    if log.get(key) == "done" and fname.exists():
        print(f"[SKIP] {key} is already downloaded")
        return
    

    request = {
        "origin": "ecmwf",  # melyik állomás méréseit kérjuk / which station do we download the data from
        "year": str(year),
        "month": f"{month:02d}",
        "day": days_of_month(year,month),
        "time": "00:00",
        "level_type": "single_level",                       # egy magassági szintű mérés / 
        "variable": [                                       # milyen paraméterek kellenek? / what parameters do we need
            "maximum_2_m_temperature_in_the_last_6_hours",  # max napi / maximum daily temp
            "minimum_2_m_temperature_in_the_last_6_hours",  # min napi / minimum daily temp
            "2_m_temperature",
            "total_precipitation"                           # csapadék / precipitation
        ],
        "forecast_type": forecast_type,
        "leadtime_hour": ["6","12","18","24"],
        "data_format": "grib",
        "area": [49, 15.5, 45.5, 23] # kapott értékek a terület leszűkítésére
    }

    for attempt in range(2):
        try:
            print(f" - [API REQUEST SENT] {key} (2/{attempt+1} try)")
            client.retrieve("tigge-forecasts", request).download(str(fname))
            log[key] = "done"
            save_log()
            return

        except Exception as error:
            print(f"[HIBA] {key}: {error}")
            log[key] = f"error: {error}"
            save_log()

# FŐCIKLUS - Letöltés
for year, month in month_breakdown(START, END):
    download_one_month(year, month)