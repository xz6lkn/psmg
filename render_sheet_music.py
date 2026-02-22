"""
Sheet music renderer using music21 + MuseScore.

Converts output from the music engine (generate_classical_period,
generate_two_clef_piece) into rendered sheet music (PNG, PDF, or
interactive display).
"""

from music21 import stream, note, chord, meter, key, clef, tempo, metadata

from full_music_engine_logic import (
    generate_classical_period,
    generate_two_clef_piece,
    create_sequence,
)


# Duration string -> music21 quarterLength mapping
DURATION_TO_QUARTER_LENGTH = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
}


def parse_duration(duration_str):
    """Parse a duration string like 'quarter (dotted)' into quarterLength."""
    dotted = "(dotted)" in duration_str
    base = duration_str.replace(" (dotted)", "").strip()
    ql = DURATION_TO_QUARTER_LENGTH.get(base, 1.0)
    if dotted:
        ql *= 1.5
    return ql


def parse_note_name(name):
    """Convert note names like 'C#4 / Db4' to music21-friendly format.

    music21 accepts 'C#4' or 'D-4' (flat = minus sign).
    We take the first spelling (sharp form) when both are given.
    """
    if "/" in name:
        name = name.split("/")[0].strip()
    return name.replace("b", "-")


def classical_to_score(data, title="Classical Period", key_str="C major",
                       time_sig=(4, 4)):
    """Convert generate_classical_period() output to a music21 Score.

    Parameters
    ----------
    data : dict with "treble" and "bass" lists of note dicts
    title : str
    key_str : str, e.g. "C major" or "A minor"
    time_sig : tuple, e.g. (4, 4)

    Returns
    -------
    music21.stream.Score
    """
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title

    parts = key_str.split()
    root = parts[0]
    mode = parts[1] if len(parts) > 1 else "major"
    k = key.Key(root, mode)
    ts = meter.TimeSignature(f"{time_sig[0]}/{time_sig[1]}")

    for clef_name in ("treble", "bass"):
        part = stream.Part()
        if clef_name == "treble":
            part.insert(0, clef.TrebleClef())
        else:
            part.insert(0, clef.BassClef())
        part.insert(0, k)
        part.insert(0, ts)

        current_measure_num = None
        m = None

        for event in data[clef_name]:
            measure_num = event.get("measure", 1)

            if measure_num != current_measure_num:
                if m is not None:
                    part.append(m)
                m = stream.Measure(number=measure_num)
                current_measure_num = measure_num

            ql = event.get("beats", 1.0)
            evt_type = event.get("type", "note")
            notes_list = event.get("notes", [])

            if evt_type == "rest" or notes_list == ["Rest"]:
                r = note.Rest(quarterLength=ql)
                m.append(r)
            elif evt_type == "chord" and len(notes_list) > 1:
                pitches = [parse_note_name(n) for n in notes_list]
                c = chord.Chord(pitches, quarterLength=ql)
                m.append(c)
            elif evt_type == "note" or (evt_type == "chord" and len(notes_list) == 1):
                n = note.Note(parse_note_name(notes_list[0]), quarterLength=ql)
                m.append(n)

        if m is not None:
            part.append(m)

        score.append(part)

    return score


def random_to_score(data, title="Random Sketch", time_sig=(4, 4)):
    """Convert generate_two_clef_piece() output (after sequencing) to a Score.

    Parameters
    ----------
    data : dict with "treble" and "bass" lists of sequence dicts
           (output of create_sequence applied to generate_random_measures)
    title : str
    time_sig : tuple

    Returns
    -------
    music21.stream.Score
    """
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title

    ts = meter.TimeSignature(f"{time_sig[0]}/{time_sig[1]}")

    for clef_name in ("treble", "bass"):
        part = stream.Part()
        if clef_name == "treble":
            part.insert(0, clef.TrebleClef())
        else:
            part.insert(0, clef.BassClef())
        part.insert(0, ts)

        current_measure_num = None
        m = None

        for event in data[clef_name]:
            evt_type = event.get("type", "note")
            if evt_type == "barline":
                continue

            measure_num = event.get("measure", 1)
            if measure_num != current_measure_num:
                if m is not None:
                    part.append(m)
                m = stream.Measure(number=measure_num)
                current_measure_num = measure_num

            ql = event.get("beats", 1.0)
            notes_list = event.get("notes", [])

            if evt_type == "rest" or notes_list == ["Rest"]:
                r = note.Rest(quarterLength=ql)
                m.append(r)
            elif evt_type == "chord" and len(notes_list) > 1:
                pitches = [parse_note_name(n) for n in notes_list]
                c = chord.Chord(pitches, quarterLength=ql)
                m.append(c)
            elif evt_type == "note" or (evt_type == "chord" and len(notes_list) == 1):
                n = note.Note(parse_note_name(notes_list[0]), quarterLength=ql)
                m.append(n)

        if m is not None:
            part.append(m)

        score.append(part)

    return score


def render(score, fmt="musicxml.png", filepath=None):
    """Render a music21 Score.

    Parameters
    ----------
    score : music21.stream.Score
    fmt : str
        Output format. Common options:
        - "musicxml.png" : PNG image via MuseScore
        - "musicxml.pdf" : PDF via MuseScore
        - "musicxml"     : open in MuseScore interactively
        - "text"         : plain text representation
    filepath : str or None
        If provided, write to this path instead of opening a viewer.
    """
    if filepath:
        score.write(fmt.replace("musicxml.", ""), fp=filepath)
        print(f"Saved to {filepath}")
    else:
        score.show(fmt)


# ==========================================
# DEMO
# ==========================================

if __name__ == "__main__":
    print("Sheet Music Renderer")
    print("=" * 40)

    choice = input("Render 'classical' or 'random'? ").strip().lower() or "classical"

    if choice.startswith("r"):
        raw = generate_two_clef_piece(measures=4)
        seq = {
            "treble": create_sequence(raw["treble"], clef="treble"),
            "bass": create_sequence(raw["bass"], clef="bass"),
        }
        score = random_to_score(seq, title="Random Sketch")
    else:
        key_in = input("Enter key (e.g. 'C major', 'A minor'): ").strip() or "C major"
        data = generate_classical_period(key_in, measures=8)
        score = classical_to_score(data, title="Classical Period", key_str=key_in)

    fmt = input("Output format — 'png', 'pdf', or 'show' (open in MuseScore)? ").strip().lower() or "show"

    if fmt == "png":
        render(score, fmt="musicxml.png", filepath="output.png")
    elif fmt == "pdf":
        render(score, fmt="musicxml.pdf", filepath="output.pdf")
    else:
        render(score, fmt="musicxml")
