import cdsapi
import calendar

start = (2006, 10)
end =   (2007, 1)

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

dataset = "tigge-forecasts"
request = {
    "origin": "ecmwf",  # melyik állomás
    "year": "2006",
    "month": "10",
    "day": "06",
    "time": "12:00",
    "level_type": "single_level",
    "variable": [                                       # milyen paraméterek kellenek?
        "maximum_2_m_temperature_in_the_last_6_hours",
        "minimum_2_m_temperature_in_the_last_6_hours",
        "temperature",
        "total_precipitation"
    ],
    "forecast_type": "control_forecast",
    "leadtime_hour": ["24"],
    "data_format": "grib",
    "area": [49, 15.5, 45.5, 23] # kapott értékek a terület leszűkítésére
}

""" client = cdsapi.Client()
client.retrieve(dataset, request).download() """