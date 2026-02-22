"""
Sheet music renderer using music21 + MuseScore.

Converts output from the music engine (generate_classical_period,
generate_two_clef_piece) into rendered sheet music (PNG, PDF, or
interactive display).
"""

import os
import subprocess
import tempfile

from music21 import stream, note, chord, meter, key, clef, tempo, metadata, spanner, interval, layout

from full_music_engine_logic import (
    generate_classical_period,
    generate_two_clef_piece,
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


def _is_stepwise(n1, n2):
    """Check if two music21 Note objects are a step apart (interval of a 2nd or less)."""
    try:
        ivl = interval.Interval(noteStart=n1, noteEnd=n2)
        return abs(ivl.generic.value) <= 2
    except Exception:
        return False


def add_slurs_to_part(part, placement="above"):
    """Add musical phrasing slurs to a Part.

    Scans all notes across the part for runs of stepwise motion.
    Groups of 3+ consecutive stepwise notes get a slur.
    Leaves at least 1 unslurred note between consecutive slurs to
    prevent visual overlap.  Treble slurs above, bass slurs below.
    """
    all_notes = []
    for m in part.getElementsByClass(stream.Measure):
        for n in m.notesAndRests:
            if isinstance(n, note.Note):
                all_notes.append(n)

    if len(all_notes) < 3:
        return

    runs = []
    current_run = [all_notes[0]]
    skip_next = False
    for i in range(1, len(all_notes)):
        if skip_next:
            skip_next = False
            current_run = [all_notes[i]]
            continue
        if _is_stepwise(current_run[-1], all_notes[i]):
            current_run.append(all_notes[i])
        else:
            if len(current_run) >= 3:
                runs.append(current_run)
                skip_next = True
            current_run = [all_notes[i]]
    if len(current_run) >= 3:
        runs.append(current_run)

    for slur_id, run in enumerate(runs, start=1):
        s = spanner.Slur(run[0], run[-1])
        s.placement = placement
        s.idLocal = slur_id
        part.insert(0, s)


def to_score(data, title="Composition", key_str=None, time_sig=(4, 4)):
    """Convert engine output to a music21 Score.

    Works with output from both generate_classical_period() and
    generate_two_clef_piece(), since they share the same format.
    """
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title

    for clef_name in ("treble", "bass"):
        part = stream.Part()

        current_measure_num = None
        m = None
        first_measure = True

        for event in data[clef_name]:
            evt_type = event.get("type", "note")
            if evt_type == "barline":
                continue

            measure_num = event.get("measure", 1)

            if measure_num != current_measure_num:
                if m is not None:
                    m.makeRests(inPlace=True)
                    part.append(m)
                m = stream.Measure(number=measure_num)
                current_measure_num = measure_num

                if first_measure:
                    if clef_name == "treble":
                        m.insert(0, clef.TrebleClef())
                    else:
                        m.insert(0, clef.BassClef())
                    if key_str:
                        parts_k = key_str.split()
                        root_k = parts_k[0]
                        mode_k = parts_k[1] if len(parts_k) > 1 else "major"
                        m.insert(0, key.Key(root_k, mode_k))
                    m.insert(0, meter.TimeSignature(f"{time_sig[0]}/{time_sig[1]}"))
                    first_measure = False

            duration_str = event.get("duration", "quarter")
            ql = parse_duration(duration_str)
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
            m.makeRests(inPlace=True)
            part.append(m)

        score.append(part)

    # Add slurs: above for treble (part 0), below for bass (part 1)
    for i, part in enumerate(score.parts):
        placement = "above" if i == 0 else "below"
        add_slurs_to_part(part, placement)

    # Grand staff: brace + connected barlines for piano
    sg = layout.StaffGroup(list(score.parts), symbol='brace', barTogether=True)
    score.insert(0, sg)

    # Final safety net: fill any remaining gaps
    score.makeRests(fillGaps=True, inPlace=True)

    return score


MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"


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
    if fmt == "text":
        if filepath:
            score.write(fmt, fp=filepath)
            print(f"Saved to {filepath}")
        else:
            score.show(fmt)
        return

    if fmt == "musicxml" and not filepath:
        # Write temp MusicXML then open in MuseScore
        tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
        tmp.close()
        score.write("musicxml", fp=tmp.name)
        subprocess.Popen([MUSESCORE_PATH, tmp.name])
        print("Opened in MuseScore.")
        return

    # For png/pdf: write MusicXML, then call MuseScore to convert
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_xml = os.path.join(script_dir, "_temp_render.musicxml")
    score.write("musicxml", fp=tmp_xml)

    if not filepath:
        ext = "png" if "png" in fmt else "pdf"
        filepath = f"output.{ext}"

    filepath = os.path.abspath(filepath)
    subprocess.run(
        [MUSESCORE_PATH, "-o", filepath, tmp_xml],
        capture_output=True, text=True
    )
    os.unlink(tmp_xml)

    # MuseScore may add page suffixes (-1, -2) for multi-page output
    base, ext = os.path.splitext(filepath)
    page1 = f"{base}-1{ext}"
    if os.path.exists(filepath) or os.path.exists(page1):
        print(f"Saved to {filepath}")
    else:
        print("MuseScore rendering failed — no output files created.")


# ==========================================
# DEMO
# ==========================================

if __name__ == "__main__":
    print("Sheet Music Renderer")
    print("=" * 40)

    choice = input("Render 'classical' or 'random'? ").strip().lower() or "classical"

    if choice.startswith("r"):
        data = generate_two_clef_piece(measures=4)
        score = to_score(data, title="Random Sketch")
    else:
        key_in = input("Enter key (e.g. 'C major', 'A minor'): ").strip() or "C major"
        data = generate_classical_period(key_in, measures=8)
        score = to_score(data, title="Classical Period", key_str=key_in)

    fmt = input("Output format -- 'png', 'pdf', or 'show' (open in MuseScore)? ").strip().lower() or "show"

    if fmt == "png":
        render(score, fmt="musicxml.png", filepath="output.png")
    elif fmt == "pdf":
        render(score, fmt="musicxml.pdf", filepath="output.pdf")
    else:
        render(score, fmt="musicxml")
