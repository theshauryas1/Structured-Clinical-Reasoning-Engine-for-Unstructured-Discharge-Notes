import math
import numpy as np
import scipy.io.wavfile as wavfile
import os

def create_soundtrack(output_path="soundtrack.wav", duration=52.0, sample_rate=48000):
    num_samples = int(duration * sample_rate)
    left = np.zeros(num_samples, dtype=np.float32)
    right = np.zeros(num_samples, dtype=np.float32)

    bpm = 105.0
    beat_dur = 60.0 / bpm  # ~0.5714s
    num_beats = int(duration / beat_dur)

    # 1. Heartbeat Monitor Sub-Bass Pulse (D2: 73.42Hz, F2: 87.31Hz, Bb1: 58.27Hz, C2: 65.41Hz)
    bass_freqs = [73.42, 87.31, 58.27, 65.41]
    for b in range(num_beats):
        beat_start = b * beat_dur
        beat_idx = int(beat_start * sample_rate)
        sub_len = int(beat_dur * 0.82 * sample_rate)
        if beat_idx + sub_len > num_samples:
            sub_len = num_samples - beat_idx
        if sub_len <= 0:
            break
        
        freq = bass_freqs[(b // 4) % len(bass_freqs)]
        bt = np.linspace(0, sub_len / sample_rate, sub_len, endpoint=False)
        # Dual-pulse heartbeat envelope (lub-dub)
        env1 = np.exp(-bt * 6.5) * 0.24
        dub_delay = int(0.12 * sample_rate)
        env2 = np.zeros_like(bt)
        if len(bt) > dub_delay:
            env2[dub_delay:] = np.exp(-(bt[dub_delay:] - 0.12) * 7.5) * 0.18
        envelope = env1 + env2
        
        bass_wave = (np.sin(2 * np.pi * freq * bt) + 0.25 * np.sin(2 * np.pi * freq * 2 * bt)) * envelope
        left[beat_idx:beat_idx + sub_len] += bass_wave
        right[beat_idx:beat_idx + sub_len] += bass_wave

    # 2. Ambient Clinical Chords / Pads (D minor, F major, Bb major, C major)
    d_minor = [146.83, 174.61, 220.00, 293.66] # D3, F3, A3, D4
    f_major = [174.61, 220.00, 261.63, 349.23] # F3, A3, C4, F4
    bb_maj  = [116.54, 146.83, 174.61, 233.08] # Bb2, D3, F3, Bb3
    c_major = [130.81, 164.81, 196.00, 261.63] # C3, E3, G3, C4
    chords = [d_minor, f_major, bb_maj, c_major]

    bar_dur = beat_dur * 4 # ~2.28s per bar
    num_bars = int(duration / bar_dur) + 1
    for bar in range(num_bars):
        bar_start = bar * bar_dur
        bar_idx = int(bar_start * sample_rate)
        bar_len = int(bar_dur * sample_rate)
        if bar_idx >= num_samples:
            break
        if bar_idx + bar_len > num_samples:
            bar_len = num_samples - bar_idx
            
        cur_chord = chords[bar % len(chords)]
        ct = np.linspace(0, bar_len / sample_rate, bar_len, endpoint=False)
        env = (np.sin(np.pi * ct / (bar_len / sample_rate)) ** 1.3) * 0.10
        
        for i, f in enumerate(cur_chord):
            detune_l = np.sin(2 * np.pi * (f - 0.3) * ct)
            detune_r = np.sin(2 * np.pi * (f + 0.3) * ct)
            left[bar_idx:bar_idx + bar_len] += detune_l * env * (0.85 + 0.15 * (i % 2))
            right[bar_idx:bar_idx + bar_len] += detune_r * env * (0.85 + 0.15 * ((i + 1) % 2))

    # 3. Precision Interface Ticks & Medical Hi-Hats
    for h in range(num_beats * 2):
        h_start = h * (beat_dur / 2.0)
        h_idx = int(h_start * sample_rate)
        h_len = int(0.025 * sample_rate)
        if h_idx + h_len > num_samples:
            break
        ht = np.linspace(0, 0.025, h_len, endpoint=False)
        noise = (np.random.rand(h_len) * 2 - 1) * np.exp(-ht * 120.0) * 0.026
        left[h_idx:h_idx + h_len] += noise * 0.9
        right[h_idx:h_idx + h_len] += noise * 1.05

    # 4. Melodic High Arpeggios (Medical Precision Shimmer: D4, F4, A4, C5, D5)
    arp_notes = [293.66, 349.23, 440.00, 523.25, 587.33, 523.25, 440.00, 349.23]
    for a in range(num_beats * 4):
        a_start = a * (beat_dur / 4.0)
        if a_start < 4.0 or a_start > 48.0:
            continue
        a_idx = int(a_start * sample_rate)
        a_len = int(0.11 * sample_rate)
        if a_idx + a_len > num_samples:
            break
        at = np.linspace(0, 0.11, a_len, endpoint=False)
        freq = arp_notes[a % len(arp_notes)]
        arp = np.sin(2 * np.pi * freq * at) * np.exp(-at * 24.0) * 0.042
        pan = 0.5 + 0.38 * np.sin(a * 0.6)
        left[a_idx:a_idx + a_len] += arp * (1.0 - pan)
        right[a_idx:a_idx + a_len] += arp * pan

    # 5. Specialized Clinical Scene SFX Cues:
    def add_hit(timestamp, freq=160.0, decay=9.0, gain=0.20):
        idx = int(timestamp * sample_rate)
        dur = int(0.5 * sample_rate)
        if idx + dur < num_samples:
            ht = np.linspace(0, 0.5, dur, endpoint=False)
            wave = np.sin(2 * np.pi * freq * ht) * np.exp(-ht * decay) * gain
            left[idx:idx + dur] += wave
            right[idx:idx + dur] += wave

    def add_glide(timestamp, start_f=480.0, end_f=75.0, dur_s=0.6, gain=0.20):
        idx = int(timestamp * sample_rate)
        dur = int(dur_s * sample_rate)
        if idx + dur < num_samples:
            gt = np.linspace(0, dur_s, dur, endpoint=False)
            freq_curve = (start_f - end_f) * np.exp(-gt * 5.5) + end_f
            phase = 2 * np.pi * np.cumsum(freq_curve) / sample_rate
            glide = np.sin(phase) * np.exp(-gt * 3.2) * gain
            left[idx:idx + dur] += glide
            right[idx:idx + dur] += glide

    def add_telemetry_beep(timestamp, freq1=880.0, freq2=1174.66, gain=0.12):
        # Two-tone medical monitor warning alert
        idx = int(timestamp * sample_rate)
        dur = int(0.25 * sample_rate)
        half = dur // 2
        if idx + dur < num_samples:
            t1 = np.linspace(0, half / sample_rate, half, endpoint=False)
            t2 = np.linspace(0, (dur - half) / sample_rate, dur - half, endpoint=False)
            beep1 = np.sin(2 * np.pi * freq1 * t1) * np.exp(-t1 * 12.0) * gain
            beep2 = np.sin(2 * np.pi * freq2 * t2) * np.exp(-t2 * 12.0) * gain
            left[idx:idx + half] += beep1
            right[idx:idx + half] += beep1
            left[idx + half:idx + dur] += beep2
            right[idx + half:idx + dur] += beep2

    def add_chime(timestamp, freq=587.33, gain=0.15):
        idx = int(timestamp * sample_rate)
        dur = int(1.5 * sample_rate)
        if idx + dur < num_samples:
            ct = np.linspace(0, 1.5, dur, endpoint=False)
            chime = (np.sin(2 * np.pi * freq * ct) + 0.3 * np.sin(2 * np.pi * freq * 2 * ct)) * np.exp(-ct * 2.8) * gain
            left[idx:idx + dur] += chime * 0.95
            right[idx:idx + dur] += chime * 1.05

    # Cues synchronized to 7 scenes:
    add_hit(0.2, freq=110.0, gain=0.22)          # Scene 1: Initial clinical heartbeat impact
    add_hit(7.4, freq=140.0, gain=0.18)          # Scene 2: Multimodal Ingestion fan-out
    add_hit(14.8, freq=160.0, gain=0.18)         # Scene 3: LangGraph state activation
    add_glide(22.2, start_f=520.0, end_f=73.0)   # Scene 4: pgvector RAG query drop
    add_telemetry_beep(29.6, freq1=880.0, freq2=1174.66) # Scene 5: Contradiction alert beep!
    add_chime(34.8, freq=587.33)                 # Scene 5: Calibrated confidence resolve (D5)
    add_hit(37.0, freq=120.0, gain=0.24)         # Scene 6: 1,000-case benchmark impact
    add_chime(44.4, freq=523.25)                 # Scene 7: Production Cloud Run resolve (C5)

    # 6. Master Fade-out over final 2.0 seconds
    fade_len = int(2.0 * sample_rate)
    fade_curve = np.linspace(1.0, 0.0, fade_len)
    left[-fade_len:] *= fade_curve
    right[-fade_len:] *= fade_curve

    # Peak normalization to -1.0 dB
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)))
    if peak > 0:
        left = (left / peak) * 0.89
        right = (right / peak) * 0.89

    stereo = np.vstack((left, right)).T
    stereo_int16 = (stereo * 32767).astype(np.int16)

    wavfile.write(output_path, sample_rate, stereo_int16)
    print(f"Generated 52s clinical soundtrack: {output_path} ({duration}s, {sample_rate}Hz stereo)")

if __name__ == "__main__":
    out_dir = r"d:\hack\clinical-brag-output\work"
    wav_path = os.path.join(out_dir, "soundtrack.wav")
    create_soundtrack(wav_path, duration=52.0)
