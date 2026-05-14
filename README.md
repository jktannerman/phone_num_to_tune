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

### `speech`

Speaks each digit aloud ("zero", "one", …) at its mapped musical pitch. The pipeline is:

1. Source recordings are loaded from `audio_numbers/0.wav` – `audio_numbers/9.wav`.
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
| `--mode` | `beep` | Playback mode: `beep` or `speech` |
| `--duration MS` | `500` | Note duration in milliseconds (beep mode) |
| `--pause MS` | same as `--duration` | Silence duration for spaces in milliseconds |

## Examples

```
python phone_to_octave.py "555 1234"
python phone_to_octave.py "867-5309" --duration 400
python phone_to_octave.py "1 800 555 0199" --duration 250 --pause 600
python phone_to_octave.py "555 1234" --mode speech
```
