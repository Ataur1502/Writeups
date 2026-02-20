# Solution Writeup : Temporal Mirror: Echoes of Troy

## Overview

This challenge hides the flag inside an audio file (`temporal.wav`) using **audio steganography**.

The file is a **stereo WAV**:
- **Left channel** contains loud white noise **plus** a very quiet encoded signal.
- **Right channel** contains white noise, but it is **time-reversed**.

The hidden signal is **Morse code**, transmitted using **high-frequency tones** (frequency-hopping).

Goal:
Extract the faint signal from heavy noise and decode the Morse to recover the flag.

---

## Step 1 : Observe the audio

Open the WAV in any waveform/spectrogram tool:
- Audacity
- Sonic Visualiser
- Adobe Audition
- Python + librosa/matplotlib

If you zoom in / view the start and end of each channel, you’ll notice:

- A **beep at the start of the LEFT channel**
- A **beep at the end of the RIGHT channel**

This is intentional , it indicates one channel’s timeline is reversed.

---

## Step 2 : Reverse the right channel

Since the right channel is the same noise but reversed, we reverse it back:

- Extract right channel
- Reverse it in time
- Now both channels share the same noise pattern

In Audacity:
1. Split Stereo to Mono
2. Select Right channel track
3. `Effect → Reverse`

---

## Step 3 : Noise cancellation (key step)

Now we use the trick:

Left channel = `noise + signal`  
Right channel (after reversing) = `noise`

So:

`Left - Right ≈ signal`

This cancels most of the white noise and reveals the hidden pattern.

In Audacity:
1. Make sure both channels are aligned
2. Invert right channel (`Effect → Invert`)
3. Mix and render (`Tracks → Mix → Mix and Render`)

The result will have the faint Morse beeps much clearer.

---

## Step 4 : View spectrogram and locate the message

Switch to spectrogram view.

In Audacity:
- Track dropdown → `Spectrogram`
- Set range around **10kHz–18kHz**

You should see Morse-like bursts at high frequencies.

The frequencies hop between:
- ~10 kHz
- ~14 kHz
- ~18 kHz

But frequency does not matter for decoding 
only the durations matter (dot vs dash).

---

## Step 5 : Decode Morse

The Morse unit timing:
- Dot = 1 unit
- Dash = 3 units
- Small gap between symbols = 1 unit
- Gap between letters = 3 units
- Gap between words = 7 units

Extract the Morse and decode it.

Online Morse decoders can work once audio is cleaned, or decode manually using the bursts.

---

## Final Flag

`BPCTF{T1M3_FL0WS_B4CKW4RDS_H3R3}`

---

