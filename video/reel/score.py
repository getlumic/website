"""Original score for the lumic reel (40 s). Pure synthesis with numpy: no samples, no licensed audio.

Writes a 48 kHz stereo 16-bit WAV, loudness-normalised to about -16 LUFS for web playback.
All hit points follow the picture in reel.html (see the CUE comments).

Usage: python3 video/reel/score.py out.wav
Needs: numpy, and ffmpeg on PATH (loudness measurement).
"""
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
OFF = 0.05                      # musical grid offset: bar lines at 0.05, 2.05, ... (120 BPM, 2-second bars)
rng = np.random.default_rng(1414)


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


# ---------------------------------------------------------------- harmony (D major; 20 bars of 2 s)
DM9 = [50, 57, 61, 64, 66]
BM9 = [47, 54, 57, 61, 62]
GM9 = [43, 50, 54, 57, 59]
AA9 = [45, 52, 59, 61, 64]
EM9 = [40, 47, 50, 54, 55]
PROG = [DM9, DM9, BM9, GM9, DM9, BM9, GM9, AA9, DM9, BM9, GM9, AA9, DM9, BM9, GM9, BM9, GM9, EM9, AA9, DM9]
ROOT = [38, 38, 35, 31, 38, 35, 31, 33, 38, 35, 31, 33, 38, 35, 31, 35, 31, 40, 33, 38]
BARS = [OFF + 2 * i for i in range(20)]
PENTA = [74, 76, 78, 81, 83, 86, 88, 90, 93, 95]          # D5 E5 F#5 A5 B5 D6 E6 F#6 A6 B6


def build():
    # ---------------- pad: one chord per bar, cross-faded
    for i, (b, ch) in enumerate(zip(BARS, PROG)):
        last = i == len(BARS) - 1
        # each chord fades in over the second before its bar line and out over the second after the next one
        place("pad", pad_chord(ch, (DUR - (b - 0.5)) if last else 3.0, fade_in=1.0, fade_out=0.02 if last else 1.0), b - 0.5)

    # ---------------- groove 8.05 → 29.5: kick, hats, clap, sub, arp
    for k in range(22):
        t0 = OFF + 8 + k
        if t0 > 29.2:
            break
        place("drum", kick(), t0, gain=0.9)
    for k in range(43):
        t0 = OFF + 8.25 + k * 0.5
        if t0 > 29.3:
            break
        place("drum", hat(), t0, pan=0.25, gain=0.55)
    for k in range(52):
        t0 = OFF + 16.125 + k * 0.25
        if t0 > 29.3:
            break
        if abs(((t0 - OFF) * 4) % 2 - 1) > 0.01:          # 16th ghosts only between the 8ths
            place("drum", hat(0.05, 90, 0.2), t0, pan=-0.3, gain=0.5)
    for k in range(14):
        t0 = OFF + 16.5 + k * 1.0
        if t0 > 29.2:
            break
        place("drum", clap(), t0, gain=0.55)
    for i in range(4, 15):
        b = BARS[i]
        for o in (0.0, 1.0):
            place("sub", subnote(midi(ROOT[i]), 0.95, decay=2.2), b + o)
    # arpeggio: 8ths from 8.05, 16ths from 16.05, filtered 8ths in the dark section
    pattern = [0, 2, 1, 3, 2, 4, 3, 1]
    for i in range(4, 19):
        b, ch = BARS[i], PROG[i]
        pool = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[2] + 24]
        step = 0.125 if 8 <= i <= 14 else 0.25
        for j in range(int(2.0 / step)):
            t0 = b + j * step
            if 29.35 < t0 < 30.3 or t0 > 36.4:
                continue
            m = pool[pattern[(j if step == 0.125 else j * 2) % 8]]
            acc = 1.0 if (j % (4 if step == 0.125 else 2)) == 0 else 0.72
            place("arp", pluck(midi(m), 0.5, idx=2.0, decay=8.5), t0, pan=0.32 if j % 2 else -0.32, gain=acc)

    # ---------------- dark section 29.55 → 36.7: drones and heartbeat
    for i in range(15, 19):
        place("sub", subnote(midi(ROOT[i]), 1.95, attack=0.08, decay=0.55), BARS[i], gain=0.85)
    for t0 in (30.05, 31.05, 32.05, 33.05, 34.05, 35.05):
        place("drum", kick(0.6, f0=80, f1=38, k=18, decay=6.0, click=0.05), t0, gain=0.55)

    # ---------------- CUES (sound design locked to the picture)
    # 0.0 ignition: bloom, air, first light
    place("fx", subnote(midi(38), 2.6, attack=0.25, decay=1.1), 0.0, gain=0.9)
    place("fx", air(1.2, 0.5), 0.03)
    place("bell", bell(midi(86), 3.0, idx=2.0, decay=1.6), 0.06, pan=0.1, gain=0.55)
    # 2.1 the orb lands as the i-dot
    place("bell", bell(midi(81), 2.8), 2.1, pan=-0.15, gain=0.75)
    place("bell", bell(midi(86), 2.8), 2.13, pan=0.15, gain=0.6)
    place("fx", subnote(midi(50), 0.35, decay=9), 2.1, gain=0.5)
    # 3.05 wordmark to the corner
    place("fx", whoosh(0.85, 700, 3000, 0.4, -0.7), 2.95, gain=0.35)
    # 3.5 → 6.3 manual work: a soft clock
    for k in range(6):
        place("drum", tick(2300 if k % 2 == 0 else 1900, 0.03, 0.6), 3.55 + 0.5 * k, pan=0.2 if k % 2 else -0.2, gain=0.55)
    # 6.35 → 8.05 riser into the grid snap
    place("fx", riser(1.7), 6.35, gain=0.55)
    place("bell", rev_bell(midi(81), 1.0), 8.05 - 1.0, gain=0.45)
    # 8.05 snap: impact + chord stab + ripple run
    place("fx", impact(1.4, 40), 8.05, gain=0.85)
    for m in DM9[1:]:
        place("arp", pluck(midi(m + 12), 0.9, idx=2.6, decay=4.5), 8.06, gain=0.5)
    for j, m in enumerate([74, 76, 78, 81, 83, 86]):
        place("bell", pluck(midi(m + 12), 0.6, idx=1.4, decay=6), 8.1 + j * 0.06, pan=-0.5 + j * 0.2, gain=0.35)
    # 9.9 card glides to its place
    place("fx", whoosh(0.9, 500, 2400, 0.6, -0.2), 9.85, gain=0.3)
    # 13.1 chart end point; 14.45 drill-down; 15.25+ rows
    place("bell", pluck(midi(93), 0.7, idx=1.2, decay=5), 13.1, pan=0.4, gain=0.45)
    place("bell", pluck(midi(78), 0.6, idx=1.6, decay=6), 14.45, pan=0.3, gain=0.45)
    for j, m in enumerate([86, 88, 90]):
        place("bell", pluck(midi(m), 0.4, idx=1.0, decay=9), 15.25 + j * 0.12, pan=-0.2 + j * 0.2, gain=0.28)
    # 16.85 scene change: dashboards out, envelope in
    place("fx", whoosh(1.1, 400, 3200, -0.7, 0.6), 16.8, gain=0.4)
    # 18.4 flap; 18.8 paper rises; 20.0 scan
    place("fx", flick(), 18.42, pan=0.3, gain=0.6)
    place("fx", whoosh(0.9, 900, 4200, 0.2, 0.3), 18.8, gain=0.22)
    place("fx", sweep(0.95, 700, 1500), 20.0, pan=0.25, gain=0.12)
    # 21.2 fields fly into the entry; they land 0.78 s later
    for j, m in enumerate([86, 90, 93]):
        place("bell", pluck(midi(m), 0.6, idx=1.5, decay=6), 21.2 + j * 0.17, pan=-0.1 + j * 0.2, gain=0.42)
        place("fx", tick(3100, 0.03, 0.8), 21.98 + j * 0.17, pan=0.45, gain=0.35)
    # 21.9 "Entry prepared · unposted"
    place("bell", pluck(midi(88), 0.5, idx=1.0, decay=8), 21.9, pan=0.3, gain=0.3)
    # 23.2 Approve: click + confirm chime
    place("fx", tick(2800, 0.035, 1.0), 23.2, pan=0.3, gain=0.8)
    place("bell", bell(midi(86), 2.2, idx=2.4), 23.3, pan=0.25, gain=0.7)
    place("bell", bell(midi(93), 2.2, idx=2.0), 23.37, pan=0.35, gain=0.55)
    # 24.7 the entry becomes the ERP hub
    place("fx", whoosh(0.95, 450, 2600, 0.6, -0.5), 24.65, gain=0.35)
    # 25.55 nodes appear
    for j, m in enumerate([81, 83, 86]):
        place("arp", pluck(midi(m), 0.5, idx=1.2, decay=8), 25.55 + j * 0.1, pan=0.4, gain=0.45)
    # pulses arrive at each node
    for t0, m in ((27.2, 86), (27.45, 88), (27.7, 90), (28.65, 93), (28.85, 95), (29.05, 98)):
        place("bell", pluck(midi(m), 0.7, idx=1.3, decay=5.5), t0, pan=0.5, gain=0.4)
    # 29.0 pulses return; 29.55 iris opens to dark; 30.0 low boom
    place("bell", rev_bell(midi(74), 0.55), 29.55 - 0.55, gain=0.5)
    place("fx", riser(0.55, 400, 5000, (300, 900)), 29.0, gain=0.35)
    place("fx", whoosh(1.3, 300, 2600, -0.3, 0.3), 29.45, gain=0.5)
    place("fx", impact(2.0, 32, air=0.2), 30.0, gain=0.75)
    # 31.0 → 33.35 comet: sparkle trail + a bell at each checkpoint
    run = PENTA[:7] + PENTA[5:0:-1] + PENTA[1:8]
    for j in range(19):
        t0 = 31.0 + j * 0.125
        if t0 > 33.35:
            break
        place("bell", pluck(midi(run[j % len(run)] + 12), 0.45, idx=0.9, decay=7), t0, pan=np.sin(j * 0.7) * 0.6, gain=0.16)
    for t0, m in ((31.364, 81), (31.856, 86), (32.218, 90), (32.592, 93)):
        place("bell", bell(midi(m), 2.2, idx=2.2, decay=2.3), t0, pan=0.3, gain=0.55)
    # 33.65 rings collapse; 34.2 orb becomes the MCP pill
    place("fx", whoosh(0.8, 500, 2200, 0.5, 0.0), 33.6, gain=0.3)
    place("bell", pluck(midi(74), 0.8, idx=1.8, decay=4), 34.2, gain=0.45)
    place("bell", pluck(midi(81), 0.8, idx=1.8, decay=4), 34.24, gain=0.35)
    place("fx", tick(2400, 0.03, 0.7), 34.3, gain=0.3)
    # 35.2 → 36.0 pulse: AI → MCP → Sage 100
    place("fx", sweep(0.8, 380, 1300, 22), 35.2, pan=0.0, gain=0.16)
    place("bell", pluck(midi(88), 0.6, idx=1.6, decay=6), 35.6, gain=0.4)
    place("bell", pluck(midi(81), 0.6, idx=1.2, decay=7), 35.95, pan=0.4, gain=0.35)
    # 36.2 pill folds back into the orb
    place("bell", pluck(midi(81), 0.5, idx=1.0, decay=8), 36.2, gain=0.3)
    place("bell", pluck(midi(74), 0.6, idx=1.0, decay=7), 36.34, gain=0.3)
    # 36.45 → 37.45 iris closes: reverse swell, then a breath
    place("bell", rev_bell(midi(86), 1.0), 37.45 - 1.0, gain=0.55)
    place("bell", rev_bell(midi(81), 1.0), 37.45 - 1.0, gain=0.4)
    place("fx", riser(0.85, 350, 6000, (250, 1000)), 36.6, gain=0.4)
    # 37.45 letters rise
    for j, m in enumerate([74, 78, 81, 85, 88]):
        place("bell", pluck(midi(m), 0.5, idx=0.9, decay=8), 37.45 + j * 0.06, pan=-0.4 + j * 0.2, gain=0.22)
    # 38.1 the orb becomes the i-dot: the resolve
    place("fx", impact(1.8, 36, air=0.3), 38.1, gain=0.7)
    place("fx", subnote(midi(38), 1.9, attack=0.01, decay=1.2), 38.1, gain=0.7)
    place("fx", air(1.4, 0.35), 38.1)
    for m, pan, g in ((74, -0.3, 0.45), (81, 0.3, 0.5), (86, 0.0, 0.7), (90, 0.2, 0.45)):
        place("bell", bell(midi(m), 1.9, idx=2.6, decay=1.7), 38.1, pan=pan, gain=g)


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


def mixdown():
    tgrid = np.arange(N) / SR
    pad = BUS["pad"]
    pad = stft_filter(pad, lambda tc, f: lp(f, curve([(0, 300), (1.6, 2600), (3.4, 2600), (4.2, 1300), (6.4, 1300), (8.05, 4200), (29.4, 4200),
                                                        (30.2, 700), (33.0, 1400), (36.3, 1300), (37.4, 5000), (40, 5000)], log=True)(tc)) * hp(f, 95, 2))
    pad *= curve([(0, 0), (0.2, 0.15), (1.6, 1.0), (3.4, 0.95), (4.2, 0.8), (7.0, 0.85), (8.05, 0.72), (29.4, 0.72), (30.2, 1.0),
                  (36.4, 0.95), (37.35, 1.15), (37.5, 0.4), (38.1, 1.2), (39.2, 1.0), (40, 0.9)])(tgrid)
    arp = BUS["arp"]
    arp = arp + 0.34 * pingpong(arp)
    arp = stft_filter(arp, lambda tc, f: lp(f, curve([(0, 6500), (29.4, 6500), (30.3, 1500), (36.4, 1500), (37.3, 6500), (40, 6500)], log=True)(tc)) * hp(f, 180, 2))
    arp *= curve([(0, 1), (29.5, 1), (30.05, 0.6), (36.4, 0.6), (37.4, 1), (40, 1)])(tgrid)
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
    mix = np.fft.irfft(spec * hp(fr, 28, 4), N, axis=1)
    fade = np.ones(N)
    fin = int(0.02 * SR)
    fade[:fin] = np.linspace(0, 1, fin)
    fo0 = int(39.2 * SR)
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
    build()
    mix = mixdown()
    tmp = Path(tempfile.gettempdir()) / "lumic-score-pre.wav"
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
