import xarray as xr

ds = xr.open_dataset(r"tigge_data/cf_2006-10.grib", engine="cfgrib")

print(ds)
print(ds.time.values)