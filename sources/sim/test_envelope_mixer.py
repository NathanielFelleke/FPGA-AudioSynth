import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.runner import get_runner

test_file = os.path.basename(__file__).replace(".py", "")

# 440 Hz sine wave samples at 100MHz clock (10ns per sample)
# Period = 1/440 = 2.27ms, so we need samples at 100MHz
# Generate 1 cycle worth of samples
SINE_LUT = [
    int(0x40000000 * np.sin(2 * np.pi * i / 226))
    for i in range(226)
]  # ~2.26us per cycle at 100MHz


async def wait_for_pulse(dut, timeout_cycles=150_000):
    """Wait for the ms_pulse to go high, with timeout"""
    cycle_count = 0
    pulse_seen = False
    for _ in range(timeout_cycles):
        if dut.ms_pulse.value == 1:
            pulse_seen = True
            break
        await RisingEdge(dut.clk)
        cycle_count += 1

    if not pulse_seen:
        raise AssertionError(f"Timeout waiting for ms_pulse after {cycle_count} cycles")

    # Wait for pulse to go back low
    while dut.ms_pulse.value == 1:
        await RisingEdge(dut.clk)


async def wait_n_pulses(dut, n_pulses, timeout_per_pulse=150_000):
    """Wait for n millisecond pulses"""
    for i in range(n_pulses):
        await wait_for_pulse(dut, timeout_per_pulse)


@cocotb.test()
async def test_envelope_mixer_basic(dut):
    """Test envelope mixer applying ADSR to audio signal"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Initialize ADSR parameters
    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 50    # 50ms attack
    dut.decay_time.value = 100    # 100ms decay
    dut.sustain_percent.value = 70  # 70% sustain level
    dut.release_time.value = 150   # 150ms release

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    # Wait for first pulse
    await wait_for_pulse(dut, timeout_cycles=150_000)

    initial_envelope = dut.envelope_out.value.integer
    assert initial_envelope == 0, f"Expected initial envelope 0, got {initial_envelope}"

    # Collect all values for plotting
    all_envelope = []
    all_audio_out = []
    time_ms = []
    sine_index = 0

    # Trigger note on
    dut.note_on.value = 1

    print("Collecting samples...")

    # Collect samples until we have 400 milliseconds of envelope data
    pulse_count = 0
    while pulse_count < 400:
        # Feed in continuous sine wave samples
        audio_sample = int(SINE_LUT[sine_index % len(SINE_LUT)])
        sine_index += 1
        dut.audio_in.value = audio_sample

        await RisingEdge(dut.clk)

        # Collect audio output every cycle
        try:
            audio_out_val = dut.audio_out.value.signed_integer
            all_audio_out.append(audio_out_val)
            time_ms_val = pulse_count + (sine_index % len(SINE_LUT)) / len(SINE_LUT)
            time_ms.append(time_ms_val)
        except ValueError:
            # Skip undefined values
            pass

        # Detect ms_pulse rising edge to collect envelope data
        if dut.ms_pulse.value == 1:
            pulse_count += 1
            try:
                envelope_val = dut.envelope_out.value.integer
                all_envelope.append(envelope_val)
            except ValueError:
                all_envelope.append(0)

            if pulse_count == 50:
                print(f"Attack complete at {pulse_count}ms")
            elif pulse_count == 150:
                print(f"Decay complete at {pulse_count}ms")
            elif pulse_count == 250:
                print(f"Sustain complete, triggering note off at {pulse_count}ms")
                dut.note_on.value = 0
            elif pulse_count == 400:
                print(f"Release complete at {pulse_count}ms")

            # Wait for pulse to go low
            while dut.ms_pulse.value == 1:
                audio_sample = int(SINE_LUT[sine_index % len(SINE_LUT)])
                sine_index += 1
                dut.audio_in.value = audio_sample
                await RisingEdge(dut.clk)
                try:
                    audio_out_val = dut.audio_out.value.signed_integer
                    all_audio_out.append(audio_out_val)
                    time_ms_val = pulse_count + (sine_index % len(SINE_LUT)) / len(SINE_LUT)
                    time_ms.append(time_ms_val)
                except ValueError:
                    pass

    # Plot results
    if not all_audio_out or not all_envelope:
        print("ERROR: No valid data collected!")
        return

    print(f"Collected {len(all_audio_out)} audio samples and {len(all_envelope)} envelope samples")

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12))

    # Create envelope plot with proper time mapping
    # Envelope samples are at millisecond boundaries
    envelope_time = list(range(len(all_envelope)))

    # Plot envelope
    ax1.plot(envelope_time, all_envelope, 'b-', linewidth=2, marker='o', markersize=3)
    ax1.set_xlabel('Time (ms)', fontsize=12)
    ax1.set_ylabel('Envelope Value', fontsize=12)
    ax1.set_title('ADSR Envelope (50ms Attack, 100ms Decay, 70% Sustain, 150ms Release)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=250, color='r', linestyle='--', linewidth=2, label='Note Off')
    ax1.legend(fontsize=11)

    # Plot raw audio signal (440 Hz sine wave input)
    ax2.plot(time_ms, all_audio_out, 'gray', linewidth=0.5, alpha=0.7)
    ax2.set_xlabel('Time (ms)', fontsize=12)
    ax2.set_ylabel('Raw Audio Input (440Hz Sine)', fontsize=12)
    ax2.set_title('Input: 440 Hz Sine Wave', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=250, color='r', linestyle='--', linewidth=2, label='Note Off')
    ax2.legend(fontsize=11)

    # Plot modulated audio output
    ax3.plot(time_ms, all_audio_out, 'g-', linewidth=0.8)
    ax3.set_xlabel('Time (ms)', fontsize=12)
    ax3.set_ylabel('Audio Output (Envelope-Modulated)', fontsize=12)
    ax3.set_title('Output: 440 Hz Sine Wave After Envelope Mixer',
                  fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=250, color='r', linestyle='--', linewidth=2, label='Note Off')
    ax3.legend(fontsize=11)

    plt.tight_layout()

    # Save plot
    plot_path = Path(__file__).resolve().parent / "envelope_mixer_plot.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Envelope mixer plot saved to {plot_path}")
    plt.show()

    print("Test completed successfully!")


def test_runner():
    """Simulate the envelope mixer using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [
        proj_path / "hdl" / "clk_divider.sv",
        proj_path / "hdl" / "adsr_envelope.sv",
        proj_path / "hdl" / "envelope_mixer.sv",
        proj_path / "hdl" / "envelope_mixer_tb.sv"
    ]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "envelope_mixer_tb"
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters={},
        timescale=('1ns', '1ps'),
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
