import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.sweden import download_data, generate_dataset, update_db


@click.group(name="sweden", chain=True, cls=OrderedGroup)
@click.pass_context
def click_sweden(ctx):
    """COVID-19 Sweden data pipeline."""
    pass


@click.command(name="get", short_help="Step 1: Get file for Sweden dataset.")
@click.pass_context
def click_sweden_get(ctx):
    """Download source file for Sweden dataset."""
    feedback_log(
        func=download_data,
        server=ctx.obj["server"],
        domain="Sweden",
        step="get",
        hide_success=True,
        text_success="Sweden file downloaded.",
    )


@click.command(name="generate", short_help="Step 2: Generate Sweden dataset.")
@click.pass_context
def click_sweden_generate(ctx):
    """Generate our COVID-19 Sweden dataset."""
    feedback_log(
        func=generate_dataset,
        server=ctx.obj["server"],
        domain="Sweden",
        step="generate",
        text_success="Sweden files generated.",
    )


@click.command(name="grapher-db", short_help="Step 3: Upload data to database.")
@click.pass_context
def click_sweden_grapherdb(ctx):
    """Download and generate our COVID-19 Decoupling dataset."""
    feedback_log(
        func=update_db,
        server=ctx.obj["server"],
        domain="Sweden",
        step="grapher-db",
        text_success="Sweden data updated in database.",
        hide_success=True,
    )


click_sweden.add_command(click_sweden_get)
click_sweden.add_command(click_sweden_generate)
click_sweden.add_command(click_sweden_grapherdb)
