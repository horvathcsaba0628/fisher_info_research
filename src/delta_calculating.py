import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_PATH = Path.cwd()
print(PROJECT_PATH)
METHU_PATH = Path(f"{PROJECT_PATH}/methu_txt")
OUT_PATH = Path(f"{PROJECT_PATH}/out_txt")

cities = {
    "Budapest": "BP",
    "Debrecen": "DE",
    "Pécs": "PE",
    "Szeged": "SZE",
    "Szombathely": "SZO"
}

month_names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

tigge_list = []
methu_list = []

def read_file(path):
    '''
    Beolvas egy txt fájlt és dataframe-t csinál belőle
    --------------------------------------------------
    Reads a txt file and makes it a pandas dataframe
    '''
    df = pd.read_csv(path, sep=";", skiprows=1, header = None, usecols = range(5), names=["datum", "d_ta", "d_tx", "d_tn", "d_rs"] )
    
    df["datum"] = pd.to_datetime(df["datum"])
    for col in ["d_ta", "d_tx", "d_tn", "d_rs"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

for city in cities.items():

    td = read_file(f"{OUT_PATH}/{city[0]}_final.txt")
    td["varos"] = city[0]
    tigge_list.append(td)

    md = read_file(f"{METHU_PATH}/{city[1]}_d.txt")
    md["varos"] = city[0]
    methu_list.append(md)

tigge_data = pd.concat(tigge_list, ignore_index=True)
methu_data = pd.concat(methu_list, ignore_index=True)

merged = pd.merge(tigge_data, methu_data, on=["datum", "varos"], how="inner", suffixes=("_tigge", "_methu"))
merged_norm = merged.copy()

for v in ["d_ta","d_tx","d_tn","d_rs"]:
    for src in ["tigge", "methu"]:
        col = f"{v}_{src}"
        merged_norm[col] = merged_norm[col] / merged_norm[col].mean()

merged_norm["delta"] = 0

merged_norm["delta"] = (
    (merged_norm["d_ta_tigge"] - merged_norm["d_ta_methu"]) ** 2
    + (merged_norm["d_tx_tigge"] - merged_norm["d_tx_methu"]) ** 2
    + (merged_norm["d_tn_tigge"] - merged_norm["d_tn_methu"]) ** 2
    + (merged_norm["d_rs_tigge"] - merged_norm["d_rs_methu"]) ** 2
) ** 0.5

merged_norm["datum"] = pd.to_datetime(merged_norm["datum"])

""" monthly = merged_norm.groupby(merged_norm["datum"].dt.month)["delta"].agg(["mean", "median", "std", "count"]).round(3)
monthly.index.name = "honap" """



data = [merged_norm.loc[merged_norm["datum"].dt.month == m, "delta"].dropna() for m in range(1, 13)]

""" fig, ax = plt.subplots(figsize=(12, 5))
ax.boxplot(data, showmeans=True)
ax.set_xticklabels(month_names)
ax.set_xlabel("month")
ax.set_ylabel("daily delta")
ax.set_title(f"Monthly Distribution of Daily Delta, {merged_norm['datum'].dt.year.min()}–{merged_norm['datum'].dt.year.max()} (összes város)")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show() """

merged_norm["delta_temp"] = (
    (merged_norm["d_ta_tigge"] - merged_norm["d_ta_methu"]) ** 2
    + (merged_norm["d_tx_tigge"] - merged_norm["d_tx_methu"]) ** 2
    + (merged_norm["d_tn_tigge"] - merged_norm["d_tn_methu"]) ** 2
) ** 0.5

month = merged_norm["datum"].dt.month
fliers = False

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, col, title in zip( axes, ["delta", "delta_temp"],
    [
        "delta (temperature + precipitation)",
        "delta (temperature)"
    ]
):
    data = [
        merged_norm.loc[month == m, col].dropna()
        for m in range(1, 13)
    ]

    counts = [len(d) for d in data]


    ax.boxplot(data, showmeans=True, showfliers=fliers)

    
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([f"{name}\n(n:{count})" for name, count in zip(month_names, counts) ], fontsize = 8)
    ax.set

    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

axes[0].set_ylabel("Daily delta")

fig.suptitle(
    f"Daily delta by month, 2006-2025 (outliers shown = {fliers})"
)

plt.tight_layout()
plt.show()