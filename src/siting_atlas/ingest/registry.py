"""The 14 data sources, declared once.

This is reference data, not logic. Each entry carries not just where a source
lives but what it costs you to believe it: the vintage trap, the coverage
break, the credential the provider echoes back. Those notes are long on
purpose — they are what `docs/data/` is generated from, so a fact recorded
here reaches the reader rather than dying in a commit message.
"""

from __future__ import annotations

from .source_types import Availability, Grain, Source

SOURCES: tuple[Source, ...] = (
    Source(
        key="acs5",
        handled_by="siting_atlas.ingest.census_api",
        title="American Community Survey, 5-year estimates",
        provider="US Census Bureau",
        grain=Grain.ZCTA,
        role="Demographics, income, age, household size (level features)",
        availability=Availability.NEEDS_KEY,
        url="https://api.census.gov/data/{year}/acs/acs5",
        probe_url=("https://api.census.gov/data/2022/acs/acs5"
                   "?get=NAME,B19013_001E"
                   "&for=zip%20code%20tabulation%20area:94608"),
        docs_url="https://www.census.gov/data/developers/data-sets/acs-5year.html",
        key_env="CENSUS_API_KEY",
        cadence="annual",
        lag_months=21,
        notes=("The query endpoint returns an HTML 'Missing Key' page with "
               "HTTP 200 when no key is supplied, which is why fetch() "
               "validates Content-Type. Keys are free and instant from "
               "https://api.census.gov/data/key_signup.html"),
        fields=("B01003_001E", "B19013_001E", "B25077_001E", "B08201_001E",
                "B01002_001E", "B15003_022E"),
    ),
    Source(
        key="acs1",
        handled_by="siting_atlas.ingest.census_api",
        title="American Community Survey, 1-year estimates",
        provider="US Census Bureau",
        grain=Grain.METRO,
        role="Recent demographic movement at a shorter lag (metro context)",
        availability=Availability.NEEDS_KEY,
        url="https://api.census.gov/data/{year}/acs/acs1",
        probe_url=("https://api.census.gov/data/2022/acs/acs1"
                   "?get=NAME,B01003_001E&for=metropolitan%20statistical%20"
                   "area/micropolitan%20statistical%20area:41860"),
        docs_url="https://www.census.gov/data/developers/data-sets/acs-1year.html",
        key_env="CENSUS_API_KEY",
        cadence="annual",
        lag_months=9,
        notes="Published only for areas above 65,000 population.",
        fields=("B01003_001E", "B19013_001E"),
    ),
    Source(
        key="gaz_zcta",
        title="Census Gazetteer, ZCTA national file",
        provider="US Census Bureau",
        grain=Grain.ZCTA,
        role=("Centroid and land area for every ZCTA - the geometry the "
              "cost model actually needs"),
        availability=Availability.OPEN,
        url=("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
             "{year}_Gazetteer/{year}_Gaz_zcta_national.zip"),
        probe_url=("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
                   "2023_Gazetteer/2023_Gaz_zcta_national.zip"),
        docs_url="https://www.census.gov/geographies/reference-files.html",
        cadence="annual",
        lag_months=None,
        notes=("1 MB, versus 520 MB for the full TIGER shapefile. Daganzo "
               "needs area and a centroid, not polygon detail, so the "
               "shapefile is only pulled when a choropleth is rendered."),
        fields=("GEOID", "ALAND_SQMI", "INTPTLAT", "INTPTLONG"),
    ),
    Source(
        key="cbsa_county",
        title="OMB metropolitan area delineation, 2023",
        provider="US Census Bureau / OMB",
        grain=Grain.COUNTY,
        role="Defines which counties constitute each metro area",
        availability=Availability.OPEN,
        url=("https://www2.census.gov/programs-surveys/metro-micro/"
             "geographies/reference-files/2023/delineation-files/"
             "list1_2023.xlsx"),
        docs_url=("https://www.census.gov/geographies/reference-files/"
                  "time-series/demo/metro-micro/delineation-files.html"),
        cadence="revised every few years",
        lag_months=None,
        notes=(
            "Metro membership must come from the official delineation, not "
            "from whichever ZCTAs happen to appear in a commercial rent "
            "index.\n\n"
            "Using Zillow's `Metro` column as the pilot filter was measured "
            "against this file and drops 35% of pilot-metro ZCTAs - and the "
            "dropped ones have a median population of 4,731 against 30,589 "
            "for those kept. Zillow publishes a rent index only where there "
            "are enough listings, so the filter silently selects for density. "
            "Those low-density fringe ZCTAs are precisely where a same-day "
            "expansion decision is contested; the dense ones are foregone "
            "conclusions. Filtering on them would be selecting the sample on "
            "something correlated with the outcome.\n\n"
            "So membership comes from here, and rent stays a feature with "
            "honest missingness rather than becoming a filter.\n\n"
            "The 2023 vintage uses Connecticut's nine planning regions. The "
            "ZCTA-to-county file is still 2020 and uses the eight old "
            "counties, so Connecticut will not join - the same known gap "
            "recorded under `bps_county`, and no pilot metro is affected."),
    ),
    Source(
        key="zcta_county_xwalk",
        title="ZCTA-to-county relationship file, 2020",
        provider="US Census Bureau",
        grain=Grain.ZCTA,
        role=("Joins county-grain sources (building permits, wages) down to "
              "ZCTA"),
        availability=Availability.OPEN,
        url=("https://www2.census.gov/geo/docs/maps-data/data/rel2020/"
             "zcta520/tab20_zcta520_county20_natl.txt"),
        docs_url="https://www.census.gov/geographies/reference-files.html",
        cadence="decennial",
        lag_months=None,
        notes=("A ZCTA can span several counties; the file carries the land "
               "area of each intersection so the join can be area-weighted "
               "rather than assigned to one county arbitrarily."),
    ),
    Source(
        key="tiger_zcta",
        title="TIGER/Line ZCTA boundaries, 2020 vintage",
        provider="US Census Bureau",
        grain=Grain.ZCTA,
        role="Geometry for spatial joins, centroids and distance bands",
        availability=Availability.OPEN,
        url=("https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/"
             "tl_2020_us_zcta520.zip"),
        docs_url="https://www.census.gov/geographies/mapping-files.html",
        cadence="decennial, with annual reissues",
        lag_months=None,
        notes=("~520 MB. Vintage is pinned: mixing 2010 and 2020 ZCTA "
               "boundaries silently corrupts a time series."),
    ),
    Source(
        key="cbp_zip",
        title="County Business Patterns, ZIP-code totals",
        provider="US Census Bureau",
        grain=Grain.ZIP,
        role="Retail density / competitive pull (administrative universe)",
        availability=Availability.OPEN,
        url=("https://www2.census.gov/programs-surveys/cbp/datasets/"
             "{year}/zbp{yy}totals.zip"),
        docs_url="https://www.census.gov/programs-surveys/cbp.html",
        cadence="annual",
        lag_months=18,
        notes=("Replaces a commercial business directory: bulk download, no "
               "key, no rate limit, and an administrative universe rather "
               "than a self-selected one."),
    ),
    Source(
        key="bps_county",
        title="Building Permits Survey, county annual",
        provider="US Census Bureau",
        grain=Grain.COUNTY,
        role="Leading indicator — construction precedes population",
        availability=Availability.OPEN,
        url="https://www2.census.gov/econ/bps/County/co{yy}12y.txt",
        docs_url="https://www.census.gov/construction/bps/",
        cadence="monthly, with annual summaries",
        lag_months=2,
        vintages=("17", "18", "19", "20", "21", "22", "23", "24", "25"),
        notes=(
            "The forward signal that offsets the ACS reporting lag.\n\n"
            "One file per year, and every vintage is fetched: a "
            "year-over-year feature is impossible from a single year. "
            "Pulling only the latest file produced a silently all-null "
            "`permits_yoy_pct` - no error, no warning, just a dead column.\n\n"
            "Two coverage breaks are real and are handled rather than "
            "smoothed over:\n\n"
            "1. **County universe widens in 2022.** Vintages 2017-2021 report "
            "~745 counties; 2022 onward report ~3,021. The earlier subset is "
            "the large counties - about 68% of national permit volume - so "
            "the series is not wrong, just narrower. Year-over-year is "
            "computed by a LEFT JOIN on year-1, so a county with no "
            "prior-year row yields NULL rather than a fabricated spike. "
            "Coverage of `permits_yoy_pct` is therefore ~33% for "
            "2018-2022 and ~93% from 2023.\n\n"
            "2. **Connecticut changes geography in 2023.** The eight counties "
            "(09001-09015) are replaced by nine planning regions "
            "(09110-09190), with no CT rows at all in the 2022 file. The "
            "ZCTA-to-county crosswalk still uses the old codes, so "
            "Connecticut ZCTAs carry permits for 2017-2021 and NULL "
            "from 2023. No pilot or hold-out metro is in Connecticut, "
            "so this is recorded as a known gap rather than repaired."
            "\n\n"
            "The file layout itself is stable across all nine vintages - 30 "
            "fields, the same two merged header rows. Only the county-name "
            "padding width changed, which is why one parser reads them all."),
    ),
    Source(
        key="zillow_zori",
        title="Zillow Observed Rent Index, ZIP level",
        provider="Zillow Research",
        grain=Grain.ZIP,
        role="Disposable income proxy and commercial land-cost proxy",
        availability=Availability.BLOCKED,
        url=("https://files.zillowstatic.com/research/public_csvs/zori/"
             "Zip_zori_uc_sfrcondomfr_sm_month.csv"),
        docs_url="https://www.zillow.com/research/data/",
        licence="Zillow Research terms — free for non-commercial research",
        cadence="monthly",
        lag_months=1,
        notes=("Egress proxy returns HTTP 503 for files.zillowstatic.com. "
               "Download manually and place in data/external/."),
    ),
    Source(
        key="bls_oes",
        title="Occupational Employment and Wage Statistics, metro",
        provider="US Bureau of Labor Statistics",
        grain=Grain.METRO,
        role="Driver and warehouse wages (largest varying capital bucket)",
        availability=Availability.BLOCKED,
        url="https://www.bls.gov/oes/special-requests/oesm{yy}ma.zip",
        docs_url="https://www.bls.gov/oes/tables.htm",
        cadence="annual",
        lag_months=12,
        notes=("bls.gov returns HTTP 403 to this environment even with a "
               "descriptive User-Agent. Download manually."),
    ),
    Source(
        key="eia_prices",
        handled_by="siting_atlas.ingest.eia_api",
        title="Regional fuel and industrial electricity prices",
        provider="US Energy Information Administration",
        grain=Grain.REGION,
        role="Fuel and energy capital bucket",
        availability=Availability.NEEDS_KEY,
        url="https://api.eia.gov/v2/electricity/retail-sales/data/",
        probe_url=("https://api.eia.gov/v2/electricity/retail-sales/data/"
                   "?frequency=monthly&data[0]=price&length=1"),
        docs_url="https://www.eia.gov/opendata/",
        key_env="EIA_API_KEY",
        cadence="monthly",
        lag_months=2,
        notes=("Free key from https://www.eia.gov/opendata/register.php. "
               "An unauthenticated request returns HTTP 403, which reads "
               "like a network block but is the missing-key response - the "
               "probe records 'blocked' until a key is present. Pages are "
               "capped at 5,000 rows and the cap is silent, so the extractor "
               "follows offsets rather than trusting one response."),
    ),
    Source(
        key="facility_panel",
        title="Logistics facility panel with opening dates",
        provider="Public facility inventories, filings and local press",
        grain=Grain.FACILITY,
        role="THE TARGET VARIABLE — service enablement and timing",
        availability=Availability.MANUAL,
        docs_url="",
        licence="Compiled from public sources; verify each compiler's terms",
        cadence="continuous",
        lag_months=1,
        notes=("No single stable endpoint. Compiled from published "
               "inventories, corporate announcements and permit records, "
               "and delivered as a 43-row CENSUS of what the sources "
               "actually yield rather than a sample - hand-verifying 100 "
               "is impossible on 43. Accuracy is instead evidenced by an "
               "external cross-check: five addresses appear in both "
               "MWPVL's 2012 table and the OSHA extract, the "
               "operating-by bound held 5 of 5, and the lag to first "
               "inspection ran 4 to 345 months. "
               "measured error rate reported. Terms of use of any "
               "third-party compilation must be checked before use."),
    ),
    Source(
        key="ejscreen",
        title="EJScreen environmental justice indicators",
        provider="US Environmental Protection Agency",
        grain=Grain.BLOCK_GROUP,
        role="Equity overlay — predicted burden by demographic stratum",
        availability=Availability.MANUAL,
        url="",
        docs_url="https://www.epa.gov/ejscreen",
        cadence="annual",
        lag_months=12,
        notes=("The historical gaftp.epa.gov paths now return 404; the "
               "distribution location has moved. Resolve the current URL "
               "from the landing page and place the file in data/external/."),
    ),
    Source(
        key="osm",
        title="OpenStreetMap road network extracts",
        provider="Geofabrik / BBBike",
        grain=Grain.NETWORK,
        role="Drive times — used once, offline, then deleted",
        availability=Availability.OPEN,
        url="https://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf",
        docs_url="https://download.geofabrik.de/",
        licence="Open Database License (ODbL) — attribution required",
        cadence="daily",
        lag_months=0,
        notes=("Infrastructure rather than an analytical source: consumed "
               "once to produce the origin-destination matrix, after which "
               "every artefact is deleted (ADR-0002)."),
    ),
)

BY_KEY = {s.key: s for s in SOURCES}

# The nine sources that feed the analytical panel. OpenStreetMap is excluded
# because it is consumed offline and never reaches the feature table.
