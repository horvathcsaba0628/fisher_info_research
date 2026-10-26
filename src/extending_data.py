import pandas as pd
from pathlib import Path

BASE = Path.cwd() / "2020-2025"

OUT_DIR = Path("out_txt")

START, END = "2020-01-01", "2025-12-31"

VAR_FOLDER = {"d_ta": "ta", "d_tx": "tx", "d_tn": "tn", "d_rs": "rs"}

CITIES = ["Budapest", "Debrecen", "Pecs", "Szeged", "Szomvbathely"]

def find_file(folder, names):

    for name in names:
        hits = list(folder.glob(f"*{name}*.csv"))

        if len(hits) == 1:
            return hits[0]

    raise FileNotFoundError(f"Nincs olyan fájl ami: {names}")

#print(find_file(Path(f"{BASE}/rs"),["Budapest", "Szombathely"]))

def read_variable(path, name):

    df = pd.read_csv(path, sep = ";", skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return pd.DataFrame({
        "datum": pd.to_datetime(df["Time"].astype(str), format="%Y%m%d"),
        name: pd.to_numeric(df.iloc[:, 1], errors="coerce"),
    })

#print(read_variable(Path(f"{BASE}/rs/r_o_Budapest_19012025.csv"),"Budapest"))