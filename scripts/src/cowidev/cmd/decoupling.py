import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.decoupling import main, update_db


@click.group(name="decoupling", chain=True, cls=OrderedGroup)
@click.pass_context
def click_decoup(ctx):
    """COVID-19 Decoupling data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate decoupling dataset.")
@click.pass_context
def click_decoup_generate(ctx):
    """Download and generate our COVID-19 Decoupling dataset."""
    feedback_log(
        func=main,
        server=ctx.obj["server"],
        domain="Decoupling",
        step="generate",
        text_success="Decoupling files generated.",
    )


@click.command(name="grapher-db", short_help="Step 2: Upload data to database.")
@click.pass_context
def click_decoup_grapherdb(ctx):
    """Download and generate our COVID-19 Decoupling dataset."""
    feedback_log(
        func=update_db,
        server=ctx.obj["server"],
        domain="Decoupling",
        step="grapher-db",
        hide_success=True,
        text_success="Decoupling data updated in database.",
    )


click_decoup.add_command(click_decoup_generate)
click_decoup.add_command(click_decoup_grapherdb)
