# phone_to_octave

Plays a phone number as a sequence of musical notes, with one note per digit spanning the range B3–D5.

## Digit-to-note mapping

| Digit | Note | Frequency |
|-------|------|-----------|
| 0     | B3   | 246.94 Hz |
| 1     | C4   | 261.63 Hz |
| 2     | D4   | 293.66 Hz |
| 3     | E4   | 329.63 Hz |
| 4     | F4   | 349.23 Hz |
| 5     | G4   | 392.00 Hz |
| 6     | A4   | 440.00 Hz |
| 7     | B4   | 493.88 Hz |
| 8     | C5   | 523.25 Hz |
| 9     | D5   | 587.33 Hz |

Spaces in the input cause a silence. Hyphens, parentheses, and other separators are ignored.

## Modes

### `beep` (default)

Uses the Windows `winsound` module to play a pure sine tone for each digit. No extra dependencies required.

### `raw`

Plays the source recordings from the selected `--source` folder directly, without any pitch-shifting. Useful for auditioning the source files or checking trim results. Requires `librosa` and `sounddevice`.

### `speech` *(needs work — use `raw` instead)*

> **Note:** The pitch-shifting pipeline does not yet produce satisfactory results. `--mode raw` is currently recommended for spoken-digit playback.

Speaks each digit aloud ("zero", "one", …) at its mapped musical pitch. The pipeline is:

1. Source recordings are loaded from a subfolder of `audio_numbers/`, one file per digit (`0.*` – `9.*`). Any format supported by librosa/soundfile is accepted (e.g. WAV, M4A, FLAC). The subfolder is selected with `--source` (default: `31st_chunks`).
2. `librosa.yin` estimates each recording's fundamental frequency.
3. `librosa.effects.pitch_shift` shifts the clip to the target note via a phase-vocoder.
4. The result is saved to `speech_cache/` as a WAV named after the digit, note, and frequency (e.g. `1_C4_261.63hz.wav`). On subsequent runs, existing files are loaded directly — only missing clips are regenerated.
5. Clips are played back with `sounddevice`.

## Requirements

Python 3.13 on Windows. The `beep` mode has no external dependencies.

For `--mode speech`, install the additional packages:

```
py -3.13 -m pip install librosa sounddevice soundfile
```

Or install everything from `requirements.txt`:

```
py -3.13 -m pip install -r requirements.txt
```

## Usage

```
python phone_to_octave.py <phone_number> [--mode {beep,speech}] [--duration MS] [--pause MS]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `phone_number` | — | The phone number string to play |
| `--source FOLDER` | `31st_chunks` | Subfolder of `audio_numbers/` to use for `speech` and `raw` modes |
| `--mode` | `beep` | Playback mode: `beep`, `speech`, or `raw` |
| `--duration MS` | `500` | Note duration in milliseconds (beep mode) |
| `--pause MS` | same as `--duration` | Silence duration for spaces in milliseconds |

## Examples

```
python phone_to_octave.py "555 1234"
python phone_to_octave.py "867-5309" --duration 400
python phone_to_octave.py "1 800 555 0199" --duration 250 --pause 600
python phone_to_octave.py "555 1234" --mode speech
```

## Audio preparation utilities

These scripts are standalone tools intended to be run manually to prepare the `audio_numbers/` source files used by `--mode speech`. They are not called by the main program.

### `split_digits.py`

Splits a single recording of the spoken digits 0–9 (in order) into ten separate files, one per digit, stripping silence between them. It searches a grid of silence-threshold and minimum-silence-gap values to find a combination that produces exactly 10 non-silent chunks. If no combination succeeds, it falls back to the closest result above 10 chunks and writes those files so the split points can be inspected manually.

```
python split_digits.py <input_file> [-o OUTPUT_DIR]
```

Output files are named `0.<ext>` through `9.<ext>` and written to `digits/` next to the input file by default.

### `split_equal.py`

Splits an audio file into 10 chunks of equal duration. Useful as a quick sanity check to see where the digit boundaries actually fall in the recording before running `split_digits.py`.

```
python split_equal.py <input_file> [-o OUTPUT_DIR]
```

Output files are named `0.<ext>` through `9.<ext>` and written to `chunks/` next to the input file by default.

### `split_manual.py`

Splits an audio file at exact timestamps supplied in a plain-text file. Each non-blank, non-comment line in the timestamps file contains a `start end` pair in seconds:

```
# timestamps.txt
0.000 1.450   # zero
1.600 2.800   # one
...
```

Use `--generate` to produce a pre-filled template (equal chunks) as a starting point, then adjust the values by hand:

```
python split_manual.py <input_file> --generate timestamps.txt
python split_manual.py <input_file> -t timestamps.txt [-o OUTPUT_DIR]
```

Output files are named `0.<ext>` through `N.<ext>` and written to `manual/` next to the input file by default.
