import pandas as pd
from pathlib import Path

BASE = Path.cwd() / "2020-2025"

OUT_DIR = Path("out_txt")

START, END = "2021-01-01", "2025-12-31"

COLS = ["d_ta", "d_tx", "d_tn", "d_rs"]
VAR_FOLDER = {"d_ta": "ta", "d_tx": "tx", "d_tn": "tn", "d_rs": "rs"}

METHU_TXT = Path("methu_txt")

METHU_FILES = {
    "Budapest": "BP_d.txt",
    "Debrecen": "DE_d.txt",
    "Pecs": "PE_d.txt",
    "Szeged": "SZE_d.txt",
    "Szombathely": "SZO_d.txt",
}

CITIES = ["Budapest", "Debrecen", "Pecs", "Szeged", "Szombathely"]

def find_file(folder, name):

    hits = list(folder.glob(f"*{name}*.csv"))

    if len(hits) == 1:
        return hits[0]

    if len(hits) > 1:
        raise ValueError( f"Több találat a(z) {name} névre: " f"{[f.name for f in hits]}")

    raise FileNotFoundError( f"Nincs olyan fájl, ami illeszkedik: {name} a {folder} mappában")


#print(find_file(Path(f"{BASE}/rs"),["Pecs"]))

def read_variable(path, name):

    df = pd.read_csv(path, sep = ";", skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return pd.DataFrame({
        "datum": pd.to_datetime(df["Time"].astype(str), format="%Y%m%d"),
        name: pd.to_numeric(df.iloc[:, 1], errors="coerce"),
    })

#print(read_variable(Path(f"{BASE}/rs/r_o_Budapest_19012025.csv"),"Budapest"))

def read_methu_txt(path):
    df = pd.read_csv(path, sep=";", skiprows=1, header=None, usecols=range(5), names=["datum"] + COLS)
    df["datum"] = pd.to_datetime(df["datum"])

    for c in COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

for city in CITIES:

    table = None

    for var, folder in VAR_FOLDER.items():
        path = find_file(BASE / folder, city)
        part = read_variable(path, var)

        if table is None:
            table = part
        else:
            table = table.merge(part, on = "datum", how = "outer")

    table = table.sort_values("datum")
    table = table[(table["datum"] >= START) & (table["datum"] <= END)].copy()
    table = table[["datum", "d_ta", "d_tx", "d_tn", "d_rs"]]

    old = read_methu_txt(METHU_TXT / METHU_FILES[city])
    last_day = old["datum"].max()

    extra = table[table["datum"] > last_day][["datum"] + COLS]
    combined = pd.concat([old, extra], ignore_index=True).sort_values("datum")

    dup = combined["datum"].duplicated().sum()
    full = pd.date_range(combined["datum"].min(), combined["datum"].max())

    gaps = len(full.difference(combined["datum"]))
    #print(f"  {last_day.date()} után +{len(extra)} nap, duplikált: {dup}, hiányzó nap: {gaps}, " f"üres érték a hozzáfűzött részben: {int(extra[COLS].isna().sum().sum())}")

    out = combined.copy()
    out["datum"] = out["datum"].dt.strftime("%Y-%m-%d")
    out_path = METHU_TXT / METHU_FILES[city]

    out.to_csv(out_path, sep=";", index=False, header=["#datum"] + COLS, float_format="%.1f", encoding="utf-8")
    print(f" mentve: {out_path.name}")