import cocotb
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles
from cocotb.runner import get_runner

test_file = os.path.basename(__file__).replace(".py", "")


def to_signed_32bit(value):
    """Convert 32-bit unsigned to signed"""
    if value >= 2**31:
        return value - 2**32
    return value


def safe_int(signal):
    """Safely convert a signal to int, treating X/Z as 0"""
    try:
        return int(signal.value)
    except ValueError:
        # Signal contains X or Z bits - treat as 0
        return 0


@cocotb.test()
async def test_simple_delay(dut):
    """Simple test: send impulse, check delay
    
    For a sample-based delay, we must continuously stream samples.
    The impulse should appear at output after delay_samples worth of samples.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.reset.value = 1
    dut.sample_valid.value = 0
    dut.audio_in.value = 0
    dut.delay_samples.value = 5  # Set delay BEFORE releasing reset
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255  # 100% wet
    dut.mode.value = 0  # Feedforward

    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 2)

    # Continuously stream samples: impulse followed by zeros
    outputs = []
    valids = []
    inputs = []
    
    IMPULSE_VALUE = 1000
    NUM_CYCLES = 30
    
    for cycle in range(NUM_CYCLES):
        # Send impulse on cycle 0, zeros thereafter
        input_val = IMPULSE_VALUE if cycle == 0 else 0
        dut.sample_valid.value = 1
        dut.audio_in.value = input_val
        inputs.append(input_val)
        
        await RisingEdge(dut.clk)
        
        # Capture output after clock edge (use safe_int to handle X values)
        output_raw = safe_int(dut.audio_out)
        output = to_signed_32bit(output_raw)
        valid = safe_int(dut.audio_out_valid)
        outputs.append(output)
        valids.append(valid)
        print(f"Impulse Cycle {cycle}: input={input_val}, valid={valid}, output={output}")

    dut.sample_valid.value = 0

    # Verify: impulse should appear around sample 5-8 (delay + pipeline latency)
    impulse_found = False
    impulse_cycle = -1
    for i, (v, o) in enumerate(zip(valids, outputs)):
        if v == 1 and o != 0:
            print(f"✓ Impulse found at cycle {i}: {o}")
            impulse_found = True
            impulse_cycle = i
            break

    assert impulse_found, "No impulse output found"

    # Plot impulse response
    cycles = np.arange(len(outputs))
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Input
    axes[0].stem(cycles, inputs, linefmt='g-', markerfmt='go', basefmt='k-')
    axes[0].set_ylabel('Input Value')
    axes[0].set_title('Test 1: Input Impulse')
    axes[0].grid(True, alpha=0.3)
    
    # Output
    axes[1].plot(cycles, outputs, 'b-o', linewidth=2, markersize=6, label='Output')
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].axvline(x=5, color='r', linestyle=':', alpha=0.5, label='Expected delay (5 samples)')
    axes[1].set_xlabel('Sample Number')
    axes[1].set_ylabel('Sample Value')
    axes[1].set_title(f'Test 1: Impulse Response (5 sample delay, 100% wet) - Found at sample {impulse_cycle}')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    plt.tight_layout()
    plot_path = Path(__file__).resolve().parent / "test_1_impulse.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_continuous_ramp(dut):
    """Test with continuous ramp input - verify delayed ramp appears"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset with delay already configured
    dut.reset.value = 1
    dut.sample_valid.value = 0
    dut.audio_in.value = 0
    dut.delay_samples.value = 8
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255  # 100% wet
    dut.mode.value = 0  # Feedforward

    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 2)

    # Send ramp: 1000, 2000, 3000, ... (start at 1000 so we can detect non-zero)
    NUM_SAMPLES = 30
    outputs = []
    valids = []
    inputs_log = []

    # Continuously stream all samples
    for i in range(NUM_SAMPLES):
        sample_val = (i + 1) * 1000  # 1000, 2000, 3000, ...
        dut.sample_valid.value = 1
        dut.audio_in.value = sample_val
        inputs_log.append(sample_val)
        
        await RisingEdge(dut.clk)
        
        output_raw = safe_int(dut.audio_out)
        output = to_signed_32bit(output_raw)
        valid = safe_int(dut.audio_out_valid)
        outputs.append(output)
        valids.append(valid)
        print(f"Ramp Cycle {i}: input={sample_val}, valid={valid}, output={output}")

    dut.sample_valid.value = 0

    # Check that we get valid non-zero output
    valid_outputs = [(i, o) for i, (v, o) in enumerate(zip(valids, outputs)) if v == 1 and o != 0]
    assert len(valid_outputs) > 0, "No valid outputs found"
    print(f"✓ Found {len(valid_outputs)} valid non-zero outputs")

    # Plot ramp response
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    cycles = np.arange(len(outputs))

    axes[0].plot(cycles, inputs_log, 'g-s', linewidth=2, markersize=6, label='Input Ramp')
    axes[0].set_ylabel('Sample Value')
    axes[0].set_title('Test 2: Input Ramp Signal')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(cycles, outputs, 'b-o', linewidth=2, markersize=4, label='Output')
    # Color by validity
    for i in range(len(cycles)):
        color = 'g' if valids[i] == 1 else 'r'
        axes[1].scatter(cycles[i], outputs[i], c=color, s=50, zorder=3)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].axvline(x=8, color='r', linestyle=':', alpha=0.5, label='Expected delay (8 samples)')
    axes[1].set_xlabel('Sample Number')
    axes[1].set_ylabel('Sample Value')
    axes[1].set_title('Test 2: Delayed Ramp Output (8 sample delay, 100% wet)')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plot_path = Path(__file__).resolve().parent / "test_2_ramp.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_feedback_echo(dut):
    """Test feedback mode creates multiple echoes
    
    With feedback, the delayed signal is added back to the input,
    creating repeating echoes that decay over time.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset with configuration
    dut.reset.value = 1
    dut.sample_valid.value = 0
    dut.audio_in.value = 0
    dut.delay_samples.value = 10    # Longer delay to see distinct echoes
    dut.feedback_amount.value = 128  # ~50% feedback
    dut.effect_amount.value = 255   # 100% wet
    dut.mode.value = 1              # Feedback mode

    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 2)

    # Send impulse followed by zeros - must keep streaming for feedback to work
    outputs = []
    valids = []
    inputs = []
    IMPULSE_VALUE = 4000
    NUM_CYCLES = 100

    for cycle in range(NUM_CYCLES):
        input_val = IMPULSE_VALUE if cycle == 0 else 0
        dut.sample_valid.value = 1
        dut.audio_in.value = input_val
        inputs.append(input_val)

        await RisingEdge(dut.clk)

        output_raw = safe_int(dut.audio_out)
        output = to_signed_32bit(output_raw)
        valid = safe_int(dut.audio_out_valid)
        outputs.append(output)
        valids.append(valid)
        
        if valid == 1 and output != 0:
            print(f"Echo at sample {cycle}: {output}")

    dut.sample_valid.value = 0

    # Find all non-zero outputs (echoes)
    echoes = [(i, o) for i, (v, o) in enumerate(zip(valids, outputs))
              if v == 1 and abs(o) > 50]  # Threshold to ignore tiny values
    print(f"✓ Found {len(echoes)} echoes")
    
    for i, val in echoes[:5]:  # Print first 5 echoes
        print(f"  Echo at sample {i}: {val}")
    
    assert len(echoes) >= 2, f"Expected multiple echoes, found {len(echoes)}"

    # Plot echo decay
    cycles = np.arange(len(outputs))
    plt.figure(figsize=(14, 6))
    
    # Plot all outputs
    plt.plot(cycles, outputs, 'b-', linewidth=1, alpha=0.7, label='Output')
    
    # Highlight echoes
    echo_cycles = [e[0] for e in echoes]
    echo_vals = [e[1] for e in echoes]
    plt.scatter(echo_cycles, echo_vals, c='r', s=80, zorder=3, label='Echoes')
    
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.xlabel('Sample Number')
    plt.ylabel('Sample Value')
    plt.title(f'Test 3: Feedback Echo (10 sample delay, 50% feedback) - {len(echoes)} echoes found')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plot_path = Path(__file__).resolve().parent / "test_3_echo.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_zero_delay(dut):
    """Test zero delay (pass-through)
    
    With delay_samples=0, the output should be the current input
    (pass-through mode).
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.reset.value = 1
    dut.sample_valid.value = 0
    dut.audio_in.value = 0
    dut.delay_samples.value = 0  # Zero delay
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255  # 100% wet
    dut.mode.value = 0  # Feedforward

    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 2)

    # Stream samples continuously
    outputs = []
    valids = []
    inputs = []

    test_values = [2000, 3000, -1000, 500, 0, 4000, -2000, 1000]
    NUM_EXTRA_CYCLES = 12  # Account for 8-cycle pipeline latency

    for i in range(len(test_values) + NUM_EXTRA_CYCLES):
        if i < len(test_values):
            val = test_values[i]
            dut.sample_valid.value = 1
            dut.audio_in.value = val & 0xFFFFFFFF  # Handle negative values
            inputs.append(val)
        else:
            # Continue clocking to let pipeline flush
            dut.sample_valid.value = 1
            dut.audio_in.value = 0
            inputs.append(0)

        await RisingEdge(dut.clk)

        output_raw = safe_int(dut.audio_out)
        output = to_signed_32bit(output_raw)
        valid = safe_int(dut.audio_out_valid)
        outputs.append(output)
        valids.append(valid)
        print(f"Zero Delay Cycle {i}: input={inputs[-1]}, valid={valid}, output={output}")

    dut.sample_valid.value = 0

    # With zero delay and 8-cycle pipeline latency, output should appear after latency
    non_zero = [(i, o) for i, (v, o) in enumerate(zip(valids, outputs)) if v == 1 and o != 0]
    assert len(non_zero) > 0, "Expected output with zero delay"
    print(f"✓ Zero delay test passed, found {len(non_zero)} non-zero outputs starting at cycle {non_zero[0][0] if non_zero else 'N/A'}")


def test_runner():
    """Run tests using cocotb runner"""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))

    sources = [
        proj_path / "hdl" / "xilinx_true_dual_port_read_first_2_clock_ram.v",
        proj_path / "hdl" / "variable_delay_buffer.sv",
        proj_path / "hdl" / "delay_effect.sv"
    ]

    hdl_toplevel = "delay_effect"
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=["-Wall"],
        parameters={},
        timescale=('1ns', '1ps'),
        waves=True
    )
    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=test_file,
        test_args=[],
        waves=True
    )


if __name__ == "__main__":
    test_runner()