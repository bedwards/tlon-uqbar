"""CLI entry point for bandmix-cli."""

import click

from bandmix_cli import __version__
from bandmix_cli.commands.auth import auth
from bandmix_cli.commands.search import search


@click.group()
@click.version_option(version=__version__)
def cli():
    """bandmix-cli — CLI tool for BandMix.com."""


cli.add_command(auth)
cli.add_command(search)


def main():
    cli()


if __name__ == "__main__":
    main()
