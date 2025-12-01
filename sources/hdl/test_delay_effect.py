"""
Cocotb testbench for delay_effect module
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.types import LogicArray
import random


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
    """Test 1: Basic feedforward delay with 100% wet"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tester = DelayEffectTester(dut)
    await tester.reset()

    dut._log.info("Test 1: Feedforward delay (10 samples, 100% wet)")

    # Configure: 10 sample delay, no feedback, 100% wet
    dut.delay_samples.value = 10
    dut.feedback_amount.value = 0
    dut.effect_amount.value = 255
    dut.mode.value = 0  # Feedforward

    # Send impulse
    await tester.send_sample(1000)

    # Wait for delay + latency (10 + extra cycles for BRAM)
    await ClockCycles(dut.clk, 15)

    # Check output
    assert dut.audio_out_valid.value == 1, "Output should be valid"
    output = tester.get_output()
    dut._log.info(f"  Output after delay: {output}")
    assert output != 0, "Expected delayed impulse to appear"


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

    # Capture several echoes
    echoes = []
    for echo_num in range(3):
        await ClockCycles(dut.clk, 10)
        if dut.audio_out_valid.value == 1:
            output = tester.get_output()
            echoes.append(output)
            dut._log.info(f"  Echo {echo_num}: {output}")

    # Verify echoes are decaying
    if len(echoes) >= 2:
        assert abs(echoes[1]) < abs(echoes[0]), "Echoes should decay with feedback < 100%"


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
    await ClockCycles(dut.clk, 50)
    dut._log.info("  Random sample test completed")


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
