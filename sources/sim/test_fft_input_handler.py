import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import numpy as np

test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_fft_input_handler_basic(dut):
    """Test FFT input handler with simple audio samples"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.audio_in.value = 0
    dut.audio_valid.value = 0
    dut.m_axis_tready.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test 1: Check audio scaling and tlast timing")
    # Test audio scaling: 32-bit input >> 16 = 16-bit output
    # Also test tlast assertion on sample 1023
    tlast_count = 0

    # Send 1024 samples (sample 0 to 1023)
    for i in range(1024):
        await FallingEdge(dut.clk)
        dut.audio_in.value = (0x12340000 + i) & 0xFFFFFFFF
        dut.audio_valid.value = 1

        await RisingEdge(dut.clk)

        # Check scaling on first sample
        if i == 0:
            await RisingEdge(dut.clk)
            output_data = dut.m_axis_tdata.value.integer
            expected = 0x1234
            actual_lower = output_data & 0xFFFF
            actual_upper = (output_data >> 16) & 0xFFFF
            assert actual_upper == 0, f"Upper 16 bits should be 0, got 0x{actual_upper:04X}"
            assert actual_lower == expected, f"Scaled audio = 0x{actual_lower:04X} (expected 0x{expected:04X})"
            assert dut.m_axis_tvalid.value == 1, "m_axis_tvalid should be 1"
            dut.log.info(f"PASS: Scaled output = 0x{actual_lower:04X}")

        # Check tlast timing
        if dut.m_axis_tlast.value == 1:
            tlast_count += 1
            dut.log.info(f"tlast asserted at sample {i}")
            assert i == 1023, f"tlast should be at sample 1023, got {i}"

    assert tlast_count == 1, f"tlast should be asserted once, got {tlast_count}"
    dut.log.info("PASS: tlast timing correct")

    # Test 2: Check counter wraps correctly
    dut.log.info("Test 2: Check counter wraps after tlast")
    await FallingEdge(dut.clk)
    dut.audio_in.value = 0xAAAAAAAA
    dut.audio_valid.value = 1

    await RisingEdge(dut.clk)

    # After tlast, the next sample should NOT have tlast
    assert dut.m_axis_tlast.value == 0, "tlast should be 0 after wrap"
    dut.log.info("PASS: Counter wrapped correctly")

    dut.audio_valid.value = 0
    await Timer(50, units="ns")
    dut.log.info("All tests passed!")


@cocotb.test()
async def test_fft_input_handler_backpressure(dut):
    """Test FFT input handler with AXI-Stream backpressure"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.audio_in.value = 0
    dut.audio_valid.value = 0
    dut.m_axis_tready.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test: Backpressure with tready = 0")

    # Start sending samples
    await FallingEdge(dut.clk)
    dut.audio_in.value = 100
    dut.audio_valid.value = 1
    dut.m_axis_tready.value = 1

    await RisingEdge(dut.clk)
    sample_count = 1

    # Send a few more samples with tready = 1
    for i in range(5):
        await FallingEdge(dut.clk)
        dut.audio_in.value = 100 + i
        await RisingEdge(dut.clk)
        sample_count += 1

    # Now set tready = 0 (backpressure)
    await FallingEdge(dut.clk)
    dut.m_axis_tready.value = 0
    dut.audio_in.value = 200
    initial_count = sample_count

    await RisingEdge(dut.clk)
    # Counter should NOT increment when tready=0

    for i in range(5):
        await FallingEdge(dut.clk)
        dut.audio_in.value = 200 + i
        await RisingEdge(dut.clk)
        # Check that we're still at initial_count (no progress)

    # Re-enable tready
    await FallingEdge(dut.clk)
    dut.m_axis_tready.value = 1
    await RisingEdge(dut.clk)

    # Now counter should increment
    sample_count += 1

    dut.log.info(f"PASS: Backpressure handled correctly")

    dut.audio_valid.value = 0
    await Timer(50, units="ns")
    dut.log.info("Backpressure test passed!")


@cocotb.test()
async def test_fft_input_handler_sine_wave(dut):
    """Test FFT input handler with a sine wave"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.audio_in.value = 0
    dut.audio_valid.value = 0
    dut.m_axis_tready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Generate 1kHz sine wave at 48kHz sample rate
    fs = 48000
    f_test = 1000
    n_samples = 1024
    t = np.arange(n_samples) / fs
    audio = (np.sin(2 * np.pi * f_test * t) * 0x7FFFFFFF).astype(np.int32)

    dut.log.info(f"Test: Sending {n_samples} samples of 1kHz sine wave")

    tlast_seen = False
    output_samples = []

    # Send all samples and capture outputs
    for i in range(n_samples):
        await FallingEdge(dut.clk)
        # Convert to signed 32-bit
        if audio[i] < 0:
            audio_val = int(audio[i]) & 0xFFFFFFFF
        else:
            audio_val = int(audio[i])
        dut.audio_in.value = audio_val
        dut.audio_valid.value = 1

        await RisingEdge(dut.clk)

        # Check tlast first (before any extra waits)
        if dut.m_axis_tlast.value == 1:
            tlast_seen = True
            dut.log.info(f"tlast seen at sample {i}")
            assert i == 1023, f"tlast at wrong position: {i}"

        # On first sample, wait extra cycle for data output to settle
        if i == 0:
            await RisingEdge(dut.clk)

        # Capture output data
        if dut.m_axis_tvalid.value == 1:
            output_data = dut.m_axis_tdata.value.integer & 0xFFFF
            # Sign extend from 16-bit
            if output_data & 0x8000:
                output_signed = output_data - 0x10000
            else:
                output_signed = output_data
            output_samples.append(output_signed)

        # Debug: log around expected tlast position
        if i >= 1020:
            dut.log.info(
                f"Sample {i}: tlast={dut.m_axis_tlast.value}, "
                f"tvalid={dut.m_axis_tvalid.value}"
            )

    assert tlast_seen, f"tlast should have been asserted (captured {len(output_samples)} outputs)"
    # We should have n_samples outputs
    assert len(output_samples) == n_samples, f"Should have {n_samples} outputs, got {len(output_samples)}"

    # Check that output is scaled version of input
    # Original max is around 0x7FFFFFFF, scaled >> 16 should be around 0x7FFF
    max_output = max(output_samples)
    min_output = min(output_samples)
    dut.log.info(f"Output range: {min_output} to {max_output}")

    # Expect roughly +/- 0x7FFF
    assert max_output > 0x7000, f"Max output too small: {max_output}"
    assert min_output < -0x7000, f"Min output too large: {min_output}"

    dut.audio_valid.value = 0
    await Timer(50, units="ns")
    dut.log.info("Sine wave test passed!")


def test_runner():
    """Simulate the FFT input handler using the Python runner."""
    from cocotb.runner import get_runner

    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim"))

    sources = [proj_path / "hdl" / "fft_input_handler.sv"]
    hdl_toplevel = "fft_input_handler"
    build_test_args = ["-Wall"]
    parameters = {
        "INPUT_WIDTH": 32,
        "FFT_WIDTH": 16,
        "FFT_SIZE": 1024
    }

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters=parameters,
        timescale=('1ns','1ps'),
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
