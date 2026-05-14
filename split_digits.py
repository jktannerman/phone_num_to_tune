"""Split a recording of spoken digits 0-9 into ten individual audio files."""

import argparse
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


EXPECTED_SEGMENTS = 10

# Tuning parameters: adjust if the split produces the wrong number of segments.
MIN_SILENCE_MS = 300       # silence gap must be at least this long to count as a split point
SILENCE_THRESH_DB = -41    # dBFS below which audio is considered silence
PADDING_MS = 50            # extra ms kept on each side of a detected chunk


def find_chunks(
    audio: AudioSegment,
    silence_thresh: int,
    min_silence_ms: int,
    padding_ms: int,
) -> list[AudioSegment]:
    """Detect and return non-silent chunks from an AudioSegment.

    Args:
        audio: The source audio.
        silence_thresh: dBFS threshold below which audio is silence.
        min_silence_ms: Minimum silence duration (ms) that counts as a gap.
        padding_ms: Milliseconds of padding added to each side of a chunk.

    Returns:
        List of AudioSegment chunks, one per detected non-silent region.
    """
    ranges = detect_nonsilent(
        audio,
        min_silence_len=min_silence_ms,
        silence_thresh=silence_thresh,
    )
    chunks: list[AudioSegment] = []
    for start_ms, end_ms in ranges:
        padded_start = max(0, start_ms - padding_ms)
        padded_end = min(len(audio), end_ms + padding_ms)
        chunks.append(audio[padded_start:padded_end])
    return chunks


def split_digits(
    input_path: Path,
    output_dir: Path,
) -> None:
    """Split a recording of digits 0-9 into ten separate files.

    Args:
        input_path: Path to the source audio file.
        output_dir: Directory where the ten output files will be written.

    Raises:
        ValueError: If no parameter combination yields 10 or more chunks.
    """
    print(f"Loading: {input_path}")
    audio = AudioSegment.from_file(input_path)
    print(f"Duration: {len(audio) / 1000:.2f}s  |  Channels: {audio.channels}  |  {audio.frame_rate} Hz")

    # Search a fine grid around the defaults to find parameters that yield exactly 10 chunks.
    thresh_candidates = list(range(SILENCE_THRESH_DB, SILENCE_THRESH_DB - 4, -1))  # -38, ..., -44
    silence_candidates = [400, 500, 600, 700, 800, 900, 1000]

    chunks: list[AudioSegment] = []
    used_thresh = SILENCE_THRESH_DB
    used_min_silence = MIN_SILENCE_MS

    # best_above tracks the closest result strictly above EXPECTED_SEGMENTS found so far.
    best_above: tuple[int, list[AudioSegment]] | None = None  # (count, chunks)

    abort = False
    for thresh in thresh_candidates:
        for min_sil in silence_candidates:
            candidate = find_chunks(audio, thresh, min_sil, PADDING_MS)
            print(f"  thresh={thresh} dBFS  min_silence={min_sil}ms  -> {len(candidate)} chunk(s)")
            if len(candidate) == EXPECTED_SEGMENTS:
                chunks = candidate
                used_thresh = thresh
                used_min_silence = min_sil
                break
            if len(candidate) > EXPECTED_SEGMENTS:
                if best_above is None or len(candidate) < best_above[0]:
                    best_above = (len(candidate), candidate)
            else:
                # Too few chunks: larger min_sil (and more-negative thresh) can only make it worse.
                if min_sil == silence_candidates[0]:
                    abort = True
                break
        if chunks or abort:
            break

    if len(chunks) != EXPECTED_SEGMENTS:
        if best_above is not None:
            count, chunks = best_above
            print(
                f"\nWarning: could not find exactly {EXPECTED_SEGMENTS} chunks. "
                f"Falling back to {count} chunks (closest above {EXPECTED_SEGMENTS}) "
                "so you can inspect where the splits landed."
            )
        else:
            raise ValueError(
                f"Could not find any split with {EXPECTED_SEGMENTS} or more chunks. "
                "Try adjusting SILENCE_THRESH_DB or MIN_SILENCE_MS manually."
            )
    else:
        print(f"\nUsing thresh={used_thresh} dBFS, min_silence={used_min_silence}ms")

    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = input_path.suffix  # preserve original format (.m4a)

    for i, chunk in enumerate(chunks):
        out_path = output_dir / f"{i}{suffix}"
        chunk.export(out_path, format="ipod")  # 'ipod' is the ffmpeg encoder for .m4a/AAC
        print(f"  Saved {out_path.name}  ({len(chunk)}ms)")

    print(f"\nDone. {len(chunks)} files written to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split a spoken-digits recording into one file per digit.")
    parser.add_argument("input", type=Path, help="Path to the source audio file.")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=None,
        help="Directory for output files (default: 'digits' folder next to the input file).",
    )
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir is not None else args.input.parent / "digits"
    split_digits(args.input, output_dir)
