"""Interactive prompt helpers with a scriptable fallback for non-tty runs."""

from __future__ import annotations

import sys

import questionary
import typer
from prompt_toolkit.completion import WordCompleter


def is_interactive() -> bool:
    """True when both stdin and stdout are a real terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def text(message: str, *, default: str = "", suggestions: list[str] | None = None) -> str:
    """Free text with Tab-suggested completions when interactive; plain prompt otherwise."""
    if is_interactive():
        completer = WordCompleter(suggestions, ignore_case=True, sentence=True) if suggestions else None
        answer = questionary.text(message, default=default, completer=completer).ask()
        if answer is None:
            raise typer.Exit(code=1)
        return answer
    return typer.prompt(message, default=default)


def select_one(message: str, choices: list[tuple[str, str]], *, default: str) -> str:
    """Pick one value from (value, label) pairs. Arrow-key picker on a tty, numbered prompt otherwise."""
    if is_interactive():
        default_choice = next((label for value, label in choices if value == default), choices[0][1])
        answer = questionary.select(
            message, choices=[label for _, label in choices], default=default_choice,
        ).ask()
        if answer is None:
            raise typer.Exit(code=1)
        return next(value for value, label in choices if label == answer)

    default_index = next((i for i, (value, _) in enumerate(choices) if value == default), 0) + 1
    print(message)
    for index, (_, label) in enumerate(choices, start=1):
        print(f"  {index}. {label}")
    raw = typer.prompt("Choose a number", default=str(default_index)).strip()
    try:
        selected_index = int(raw) - 1
    except ValueError as error:
        raise typer.BadParameter("Enter a number from the list above.") from error
    if not 0 <= selected_index < len(choices):
        raise typer.BadParameter("Enter a number from the list above.")
    return choices[selected_index][0]


def checkbox(message: str, choices: list[str]) -> list[str]:
    """Pick zero or more values. Space/Tab-to-toggle picker on a tty, comma-separated prompt otherwise."""
    if is_interactive():
        answer = questionary.checkbox(message, choices=choices).ask()
        if answer is None:
            raise typer.Exit(code=1)
        return answer

    print(f"{message} (comma-separated, choose from: {', '.join(choices)})")
    raw = typer.prompt("Selection", default="").strip()
    if not raw:
        return []
    selected = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = [item for item in selected if item not in choices]
    if unknown:
        raise typer.BadParameter(f"Unknown option(s): {', '.join(unknown)}")
    return selected


def text_loop(message: str, *, done_label: str = "(leave blank to finish)") -> list[str]:
    """Repeatedly prompt for free text until the user enters a blank line."""
    values: list[str] = []
    while True:
        raw = typer.prompt(f"{message} {done_label}", default="").strip()
        if not raw:
            if not values:
                raise typer.BadParameter("At least one value is required.")
            return values
        values.append(raw)
