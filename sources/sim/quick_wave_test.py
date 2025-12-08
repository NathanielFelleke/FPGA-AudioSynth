import cocotb
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

async def send_midi_byte(dut, byte_data):
    """Send a single MIDI byte with start and stop bits"""
    dut.midi_in.value = 0
    await Timer(32000, 'ns')
    for i in range(7, -1, -1):
        bit = (byte_data >> i) & 1
        dut.midi_in.value = bit
        await Timer(32000, 'ns')
    dut.midi_in.value = 1
    await Timer(32000, 'ns')

async def send_midi_message(dut, status, data1, data2):
    """Send a complete 3-byte MIDI message"""
    await send_midi_byte(dut, status)
    await send_midi_byte(dut, data1)
    await send_midi_byte(dut, data2)

async def send_note_on(dut, channel, note, velocity):
    """Send a MIDI Note On message"""
    status = 0x90 | (channel & 0x0F)
    await send_midi_message(dut, status, note & 0x7F, velocity & 0x7F)

async def send_program_change(dut, channel, wave_type):
    """Send a MIDI Program Change message to set wave type"""
    status = 0xC0 | (channel & 0x0F)
    await send_midi_byte(dut, status)
    await send_midi_byte(dut, wave_type & 0x03)

@cocotb.test()
async def quick_waveform_test(dut):
    """Quick test of all 4 waveform types"""
    dut._log.info("Starting quick waveform test")

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
    test_note = 60  # Middle C

    for wave_idx, wave_name in enumerate(wave_types):
        dut._log.info(f"Testing {wave_name} wave")

        # Set wave type
        await send_program_change(dut, 0, wave_idx)
        await Timer(500, 'ns')

        # Send note on
        await send_note_on(dut, 0, test_note, 7)
        await Timer(500, 'ns')

        # Capture 400 samples (about 2 periods at 262Hz)
        voice_data = []
        for _ in range(400):
            await RisingEdge(dut.clk)
            while dut.data_valid.value == 0:
                await RisingEdge(dut.clk)
            voice_data.append(dut.voice_1_out.value.signed_integer)

        voice_outputs.append((wave_name, voice_data))

    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Quick Waveform Test - Note 60 (Middle C)')

    for idx, (wave_name, data) in enumerate(voice_outputs):
        ax = axes[idx // 2, idx % 2]
        data_array = np.array(data, dtype=np.int64)

        # Log statistics
        dut._log.info(f"{wave_name}: min={np.min(data_array):e}, max={np.max(data_array):e}, mean={np.mean(data_array):.2e}")

        ax.plot(data_array)
        ax.set_title(f'{wave_name}')
        ax.set_xlabel('Sample')
        ax.set_ylabel('Amplitude')
        ax.grid(True)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig('quick_wave_test.png', dpi=150)
    dut._log.info("Quick waveform test complete")


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
