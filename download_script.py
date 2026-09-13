import cdsapi

start = (2006, 10)
end =   (2007, 1)

dataset = "tigge-forecasts"
request = {
    "origin": "ecmwf",  # melyik állomás
    "year": "2006",
    "month": "10",
    "day": "06",
    "time": "12:00",
    "level_type": "single_level",
    "variable": [                       # milyen paraméterek kellenek?
        "2_m_dewpoint_temperature",   
        "mean_sea_level_pressure",
        "total_precipitation"
    ],
    "forecast_type": "control_forecast",
    "leadtime_hour": ["24"],
    "data_format": "grib",
    "area": [49, 15.5, 45.5, 23] # kapott értékek a terület leszűkítésére
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()
