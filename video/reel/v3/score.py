"""Original score for the lumic film v3 (40 s). Pure synthesis with numpy: no samples, no licensed audio.

The instruments and the mix chain are the v1 engine (video/reel/score.py); the composition is new:
F# minor (the work done by hand) resolving to A major (automated, kept working), 120 BPM, 2-second bars.
Hit points come from the picture: reel.html exports window.CUES and render.py passes them in as JSON.

Usage: python3 video/reel/v3/score.py out.wav [cues.json]
Needs: numpy, and ffmpeg on PATH (loudness measurement).
"""
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 40.0
N = int(SR * DUR)
OFF = 0.0                       # bar lines at 0, 2, 4, ... (120 BPM, 2-second bars)
rng = np.random.default_rng(2030)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tl(d):
    return np.arange(int(round(d * SR))) / SR


BUS = {k: np.zeros((2, N)) for k in ("pad", "arp", "drum", "sub", "bell", "fx")}


def place(bus, sig, t0, pan=0.0, gain=1.0):
    """Mix a mono (panned, equal power, centre = unity) or stereo signal into a bus at time t0."""
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
    sig = sig * gain
    i0 = int(round(t0 * SR))
    if i0 < 0:
        sig, i0 = sig[:, -i0:], 0
    i1 = min(N, i0 + sig.shape[1])
    if i1 > i0:
        BUS[bus][:, i0:i1] += sig[:, : i1 - i0]


def stft_filter(x, gain_fn, nfft=2048, hop=512):
    """Time-varying spectral filter. gain_fn(t_local_seconds, freqs) -> gain per bin."""
    mono = x.ndim == 1
    if mono:
        x = x[None, :]
    c, n = x.shape
    win = np.hanning(nfft + 1)[:-1]
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    out = np.zeros((c, n))
    norm = np.zeros(n)
    for s in range(-nfft + hop, n, hop):
        a, b = max(0, s), min(n, s + nfft)
        seg = np.zeros((c, nfft))
        seg[:, a - s : b - s] = x[:, a:b]
        g = gain_fn((s + nfft / 2) / SR, freqs)
        y = np.fft.irfft(np.fft.rfft(seg * win, axis=1) * g, n=nfft, axis=1) * win
        out[:, a:b] += y[:, a - s : b - s]
        norm[a:b] += win[a - s : b - s] ** 2
    out /= np.maximum(norm, 1e-8)
    return out[0] if mono else out


def lp(f, fc, order=4):
    return 1 / (1 + (f / fc) ** order)


def hp(f, fc, order=4):
    return 1 - lp(f, fc, order)


def curve(keys, log=False):
    ts = np.array([k[0] for k in keys], float)
    vs = np.array([k[1] for k in keys], float)
    if log:
        vs = np.log(vs)
    return lambda t: np.exp(np.interp(t, ts, vs)) if log else np.interp(t, ts, vs)


# ---------------------------------------------------------------- instruments
def pad_chord(notes, dur, fade_in=1.0, fade_out=1.0, bright=1.35):
    """One chord with equal-power fades, so consecutive chords cross-fade without a dip."""
    t = tl(dur)
    n = len(t)
    env = np.sin(np.pi / 2 * np.minimum(1, t / fade_in)) * np.sin(np.pi / 2 * np.clip((dur - t) / fade_out, 0, 1))
    out = np.zeros((2, n))
    for m in notes:
        f = midi(m)
        for weight, cents in ((1.0, 5), (0.55, 12)):
            ph = rng.uniform(0, 2 * np.pi)                 # shared by both channels: wide but mono-safe
            for ch, sign in ((0, -1), (1, 1)):
                ff = f * 2 ** (sign * cents / 1200)
                s = np.zeros(n)
                for k in range(1, 9):
                    if ff * k > 8000:
                        break
                    s += np.sin(2 * np.pi * ff * k * t + ph * k) / k ** bright
                out[ch] += s * weight
    root = midi(min(notes) - 12)
    out += np.sin(2 * np.pi * root * t) * 0.3
    return out * env


def pluck(f, dur=0.55, idx=2.2, ratio=2.0, decay=7.5, bright=16.0):
    t = tl(dur)
    I = idx * np.exp(-t * bright)
    s = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * ratio * t))
    return s * np.exp(-t * decay) * np.minimum(1, t / 0.003)


def bell(f, dur=2.6, idx=3.2, ratio=3.5, decay=2.0):
    t = tl(dur)
    I = idx * np.exp(-t * 2.6)
    s = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * ratio * t))
    s += 0.32 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 3.5)
    s += 0.18 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 6)
    return s * np.exp(-t * decay) * np.minimum(1, t / 0.002)


def rev_bell(f, dur=1.2):
    b = bell(f, dur, idx=2.6, decay=2.4)[::-1].copy()
    b[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    return b


def kick(dur=0.5, f0=110, f1=44, k=26, decay=7.5, click=0.22):
    t = tl(dur)
    f = f1 + (f0 - f1) * np.exp(-t * k)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * decay)
    c = rng.standard_normal(len(t)) * np.exp(-t * 420) * click
    return s + c


def hat(dur=0.09, decay=65, level=0.32):
    t = tl(dur)
    x = rng.standard_normal(len(t))
    x = np.diff(np.diff(np.concatenate([[0, 0], x])))
    return x * np.exp(-t * decay) * level


def clap(dur=0.4):
    t = tl(dur)
    x = np.diff(np.concatenate([[0], rng.standard_normal(len(t))]))
    env = np.zeros(len(t))
    for o in (0.0, 0.012, 0.024):
        i = int(o * SR)
        env[i:] += np.exp(-(t[i:] - o) * 130)
    env += 0.4 * np.exp(-t * 13) * (t > 0.028)
    x = stft_filter(x * env, lambda tc, f: hp(f, 700, 2) * lp(f, 6000, 2), nfft=512, hop=128)
    return x * 0.5


def subnote(f, dur, attack=0.012, decay=1.6):
    t = tl(dur)
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / attack) * np.exp(-t * decay) * np.clip((dur - t) / 0.06, 0, 1)
    return np.tanh(1.4 * s) * env


def tick(f=2600, dur=0.035, level=1.0):
    t = tl(dur)
    return (np.sin(2 * np.pi * f * t) * 0.6 + rng.standard_normal(len(t)) * 0.22) * np.exp(-t * 210) * level


def whoosh(dur, fc0=450, fc1=3600, pan0=-0.6, pan1=0.6):
    t = tl(dur)
    p = t / dur

    def g(tc, f):
        fc = fc0 * (fc1 / fc0) ** np.sin(np.pi * np.clip(tc / dur, 0, 1))
        return np.exp(-0.5 * (np.log(np.maximum(f, 1) / fc) / 0.6) ** 2)

    x = stft_filter(rng.standard_normal(len(t)), g, nfft=1024, hop=256) * np.sin(np.pi * p) ** 2
    a = (pan0 + (pan1 - pan0) * p + 1) * np.pi / 4
    return np.vstack([x * np.cos(a), x * np.sin(a)]) * np.sqrt(2)


def riser(dur, f_lo=260, f_hi=7500, tone=(170, 880)):
    t = tl(dur)
    p = t / dur
    x = stft_filter(rng.standard_normal((2, len(t))),
                    lambda tc, f: lp(f, f_lo * (f_hi / f_lo) ** np.clip(tc / dur, 0, 1)) * hp(f, 140),
                    nfft=1024, hop=256)
    sw = np.sin(2 * np.pi * np.cumsum(tone[0] * (tone[1] / tone[0]) ** p) / SR) * 0.22
    return (x + sw) * p ** 2.3


def impact(dur=1.4, f1=38, air=0.45):
    t = tl(dur)
    k = kick(dur, f0=100, f1=f1, k=13, decay=2.9, click=0.35)
    a = stft_filter(rng.standard_normal(len(t)), lambda tc, f: lp(f, 2600, 2) * hp(f, 220, 2), nfft=1024, hop=256)
    return k + a * np.exp(-t * 8) * air


def sweep(dur, f0, f1, trem=14.0):
    t = tl(dur)
    p = t / dur
    f = f0 * (f1 / f0) ** p
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.65 + 0.35 * np.sin(2 * np.pi * trem * t))
    return s * np.sin(np.pi * p) ** 1.4


def flick(dur=0.08):
    t = tl(dur)
    x = stft_filter(rng.standard_normal(len(t)), lambda tc, f: hp(f, 1800, 2) * lp(f, 7000, 2), nfft=256, hop=64)
    return x * np.exp(-t * 55)


def air(dur, level=1.0):
    t = tl(dur)
    x = stft_filter(rng.standard_normal((2, len(t))), lambda tc, f: hp(f, 3500, 2), nfft=1024, hop=256)
    return x * np.minimum(1, t / 0.02) * np.exp(-t * 4.5) * level



# ---------------------------------------------------------------- cues (exported by reel.html as window.CUES)
def load_cues(path):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text())
    # fallback: the timeline defaults in reel.html (scene starts on the 120 BPM grid)
    S = {"s2": 4.0, "s3": 7.0, "s4": 10.0, "s5": 14.0, "s6": 19.0, "s6b": 23.0, "s7": 26.5, "s8": 30.0, "s9": 35.0}
    return {"S": S, "tour": [4.5 + 0.375 * k for k in range(6)], "nodes": [10.5, 10.95, 11.45, 11.95, 12.75, 13.0],
            "sentBack": 12.2, "drawA": 10.5, "drawB": 13.0, "run": [15.0, 15.5, 16.0, 16.5, 17.5, 18.0],
            "dep": [15.0, 15.5, 16.0, 17.2, 17.5], "click": 17.0, "land": 20.0, "log": [24.5, 25.0, 25.5, 26.0],
            "fix": 25.75, "grid": [27.7 + 0.05 * k for k in range(12)]}


# ---------------------------------------------------------------- harmony: F# minor -> A major (20 bars of 2 s)
FSm11 = [54, 61, 64, 68, 71]
DM9 = [50, 57, 61, 64, 66]
BM9 = [47, 54, 57, 61, 62]
E69 = [52, 59, 61, 64, 66]
AM9 = [45, 52, 56, 59, 61]
FSm9 = [54, 57, 61, 64, 68]
EGs = [44, 52, 56, 59, 64]
BM11 = [47, 54, 57, 61, 64]
DM7s11 = [50, 57, 61, 64, 68]
ESUS = [52, 57, 59, 64, 66]
#        0      1    2    3    4    5    6    7    8     9    10   11   12    13   14   15    16      17    18   19
PROG = [FSm11, DM9, DM9, BM9, DM9, E69, BM9, AM9, FSm9, DM9, AM9, EGs, FSm9, DM9, AM9, BM11, DM7s11, ESUS, AM9, AM9]
ROOT = [42, 38, 38, 35, 38, 40, 35, 33, 42, 38, 33, 32, 42, 38, 33, 35, 38, 40, 33, 33]
BARS = [OFF + 2 * i for i in range(20)]
PENTA = [69, 71, 73, 76, 78, 81, 83, 85, 88, 90, 93, 95]          # A major pentatonic, A4 .. B6


def groove(t0, t1, claps=True, ghosts=True, kick_gain=0.9):
    """Kick on the beat, hats on the off-beat 8ths, optional 16th ghosts and back-beat claps (bars on even seconds)."""
    b = np.ceil((t0 - OFF) * 2) / 2 + OFF
    while b < t1 - 0.01:
        place("drum", kick(), b, gain=kick_gain)
        place("drum", hat(), b + 0.25, pan=0.25, gain=0.55)
        if ghosts:
            for g in (0.125, 0.375):
                if b + g < t1:
                    place("drum", hat(0.05, 90, 0.2), b + g, pan=-0.3, gain=0.45)
        beat = int(round((b - OFF) * 2)) % 4
        if claps and beat in (1, 3):
            place("drum", clap(), b, gain=0.55)
        b += 0.5


def arp(t0, t1, step, gain=1.0):
    pattern = [0, 2, 1, 3, 2, 4, 3, 1]
    k = 0
    t = np.ceil((t0 - OFF) / step) * step + OFF
    while t < t1 - 1e-6:
        i = min(19, int((t - OFF) // 2))
        ch = PROG[i]
        pool = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[2] + 24]
        m = pool[pattern[k % 8]]
        acc = 1.0 if k % (4 if step < 0.2 else 2) == 0 else 0.72
        place("arp", pluck(midi(m), 0.5, idx=2.0, decay=8.5), t, pan=0.32 if k % 2 else -0.32, gain=acc * gain)
        t += step
        k += 1


def bass(t0, t1, every=1.0, decay=2.2, gain=1.0):
    t = np.ceil((t0 - OFF) / every) * every + OFF
    while t < t1 - 1e-6:
        i = min(19, int((t - OFF) // 2))
        place("sub", subnote(midi(ROOT[i]), min(0.95, every - 0.05), decay=decay), t, gain=gain)
        t += every


def build(C):
    S = C["S"]
    # ---------------- pad: one chord per bar, cross-faded
    for i, (b, ch) in enumerate(zip(BARS, PROG)):
        last = i == len(BARS) - 1
        place("pad", pad_chord(ch, (DUR - (b - 0.5)) if last else 3.0, fade_in=1.0, fade_out=0.02 if last else 1.0), b - 0.5)

    # ---------------- 0.0 ignition: bloom, air, first light; 1.5 the light becomes the headline's bullet
    place("fx", subnote(midi(42), 2.6, attack=0.25, decay=1.1), 0.0, gain=0.85)
    place("fx", air(1.2, 0.5), 0.03)
    place("bell", bell(midi(85), 3.0, idx=2.0, decay=1.6), 0.06, pan=0.1, gain=0.55)
    place("bell", bell(midi(81), 2.6, idx=1.8), 1.5, pan=-0.2, gain=0.45)
    place("fx", subnote(midi(54), 0.3, decay=9), 1.5, gain=0.35)
    # 3.85 the headline rises to make room
    place("fx", whoosh(0.7, 700, 2600, -0.2, 0.3), S["s2"] - 0.25, gain=0.25)

    # ---------------- 4.0 -> 7.0 any business: a soft clock, a falling line at each workplace
    t = S["s2"]
    k = 0
    while t < S["s3"] - 0.3:
        place("drum", tick(2300 if k % 2 == 0 else 1900, 0.03, 0.55), t, pan=0.2 if k % 2 else -0.2, gain=0.5)
        t += 0.25
        k += 1
    for j, (t0, m) in enumerate(zip(C["tour"], [81, 78, 76, 73, 71, 69])):
        place("bell", pluck(midi(m), 0.7, idx=1.6, decay=5.5), t0, pan=-0.45 + j * 0.18, gain=0.5)
        place("fx", tick(3000, 0.025, 0.6), t0 + 0.04, pan=0.4, gain=0.25)
    bass(S["s2"], S["s3"] - 0.5, every=2.0, decay=0.9, gain=0.6)
    # 6.3 -> 7.0 into the business
    place("fx", riser(0.75, 300, 6000, (220, 900)), S["s3"] - 0.75, gain=0.45)
    place("bell", rev_bell(midi(81), 0.8), S["s3"] - 0.8, gain=0.4)

    # ---------------- 7.0 we come in: a soft impact, a warm stab, a heartbeat
    place("fx", impact(1.6, 42, air=0.35), S["s3"], gain=0.55)
    place("fx", whoosh(1.0, 500, 3000, 0.5, -0.4), S["s3"] - 0.1, gain=0.3)
    for m in DM9[1:]:
        place("arp", pluck(midi(m + 12), 1.0, idx=2.4, decay=4.0), S["s3"] + 0.01, gain=0.45)
    place("bell", bell(midi(81), 2.4, idx=2.0), S["s3"] + 0.4, pan=-0.15, gain=0.5)
    on = C.get("landOn", S["s3"] + 2.2)                                                   # touchdown on the first step
    place("bell", bell(midi(76), 2.0, idx=1.8, decay=2.2), on, pan=-0.3, gain=0.42)
    place("fx", subnote(midi(52), 0.4, decay=7), on, gain=0.35)
    for t0 in (S["s3"], S["s3"] + 1, S["s3"] + 2):
        place("drum", kick(0.6, f0=90, f1=42, k=20, decay=6.5, click=0.06), t0, gain=0.5)
    arp(S["s3"] + 1.0, S["s4"], 0.25, gain=0.55)
    bass(S["s3"], S["s4"], every=1.0, decay=1.4, gain=0.7)

    # ---------------- 10.0 -> 14.0 learn how the work is really done: a searching line at each step
    place("fx", whoosh(0.8, 450, 2200, -0.5, 0.3), S["s4"] - 0.15, gain=0.25)
    for t0 in (S["s4"], S["s4"] + 1, S["s4"] + 2, S["s4"] + 3):
        place("drum", kick(0.6, f0=90, f1=42, k=20, decay=6.5, click=0.06), t0, gain=0.5)
    b = S["s4"] + 0.75
    while b < S["s5"] - 0.6:
        place("drum", hat(0.07, 70, 0.22), b, pan=0.3, gain=0.5)
        b += 0.5
    arp(S["s4"], S["s5"] - 0.5, 0.25, gain=0.6)
    bass(S["s4"], S["s5"] - 0.5, every=1.0, decay=1.6, gain=0.75)
    for j, (t0, m) in enumerate(zip(C["nodes"], [76, 83, 78, 81, 85, 88])):
        place("bell", pluck(midi(m), 0.8, idx=1.4, decay=5.0), t0, pan=-0.5 + j * 0.2, gain=0.55)
        place("fx", tick(2700, 0.025, 0.6), t0 + 0.12, pan=0.3, gain=0.22)
    place("bell", rev_bell(midi(83), 0.6), C["sentBack"] - 0.6, gain=0.35)
    place("fx", sweep(0.5, 1300, 600, 0), C["sentBack"], pan=-0.3, gain=0.1)
    place("bell", bell(midi(76), 2.0, idx=1.6), C["drawB"], pan=0.3, gain=0.35)
    # 13.0 -> 14.0 riser into the straightening
    place("fx", riser(1.0, 280, 7500, (170, 880)), S["s5"] - 1.0, gain=0.55)
    place("bell", rev_bell(midi(85), 1.0), S["s5"] - 1.0, gain=0.45)

    # ---------------- 14.0 we automate it: impact, a bright stab, the groove starts
    place("fx", impact(1.4, 40), S["s5"], gain=0.85)
    for m in AM9[1:]:
        place("arp", pluck(midi(m + 24), 0.9, idx=2.6, decay=4.5), S["s5"] + 0.01, gain=0.5)
    for j, m in enumerate([69, 73, 76, 81, 85, 88]):
        place("bell", pluck(midi(m + 12), 0.6, idx=1.4, decay=6), S["s5"] + 0.05 + j * 0.06, pan=-0.5 + j * 0.2, gain=0.32)
    groove(S["s5"], S["s6"] - 0.55)
    arp(S["s5"], S["s6"] - 0.55, 0.125)
    bass(S["s5"], S["s6"] - 0.55, every=1.0)
    place("fx", tick(3100, 0.03, 0.8), S["s5"] + 1.1, pan=-0.4, gain=0.3)          # counter swaps
    # the invoice runs: a rising note at each step; the person approves on the beat
    for j, (t0, m) in enumerate(zip(C["run"], [81, 85, 88, 90, 93, 97])):
        place("bell", pluck(midi(m), 0.7, idx=1.3, decay=5.5), t0, pan=-0.5 + j * 0.2, gain=0.42)
    place("bell", bell(midi(90), 0.9, idx=0.8, decay=2.8), C["run"][3] + 0.02, pan=0.1, gain=0.18)   # it waits
    place("fx", tick(2800, 0.035, 1.0), C["click"], pan=0.15, gain=0.85)
    place("bell", bell(midi(88), 2.2, idx=2.4), C["click"] + 0.07, pan=0.1, gain=0.65)
    place("bell", bell(midi(93), 2.2, idx=2.0), C["click"] + 0.14, pan=0.25, gain=0.5)

    # ---------------- 18.55 -> 20.0 the light leaves the diagram and flies into the business
    place("fx", whoosh(1.5, 300, 3600, -0.7, 0.5), S["s6"] - 0.5, gain=0.45)
    place("fx", riser(1.4, 260, 8000, (160, 1000)), C["land"] - 1.4, gain=0.6)
    place("bell", rev_bell(midi(88), 1.1), C["land"] - 1.1, gain=0.5)
    place("bell", rev_bell(midi(81), 1.1), C["land"] - 1.1, gain=0.35)

    # ---------------- 20.0 it lands: the computer's light comes on
    place("fx", impact(2.2, 36, air=0.4), C["land"], gain=0.95)
    place("fx", subnote(midi(33), 2.2, attack=0.01, decay=1.0), C["land"], gain=0.75)
    place("fx", air(1.6, 0.4), C["land"])
    for m, pan, g in ((69, -0.35, 0.45), (76, 0.3, 0.5), (81, 0.0, 0.75), (85, 0.2, 0.5), (88, -0.15, 0.35)):
        place("bell", bell(midi(m), 2.4, idx=2.6, decay=1.5), C["land"], pan=pan, gain=g)
    for t0 in (S["s6"] + 2.0, S["s6"] + 3.0):
        place("drum", kick(0.6, f0=85, f1=40, k=18, decay=6.0, click=0.05), t0, gain=0.5)
    arp(S["s6"] + 1.5, S["s6b"], 0.25, gain=0.5)
    bass(S["s6"] + 1.0, S["s6b"], every=2.0, decay=0.8, gain=0.7)
    place("bell", pluck(midi(81), 0.8, idx=1.0, decay=5), S["s6"] + 1.55, pan=-0.3, gain=0.3)        # caption

    # ---------------- 23.0 match cut to the product; we keep it working
    place("fx", whoosh(0.9, 500, 2800, 0.4, -0.4), S["s6b"] - 0.2, gain=0.35)
    place("fx", impact(1.2, 46, air=0.25), S["s6b"], gain=0.4)
    groove(S["s6b"] + 1.0, S["s7"] - 0.1, claps=False, ghosts=False, kick_gain=0.75)
    arp(S["s6b"] + 0.5, S["s6b"] + 2.0, 0.25, gain=0.7)
    arp(S["s6b"] + 2.0, S["s7"] - 0.1, 0.125, gain=0.8)
    bass(S["s6b"] + 1.0, S["s7"] - 0.1, every=1.0, gain=0.9)
    # each month: a check, a bell; December finds a change and fixes it
    for t0, m in zip(C["log"], [81, 85, 86, 93]):
        place("bell", bell(midi(m), 1.8, idx=2.0, decay=2.2), t0 + 0.12, pan=0.3, gain=0.45)
        place("fx", tick(3200, 0.03, 0.8), t0 + 0.12, pan=-0.3, gain=0.3)
    place("bell", bell(midi(88), 1.8, idx=2.2, decay=2.2), C["fix"], pan=0.2, gain=0.5)

    # ---------------- 26.5 -> 30.0 dozens of workflows: the full groove, the light spreads
    place("fx", whoosh(1.4, 2600, 400, 0.3, -0.3), S["s7"] - 0.1, gain=0.42)
    place("fx", riser(1.2, 300, 7000, (200, 900)), S["s7"] - 0.1, gain=0.35)
    place("fx", impact(1.6, 44, air=0.4), S["s7"] + 1.1, gain=0.45)                      # the lights come on
    groove(S["s7"], S["s8"] - 0.25)
    arp(S["s7"], S["s8"] - 0.25, 0.125, gain=1.05)
    bass(S["s7"], S["s8"] - 0.25, every=1.0)
    for j, t0 in enumerate(sorted(C["grid"])):
        place("bell", pluck(midi(PENTA[(j + 3) % len(PENTA)] + (12 if j > 8 else 0)), 0.5, idx=0.9, decay=7), t0,
              pan=np.sin(j * 1.3) * 0.6, gain=0.22)
    place("bell", bell(midi(81), 2.0, idx=1.8), S["s7"] + 0.75, pan=-0.2, gain=0.4)               # headline

    # ---------------- 30.0 -> 35.0 the connector (dark): boom, drones, heartbeat
    place("bell", rev_bell(midi(76), 0.55), S["s8"] - 0.55, gain=0.45)
    place("fx", impact(2.2, 32, air=0.2), S["s8"], gain=0.8)
    for i in range(15, 18):
        place("sub", subnote(midi(ROOT[i]), 1.95, attack=0.08, decay=0.55), BARS[i], gain=0.85)
    for t0 in (S["s8"] + 1, S["s8"] + 2, S["s8"] + 3, S["s8"] + 4):
        place("drum", kick(0.6, f0=80, f1=38, k=18, decay=6.0, click=0.05), t0, gain=0.55)
    arp(S["s8"] + 0.5, S["s9"] - 0.6, 0.25, gain=0.8)
    cn = C.get("conn", {"head": S["s8"] + 0.9, "morph": S["s8"] + 1.0, "pulse": S["s8"] + 2.0, "mid": S["s8"] + 2.5,
                        "tag": S["s8"] + 3.0, "out": S["s8"] + 4.1})
    place("bell", pluck(midi(74), 0.8, idx=1.8, decay=4), cn["morph"], gain=0.45)                  # orb -> MCP
    place("bell", pluck(midi(81), 0.8, idx=1.8, decay=4), cn["morph"] + 0.04, gain=0.35)
    place("fx", sweep(1.0, 380, 1300, 22), cn["pulse"], gain=0.16)                                 # the pulse
    place("bell", pluck(midi(88), 0.6, idx=1.6, decay=6), cn["mid"], gain=0.4)
    place("bell", pluck(midi(85), 0.6, idx=1.2, decay=7), cn["tag"], pan=0.4, gain=0.35)          # entry prepared
    place("bell", bell(midi(81), 2.0, idx=1.8), cn["head"], pan=0.2, gain=0.35)                   # headline
    place("fx", whoosh(0.8, 500, 2200, 0.5, 0.0), cn["out"], gain=0.3)

    # ---------------- 35.0 -> 40.0 the iris closes; the light becomes the dot of the wordmark
    place("bell", rev_bell(midi(88), 0.85), S["s9"] + 0.85 - 0.85, gain=0.5)
    place("fx", riser(0.8, 350, 6000, (250, 1000)), S["s9"], gain=0.4)
    for j, m in enumerate([69, 73, 76, 80, 83]):
        place("bell", pluck(midi(m), 0.5, idx=0.9, decay=8), S["s9"] + 0.85 + j * 0.06, pan=-0.4 + j * 0.2, gain=0.22)
    land = S["s9"] + 1.5
    place("fx", impact(1.9, 33, air=0.3), land, gain=0.72)
    place("fx", subnote(midi(33), 2.4, attack=0.01, decay=1.0), land, gain=0.7)
    place("fx", air(1.4, 0.35), land)
    for m, pan, g in ((69, -0.3, 0.45), (76, 0.3, 0.5), (81, 0.0, 0.7), (85, 0.2, 0.45), (88, -0.2, 0.3)):
        place("bell", bell(midi(m), 2.6, idx=2.6, decay=1.4), land, pan=pan, gain=g)
    place("bell", pluck(midi(93), 0.9, idx=0.8, decay=4), S["s9"] + 1.95, pan=0.3, gain=0.22)       # tagline
    place("fx", tick(2600, 0.03, 0.6), S["s9"] + 2.4, gain=0.2)                                      # URL

def make_ir(rt=2.4, pre=0.018):
    n = int(rt * 1.25 * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((2, n)) * np.exp(-6.91 * t / rt)
    ir = stft_filter(ir, lambda tc, f: lp(f, 5200 * np.exp(-tc * 0.9) + 900, 2), nfft=1024, hop=256)
    ir[:, : int(pre * SR)] = 0
    for d, g in ((0.011, 0.5), (0.019, 0.38), (0.027, 0.3), (0.041, 0.22)):
        ir[0, int(d * SR)] += g * 4
        ir[1, int(d * SR * 1.13)] += g * 4
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return ir


def convolve(x, ir):
    n = x.shape[1] + ir.shape[1]
    nf = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nf, axis=1) * np.fft.rfft(ir, nf, axis=1), nf, axis=1)
    return y[:, : x.shape[1]]


def pingpong(x, d=0.375, fb=0.36, taps=6):
    y = np.zeros_like(x)
    m = x.sum(axis=0) * 0.5
    ds = int(d * SR)
    for k in range(1, taps + 1):
        sh = k * ds
        if sh >= N:
            break
        tap = np.zeros(N)
        tap[sh:] = m[: N - sh] * fb ** k
        w = 2 * k + 1
        y[k % 2] += np.convolve(tap, np.ones(w) / w, mode="same")
    return y


def rms(x):
    return float(np.sqrt(np.mean(x ** 2) + 1e-12))


def to_rms(x, db):
    return x * (10 ** (db / 20) / rms(x))


def to_peak(x, db):
    return x * (10 ** (db / 20) / (np.max(np.abs(x)) + 1e-12))



def mixdown(C):
    S = C["S"]
    s5, s6, s7, s8, s9, land = S["s5"], S["s6"], S["s7"], S["s8"], S["s9"], C["land"]
    tgrid = np.arange(N) / SR
    pad = BUS["pad"]
    pad = stft_filter(pad, lambda tc, f: lp(f, curve([(0, 300), (1.6, 2600), (3.8, 2600), (4.3, 1500), (6.9, 1500), (7.05, 3200),
                                                        (10.0, 3200), (10.3, 2200), (s5 - 0.1, 2600), (s5, 4800), (s6 - 0.6, 4800), (s6, 2000),
                                                        (land, 5200), (S["s6b"], 4200), (s7, 4800), (s8 - 0.1, 4800), (s8 + 0.2, 800),
                                                        (s9 - 0.5, 1400), (s9 + 0.75, 5000), (40, 5000)], log=True)(tc)) * hp(f, 95, 2))
    pad *= curve([(0, 0), (0.2, 0.15), (1.6, 1.0), (3.8, 0.95), (4.3, 0.8), (6.9, 0.85), (7.05, 0.95), (s5 - 0.1, 0.8), (s5, 0.7),
                  (s6 - 0.6, 0.7), (s6, 0.95), (land, 1.1), (land + 1, 0.95), (S["s6b"], 0.85), (s7, 0.75), (s8 - 0.1, 0.75),
                  (s8 + 0.2, 1.0), (s9, 0.95), (s9 + 0.7, 1.15), (s9 + 0.8, 0.45), (s9 + 1.5, 1.2), (s9 + 3.0, 1.0), (40, 0.9)])(tgrid)
    arp = BUS["arp"]
    arp = arp + 0.34 * pingpong(arp)
    arp = stft_filter(arp, lambda tc, f: lp(f, curve([(0, 6500), (s8 - 0.1, 6500), (s8 + 0.3, 1500), (s9, 1500), (s9 + 1.0, 6500), (40, 6500)],
                                                       log=True)(tc)) * hp(f, 180, 2))
    arp *= curve([(0, 1), (s8 - 0.1, 1), (s8 + 0.05, 0.6), (s9, 0.6), (s9 + 1.0, 1), (40, 1)])(tgrid)
    bells = BUS["bell"] + 0.22 * pingpong(BUS["bell"], d=0.25, fb=0.3, taps=4)
    pad = to_rms(pad, -21)
    arp = to_rms(arp, -31)
    drum = to_rms(BUS["drum"], -31)
    sub = to_rms(BUS["sub"], -30.5)
    bells = to_peak(bells, -9)
    fx = to_peak(BUS["fx"], -8)
    dry = pad + arp + drum + sub + bells + fx
    wet = convolve(0.28 * pad + 0.45 * arp + 0.6 * bells + 0.35 * fx + 0.1 * drum, make_ir())
    wet = wet * (0.5 * rms(dry) / rms(wet))
    mix = dry + wet
    # master: DC/rumble high-pass, fades, soft clip
    spec = np.fft.rfft(mix, axis=1)
    fr = np.fft.rfftfreq(N, 1 / SR)
    mix = np.fft.irfft(spec * hp(fr, 28, 4) * (1 + 0.32 * hp(fr, 6500, 2)), N, axis=1)   # + a gentle air shelf
    fade = np.ones(N)
    fin = int(0.02 * SR)
    fade[:fin] = np.linspace(0, 1, fin)
    fo0 = int(39.0 * SR)
    fade[fo0:] = np.cos(np.linspace(0, np.pi / 2, N - fo0)) ** 2
    mix *= fade
    mid, side = (mix[0] + mix[1]) / 2, (mix[0] - mix[1]) / 2   # narrow slightly: mono-safe on phone speakers
    side *= 0.78
    mix = np.vstack([mid + side, mid - side])
    mix = to_peak(mix, -1.0)
    mix = np.tanh(1.15 * mix) / np.tanh(1.15)
    return mix


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x.T * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def integrated_lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return float(i[-1]), float(tp[-1]) if tp else None



def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("score.wav")
    C = load_cues(sys.argv[2] if len(sys.argv) > 2 else None)
    build(C)
    mix = mixdown(C)
    tmp = Path(tempfile.gettempdir()) / "lumic-score-v3-pre.wav"
    write_wav(tmp, mix)
    lufs, _ = integrated_lufs(tmp)
    mix = mix * 10 ** ((-16.0 - lufs) / 20)
    peak = np.max(np.abs(mix))
    if peak > 0.89:                                  # keep true peak under about -1 dBFS
        mix = np.tanh(mix / 0.89 * 1.2) / np.tanh(1.2) * 0.89
    write_wav(out, mix)
    lufs2, tp2 = integrated_lufs(out)
    print(f"wrote {out}  integrated {lufs2:.1f} LUFS  true peak {tp2} dBFS")


if __name__ == "__main__":
    main()
