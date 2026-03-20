"""CLI entry point for bandmix-cli."""

import click

from bandmix_cli import __version__
from bandmix_cli.commands.auth import auth
from bandmix_cli.commands.calendar import calendar
from bandmix_cli.commands.feed import feed
from bandmix_cli.commands.hidden import hidden
from bandmix_cli.commands.matches import matches
from bandmix_cli.commands.member import member
from bandmix_cli.commands.messages import messages
from bandmix_cli.commands.music import music
from bandmix_cli.commands.musiclist import musiclist
from bandmix_cli.commands.photos import photos
from bandmix_cli.commands.profile import profile
from bandmix_cli.commands.search import search
from bandmix_cli.commands.seeking import seeking
from bandmix_cli.commands.settings import settings
from bandmix_cli.commands.videos import videos


@click.group()
@click.version_option(version=__version__)
def cli():
    """bandmix-cli — CLI tool for BandMix.com."""


cli.add_command(auth)
cli.add_command(calendar)
cli.add_command(feed)
cli.add_command(hidden)
cli.add_command(matches)
cli.add_command(member)
cli.add_command(messages)
cli.add_command(music)
cli.add_command(musiclist)
cli.add_command(photos)
cli.add_command(profile)
cli.add_command(search)
cli.add_command(seeking)
cli.add_command(settings)
cli.add_command(videos)


def main():
    cli()


if __name__ == "__main__":
    main()
