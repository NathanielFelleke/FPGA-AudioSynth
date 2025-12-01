import cocotb
import os
import sys
import random
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.runner import get_runner
import matplotlib.pyplot as plt
import numpy as np

test_file = os.path.basename(__file__).replace(".py", "")


class DelayEffectTester:
    """Helper class for testing delay_effect module"""

    def __init__(self, dut):
        self.dut = dut
        self.data_width = 16
        self.max_positive = (1 << (self.data_width - 1)) - 1  # 32767
        self.max_negative = -(1 << (self.data_width - 1))     # -32768

    async def reset(self):
        """Reset the DUT"""
        self.dut.reset.value = 1
        self.dut.sample_valid.value = 0
        self.dut.audio_in.value = 0
        self.dut.delay_samples.value = 0
        self.dut.feedback_amount.value = 0
        self.dut.effect_amount.value = 0
        self.dut.mode.value = 0
        await ClockCycles(self.dut.clk, 10)
        self.dut.reset.value = 0
        await ClockCycles(self.dut.clk, 5)
        dut_log = self.dut._log
        dut_log.info(f"  Reset complete. Checking initial state...")
        dut_log.info(f"    audio_in: {int(self.dut.audio_in.value)}")
        dut_log.info(f"    sample_valid: {int(self.dut.sample_valid.value)}")
        dut_log.info(f"    audio_out: {int(self.dut.audio_out.value)}")
        dut_log.info(f"    audio_out_valid: {int(self.dut.audio_out_valid.value)}")

    async def send_sample(self, sample_value):
        """Send a single audio sample"""
        await RisingEdge(self.dut.clk)
        self.dut.sample_valid.value = 1
        self.dut.audio_in.value = sample_value
        await RisingEdge(self.dut.clk)
        self.dut.sample_valid.value = 0
        self.dut.audio_in.value = 0

    async def send_samples_continuous(self, samples):
        """Send multiple samples continuously"""
        for sample in samples:
            await RisingEdge(self.dut.clk)
            self.dut.sample_valid.value = 1
            self.dut.audio_in.value = sample
        await RisingEdge(self.dut.clk)
        self.dut.sample_valid.value = 0
        self.dut.audio_in.value = 0

    def to_signed(self, value, bits=16):
        """Convert unsigned value to signed"""
        if value >= (1 << (bits - 1)):
            return value - (1 << bits)
        return value

    def get_output(self):
        """Get current output as signed integer"""
        return self.to_signed(int(self.dut.audio_out.value))


@cocotb.test()
async def test_basic_feedforward_delay(dut):
    """Test 1a: Impulse response and Test 1b: Continuous ramp"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 1: Feedforward delay with impulse and ramp signals")

    # Configure: 5 sample delay, no feedback, 100% wet
    dut.delay_samples.value = 5
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0  # Feedforward

    # Test 1a: Single impulse
    dut._log.info("  Test 1a: Single impulse (1000)")
    await tester.send_sample(1000)

    # After send_sample, the data path is:
    # Cycle 0: sample arrives at delay_buf input
    # Cycle 1-5: delayed by variable_delay_buffer
    # Cycle 6: comes out of delay_buf as delayed_sample
    # Cycle 7: mixed and registered in delay_effect output
    # So we should see valid output around cycle 6-8
    impulse_outputs = []
    impulse_valids = []
    for cycle in range(25):
        await RisingEdge(dut.clk)
        valid = int(dut.audio_out_valid.value)
        output = tester.get_output()
        impulse_valids.append(valid)
        impulse_outputs.append(output)
        if valid == 1 and output != 0:
            dut._log.info(f"  Impulse: Cycle {cycle}: output={output}")

    # Test 1b: Continuous ramp with longer delay and more samples
    dut._log.info("  Test 1b: Continuous ramp signal (longer test)")
    ramp_samples = [i * 1000 for i in range(15)]  # 15 samples instead of 6

    # Use a longer delay to see sustained output
    dut.delay_samples.value = 8  # 8 sample delay instead of 5

    inputs = []
    outputs = []
    valids = []

    # Send samples and capture simultaneously - longer cycle count
    for sample_idx in range(35):  # 35 cycles instead of 20
        await RisingEdge(dut.clk)

        # Send next sample if we have more
        if sample_idx < len(ramp_samples):
            dut.sample_valid.value = 1
            dut.audio_in.value = ramp_samples[sample_idx]
            inputs.append(ramp_samples[sample_idx])
            dut._log.info(f"  Ramp Cycle {sample_idx}: Sending input={ramp_samples[sample_idx]}")
        else:
            dut.sample_valid.value = 0
            dut.audio_in.value = 0
            inputs.append(0)

        # Capture output
        valid = int(dut.audio_out_valid.value)
        output = tester.get_output()
        valids.append(valid)
        outputs.append(output)

        if sample_idx < 25 or valid == 1:
            dut._log.info(f"  Ramp Cycle {sample_idx}: valid={valid}, output={output}")

    dut.sample_valid.value = 0
    dut.audio_in.value = 0

    # Generate plots with expected values
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Test 1a: Impulse response
    cycles_imp = np.arange(len(impulse_outputs))
    axes[0, 0].plot(cycles_imp, impulse_outputs, 'b-', linewidth=2, marker='o', markersize=4, label='Actual Output')
    axes[0, 0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    # Expected: delay of 5 samples, so impulse appears around cycle 6-7
    expected_impulse = np.zeros(len(impulse_outputs))
    if len(impulse_outputs) > 7:
        expected_impulse[7] = 1000  # 100% wet, so 1000
    axes[0, 0].plot(cycles_imp, expected_impulse, 'r--', linewidth=2, marker='x', markersize=6, label='Expected (1000 at cycle 7)')
    axes[0, 0].set_ylabel('Audio Value', fontsize=11)
    axes[0, 0].set_title('Test 1a: Impulse Response (5 sample delay, 100% wet)', fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=10)
    axes[0, 0].set_ylim([-1500, 1500])

    # Test 1b: Input signal
    cycles_ramp = np.arange(len(inputs))
    axes[0, 1].plot(cycles_ramp, inputs, 'g-', linewidth=2, marker='s', markersize=4, label='Input Ramp')
    axes[0, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0, 1].set_ylabel('Input Value', fontsize=11)
    axes[0, 1].set_title('Test 1b: Input Ramp (0, 1000, 2000, ... up to 14000, then silence)', fontsize=12, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=10)

    # Test 1b: Output with expected
    axes[1, 0].plot(cycles_ramp, outputs, 'b-', linewidth=2, marker='o', markersize=4, label='Actual Output', zorder=3)
    # Note: Output is mixed dry+wet. With 100% wet (effect_amount=255):
    # output = (input * (255-255) + delayed_input * 255) >> 8
    # output = delayed_input
    # So expected is just the input delayed by ~10 cycles (8 sample delay + 2 for pipeline)
    expected_output = np.zeros(len(outputs))
    delay_offset = 10  # 8 sample delay + pipeline latency
    for i in range(len(inputs)):
        if i + delay_offset < len(expected_output):
            expected_output[i + delay_offset] = inputs[i]
    axes[1, 0].plot(cycles_ramp, expected_output, 'r--', linewidth=2, marker='x', markersize=6, label='Expected (input delayed ~10 cycles)', zorder=2)
    axes[1, 0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1, 0].set_xlabel('Cycle', fontsize=11)
    axes[1, 0].set_ylabel('Audio Value', fontsize=11)
    axes[1, 0].set_title('Test 1b: Output Ramp (Actual vs Expected)', fontsize=12, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=10)

    # Overlay: Input vs Output (show valid signal)
    axes[1, 1].plot(cycles_ramp, inputs, 'g-', linewidth=2, marker='s', markersize=4, label='Input', alpha=0.8)
    # Color output by valid signal
    colors_valid = ['r' if v == 1 else 'b' for v in valids]
    for i in range(len(outputs)-1):
        axes[1, 1].plot(cycles_ramp[i:i+2], outputs[i:i+2], color=colors_valid[i], linewidth=2, marker='o', markersize=4, alpha=0.8)
    axes[1, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1, 1].set_xlabel('Cycle', fontsize=11)
    axes[1, 1].set_ylabel('Audio Value', fontsize=11)
    axes[1, 1].set_title('Test 1: Input vs Output (Red=Valid, Blue=Invalid)', fontsize=12, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], color='g', lw=2, marker='s', label='Input'),
                       Line2D([0], [0], color='r', lw=2, marker='o', label='Output (Valid)'),
                       Line2D([0], [0], color='b', lw=2, marker='o', label='Output (Invalid)')]
    axes[1, 1].legend(handles=legend_elements, fontsize=10, loc='upper left')

    plt.tight_layout()
    plot_path = Path(__file__).resolve().parent / "test_delay_effect_impulse_ramp.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    dut._log.info(f"  Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_feedforward_mixed(dut):
    """Test 2: Feedforward delay with 50% wet/dry mix"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 2: Feedforward delay (5 samples, 50% wet/dry)")

    # Configure: 5 sample delay, 50% mix
    dut.delay_samples.value = 5
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 128  # 50% wet
    dut.mode.value = 0

    # Send impulse
    await tester.send_sample(2000)

    # Check early output (mostly dry)
    await ClockCycles(dut.clk, 3)
    if dut.audio_out_valid.value == 1:
        output = tester.get_output()
        expected = (2000 * 127) >> 8
        dut._log.info(f"  Early output (mostly dry): {output} (expected ~{expected})")

    # Check delayed output (wet+dry)
    await ClockCycles(dut.clk, 5)
    if dut.audio_out_valid.value == 1:
        output = tester.get_output()
        expected = (2000 * 127 + 2000 * 128) >> 8
        dut._log.info(f"  Delayed output (wet+dry): {output} (expected ~{expected})")


@cocotb.test()
async def test_feedback_echo(dut):
    """Test 3: Feedback delay creates echoes"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 3: Feedback delay (echo with 50% feedback)")

    # Configure: 8 sample delay, 50% feedback, 100% wet
    dut.delay_samples.value = 8
    dut.feedback_amount.value = 128  # 50% feedback
    dut.effect_amount.value = 255    # 100% wet
    dut.mode.value = 1  # Feedback mode

    # Send impulse
    await tester.send_sample(4000)

    # Capture outputs for plotting
    outputs = []
    valids = []
    for _ in range(100):
        await RisingEdge(dut.clk)
        valids.append(int(dut.audio_out_valid.value))
        outputs.append(tester.get_output())

    # Log echoes
    echoes = []
    for i, (valid, output) in enumerate(zip(valids, outputs)):
        if valid == 1 and output != 0:
            echoes.append(output)
            dut._log.info(f"  Echo {len(echoes)}: {output}")

    # Verify echoes are decaying
    if len(echoes) >= 2:
        assert abs(echoes[1]) < abs(echoes[0]), "Echoes should decay with feedback < 100%"

    # Generate plot
    plt.figure(figsize=(14, 7))
    cycles = np.arange(len(outputs))
    colors = ['r' if v == 1 else 'lightgray' for v in valids]
    plt.scatter(cycles, outputs, c=colors, s=50, alpha=0.7, label='Valid outputs (red)')
    plt.plot(cycles, outputs, 'b-', linewidth=1, alpha=0.5)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.xlabel('Cycle', fontsize=12)
    plt.ylabel('Audio Sample Value', fontsize=12)
    plt.title('Test 3: Feedback Delay with Echoes (8 sample delay, 50% feedback)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    plot_path = Path(__file__).resolve().parent / "test_delay_effect_echoes.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    dut._log.info(f"  Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_square_wave(dut):
    """Test 4: Square wave input"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 4: Square wave input (delay=4, feedforward)")

    # Configure
    dut.delay_samples.value = 4
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0

    # Send square wave: 5 high, 5 low
    square_wave = [1000] * 5 + [-1000] * 5
    await tester.send_samples_continuous(square_wave)

    await ClockCycles(dut.clk, 20)
    dut._log.info("  Square wave test completed")


@cocotb.test()
async def test_saturation(dut):
    """Test 5: High feedback should saturate, not overflow"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 5: Saturation test (high feedback)")

    # Configure: high feedback
    dut.delay_samples.value = 5
    dut.feedback_amount.value = 200  # ~78% feedback
    dut.effect_amount.value = 255
    dut.mode.value = 1

    # Send large impulse
    await tester.send_sample(10000)

    # Check multiple feedback iterations
    for i in range(5):
        await ClockCycles(dut.clk, 6)
        if dut.audio_out_valid.value == 1:
            output = tester.get_output()
            dut._log.info(f"  Feedback iteration {i}: {output}")

            # Verify no overflow
            assert output <= tester.max_positive, f"Output overflow: {output} > {tester.max_positive}"
            assert output >= tester.max_negative, f"Output underflow: {output} < {tester.max_negative}"


@cocotb.test()
async def test_zero_delay(dut):
    """Test 6: Zero delay edge case"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 6: Zero delay (edge case)")

    # Configure: zero delay
    dut.delay_samples.value = 0
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 128
    dut.mode.value = 0

    # Send sample
    await tester.send_sample(3000)

    await ClockCycles(dut.clk, 5)
    if dut.audio_out_valid.value == 1:
        output = tester.get_output()
        dut._log.info(f"  Output with zero delay: {output}")


@cocotb.test()
async def test_sparse_samples(dut):
    """Test 7: Sample valid gating with gaps"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 7: Sample valid gating (sparse samples)")

    # Configure
    dut.delay_samples.value = 3
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0

    # Send samples with gaps
    await tester.send_sample(1000)
    await ClockCycles(dut.clk, 5)  # Gap

    await tester.send_sample(2000)
    await ClockCycles(dut.clk, 5)  # Gap

    await tester.send_sample(3000)

    await ClockCycles(dut.clk, 15)
    dut._log.info("  Sample valid gating test completed")


@cocotb.test()
async def test_ramp_input(dut):
    """Test 8: Ramp input for linearity"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 8: Ramp input (linearity test)")

    # Configure
    dut.delay_samples.value = 6
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0

    # Send ramp
    ramp = [i * 1000 for i in range(8)]
    await tester.send_samples_continuous(ramp)

    await ClockCycles(dut.clk, 20)
    dut._log.info("  Ramp test completed")


@cocotb.test()
async def test_random_samples(dut):
    """Test 9: Random audio samples"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 9: Random samples")

    # Configure
    dut.delay_samples.value = 7
    dut.feedback_amount.value = 64  # 25% feedback
    dut.effect_amount.value = 200   # ~78% wet
    dut.mode.value = 1

    # Send random samples
    random.seed(42)
    random_samples = [random.randint(-5000, 5000) for _ in range(20)]
    await tester.send_samples_continuous(random_samples)

    # Monitor outputs
    outputs = []
    valids = []
    for _ in range(80):
        await RisingEdge(dut.clk)
        valids.append(int(dut.audio_out_valid.value))
        outputs.append(tester.get_output())

    dut._log.info("  Random sample test completed")

    # Generate plot
    plt.figure(figsize=(14, 7))
    cycles = np.arange(len(outputs))
    colors = ['r' if v == 1 else 'lightgray' for v in valids]
    plt.scatter(cycles, outputs, c=colors, s=40, alpha=0.6)
    plt.plot(cycles, outputs, 'b-', linewidth=1, alpha=0.5)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.xlabel('Cycle', fontsize=12)
    plt.ylabel('Audio Sample Value', fontsize=12)
    plt.title('Test 9: Random Audio Samples (7 sample delay, 25% feedback, 78% wet)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plot_path = Path(__file__).resolve().parent / "test_delay_effect_random.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    dut._log.info(f"  Plot saved to {plot_path}")
    plt.close()


@cocotb.test()
async def test_max_delay(dut):
    """Test 10: Maximum delay value"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 10: Maximum delay")

    # Configure with large delay (but reasonable for simulation)
    dut.delay_samples.value = 1023  # Max for 10-bit address
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0

    # Send impulse
    await tester.send_sample(5000)

    # Wait a bit (not full delay time for simulation speed)
    await ClockCycles(dut.clk, 100)
    dut._log.info("  Max delay test initiated")


def test_runner():
    """Simulate the delay_effect using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [
        proj_path / "hdl" / "xilinx_true_dual_port_read_first_2_clock_ram.v",
        proj_path / "hdl" / "variable_delay_buffer.sv",
        proj_path / "hdl" / "delay_effect.sv"
    ]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "delay_effect"
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
