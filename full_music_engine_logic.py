import random

# ==========================================
# 🎹 BASE NOTE DATA
# ==========================================

notes = {
    "N1": "A0", "N2": "A#0 / Bb0", "N3": "B0", "N4": "C1", "N5": "C#1 / Db1",
    "N6": "D1", "N7": "D#1 / Eb1", "N8": "E1", "N9": "F1", "N10": "F#1 / Gb1",
    "N11": "G1", "N12": "G#1 / Ab1", "N13": "A1", "N14": "A#1 / Bb1", "N15": "B1",
    "N16": "C2", "N17": "C#2 / Db2", "N18": "D2", "N19": "D#2 / Eb2", "N20": "E2",
    "N21": "F2", "N22": "F#2 / Gb2", "N23": "G2", "N24": "G#2 / Ab2", "N25": "A2",
    "N26": "A#2 / Bb2", "N27": "B2", "N28": "C3", "N29": "C#3 / Db3", "N30": "D3",
    "N31": "D#3 / Eb3", "N32": "E3", "N33": "F3", "N34": "F#3 / Gb3", "N35": "G3",
    "N36": "G#3 / Ab3", "N37": "A3", "N38": "A#3 / Bb3", "N39": "B3",
    "N40": "C4", "N41": "C#4 / Db4", "N42": "D4", "N43": "D#4 / Eb4", "N44": "E4",
    "N45": "F4", "N46": "F#4 / Gb4", "N47": "G4", "N48": "G#4 / Ab4", "N49": "A4",
    "N50": "A#4 / Bb4", "N51": "B4", "N52": "C5", "N53": "C#5 / Db5", "N54": "D5",
    "N55": "D#5 / Eb5", "N56": "E5", "N57": "F5", "N58": "F#5 / Gb5", "N59": "G5",
    "N60": "G#5 / Ab5", "N61": "A5", "N62": "A#5 / Bb5", "N63": "B5", "N64": "C6",
    "N65": "C#6 / Db6", "N66": "D6", "N67": "D#6 / Eb6", "N68": "E6", "N69": "F6",
    "N70": "F#6 / Gb6", "N71": "G6", "N72": "G#6 / Ab6", "N73": "A6",
    "N74": "A#6 / Bb6", "N75": "B6", "N76": "C7", "N77": "C#7 / Db7", "N78": "D7",
    "N79": "D#7 / Eb7", "N80": "E7", "N81": "F7", "N82": "F#7 / Gb7",
    "N83": "G7", "N84": "G#7 / Ab7", "N85": "A7", "N86": "A#7 / Bb7",
    "N87": "B7", "N88": "C8"
}

note_values = {
    "whole": 1.0,
    "half": 0.5,
    "quarter": 0.25,
    "eighth": 0.125,
    "sixteenth": 0.0625
}

bass_clef  = {n: {"note": v, "clef": "Bass"} for n, v in notes.items()}
treble_clef = {n: {"note": v, "clef": "Treble"} for n, v in notes.items()}


# ==========================================
# 🎼 SEQUENCER
# ==========================================

def get_note_length(name, dotted=False):
    val = note_values[name]
    return val * 1.5 if dotted else val


def create_sequence(data, clef="treble", time_signature=(4,4)):
    clef_dict = bass_clef if clef.lower()=="bass" else treble_clef
    beats_pm = time_signature[0]
    beat_unit = time_signature[1]
    base_beat_value = 1.0 / (beat_unit/4.0)
    sequence, measure, beat_pos, total = [],1,1.0,0.0

    for entry in data:
        kind = entry[0]
        if kind=="barline": continue
        if kind=="rest":
            length, dotted = entry[1], entry[2]
            beats=get_note_length(length,dotted)/base_beat_value
            notes_set=["Rest"]
        else:
            ids = entry[1] if kind=="chord" else [entry[1]]
            length,dotted=entry[2],entry[3]
            beats=get_note_length(length,dotted)/base_beat_value
            notes_set=[clef_dict[n]["note"] for n in ids]
        sequence.append({
            "index":f"{measure}.{round(beat_pos,3)}",
            "measure":measure,
            "beat_start":round(beat_pos,3),
            "type":kind,
            "notes":notes_set,
            "clef":clef.capitalize(),
            "duration":length+(" (dotted)" if dotted else ""),
            "beats":round(beats,3)
        })
        beat_pos+=beats; total+=beats
        if total>=beats_pm-1e-6:  # barline
            sequence.append({"type":"barline","measure":measure,"notes":["|"]})
            measure+=1; beat_pos,total=1.0,0.0
    return sequence


# ==========================================
# 🎲 RANDOM NOTE GENERATOR
# ==========================================

def get_random_note_ids(clef):
    rng=list(range(1,39)) if clef=="bass" else list(range(40,89))
    if random.random()<0.2:
        return [f"N{n}" for n in random.sample(rng, random.choice([2,3]))]
    return f"N{random.choice(rng)}"

def get_note_beats(length,dotted,denom):
    base={"whole":1.0,"half":0.5,"quarter":0.25,"eighth":0.125,"sixteenth":0.0625}[length]
    return (base*(1.5 if dotted else 1))/(1/(4/denom))

def generate_random_measures(clef="treble",measures=5,time_signature=(4,4)):
    num,den=time_signature; beats_pm=num*(4/den)
    vals=["whole","half","quarter","eighth","sixteenth"]
    events,m,bpos,used=[],1,1.0,0.0
    while m<=measures:
        remain=beats_pm-used; l=random.choice(vals); dot=random.random()<0.15
        b=get_note_beats(l,dot,den); b=min(b,remain)
        typ=random.choices(["note","rest","chord"],[0.6,0.25,0.15])[0]
        if typ=="rest": ev=("rest",l,dot)
        elif typ=="chord": ids=get_random_note_ids(clef); ev=("chord",ids,l,dot)
        else: ev=("note",get_random_note_ids(clef),l,dot)
        events.append(ev); used+=b
        if used>=beats_pm-1e-6:
            m+=1;bpos,used=1.0,0.0
    return events

def generate_two_clef_piece(measures=5,time_signature=(4,4)):
    return {
        "treble":generate_random_measures("treble",measures,time_signature),
        "bass":generate_random_measures("bass",measures,time_signature)
    }


# ==========================================
# 🎵 MUSIC THEORY ENGINE
# ==========================================

PITCHES=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
SCALE_PATTERNS={"major":[0,2,4,5,7,9,11],"minor":[0,2,3,5,7,8,10]}

def parse_key(k):
    parts=k.split(); root=parts[0].capitalize(); mode=parts[1].lower() if len(parts)>1 else "major"
    return root,mode

def build_scale(root,mode):
    idx=PITCHES.index(root)
    return [PITCHES[(idx+i)%12] for i in SCALE_PATTERNS[mode]]

def roman_to_chord(rn,scale):
    mapR={"I":0,"ii":1,"iii":2,"IV":3,"V":4,"vi":5,"vii":6,
          "i":0,"ii°":1,"III":2,"iv":3,"V":4,"VI":5,"vii°":6}
    i=mapR.get(rn,0)
    return [scale[i%7], scale[(i+2)%7], scale[(i+4)%7]]

def semitone_distance(a,b):
    i1,i2=PITCHES.index(a),PITCHES.index(b)
    return min(abs(i2-i1),12-abs(i2-i1))

def melodic_next(last,scale):
    if not last:return random.choice(scale)
    pitch=last[:-1] if last[-1].isdigit() else last
    steps=[n for n in scale if semitone_distance(pitch,n)<=2]
    leaps=[n for n in scale if semitone_distance(pitch,n)>2]
    return random.choice(steps) if random.random()<0.75 and steps else random.choice(leaps or scale)


# ==========================================
# 🎻 CLASSICAL PERIOD COMPOSER
# ==========================================

def generate_classical_period(key_string="C major",measures=8,time_signature=(4,4)):
    """Creates an 8‑measure Classical period (antecedent + consequent)."""
    root,mode=parse_key(key_string)
    num,den=time_signature; beats_pm=num*(4/den)
    scale=build_scale(root,mode)
    major_pats=[["I","IV","V","I"],["I","ii","V","I"],["I","vi","IV","V","I"]]
    minor_pats=[["i","iv","V","i"],["i","ii°","V","i"],["i","VI","ii°","V","i"]]
    patterns=major_pats if mode=="major" else minor_pats

    treble,bass=[],[]
    last_treble=None
    last_bass=None

    def cadence_half(sc): return [roman_to_chord("I",sc), roman_to_chord("V",sc)]
    def cadence_full(sc): return [roman_to_chord("V",sc), roman_to_chord("I",sc)]

    # -------- Antecedent -------------
    ante_prog=random.choice(patterns)
    for m in range(1,measures//2+1):
        chords=cadence_half(scale) if m==measures//2 else [roman_to_chord(random.choice(ante_prog),scale)]
        for ch in chords:
            play_chord=random.random()<0.7; octv=random.choice([2,3])
            if play_chord:
                notes_b=[ch[0]+str(octv), ch[2]+str(octv)]
                if random.random()<0.3: notes_b.append(ch[1]+str(octv))
                typ="chord"
            else:
                typ="note"; notes_b=[ch[0]+str(octv)]
            bass.append({"measure":m,"beat_start":1.0,"type":typ,"notes":notes_b,
                         "duration":"half","beats":2.0,"key":f"{root} {mode}"})
            used,beat=0.0,1.0
            while used<beats_pm:
                nlen=random.choice(["quarter","eighth"]); dot=random.random()<0.1
                nbeats=get_note_beats(nlen,dot,den)
                if used+nbeats>beats_pm: break
                nextp=melodic_next(last_treble,scale)
                if last_treble and semitone_distance(nextp,last_treble[:-1])>7:
                    nextp=random.choice(scale)
                note_full=nextp+str(random.choice([4,5])); last_treble=note_full
                treble.append({"measure":m,"beat_start":round(beat,3),"type":"note",
                               "notes":[note_full],"duration":nlen+(" (dotted)" if dot else ""),
                               "beats":round(nbeats,3),"key":f"{root} {mode}"})
                beat+=nbeats; used+=nbeats

    # -------- Consequent -------------
    cons_prog=random.choice(patterns)
    var_trans=random.choice([-2,0,2,4])
    for m in range(measures//2+1,measures+1):
        chords=cadence_full(scale) if m==measures else [roman_to_chord(random.choice(cons_prog),scale)]
        for ch in chords:
            play_chord=random.random()<0.8; octv=random.choice([2,3])
            if play_chord:
                notes_b=[ch[0]+str(octv),ch[2]+str(octv)]
                if random.random()<0.4: notes_b.append(ch[1]+str(octv))
                typ="chord"
            else:
                typ="note"; notes_b=[ch[0]+str(octv)]
            bass.append({"measure":m,"beat_start":1.0,"type":typ,"notes":notes_b,
                         "duration":"half","beats":2.0,"key":f"{root} {mode}"})
            used,beat=0.0,1.0
            while used<beats_pm:
                nlen=random.choice(["quarter","eighth"]); dot=random.random()<0.1
                nbeats=get_note_beats(nlen,dot,den)
                if used+nbeats>beats_pm: break
                nextp=melodic_next(last_treble,scale)
                if random.random()<0.5:   # motivic variation
                    idx=PITCHES.index(nextp); nextp=PITCHES[(idx+var_trans)%12]
                note_full=nextp+str(random.choice([4,5])); last_treble=note_full
                treble.append({"measure":m,"beat_start":round(beat,3),"type":"note",
                               "notes":[note_full],"duration":nlen+(" (dotted)" if dot else ""),
                               "beats":round(nbeats,3),"key":f"{root} {mode}"})
                beat+=nbeats; used+=nbeats
    return {"treble":treble,"bass":bass}


# ==========================================
# 🧭 DEMO / MAIN EXECUTION
# ==========================================

if __name__=="__main__":
    print("🎹  Classical Composition Engine")
    mode_choice=input("Enter 'classical' for Classical period piece or 'random' for random sketch: ").strip().lower() or "classical"

    if mode_choice.startswith("r"):
        rand=generate_two_clef_piece(measures=5)
        print("\n🎼 Treble (random)")
        for e in rand["treble"]: print(e)
        print("\n🎵 Bass (random)")
        for e in rand["bass"]: print(e)

    else:
        key_in=input("Enter key (e.g. 'C major', 'A minor'): ").strip() or "C major"
        comp=generate_classical_period(key_in,measures=8)
        print("\n🎼 TREBLE\n")
        for n in comp["treble"]:
            print(f"M{n['measure']:>2} | Beat {n['beat_start']:<4} | {n['notes'][0]:<6} | "
                  f"{n['duration']:<13} | {n['beats']}b | {n['key']}")
        print("\n🎵 BASS\n")
        for n in comp["bass"]:
            bassnotes=", ".join(n['notes'])
            print(f"M{n['measure']:>2} | Beat {n['beat_start']:<4} | {bassnotes:<10} | "
                  f"{n['duration']:<13} | {n['beats']}b | {n['key']}")
