import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.uk_nations import generate_dataset, update_db


@click.group(name="uk-nations", chain=True, cls=OrderedGroup)
@click.pass_context
def click_uk_nations(ctx):
    """COVID-19 UK Nations data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate UK Nations dataset.")
@click.pass_context
def click_uk_get(ctx):
    """Generate dataset."""
    feedback_log(
        func=generate_dataset,
        server=ctx.obj["server"],
        domain="UK Nations",
        step="generate",
        hide_success=True,
    )


@click.command(name="grapher-db", short_help="Step 2: Upload data to database.")
@click.pass_context
def click_uk_grapherdb(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=update_db,
        server=ctx.obj["server"],
        domain="UK Nations",
        step="grapher-db",
        text_success="UK nation data updated in database.",
        hide_success=True,
    )


click_uk_nations.add_command(click_uk_get)
click_uk_nations.add_command(click_uk_grapherdb)
