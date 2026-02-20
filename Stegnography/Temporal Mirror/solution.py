import numpy as np
from scipy.io.wavfile import read, write

# === CONFIGURATION ===
INPUT_FILE = "D:/BPSOT/Stego/Temporal Mirror/temporal.wav"
OUTPUT_FILE = "solved_flag.wav"
UNIT_TIME = 0.08 

MORSE_CODE_REVERSE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', 
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', 
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O', 
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T', 
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y', 
    '--..': 'Z', '.----': '1', '..---': '2', '...--': '3', 
    '....-': '4', '.....': '5', '-....': '6', '--...': '7', 
    '---..': '8', '----.': '9', '-----': '0', '-.-.-': '{', '..--.-': '_'
}

def decode_morse_with_smoothing(signal, sample_rate):
    # 1. Rectify (Absolute value)
    envelope = np.abs(signal)
    
    # === NEW: SMOOTHING STEP ===
    # Create a 10ms sliding window to average out the sine wave vibrations
    window_size = int(sample_rate * 0.01) 
    window = np.ones(window_size) / window_size
    # Convolve applies the rolling average
    smoothed = np.convolve(envelope, window, mode='same')
    
    # 2. Thresholding (Skip first 1s sync beep)
    analysis_start = int(sample_rate * 1.0)
    local_max = np.max(smoothed[analysis_start:])
    threshold = local_max * 0.5 
    
    print(f"[DEBUG] Max Signal: {local_max:.2f} | Threshold: {threshold:.2f}")

    # 3. Digitizing (Clean 0s and 1s)
    digital_signal = (smoothed > threshold).astype(int)
    
    # 4. Run-Length Encoding
    diffs = np.diff(digital_signal)
    changes = np.where(diffs != 0)[0]
    changes = np.concatenate(([0], changes, [len(digital_signal)-1]))
    durations = np.diff(changes)
    values = digital_signal[changes[:-1] + 1]
    
    print(f"[DEBUG] Detected signal blocks: {len(durations)} (This should be < 200)")

    # 5. Decode
    samples_per_unit = sample_rate * UNIT_TIME
    morse_string = ""
    decoded_message = ""
    
    for val, dur in zip(values, durations):
        ratio = dur / samples_per_unit
        
        if val == 1: # Sound
            if 0.5 < ratio < 1.5:
                morse_string += "."
            elif ratio > 2.0:
                morse_string += "-"
        
        else: # Silence
            if ratio > 2.0 and ratio < 5.0: # Letter Space
                if morse_string in MORSE_CODE_REVERSE:
                    decoded_message += MORSE_CODE_REVERSE[morse_string]
                elif morse_string == "-.-.-":
                     decoded_message += "}" 
                morse_string = ""
            elif ratio > 5.0: # Word Space
                if morse_string in MORSE_CODE_REVERSE:
                    decoded_message += MORSE_CODE_REVERSE[morse_string]
                decoded_message += " "
                morse_string = ""

    # Catch last character
    if morse_string in MORSE_CODE_REVERSE:
        decoded_message += MORSE_CODE_REVERSE[morse_string]
    elif morse_string == "-.-.-":
        decoded_message += "}"

    return decoded_message

def solve():
    print(f"[*] Reading {INPUT_FILE}...")
    try:
        rate, data = read(INPUT_FILE)
    except FileNotFoundError:
        print(f"[-] Error: Could not find {INPUT_FILE}")
        return

    left = data[:, 0].astype(float)
    right = data[:, 1].astype(float)
    
    print("[*] Canceling Noise...")
    right_reversed = right[::-1]
    clean_signal = left - right_reversed
    
    # Save the clean audio for verification
    write(OUTPUT_FILE, rate, clean_signal.astype(np.int16))
    
    print("[*] Decoding...")
    try:
        flag = decode_morse_with_smoothing(clean_signal, rate)
        print("\n" + "="*40)
        print(f"FLAG: {flag}")
        print("="*40 + "\n")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    solve()