import xarray as xr
from pathlib import Path
import numpy as np
import pandas as pd
import eccodes
from tqdm import tqdm

KELVIN = 273.15

PROJECT_DIRECTORY = Path.cwd()

TXT_DIRECTORY = Path(f"{PROJECT_DIRECTORY}/out_txt") # output mappa létrehozása
TXT_DIRECTORY.mkdir(exist_ok=True)

START = (2006, 10)
END =   (2020, 12)

files = sorted(Path(f"{PROJECT_DIRECTORY}/tigge_data").glob("*.grib"))

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

def scan_grib_grids(fname):
    """Végigmegy a GRIB fájl üzenetein (csak a fejléceket olvassa),
    és üzenetenként visszaadja a dátumot, a lépést, a változót és a rács adatait."""
    rows = []
    with open(fname, "rb") as f:
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None:
                break
            rows.append({
                "date": eccodes.codes_get(gid, "dataDate"),
                "step": eccodes.codes_get(gid, "step"),
                "shortName": eccodes.codes_get(gid, "shortName"),
                "numberOfPoints": eccodes.codes_get(gid, "numberOfPoints"),
                "gridType": eccodes.codes_get(gid, "gridType"),
                "N": eccodes.codes_get(gid, "N") if eccodes.codes_is_defined(gid, "N") else None,
            })
            eccodes.codes_release(gid)
 
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"].astype(str))
    return df
 
def open_grib_all_grids(fname):
    """Egy GRIB fájlt rácsonként külön Datasetként nyit meg."""
    npoints_list = sorted(scan_grib_grids(fname)["numberOfPoints"].unique())
    return [
        xr.open_dataset(fname, engine="cfgrib",
                        backend_kwargs={"filter_by_keys": {"numberOfPoints": int(n)}})
        for n in npoints_list
    ]
 
def open_point_all_grids(fname, city):
    """Rácsonként kivágja a város legközelebbi pontját (a nearest_point-tal),
    majd időben összefűzi a részeket."""
    lat, lon = cities[city]
    parts = []
    for ds in open_grib_all_grids(fname):
        pt = nearest_point(ds, lat, lon).drop_vars(["latitude", "longitude"])
        if "time" not in pt.dims:           # ha a cfgrib skalárrá szűkítette az időt
            pt = pt.expand_dims("time")
        parts.append(pt)
    return xr.concat(parts, dim="time", data_vars="all",
                     coords="minimal", compat="override").sortby("time")
 
def get_month_point(year, month, city, debug = False):
    """A get_month_context_range + nearest_point együtt, rácsváltás-biztosan.
    Ugyanazt adja vissza, amit nearest_point(get_month_context_range(...)) adna:
    egy (time, step) dimenziós pont-Datasetet, a szomszéd hónapok 1-1 napjával kiegészítve."""
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_file = Path(f"tigge_data/{prev_year}-{prev_month:02}_cf.grib")
 
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    next_file = Path(f"tigge_data/{next_year}-{next_month:02}_cf.grib")
 
    fname = Path(f"tigge_data/{year}-{month:02}_cf.grib")
 
    if not fname.exists():
        if debug: print(f"[KIHAGYVA] A hónap hiányzik: {fname}")
        return None
 
    parts = [open_point_all_grids(fname, city)]
 
    if prev_file.exists():
        parts.insert(0, open_point_all_grids(prev_file, city).isel(time=[-1]))
    else:
        if debug: print(f"[FIGYELEM] Nincs meg az előző hónap fájlja: {prev_file.name}")
 
    if next_file.exists():
        parts.append(open_point_all_grids(next_file, city).isel(time=[0]))
    else:
        if debug: print(f"[FIGYELEM] Nincs meg a következő hónap fájlja: {next_file.name}")
 
    return xr.concat(parts, dim="time", data_vars="all",
                     coords="minimal", compat="override").sortby("time")

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

def output_multiple_months(start, end, city, debug = False):
    """Hónapokon végigmegy, és a város napi értékeit kiírja a out_txt/<város>_final.txt fájlba.
    Rácsváltás-biztos: a get_month_point rácsonként külön olvassa be a fájlokat."""
 
    months = list(month_breakdown(start, end))
    skipped = []
 
    with open(TXT_DIRECTORY / f"{city}_final.txt", "w", encoding="utf-8") as f:
 
        f.write("#datum;d_ta;d_tx;d_tn;d_rs\n")
 
        for month in tqdm(months, total= len(months), desc=city, unit="hónap"):
            pt = get_month_point(month[0], month[1], city, debug)
 
            if pt is None:
                skipped.append(month)
                continue
 
            df = daily_aggregation_methu(pt, month[0], month[1])
 
            for idx, row in df.iterrows():
                f.write(f"{row['datum']};{row['d_ta']};{row['d_tx']};{row['d_tn']};{row['d_rs']}\n")
 
    print(f"{city}: kihagyott hónapok ({len(skipped)} db): {skipped}")

#FŐciklus
for city in cities:
    output_multiple_months(START, (2007,6), city)