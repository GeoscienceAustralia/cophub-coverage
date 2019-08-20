#!/usr/bin/env python

from datetime import datetime
import json
import subprocess
from pathlib import Path
import click
import pandas
import structlog


LOG = structlog.get_logger()


# Financial years
PERIODS = pandas.date_range('2015', '2020', freq='AS-JUL')

REGIONS = [
    "Oceania",
    "Asia",
    "Antartica",
    "OpenOcean",
    "Africa",
    "Europe",
    "NorthAmerica",
    "SouthAmerica",
    "Unclassified"
]

# product, sentinel mission
COMBINATIONS = [
#     ("SLC", "1"),
#     ("GRD", "1"),
#     ("OCN", "1"),
#     ("RAW", "1"),
    ("S2MSIL1C", "2"),
    ("S2MSIL2A", "2"),
#     ("OL_1_EFR___", "3"),
#     ("OL_1_ERR___", "3"),
#     ("OL_2_LFR___", "3"),
#     ("OL_2_LRR___", "3"),
#     ("OL_2_WFR___", "3"),
#     ("OL_2_WRR___", "3"),
#     ("SL_1_RBT___", "3"),
#     ("SL_2_LST___", "3"),
#     ("SL_2_WST___", "3"),
#     ("SR_1_SRA_A_", "3"),
#     ("SR_1_SRA_BS", "3"),
#     ("SL_2_SRA___", "3"),
#     ("SR_2_LAN___", "3"),
#     ("SR_2_WAT___", "3"),
#     ("SY_2_SYN___", "3"),
#     ("SY_2_V10___", "3"),
#     ("SY_2_VG1___", "3"),
#     ("SY_2_SGP___", "3"),
]


@click.command()
@click.option("--outdir", required=True,
              type=click.Path(file_okay=False, writable=True, dir_okay=True),
              help="The output directory in which to write the results.")
def main(outdir):
    """
    Main level.
    Output JSON results from each query, and summarise into a file
    named 'region-stats.csv'.
    """
    outdir = Path(outdir)
    result = {
       'region': [],
       'sentinel_mission': [],
       'product': [],
       'start_date': [],
       'end_date': [],
       'bytes': []
    }

    for i in range(1, len(PERIODS)):
        start_date = PERIODS[i-1].strftime('%Y-%m-%d')
        end_date = PERIODS[i].strftime('%Y-%m-%d')

        for region in REGIONS:
            for combo in COMBINATIONS:
                out_fname = outdir.joinpath(
                    "sentinel-{}-{}-{}-{}-{}.json".format(combo[1], combo[0],
                                                          region, start_date,
                                                          end_date)
                )
                cmd = [
                    "auscophub_searchSara.py",
                    "--sentinel", combo[1],
                    "-q", "startDate={}".format(start_date),
                    "-q", "completionDate={}".format(end_date),
                    "-q", "productType={}".format(combo[0]),
                    "-q", "name={}".format(region),
                    "--jsonfeaturesfile", out_fname
                ]

                LOG.info('executing',
                         command=cmd,
                         time=datetime.now().isoformat())
                try:
                    subprocess.check_call(cmd)
                except subprocess.CalledProcessError:
                    LOG.error('Failed to execute',
                              command=cmd,
                              time=datetime.now().isoformat())
                    continue

                with open(out_fname, 'r') as src:
                    data = json.load(src)

                # tally the size in bytes
                size = 0
                for feat in data['features']:
                    size += feat['properties']['services']['download']['size']

                # append record
                result['region'].append(region)
                result['sentinel_mission'].append(combo[1])
                result['product'].append(combo[0])
                result['start_date'].append(start_date)
                result['end_date'].append(end_date)
                result['bytes'] = size

    df = pandas.DataFrame(result)
    df.to_csv(outdir.joinpath('region-stats-S2.csv'))


if __name__ == '__main__':
    main()
