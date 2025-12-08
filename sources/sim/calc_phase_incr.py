#!/usr/bin/env python3
"""Calculate phase increment values for 48kHz sample rate"""

import math

SAMPLE_RATE = 48000
PHASE_ACCUMULATOR_BITS = 32

# MIDI note 0 is C-1 at 8.176 Hz
# MIDI note 60 is middle C (C4) at 261.63 Hz
# Formula: freq = 440 * 2^((note - 69) / 12)

def midi_note_to_freq(note):
    """Convert MIDI note number to frequency in Hz"""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def calc_phase_incr(freq, sample_rate, bits=32):
    """Calculate phase increment for DDS at given sample rate"""
    phase_incr = (freq * (2 ** bits)) / sample_rate
    return int(round(phase_incr))

print("// Phase increment values for 48kHz sample rate")
print("// Formula: PHASE_INCR = (frequency * 2^32) / 48000")
print()

for note in range(128):
    freq = midi_note_to_freq(note)
    phase_incr = calc_phase_incr(freq, SAMPLE_RATE, PHASE_ACCUMULATOR_BITS)
    print(f"assign note_freqs[{note}] = 32'd{phase_incr};  // Note {note}: {freq:.2f} Hz")

# Verify a few key notes
print("\n// Verification:")
print(f"// Note 60 (middle C): {midi_note_to_freq(60):.2f} Hz -> PHASE_INCR = {calc_phase_incr(midi_note_to_freq(60), SAMPLE_RATE)}")
print(f"// Note 69 (A4 440Hz): {midi_note_to_freq(69):.2f} Hz -> PHASE_INCR = {calc_phase_incr(midi_note_to_freq(69), SAMPLE_RATE)}")
