"""A one-shot ASCII intro animation played after a successful `club init`."""

from __future__ import annotations

import time

import pyfiglet
from rich.console import Console


def play_intro_animation(console: Console, *, frame_delay: float = 0.05) -> None:
    """Reveal the CLUB wordmark row by row. Purely cosmetic; Ctrl+C skips it."""
    art = pyfiglet.figlet_format("CLUB", font="standard").splitlines()
    try:
        for row_count in range(1, len(art) + 1):
            console.clear()
            console.print("\n".join(art[:row_count]), style="bold cyan")
            time.sleep(frame_delay)
        console.print("\n[dim]Your club is ready.[/dim]\n")
    except KeyboardInterrupt:
        console.print("\n[dim]Your club is ready.[/dim]\n")
