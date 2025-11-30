import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.runner import get_runner

test_file = os.path.basename(__file__).replace(".py", "")

# Generate sine wave samples
SAMPLE_RATE = 100e6  # 100 MHz clock
FREQUENCIES = [440, 880, 1320, 1760, 2200, 2640, 3080, 3520]  # Hz for 8 voices
AMPLITUDE = 0x10000000  # ~0.125 of max int32

def generate_sine_samples(frequency, num_samples):
    """Generate sine wave samples at SAMPLE_RATE"""
    t = np.arange(num_samples) / SAMPLE_RATE
    samples = AMPLITUDE * np.sin(2 * np.pi * frequency * t)
    return samples.astype(np.int32)


@cocotb.test()
async def test_voice_mixer_sine_waves(dut):
    """Test voice mixer with sine wave inputs and plot output"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.data_in_valid.value = 0
    for i in range(8):
        dut.voice_in[i].value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Generate sine wave samples for each voice
    num_samples = 100000  # ~1ms of audio at 100MHz
    voice_samples = [
        generate_sine_samples(FREQUENCIES[i], num_samples)
        for i in range(8)
    ]

    # Collect output data
    collected_outputs = []
    collected_valid = []
    sample_indices = [0] * 8

    print("\nFeeding sine wave data and collecting output...")
    print(f"Sampling {num_samples} samples ({num_samples/SAMPLE_RATE*1e3:.2f}ms at 100MHz)")
    print(f"Voice frequencies: {FREQUENCIES} Hz")

    # Feed in samples and collect output
    for sample_idx in range(num_samples + 10):  # +10 to drain pipeline
        dut.data_in_valid.value = 1 if sample_idx < num_samples else 0

        # Set voice inputs
        if sample_idx < num_samples:
            for voice_idx in range(8):
                dut.voice_in[voice_idx].value = int(voice_samples[voice_idx][sample_idx])

        await RisingEdge(dut.clk)

        # Collect output
        if dut.data_out_valid.value == 1:
            output = dut.mixed_out.value.signed_integer
            collected_outputs.append(output)
            collected_valid.append(True)
        else:
            collected_valid.append(False)

    print(f"Collected {len(collected_outputs)} valid output samples\n")

    # Plot results
    if not collected_outputs:
        print("ERROR: No valid output data collected!")
        return

    # Create time array (in microseconds)
    time_us = np.arange(len(collected_outputs)) * 10 / 1000  # 10ns per sample -> us

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Plot 1: Individual voice signals (first ~10 samples to show detail)
    detail_samples = 1000
    detail_time_us = np.arange(detail_samples) * 10 / 1000

    for voice_idx in range(8):
        detail_samples_data = voice_samples[voice_idx][:detail_samples]
        axes[0].plot(
            detail_time_us, detail_samples_data,
            label=f"Voice {voice_idx} ({FREQUENCIES[voice_idx]}Hz)",
            linewidth=1.5, alpha=0.7
        )

    axes[0].set_xlabel('Time (µs)', fontsize=11)
    axes[0].set_ylabel('Sample Value', fontsize=11)
    axes[0].set_title('Individual Voice Sine Waves (First ~10µs)', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=9, loc='upper right')

    # Plot 2: Mixed output waveform
    axes[1].plot(time_us, collected_outputs, 'b-', linewidth=0.8)
    axes[1].set_xlabel('Time (µs)', fontsize=11)
    axes[1].set_ylabel('Mixed Output Value', fontsize=11)
    axes[1].set_title('Voice Mixer Output (All 8 Voices Combined)', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Zoomed in view of output (first 100 samples)
    zoom_samples = 100
    zoom_time_us = time_us[:zoom_samples]
    zoom_output = collected_outputs[:zoom_samples]

    axes[2].plot(zoom_time_us, zoom_output, 'g-', linewidth=1.5, marker='o', markersize=3)
    axes[2].set_xlabel('Time (µs)', fontsize=11)
    axes[2].set_ylabel('Mixed Output Value', fontsize=11)
    axes[2].set_title('Voice Mixer Output - Zoomed (First ~1µs)', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    plot_path = Path(__file__).resolve().parent / "voice_mixer_output.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {plot_path}")
    plt.show()

    # Print statistics
    min_val = min(collected_outputs)
    max_val = max(collected_outputs)
    mean_val = np.mean(collected_outputs)
    std_val = np.std(collected_outputs)

    print(f"\nOutput Statistics:")
    print(f"  Min: {min_val}")
    print(f"  Max: {max_val}")
    print(f"  Mean: {mean_val:.2f}")
    print(f"  Std Dev: {std_val:.2f}")
    print(f"\nTest completed successfully!")


def test_runner():
    """Simulate the voice mixer using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "hdl" / "voice_mixer.sv"]

    build_test_args = ["-Wall"]
    hdl_toplevel = "voice_mixer"

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters={"DATA_WIDTH": 32, "NUM_VOICES": 8},
        timescale=('1ns', '1ps'),
        waves=True
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=test_file,
        waves=True
    )


if __name__ == "__main__":
    test_runner()
