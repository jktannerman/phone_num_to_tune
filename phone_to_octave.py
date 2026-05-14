#!/usr/bin/env python3
"""Play musical notes corresponding to phone number digits via winsound."""

import argparse
import time
import winsound

# Digit-to-frequency mapping (Hz)
# 0 = B3 (one step below middle C), 1-9 = C4 through D5
DIGIT_FREQUENCIES: dict[str, float] = {
    "0": 246.94,  # B3  — tone below C4
    "1": 261.63,  # C4  — middle C
    "2": 293.66,  # D4
    "3": 329.63,  # E4
    "4": 349.23,  # F4
    "5": 392.00,  # G4
    "6": 440.00,  # A4
    "7": 493.88,  # B4
    "8": 523.25,  # C5
    "9": 587.33,  # D5
}

# Short silent gap between consecutive notes so repeated digits stay distinct
_GAP_S = 0.05


def play_phone_number(phone_number: str, duration_ms: int, pause_ms: int) -> None:
    """Play a sequence of notes for each digit in a phone number string.

    Args:
        phone_number: The string to play. Digits map to notes, spaces cause a
            pause, and any other characters (``-``, ``(``, ``)``, etc.) are
            silently ignored.
        duration_ms: Duration of each note in milliseconds.
        pause_ms: Duration of silence inserted for each space character in
            milliseconds.
    """
    for char in phone_number:
        if char == " ":
            time.sleep(pause_ms / 1000.0)
        elif char in DIGIT_FREQUENCIES:
            freq = round(DIGIT_FREQUENCIES[char])
            winsound.Beep(freq, duration_ms)
            time.sleep(_GAP_S)
        else:
            time.sleep(pause_ms / 1000.0)


def main() -> None:
    """Parse command-line arguments and play the phone number."""
    parser = argparse.ArgumentParser(
        description="Play musical notes for each digit in a phone number.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Digit-to-note mapping:\n"
            "  0=B3  1=C4  2=D4  3=E4  4=F4  5=G4  6=A4  7=B4  8=C5  9=D5\n\n"
            "Examples:\n"
            '  python phone_to_octave.py "555 1234"\n'
            '  python phone_to_octave.py "867-5309" --duration 400\n'
            '  python phone_to_octave.py "1 800 555 0199" --duration 250 --pause 600'
        ),
    )
    parser.add_argument("phone_number", type=str, help="Phone number string to play")
    parser.add_argument(
        "--duration",
        type=int,
        default=500,
        metavar="MS",
        help="Note duration in milliseconds (default: 500)",
    )
    parser.add_argument(
        "--pause",
        type=int,
        default=None,
        metavar="MS",
        help=(
            "Silence duration for spaces in milliseconds "
            "(default: same as --duration)"
        ),
    )

    args = parser.parse_args()
    pause_ms = args.pause if args.pause is not None else args.duration

    if args.duration <= 0:
        parser.error("--duration must be a positive integer")
    if pause_ms <= 0:
        parser.error("--pause must be a positive integer")

    play_phone_number(args.phone_number, args.duration, pause_ms)


if __name__ == "__main__":
    main()
