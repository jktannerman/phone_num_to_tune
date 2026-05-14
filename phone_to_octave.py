#!/usr/bin/env python3
"""Play musical notes corresponding to phone number digits via winsound or pitched speech."""

import argparse
import sys
import time
import winsound
from pathlib import Path

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

DIGIT_WORDS: dict[str, str] = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}

DIGIT_NOTES: dict[str, str] = {
    "0": "B3", "1": "C4", "2": "D4", "3": "E4", "4": "F4",
    "5": "G4", "6": "A4", "7": "B4", "8": "C5", "9": "D5",
}

_AUDIO_NUMBERS_DIR = Path(__file__).parent / "audio_numbers" / "25th_chunks"
_SPEECH_CACHE_DIR = Path(__file__).parent / "speech_cache"

# Short silent gap between consecutive notes so repeated digits stay distinct
_GAP_S = 0.05


def _cache_path(digit: str) -> Path:
    """Return the WAV path for a digit's pitch-shifted audio."""
    freq = DIGIT_FREQUENCIES[digit]
    note = DIGIT_NOTES[digit]
    return _SPEECH_CACHE_DIR / f"{digit}_{note}_{freq:.2f}hz.wav"


def play_phone_number(phone_number: str, duration_ms: int, pause_ms: int) -> None:
    """Play a sequence of beep tones for each digit in a phone number string.

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


def build_speech_cache() -> dict[str, tuple[object, int]]:
    """Load or generate pitch-shifted spoken audio for all ten digits.

    Cached WAV files are stored in ``speech_cache/`` next to this script,
    named ``{digit}_{note}_{freq:.2f}hz.wav`` (e.g. ``1_C4_261.63hz.wav``).
    A file is only (re)generated when it is absent; existing files are loaded
    directly, so subsequent runs are fast.

    Each digit word is synthesized via pyttsx3, its fundamental frequency is
    estimated with librosa.yin, and the clip is pitch-shifted to the target
    musical frequency with a phase-vocoder.

    Returns:
        A dict mapping each digit character to a ``(audio_array, sample_rate)``
        tuple ready for playback.

    Raises:
        SystemExit: If the required speech packages are not installed.
    """
    try:
        import librosa
        import numpy as np
        import soundfile as sf
    except ImportError as exc:
        sys.exit(
            "Speech mode requires additional packages. Install with:\n"
            "  py -3.13 -m pip install librosa sounddevice soundfile\n"
            f"\nMissing: {exc}"
        )

    missing = [d for d in DIGIT_WORDS if not _cache_path(d).exists()]
    if missing:
        print(f"Generating {len(missing)} new clip(s):")
        _SPEECH_CACHE_DIR.mkdir(exist_ok=True)

        for i, digit in enumerate(missing, 1):
            word = DIGIT_WORDS[digit]
            note = DIGIT_NOTES[digit]
            target_hz = DIGIT_FREQUENCIES[digit]
            print(f"  [{i}/{len(missing)}] {word!r:>8}  ({note}, {target_hz:.2f} Hz)...", end=" ", flush=True)

            src = next(_AUDIO_NUMBERS_DIR.glob(f"{digit}.*"))
            y, sr = librosa.load(str(src), sr=None, mono=True)
            y, _ = librosa.effects.trim(y, top_db=25)

            # pyin is the probabilistic variant of yin; it returns per-frame
            # voiced/unvoiced flags, which avoids the octave errors that plain
            # yin produces when it locks onto a sub-harmonic.
            f0, voiced_flag, _ = librosa.pyin(y, sr=sr, fmin=70.0, fmax=400.0)
            voiced = f0[voiced_flag]
            source_hz: float = float(np.median(voiced)) if len(voiced) > 0 else 150.0

            n_steps: float = 12.0 * np.log2(target_hz / source_hz) - 24.0
            y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

            sf.write(str(_cache_path(digit)), y_shifted, sr)
            print("done.")

    audio_cache: dict[str, tuple[object, int]] = {}
    for digit in DIGIT_WORDS:
        y, sr = librosa.load(str(_cache_path(digit)), sr=None, mono=True)
        audio_cache[digit] = (y, sr)

    return audio_cache


def _load_audio_sources() -> dict[str, tuple[object, int]]:
    """Load the raw source files from ``audio_numbers/`` for all ten digits.

    Returns:
        A dict mapping each digit character to a ``(audio_array, sample_rate)``
        tuple ready for playback.

    Raises:
        SystemExit: If required packages are not installed or a source file is
            missing.
    """
    try:
        import librosa
    except ImportError as exc:
        sys.exit(
            "Raw mode requires additional packages. Install with:\n"
            "  py -3.13 -m pip install librosa sounddevice\n"
            f"\nMissing: {exc}"
        )

    sources: dict[str, tuple[object, int]] = {}
    for digit in DIGIT_WORDS:
        matches = list(_AUDIO_NUMBERS_DIR.glob(f"{digit}.*"))
        if not matches:
            sys.exit(f"Source file for digit '{digit}' not found in {_AUDIO_NUMBERS_DIR}")
        y, sr = librosa.load(str(matches[0]), sr=None, mono=True)
        sources[digit] = (y, sr)
    return sources


def _play_audio_sequence(
    phone_number: str,
    pause_ms: int,
    audio: dict[str, tuple[object, int]],
) -> None:
    """Play a sequence of audio clips for each digit in a phone number string.

    Args:
        phone_number: The string to play. Digits are looked up in ``audio``,
            spaces cause a pause, and other characters are silently ignored.
        pause_ms: Duration of silence inserted for each space character in
            milliseconds.
        audio: Dict mapping digit characters to ``(audio_array, sample_rate)``
            tuples.
    """
    try:
        import sounddevice as sd
    except ImportError as exc:
        sys.exit(
            "This mode requires sounddevice. Install with:\n"
            "  py -3.13 -m pip install sounddevice\n"
            f"\nMissing: {exc}"
        )

    for char in phone_number:
        if char == " ":
            time.sleep(pause_ms / 1000.0)
        elif char in audio:
            y, sr = audio[char]
            sd.play(y, sr)
            sd.wait()
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
            '  python phone_to_octave.py "1 800 555 0199" --duration 250 --pause 600\n'
            '  python phone_to_octave.py "555 1234" --mode speech\n'
            '  python phone_to_octave.py "555 1234" --mode raw'
        ),
    )
    parser.add_argument("phone_number", type=str, help="Phone number string to play")
    parser.add_argument(
        "--duration",
        type=int,
        default=500,
        metavar="MS",
        help="Note duration in milliseconds for beep mode (default: 500)",
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
    parser.add_argument(
        "--mode",
        choices=["beep", "speech", "raw"],
        default="beep",
        help=(
            "Playback mode: 'beep' (default) plays sine tones via winsound; "
            "'speech' speaks each digit at its musical pitch using pitch-shifting; "
            "'raw' plays the source audio files unmodified "
            "(requires librosa, sounddevice)"
        ),
    )

    args = parser.parse_args()
    pause_ms = args.pause if args.pause is not None else args.duration

    if args.duration <= 0:
        parser.error("--duration must be a positive integer")
    if pause_ms <= 0:
        parser.error("--pause must be a positive integer")

    if args.mode == "speech":
        _play_audio_sequence(args.phone_number, pause_ms, build_speech_cache())
    elif args.mode == "raw":
        _play_audio_sequence(args.phone_number, pause_ms, _load_audio_sources())
    else:
        play_phone_number(args.phone_number, args.duration, pause_ms)


if __name__ == "__main__":
    main()
