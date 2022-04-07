#!/usr/bin/env python
"""
Prepare the NorESM2 output by getting it directly from the http://noresg.nird.sigma2.no THREDDS server
"""
import os.path
import pandas as pd
import xarray as xr
from siphon import catalog
from dask.distributed import Client, LocalCluster
import warnings
from tqdm import tqdm
import dask
from dask.diagnostics import ProgressBar

overwrite = False

model = 'NorESM2-LM'
experiments = [
               '1pctCO2', 'abrupt-4xCO2', 'historical', 'piControl', # CMIP
               'hist-GHG', 'hist-aer', # DAMIP
               'ssp126', 'ssp245', 'ssp370', 'ssp370-lowNTCF', 'ssp585' #	ScenarioMIP
]
variables = [
             'tas', 'tasmin', 'tasmax', 'pr'
]



# using NIRD ESGF node directly

def get_MIP(experiment):
    if experiment == 'ssp245-covid':
        return 'DAMIP'
    elif experiment == 'ssp370-lowNTCF':
        return 'AerChemMIP'
    elif experiment.startswith('ssp'):
        return 'ScenarioMIP'
    elif experiment.startswith('hist-'):
        return 'DAMIP'
    else:
        return 'CMIP'


def get_esgf_data(variable, experiment, ensemble_member):
    """
    Inspired by https://github.com/rabernat/pangeo_esgf_demo/blob/master/narr_noaa_thredds.ipynb
    """

    # Get the relevant catalog references
    #print(full_catalog.catalog_refs.items())
    cat_refs = list({k:v for k,v in full_catalog.catalog_refs.items() if k.startswith(f"CMIP6.{get_MIP(experiment)}.NCC.NorESM2-LM.{experiment}.{ensemble_member}.day.{variable}.")}.values())
    # Get the latest version (in case there are multiple)
    #print(cat_refs)
    cat_ref = sorted(cat_refs, key=lambda x: str(x))[-1]
    sub_cat = cat_ref.follow().datasets
    datasets = []
    # Filter and fix the datasets
    for cds in sub_cat[:]:
    # Only pull out the (un-aggregated) NetCDF files
        if (str(cds).endswith('.nc') and ('aggregated' not in str(cds))):
        # For some reason these OpenDAP Urls are not referred to as Siphon expects...
            cds.access_urls['OPENDAP'] = cds.access_urls['OpenDAPServer']
            datasets.append(cds)
    dsets = [(cds.remote_access(use_xarray=True).reset_coords(drop=True).chunk({'time': 365})) for cds in datasets]
    ds = xr.combine_by_coords(dsets, combine_attrs='drop')
    return ds[variable]

if __name__ == '__main__':
    #cluster = LocalCluster(n_workers=4, processes=True, diagnostics_port=None, scheduler_port=0, silence_logs=10, worker_dashboard_address=':0', dashboard_address=':0', threads_per_worker=1)
    #print(cluster)
    #client = Client(cluster, worker_dashboard_address=':0', dashboard_address=':0', local_directory='/tmp')
    #print(client)
    print("starting")
    # Cache the full catalogue from NorESG
    # !! origina link (http://noresg.nird.sigma2.no/thredds/catalog/esgcet/catalog.xml) not working !!
    full_catalog = catalog.TDSCatalog('http://esgf.nci.org.au/thredds/catalog/esgcet/catalog.xml')
    print("Read full catalogue")
    #Loop over experiments and members creating one (annual mean) file with all variables in for each one
    for experiment in tqdm(experiments):
        print('gathering ensemble members for ', experiment)
        # Just take three ensemble members (there are more in the COVID simulation but we don't need them all)
        for i in range(3):
            physics = 2 if experiment == 'ssp245-covid' else 1  # The COVID simulation uses a different physics setup
            # TODO - check the differences...
            member = f"r{i+1}i1p1f{physics}"
            #print(f"Processing {member} of {experiment}...")
            outfile = f"{model}_{experiment}_{member}.nc"
            if (not overwrite) and os.path.isfile(outfile):
                print("File already exists, skipping.")
                continue

            try:
                tasmin = get_esgf_data('tasmin', experiment, member)
                tasmax = get_esgf_data('tasmax', experiment, member)
                tas = get_esgf_data('tas', experiment, member)
                pr = get_esgf_data('pr', experiment, member).persist()  # Since we need to process it twice
                print('obtained data')
            except IndexError:
                print("Skipping this realisation as no data present")
                continue

            # Derive additional vars
            print('constructing dataset')
            dtr = tasmax-tasmin
            ds = xr.Dataset({'diurnal_temperature_range': dtr.groupby('time.year').mean('time'),
                             'tas': tas.groupby('time.year').mean('time'),
                             'pr': pr.groupby('time.year').mean('time'),
                             'pr90': pr.groupby('time.year').quantile(0.9, skipna=True)})
            print('obtained ds')
            print(ds)
            # for faster computation and progress report, convert to dask
            ds.to_dask_dataframe()
            # making use of chunkwise computation as ds is very big
            delayed_ds = ds.to_netcdf(f"data/{model}_{experiment}_{member}.nc", format='netCDF4', engine='netcdf4', compute=False)
            with ProgressBar():
              results = delayed_ds.compute()
