import os
from datetime import date

import pandas as pd

from cowidev.utils.utils import export_timestamp
from cowidev import PATHS
from cowidev.megafile.steps import (
    get_base_dataset,
    add_macro_variables,
    add_excess_mortality,
    add_rolling_vaccinations,
)
from cowidev.megafile.export import (
    create_internal,
    create_dataset,
    create_latest,
    generate_readme,
    generate_status,
    generate_htmls,
)


INPUT_DIR = PATHS.INTERNAL_INPUT_DIR
DATA_DIR = PATHS.DATA_DIR
DATA_VAX_COUNTRIES_DIR = PATHS.DATA_VAX_COUNTRY_DIR
ANNOTATIONS_PATH = PATHS.INTERNAL_INPUT_OWID_ANNOTATIONS_FILE
README_TMP = PATHS.INTERNAL_INPUT_OWID_READ_FILE
README_FILE = PATHS.DATA_READ_FILE


def generate_megafile(logger):
    """Generate megafile data."""
    all_covid = get_base_dataset(logger)

    # Remove today's datapoint
    all_covid = all_covid[all_covid["date"] < str(date.today())]

    # Exclude some entities from megafile
    excluded = ["Summer Olympics 2020", "Winter Olympics 2022"]
    all_covid = all_covid[-all_covid.location.isin(excluded)]

    # Add ISO codes
    logger.info("Adding ISO codes…")
    iso_codes = pd.read_csv(PATHS.INTERNAL_INPUT_ISO_FILE)

    missing_iso = set(all_covid.location).difference(set(iso_codes.location))
    if len(missing_iso) > 0:
        # print(missing_iso)
        raise Exception(f"Missing ISO code for some locations: {missing_iso}")

    all_covid = iso_codes.merge(all_covid, on="location")

    # Add continents
    logger.info("Adding continents…")
    continents = pd.read_csv(
        PATHS.INTERNAL_INPUT_OWID_CONT_FILE,
        names=["_1", "iso_code", "_2", "continent"],
        usecols=["iso_code", "continent"],
        header=0,
    )

    all_covid = continents.merge(all_covid, on="iso_code", how="right")

    # Add macro variables
    # - the key is the name of the variable of interest
    # - the value is the path to the corresponding file
    macro_variables = {
        "population": "un/population_latest.csv",
        "population_density": "wb/population_density.csv",
        "median_age": "un/median_age.csv",
        "aged_65_older": "wb/aged_65_older.csv",
        "aged_70_older": "un/aged_70_older.csv",
        "gdp_per_capita": "wb/gdp_per_capita.csv",
        "extreme_poverty": "wb/extreme_poverty.csv",
        "cardiovasc_death_rate": "gbd/cardiovasc_death_rate.csv",
        "diabetes_prevalence": "wb/diabetes_prevalence.csv",
        "female_smokers": "wb/female_smokers.csv",
        "male_smokers": "wb/male_smokers.csv",
        "handwashing_facilities": "un/handwashing_facilities.csv",
        "hospital_beds_per_thousand": "owid/hospital_beds.csv",
        "life_expectancy": "owid/life_expectancy.csv",
        "human_development_index": "un/human_development_index.csv",
    }
    all_covid = add_macro_variables(all_covid, macro_variables, INPUT_DIR)

    # Add excess mortality
    all_covid = add_excess_mortality(
        df=all_covid,
        wmd_hmd_file=os.path.join(DATA_DIR, "excess_mortality", "excess_mortality.csv"),
        economist_file=os.path.join(DATA_DIR, "excess_mortality", "excess_mortality_economist_estimates.csv"),
    )

    # Calculate rolling vaccinations
    all_covid = add_rolling_vaccinations(all_covid)

    # Sort by location and date
    all_covid = all_covid.sort_values(["location", "date"])

    # Check that we only have 1 unique row for each location/date pair
    assert all_covid.drop_duplicates(subset=["location", "date"]).shape == all_covid.shape

    logger.info("Creating internal files…")
    create_internal(
        df=all_covid,
        output_dir=os.path.join(DATA_DIR, "internal"),
        annotations_path=ANNOTATIONS_PATH,
        country_data=DATA_VAX_COUNTRIES_DIR,
        logger=logger,
    )

    # Drop columns not included in final dataset
    cols_drop = [
        "excess_mortality_count_week",
        "excess_mortality_count_week_pm",
        "share_cases_sequenced",
        "rolling_vaccinations_6m",
        "rolling_vaccinations_6m_per_hundred",
        "rolling_vaccinations_9m",
        "rolling_vaccinations_9m_per_hundred",
        "rolling_vaccinations_12m",
        "rolling_vaccinations_12m_per_hundred",
        "cumulative_estimated_daily_excess_deaths",
        "cumulative_estimated_daily_excess_deaths_ci_95_top",
        "cumulative_estimated_daily_excess_deaths_ci_95_bot",
        "cumulative_estimated_daily_excess_deaths_per_100k",
        "cumulative_estimated_daily_excess_deaths_ci_95_top_per_100k",
        "cumulative_estimated_daily_excess_deaths_ci_95_bot_per_100k",
        "estimated_daily_excess_deaths",
        "estimated_daily_excess_deaths_ci_95_top",
        "estimated_daily_excess_deaths_ci_95_bot",
        "estimated_daily_excess_deaths_per_100k",
        "estimated_daily_excess_deaths_ci_95_top_per_100k",
        "estimated_daily_excess_deaths_ci_95_bot_per_100k",
        "stringency_index_nonvac",
        "stringency_index_vac",
        "stringency_index_weighted_avg",
    ]
    all_covid = all_covid.drop(columns=cols_drop)

    # Create light versions of complete dataset with only the latest data point
    logger.info("Writing latest…")
    create_latest(all_covid, logger)

    # Create datasets
    create_dataset(all_covid, macro_variables, logger)

    # Store the last updated time
    # export_timestamp(PATHS.DATA_TIMESTAMP_OLD_FILE, force_directory=PATHS.DATA_DIR)  # @deprecate

    # Update readme
    logger.info("Generating public/data/README.md")
    generate_readme(readme_template=README_TMP, readme_output=README_FILE)

    # Update readme
    logger.info("Generating scripts/STATUS.md")
    generate_status(template=PATHS.INTERNAL_INPUT_TEMPLATE_STATUS, output=PATHS.INTERNAL_STATUS_FILE)

    # Generate HTML aux tables
    logger.info("Generating aux tables…")
    generate_htmls()

    # Export timestamp
    timestamp = generate_timestamp()
    print(timestamp)
    export_timestamp(PATHS.DATA_TIMESTAMP_ROOT_FILE, timestamp=timestamp)

    logger.info("All done!")


def generate_timestamp():
    files = [
        PATHS.DATA_TIMESTAMP_HOSP_FILE,
        PATHS.DATA_TIMESTAMP_TEST_FILE,
        PATHS.DATA_TIMESTAMP_VAX_FILE,
        PATHS.DATA_TIMESTAMP_XM_FILE,
        PATHS.DATA_TIMESTAMP_JHU_FILE,
    ]
    timestamps = []
    for f in files:
        with open(f, "r") as f:
            timestamps.append(f.read())
    return max(timestamps)
