import cocotb
import os
import sys
from math import log
import logging
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge
from cocotb.triggers import ReadOnly,with_timeout, Edge, ReadWrite, NextTimeStep, First
from cocotb.utils import get_sim_time as gst
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

async def send_midi_byte(dut, byte_data):
    """Send a single MIDI byte with start and stop bits"""
    # Start bit (0)
    dut.midi_in.value = 0
    await Timer(32000, 'ns')

    # Data bits (LSB first, reversed for MSB first)
    for i in range(7, -1, -1):
        bit = (byte_data >> i) & 1
        dut.midi_in.value = bit
        await Timer(32000, 'ns')

    # Stop bit (1)
    dut.midi_in.value = 1
    await Timer(32000, 'ns')

async def send_midi_message(dut, status, data1, data2):
    """Send a complete 3-byte MIDI message"""
    await send_midi_byte(dut, status)
    await send_midi_byte(dut, data1)
    await send_midi_byte(dut, data2)

async def send_note_on(dut, channel, note, velocity):
    """Send a MIDI Note On message"""
    status = 0x90 | (channel & 0x0F)  # Note On status
    await send_midi_message(dut, status, note & 0x7F, velocity & 0x7F)

async def send_note_off(dut, channel, note):
    """Send a MIDI Note Off message"""
    status = 0x80 | (channel & 0x0F)  # Note Off status
    await send_midi_message(dut, status, note & 0x7F, 0)

async def send_program_change(dut, channel, wave_type):
    """Send a MIDI Program Change message to set wave type"""
    status = 0xC0 | (channel & 0x0F)  # Program Change status
    await send_midi_byte(dut, status)
    await send_midi_byte(dut, wave_type & 0x03)

@cocotb.test()
async def test_single_voice(dut):
    """Test single voice output with different wave types"""
    dut._log.info("Starting single voice test")

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.midi_in.value = 1
    dut.octave_on.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')

    voice_outputs = []
    wave_types = ['Sine', 'Square', 'Sawtooth', 'Triangle']
    test_notes = [60, 64, 67, 72]  # C4, E4, G4, C5

    for wave_idx, (wave_name, note) in enumerate(zip(wave_types, test_notes)):
        dut._log.info(f"Testing {wave_name} wave with note {note}")

        # Set wave type
        await send_program_change(dut, 0, wave_idx)
        await Timer(1000, 'ns')

        # Send note on
        velocity = 7  # Max velocity (3 bits)
        await send_note_on(dut, 0, note, velocity)
        await Timer(1000, 'ns')

        # Capture output - enough samples to see 3-4 periods of the waveform
        # At 48kHz sample rate, note 60 (262Hz) has ~183 samples/period
        voice_data = []
        for _ in range(800):
            # Wait for valid data signal (48kHz sample rate)
            await RisingEdge(dut.clk)
            while dut.data_valid.value == 0:
                await RisingEdge(dut.clk)
            voice_data.append(dut.voice_1_out.value.signed_integer)

        voice_outputs.append((wave_name, note, voice_data))

        # Send note off
        await send_note_off(dut, 0, note)
        await Timer(1000, 'ns')

    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Single Voice Output - Different Wave Types')

    for idx, (wave_name, note, data) in enumerate(voice_outputs):
        ax = axes[idx // 2, idx % 2]
        data_array = np.array(data, dtype=np.int64)
        dut._log.info(f"{wave_name}: min={np.min(data_array)}, max={np.max(data_array)}, mean={np.mean(data_array):.2f}")
        ax.plot(data_array)
        ax.set_title(f'{wave_name} - Note {note}')
        ax.set_xlabel('Sample')
        ax.set_ylabel('Amplitude')
        ax.grid(True)

    plt.tight_layout()
    plt.savefig('synth_test_single_voice.png')
    dut._log.info("Single voice test complete - plot saved")

@cocotb.test()
async def test_polyphony(dut):
    """Test polyphonic operation with multiple voices"""
    dut._log.info("Starting polyphony test")

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.midi_in.value = 1
    dut.octave_on.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')

    # Set wave type to sine
    await send_program_change(dut, 0, 0)
    await Timer(1000, 'ns')

    # Play a C major chord (C4, E4, G4)
    chord_notes = [60, 64, 67]
    dut._log.info(f"Playing chord: {chord_notes}")

    # Send note on for all notes in chord
    for note in chord_notes:
        await send_note_on(dut, 0, note, 7)
        await Timer(500, 'ns')

    # Capture outputs from all active voices - enough to see multiple periods
    voice_data = [[] for _ in range(8)]
    for _ in range(1200):
        # Wait for valid data signal (48kHz sample rate)
        await RisingEdge(dut.clk)
        while dut.data_valid.value == 0:
            await RisingEdge(dut.clk)
        voice_data[0].append(dut.voice_1_out.value.signed_integer)
        voice_data[1].append(dut.voice_2_out.value.signed_integer)
        voice_data[2].append(dut.voice_3_out.value.signed_integer)

    # Send note off for all notes
    for note in chord_notes:
        await send_note_off(dut, 0, note)
        await Timer(500, 'ns')

    # Plot the three voices
    fig, axes = plt.subplots(3, 1, figsize=(12, 8))
    fig.suptitle('Polyphonic Output - C Major Chord')

    for idx in range(3):
        axes[idx].plot(np.array(voice_data[idx]))
        axes[idx].set_title(f'Voice {idx+1} - Note {chord_notes[idx]}')
        axes[idx].set_xlabel('Sample')
        axes[idx].set_ylabel('Amplitude')
        axes[idx].grid(True)

    plt.tight_layout()
    plt.savefig('synth_test_polyphony.png')
    dut._log.info("Polyphony test complete - plot saved")

@cocotb.test()
async def test_octave_mode(dut):
    """Test octave doubling functionality"""
    dut._log.info("Starting octave mode test")

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.midi_in.value = 1
    dut.octave_on.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')

    # Set wave type to sine
    await send_program_change(dut, 0, 0)
    await Timer(1000, 'ns')

    test_note = 60  # C4

    # Test without octave
    dut._log.info(f"Testing note {test_note} WITHOUT octave")
    dut.octave_on.value = 0
    await send_note_on(dut, 0, test_note, 7)
    await Timer(1000, 'ns')

    voice_no_octave = []
    for _ in range(800):
        # Wait for valid data signal (48kHz sample rate)
        await RisingEdge(dut.clk)
        while dut.data_valid.value == 0:
            await RisingEdge(dut.clk)
        voice_no_octave.append(dut.voice_1_out.value.signed_integer)

    await send_note_off(dut, 0, test_note)
    await Timer(1000, 'ns')

    # Test with octave
    dut._log.info(f"Testing note {test_note} WITH octave")
    dut.octave_on.value = 1
    await send_note_on(dut, 0, test_note, 7)
    await Timer(1000, 'ns')

    voice_with_octave = []
    for _ in range(800):
        # Wait for valid data signal (48kHz sample rate)
        await RisingEdge(dut.clk)
        while dut.data_valid.value == 0:
            await RisingEdge(dut.clk)
        voice_with_octave.append(dut.voice_1_out.value.signed_integer)

    await send_note_off(dut, 0, test_note)
    await Timer(1000, 'ns')

    # Plot comparison
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f'Octave Mode Comparison - Note {test_note}')

    axes[0].plot(np.array(voice_no_octave))
    axes[0].set_title('Without Octave Doubling')
    axes[0].set_xlabel('Sample')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(True)

    axes[1].plot(np.array(voice_with_octave))
    axes[1].set_title('With Octave Doubling')
    axes[1].set_xlabel('Sample')
    axes[1].set_ylabel('Amplitude')
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig('synth_test_octave.png')
    dut._log.info("Octave mode test complete - plot saved")

@cocotb.test()
async def test_voice_allocation(dut):
    """Test voice allocation and management"""
    dut._log.info("Starting voice allocation test")

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.midi_in.value = 1
    dut.octave_on.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')

    # Set wave type to sawtooth
    await send_program_change(dut, 0, 2)
    await Timer(1000, 'ns')

    # Play 8 notes sequentially to fill all voices
    notes = [60, 62, 64, 65, 67, 69, 71, 72]
    dut._log.info(f"Playing 8 notes to fill all voices: {notes}")

    for note in notes:
        await send_note_on(dut, 0, note, 7)
        await Timer(500, 'ns')

    # Check ons_out to verify all voices are active
    await Timer(1000, 'ns')
    ons_value = dut.ons_out.value.integer
    dut._log.info(f"Voice active status (ons_out): 0b{ons_value:08b}")

    # Capture all voice outputs - enough to see multiple periods
    all_voices = [[] for _ in range(8)]
    for _ in range(1000):
        # Wait for valid data signal (48kHz sample rate)
        await RisingEdge(dut.clk)
        while dut.data_valid.value == 0:
            await RisingEdge(dut.clk)
        all_voices[0].append(dut.voice_1_out.value.signed_integer)
        all_voices[1].append(dut.voice_2_out.value.signed_integer)
        all_voices[2].append(dut.voice_3_out.value.signed_integer)
        all_voices[3].append(dut.voice_4_out.value.signed_integer)
        all_voices[4].append(dut.voice_5_out.value.signed_integer)
        all_voices[5].append(dut.voice_6_out.value.signed_integer)
        all_voices[6].append(dut.voice_7_out.value.signed_integer)
        all_voices[7].append(dut.voice_8_out.value.signed_integer)

    # Release all notes
    for note in notes:
        await send_note_off(dut, 0, note)
        await Timer(500, 'ns')

    # Verify all voices are released
    ons_value = dut.ons_out.value.integer
    dut._log.info(f"Voice active status after release (ons_out): 0b{ons_value:08b}")

    # Plot all 8 voices
    fig, axes = plt.subplots(4, 2, figsize=(14, 12))
    fig.suptitle('Voice Allocation Test - All 8 Voices')

    for idx in range(8):
        ax = axes[idx // 2, idx % 2]
        ax.plot(np.array(all_voices[idx]))
        ax.set_title(f'Voice {idx+1} - Note {notes[idx]}')
        ax.set_xlabel('Sample')
        ax.set_ylabel('Amplitude')
        ax.grid(True)

    plt.tight_layout()
    plt.savefig('synth_test_voice_allocation.png')
    dut._log.info("Voice allocation test complete - plot saved")


def test_runner():
    """Simulate the synth using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))

    sources = [
        proj_path / "hdl" / "synth.sv",
        proj_path / "hdl" / "sample_clk.sv",
        proj_path / "hdl" / "oscillator.sv",
        proj_path / "hdl" / "sine.sv",
        proj_path / "hdl" / "square.sv",
        proj_path / "hdl" / "sawtooth.sv",
        proj_path / "hdl" / "triangle.sv",
        proj_path / "hdl" / "midi_rx.sv"
    ]

    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "synth"
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters={},
        timescale = ('1ns','1ps'),
        waves=True
    )
    run_test_args = []
    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=test_file,
        test_args=run_test_args,
        waves=True
    )

if __name__ == "__main__":
    test_runner()
