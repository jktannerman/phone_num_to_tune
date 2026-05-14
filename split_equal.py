"""Split an audio file into 10 equal-duration chunks."""

import argparse
from pathlib import Path
from pydub import AudioSegment


def split_equal(input_path: Path, output_dir: Path, n: int = 10) -> None:
    """Split an audio file into n equal-duration chunks.

    Args:
        input_path: Path to the source audio file.
        output_dir: Directory where the output files will be written.
        n: Number of equal chunks to produce.
    """
    print(f"Loading: {input_path}")
    audio = AudioSegment.from_file(input_path)
    print(f"Duration: {len(audio) / 1000:.2f}s  |  Channels: {audio.channels}  |  {audio.frame_rate} Hz")

    chunk_ms = len(audio) // n
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = input_path.suffix

    for i in range(n):
        start = i * chunk_ms
        end = (i + 1) * chunk_ms if i < n - 1 else len(audio)
        chunk = audio[start:end]
        out_path = output_dir / f"{i}{suffix}"
        chunk.export(out_path, format="ipod")
        print(f"  Saved {out_path.name}  ({start}ms - {end}ms)")

    print(f"\nDone. {n} files written to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split an audio file into 10 equal-duration chunks.")
    parser.add_argument("input", type=Path, help="Path to the source audio file.")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=None,
        help="Directory for output files (default: 'chunks' folder next to the input file).",
    )
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir is not None else args.input.parent / "chunks"
    split_equal(args.input, output_dir)
