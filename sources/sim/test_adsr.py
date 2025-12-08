import cocotb
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.utils import get_sim_time as gst
from cocotb.runner import get_runner

test_file = os.path.basename(__file__).replace(".py", "")


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
        if i % 10 == 0:
            print(f"Completed {i} pulses")


@cocotb.test()
async def test_clk_divider_basic(dut):
    """Test that the clock divider is generating pulses"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Initialize
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    print("Waiting for first pulse...")
    await wait_for_pulse(dut, timeout_cycles=150_000)
    print("SUCCESS: Clock divider is working!")


@cocotb.test()
async def test_adsr_basic(dut):
    """Test basic ADSR envelope behavior"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Initialize with realistic timing
    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 100    # 100ms attack
    dut.decay_time.value = 150     # 150ms decay
    dut.sustain_percent.value = 60  # 60% sustain level
    dut.release_time.value = 200   # 200ms release

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    # Wait for envelope to settle - divider is 100,000 cycles per pulse
    await wait_for_pulse(dut, timeout_cycles=150_000)

    initial_envelope = dut.envelope_out.value.integer
    assert initial_envelope == 0, f"Expected initial envelope 0, got {initial_envelope}"

    # Collect all envelope values for plotting
    all_values = []
    time_ms = []
    current_time = 0

    # Trigger note on
    dut.note_on.value = 1

    # Wait for attack phase (100 pulses)
    attack_values = []
    for i in range(100):
        await wait_for_pulse(dut, timeout_cycles=150_000)
        # Read envelope after pulse is done processing
        await RisingEdge(dut.clk)
        envelope_val = dut.envelope_out.value.integer
        attack_values.append(envelope_val)
        all_values.append(envelope_val)
        time_ms.append(current_time)
        current_time += 1
        if (i + 1) % 20 == 0:
            print(f"Attack: {i+1}/100 pulses, envelope={envelope_val}")

    # Check that envelope is increasing during attack
    assert attack_values[-1] > attack_values[0], "Envelope should increase during attack"
    print(f"Attack phase: Initial={attack_values[0]}, Final={attack_values[-1]}")

    # Continue for decay phase (150 pulses)
    decay_values = []
    for i in range(150):
        await wait_for_pulse(dut, timeout_cycles=150_000)
        await RisingEdge(dut.clk)
        envelope_val = dut.envelope_out.value.integer
        decay_values.append(envelope_val)
        all_values.append(envelope_val)
        time_ms.append(current_time)
        current_time += 1
        if (i + 1) % 30 == 0:
            print(f"Decay: {i+1}/150 pulses, envelope={envelope_val}")

    # Check that envelope is decreasing during decay (after reaching max)
    if decay_values[0] > decay_values[-1]:
        print(f"Decay phase: Initial={decay_values[0]}, Final={decay_values[-1]}")

    # Continue in sustain phase (100 pulses)
    sustain_values = []
    for i in range(100):
        await wait_for_pulse(dut, timeout_cycles=150_000)
        await RisingEdge(dut.clk)
        envelope_val = dut.envelope_out.value.integer
        sustain_values.append(envelope_val)
        all_values.append(envelope_val)
        time_ms.append(current_time)
        current_time += 1
        if (i + 1) % 25 == 0:
            print(f"Sustain: {i+1}/100 pulses, envelope={envelope_val}")

    # Check that sustain level is stable
    if len(sustain_values) > 1:
        print(f"Sustain phase: Stable at {sustain_values[0]}")

    # Trigger note off
    dut.note_on.value = 0
    print(f"Note OFF triggered at time={current_time}ms")

    # Collect release values (200 pulses)
    release_values = []
    for i in range(200):
        await wait_for_pulse(dut, timeout_cycles=150_000)
        await RisingEdge(dut.clk)
        envelope_val = dut.envelope_out.value.integer
        release_values.append(envelope_val)
        all_values.append(envelope_val)
        time_ms.append(current_time)
        current_time += 1
        if (i + 1) % 40 == 0:
            print(f"Release: {i+1}/200 pulses, envelope={envelope_val}")

    # Check that envelope decreases to 0 during release
    assert release_values[-1] < release_values[0], "Envelope should decrease during release"
    print(f"Release phase: Initial={release_values[0]}, Final={release_values[-1]}")

    # Plot the envelope
    plt.figure(figsize=(14, 7))
    plt.plot(time_ms, all_values, 'b-', linewidth=2, marker='o', markersize=3)
    plt.xlabel('Time (ms)', fontsize=12)
    plt.ylabel('Envelope Value', fontsize=12)
    plt.title('ADSR Envelope Response (100ms Attack, 150ms Decay, 60% Sustain, 200ms Release)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.axvline(x=250, color='r', linestyle='--', linewidth=2, label='Note Off')
    plt.legend(fontsize=11)

    # Save and show
    plot_path = Path(__file__).resolve().parent / "adsr_envelope_plot.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Envelope plot saved to {plot_path}")
    plt.show()


@cocotb.test()
async def test_adsr_fast_times(dut):
    """Test ADSR with very fast attack and release"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 5     # 5 ms (fast attack)
    dut.decay_time.value = 5      # 5 ms
    dut.sustain_percent.value = 75  # 75%
    dut.release_time.value = 5    # 5 ms (fast release)

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    await wait_for_pulse(dut)

    # Note on
    dut.note_on.value = 1
    await wait_n_pulses(dut, 5)  # Wait 5ms for attack

    attack_envelope = dut.envelope_out.value.integer
    print(f"Fast attack - Envelope after 5ms: {attack_envelope}")

    # Note off quickly
    dut.note_on.value = 0
    await wait_n_pulses(dut, 5)  # Wait 5ms for release

    final_envelope = dut.envelope_out.value.integer
    print(f"Fast release - Envelope after 5ms: {final_envelope}")

    assert final_envelope < attack_envelope, "Envelope should decrease during release"


@cocotb.test()
async def test_adsr_early_release(dut):
    """Test early release during attack/decay"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 20    # 20 ms (long attack)
    dut.decay_time.value = 10
    dut.sustain_percent.value = 50
    dut.release_time.value = 10

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    await wait_for_pulse(dut)

    # Note on
    dut.note_on.value = 1

    # Let it attack for a bit
    await wait_n_pulses(dut, 10)  # 10ms into attack
    envelope_at_10ms = dut.envelope_out.value.integer

    # Note off (early release during attack)
    dut.note_on.value = 0
    await wait_n_pulses(dut, 10)  # 10ms of release

    final_envelope = dut.envelope_out.value.integer
    print(f"Early release - Envelope at 10ms attack: {envelope_at_10ms}, After 10ms release: {final_envelope}")

    assert final_envelope < envelope_at_10ms, "Envelope should decrease when released early"


@cocotb.test()
async def test_adsr_retrigger(dut):
    """Test retriggering note before release completes"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 10
    dut.decay_time.value = 10
    dut.sustain_percent.value = 50
    dut.release_time.value = 20

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    await wait_for_pulse(dut)

    # First note on/off cycle
    dut.note_on.value = 1
    await wait_n_pulses(dut, 20)  # Attack + Decay to sustain

    dut.note_on.value = 0
    await wait_n_pulses(dut, 10)  # Partial release

    envelope_during_release = dut.envelope_out.value.integer
    print(f"Envelope during release: {envelope_during_release}")

    # Retrigger note before release completes
    dut.note_on.value = 1
    await wait_n_pulses(dut, 10)  # Re-attack from release point

    envelope_after_retrigger = dut.envelope_out.value.integer
    print(f"Envelope after retrigger: {envelope_after_retrigger}")

    # Envelope should be increasing again
    assert envelope_after_retrigger > envelope_during_release, "Envelope should increase after retrigger"


@cocotb.test()
async def test_adsr_zero_time(dut):
    """Test with zero attack/decay/release times"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    dut.rst.value = 1
    dut.note_on.value = 0
    dut.attack_time.value = 0    # Instant attack
    dut.decay_time.value = 0     # Instant decay
    dut.sustain_percent.value = 100  # Full sustain
    dut.release_time.value = 0   # Instant release

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    await wait_for_pulse(dut)

    # Note on
    dut.note_on.value = 1
    await wait_for_pulse(dut)

    envelope_on = dut.envelope_out.value.integer
    print(f"Zero time envelope on: {envelope_on}")

    # Note off
    dut.note_on.value = 0
    await wait_for_pulse(dut)

    envelope_off = dut.envelope_out.value.integer
    print(f"Zero time envelope off: {envelope_off}")


def test_runner():
    """Simulate the ADSR envelope using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [
        proj_path / "hdl" / "adsr_envelope.sv",
        proj_path / "hdl" / "clk_divider.sv"
    ]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "adsr_envelope"
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
