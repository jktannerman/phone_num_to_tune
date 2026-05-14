"""Split an audio file into chunks at user-specified timestamps."""

import argparse
import sys
from pathlib import Path
from pydub import AudioSegment


def parse_timestamps(timestamps_path: Path) -> list[tuple[float, float]]:
    """Parse a timestamps file into a list of (start, end) pairs in seconds.

    Each non-blank, non-comment line must contain exactly two whitespace-separated
    numbers representing the start and end of a chunk in seconds.

    Args:
        timestamps_path: Path to the timestamps file.

    Returns:
        List of (start_seconds, end_seconds) tuples.

    Raises:
        ValueError: If any line is malformed.
    """
    pairs: list[tuple[float, float]] = []
    with timestamps_path.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.split("#")[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(
                    f"{timestamps_path}:{lineno}: expected 'start end', got {raw.rstrip()!r}"
                )
            try:
                start, end = float(parts[0]), float(parts[1])
            except ValueError:
                raise ValueError(
                    f"{timestamps_path}:{lineno}: could not parse numbers from {raw.rstrip()!r}"
                )
            if end <= start:
                raise ValueError(
                    f"{timestamps_path}:{lineno}: end ({end}) must be greater than start ({start})"
                )
            pairs.append((start, end))
    return pairs


def generate_template(audio_path: Path, output_path: Path, n: int = 10) -> None:
    """Write a template timestamps file dividing the audio into n equal chunks.

    Args:
        audio_path: Path to the source audio file.
        output_path: Path where the template file will be written.
        n: Number of equal chunks to pre-fill.
    """
    audio = AudioSegment.from_file(audio_path)
    duration = len(audio) / 1000.0
    chunk = duration / n

    lines = [
        f"# Timestamps for {audio_path.name}",
        f"# Total duration: {duration:.3f}s",
        f"# Format: start_seconds end_seconds  (one chunk per line, # for comments)",
        "",
    ]
    for i in range(n):
        start = i * chunk
        end = (i + 1) * chunk if i < n - 1 else duration
        lines.append(f"{start:.3f} {end:.3f}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Template written to: {output_path}")


def split_manual(
    input_path: Path,
    timestamps_path: Path,
    output_dir: Path,
) -> None:
    """Split an audio file at timestamps specified in a file.

    Args:
        input_path: Path to the source audio file.
        timestamps_path: Path to the timestamps file.
        output_dir: Directory where the output files will be written.
    """
    pairs = parse_timestamps(timestamps_path)
    if not pairs:
        print("Error: timestamps file contains no chunks.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {input_path}")
    audio = AudioSegment.from_file(input_path)
    duration_s = len(audio) / 1000.0
    print(f"Duration: {duration_s:.2f}s  |  {len(pairs)} chunk(s) specified")

    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = input_path.suffix

    for i, (start_s, end_s) in enumerate(pairs):
        start_ms = int(start_s * 1000)
        end_ms = int(end_s * 1000)
        chunk = audio[start_ms:end_ms]
        out_path = output_dir / f"{i}{suffix}"
        chunk.export(out_path, format="ipod")
        print(f"  Saved {out_path.name}  ({start_s:.3f}s - {end_s:.3f}s,  {len(chunk)}ms)")

    print(f"\nDone. {len(pairs)} files written to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split an audio file at user-specified timestamps."
    )
    parser.add_argument("input", type=Path, help="Path to the source audio file.")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=None,
        help="Directory for output files (default: 'manual' folder next to the input file).",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-t", "--timestamps", type=Path, metavar="FILE",
        help="Timestamps file: one 'start end' pair per line in seconds.",
    )
    mode.add_argument(
        "--generate", type=Path, metavar="FILE",
        help="Generate a template timestamps file at FILE (does not split).",
    )

    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir is not None else args.input.parent / "manual"

    if args.generate:
        generate_template(args.input, args.generate)
    else:
        split_manual(args.input, args.timestamps, output_dir)
