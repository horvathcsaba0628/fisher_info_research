import xarray as xr
from pathlib import Path
import numpy as np
import pandas as pd

KELVIN = 273.15

files = sorted(Path(r"tigge_data").glob("*.grib"))

cities = {
        "Budapest": (47.4979, 19.0402),
        "Debrecen": (47.5316, 21.6273),
        "Pécs":     (46.0727, 18.2323),
        "Szeged":   (46.2530, 20.1414),
        "Szombathely": (47.23,16.62)
}

def month_breakdown(start, end):

    year, month = start
    while (year, month) <= end:
        yield year, month

        month += 1
        if month > 12:
            month = 1
            year += 1

def nearest_point(ds, cel_latitude, cel_longitude):
    lat = ds.latitude.values
    lon = ds.longitude.values
    distance = (lat - cel_latitude)**2 + (lon - cel_longitude)**2
    idx = np.argmin(distance)
    return ds.isel(values=idx)

def get_month_context_range(year, month, debug = False):
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_file = Path(f"tigge_data/{prev_year}-{prev_month:02}_cf.grib")

    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    next_file = Path(f"tigge_data/{next_year}-{next_month:02}_cf.grib")

    fname = Path(f"tigge_data/{year}-{month:02}_cf.grib")
    
    if not fname.exists():
        if debug : print(f"[KIHAGYVA] A hónap hiányzik: {fname}")
        return None
    
    file = xr.open_dataset(fname, engine="cfgrib")
    parts = [file]

    if prev_file.exists():
        prev = xr.open_dataset(prev_file, engine="cfgrib").isel(time=-1)
        parts.insert(0, prev.expand_dims("time"))
    else:
        if debug: print(f"[FIGYELEM] Nincs meg az előző hónap fájlja: {prev_file.name}")

    if next_file.exists():
        nxt = xr.open_dataset(next_file, engine="cfgrib").isel(time=0)
        parts.append(nxt.expand_dims("time"))
    else:
        if debug: print(f"[FIGYELEM] Nincs meg a következő hónap fájlja: {next_file.name}")

    merged = xr.concat(parts, dim="time")
    return merged.sortby("time")

def daily_max_min_methu(pont_ds, day_index):

    prev_day_24h_max = pont_ds["mx2t6"].isel(time = day_index - 1, step = 3)
    current_day_6_12_24_max = pont_ds["mx2t6"].isel(time = day_index, step=[0, 1, 2])
    current_day_max = current_day_6_12_24_max.max()

    daily_max = max(float(prev_day_24h_max), float(current_day_max)) - KELVIN


    prev_day_24h_min = pont_ds["mn2t6"].isel(time = day_index - 1, step = 3)
    current_day_6_12_24_min = pont_ds["mn2t6"].isel(time=day_index, step = [0, 1, 2])
    current_day_min = current_day_6_12_24_min.min()

    daily_min = min(float(prev_day_24h_min), float(current_day_min)) - KELVIN

    return [daily_max, daily_min]

def daily_precipitation_methu(pont_ds, day_index):

    current_step6 = float(pont_ds["tp"].isel(time = day_index, step = 0))
    current_step24 = float(pont_ds["tp"].isel(time = day_index, step = 3))
    next_step6 = float(pont_ds["tp"].isel(time = day_index + 1, step = 0))

    precipitation_m = (current_step24 - current_step6) + next_step6

    return max(precipitation_m, 0)

def daily_aggregation_methu(pont_ds, year, month):
    n_days = pont_ds.sizes["time"]
    
    rows = []
    for day_index in range(n_days):
        datum = pont_ds["time"].isel(time=day_index).values
        
        if day_index - 1 < 0 or day_index + 1 >= n_days:
            nap = pont_ds.isel(time=day_index)
            d_tx = float(nap["mx2t6"].max(dim="step")) - KELVIN
            d_tn = float(nap["mn2t6"].min(dim="step")) - KELVIN
            csapadek = max(float(nap["tp"].isel(step=-1)), 0)
            
        else:
            d_tx, d_tn = daily_max_min_methu(pont_ds, day_index)
            csapadek = daily_precipitation_methu(pont_ds, day_index)
        
        d_ta = (d_tx + d_tn) / 2 if not (np.isnan(d_tx) or np.isnan(d_tn)) else np.nan
        
        rows.append({
            "datum": pd.Timestamp(datum),
            "d_ta": round(d_ta,1),
            "d_tx": round(d_tx,1),
            "d_tn": round(d_tn,1),
            "d_rs": round(csapadek,1),
        })
    
    df = pd.DataFrame(rows)
    
    # csak az adott hónap saját napjai maradjanak - a becsatolt szomszéd-napokat dobjuk el
    df = df[(df["datum"].dt.year == year) & (df["datum"].dt.month == month)].reset_index(drop=True)

    df["datum"] = df["datum"].astype(str).str[0:10]
    
    return df

TXT_DIRECTORY = Path("out_txt") # output mappa létrehozása
TXT_DIRECTORY.mkdir(exist_ok=True)

def output_multiple_months(start,end, city, debug = False):
        
        months = month_breakdown(start,end)
        skipped = []

        with open("out_txt/bp_output3.txt", "w") as f:

                f.write("#datum;d_ta;d_tx;d_tn;d_rs\n")

                for month in months:
                        context = get_month_context_range(month[0],month[1], debug)

                        if context is None:
                                skipped.append(month)
                                continue

                        pt = nearest_point(context,cities[city][0],cities[city][1])

                        df = daily_aggregation_methu(pt, month[0],month[1])

                        for idx, row in df.iterrows():
                                f.write(f"{row["datum"]};{row["d_ta"]};{row["d_tx"]};{row["d_tn"]};{row["d_rs"]}\n")

        f.close()

# FŐŐ
output_multiple_months((2010,1), (2010,3), "Budapest", True)