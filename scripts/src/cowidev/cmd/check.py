import datetime
import pandas as pd

import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log


JHU_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/jhu/full_data.csv"
VAX_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"
TESTING_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/testing/covid-testing-all-observations.csv"


def check_updated(url, date_col, allowed_days, weekends) -> None:
    if not weekends and datetime.datetime.today().weekday() in [5, 6]:
        print("Today is a weekend, skipping...")
        return
    df = pd.read_csv(url)
    max_date = df[date_col].max()
    if max_date < str(datetime.date.today() - datetime.timedelta(days=allowed_days)):
        raise Exception(
            f"Data is not updated! "
            f"Check if something is broken in our pipeline and/or if someone is in charge of today's update."
        )
    else:
        print("Check passed. All good!")


@click.group(name="check", chain=True, cls=OrderedGroup)
@click.pass_context
def click_check(ctx):
    """COVID-19 data pipeline checks."""
    pass


@click.command(name="vax", short_help="Vaccination data.")
@click.pass_context
def click_check_vax(ctx):
    """Generate dataset."""
    feedback_log(
        func=check_updated,
        url=VAX_URL,
        date_col="date",
        allowed_days=1,
        weekends=False,
        server=ctx.obj["server"],
        domain="Check",
        step="vaccinations",
        hide_success=True,
    )


@click.command(name="jhu", short_help="JHU data.")
@click.pass_context
def click_check_jhu(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=check_updated,
        url=JHU_URL,
        date_col="date",
        allowed_days=1,
        weekends=True,
        server=ctx.obj["server"],
        domain="Check",
        step="vaccinations",
        hide_success=True,
    )


@click.command(name="test", short_help="Testing data.")
@click.pass_context
def click_check_test(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=check_updated,
        url=TESTING_URL,
        date_col="Date",
        allowed_days=7,
        weekends=False,
        server=ctx.obj["server"],
        domain="Check",
        step="vaccinations",
        hide_success=True,
    )


click_check.add_command(click_check_vax)
click_check.add_command(click_check_jhu)
click_check.add_command(click_check_test)
