import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_fft_bin_filter_basic(dut):
    """Test FFT bin filter passes only first 512 bins"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.fft_data.value = 0
    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test 1: Send 1024 bins, expect only 512 valid outputs")

    valid_count = 0
    last_seen = False
    last_bin_num = -1

    # Send 1024 FFT bins
    for bin_num in range(1024):
        await FallingEdge(dut.clk)
        # Use bin number as data for easy verification
        dut.fft_data.value = bin_num
        dut.fft_valid.value = 1
        dut.fft_last.value = 1 if bin_num == 1023 else 0

        await RisingEdge(dut.clk)

        # Check output
        if dut.out_valid.value == 1:
            valid_count += 1
            out_data = dut.out_data.value.integer
            assert out_data == bin_num, f"Data mismatch at bin {bin_num}: got {out_data}"

            if dut.out_last.value == 1:
                last_seen = True
                last_bin_num = bin_num
                dut.log.info(f"out_last asserted at bin {bin_num}")

    assert valid_count == 512, f"Expected 512 valid outputs, got {valid_count}"
    assert last_seen, "out_last should have been asserted"
    assert last_bin_num == 511, f"out_last should be at bin 511, got {last_bin_num}"

    dut.log.info(f"PASS: {valid_count} valid outputs, out_last at bin {last_bin_num}")

    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await Timer(50, units="ns")
    dut.log.info("Basic test passed!")


@cocotb.test()
async def test_fft_bin_filter_multiple_frames(dut):
    """Test FFT bin filter with multiple FFT frames"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.fft_data.value = 0
    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test 2: Send 3 frames of 1024 bins each")

    for frame in range(3):
        dut.log.info(f"Frame {frame}")
        valid_count = 0
        last_seen = False

        for bin_num in range(1024):
            await FallingEdge(dut.clk)
            dut.fft_data.value = (frame << 16) | bin_num
            dut.fft_valid.value = 1
            dut.fft_last.value = 1 if bin_num == 1023 else 0

            await RisingEdge(dut.clk)

            if dut.out_valid.value == 1:
                valid_count += 1
                out_data = dut.out_data.value.integer
                expected = (frame << 16) | bin_num
                assert out_data == expected, f"Frame {frame} bin {bin_num}: got {out_data}, expected {expected}"

                if dut.out_last.value == 1:
                    last_seen = True
                    assert bin_num == 511, f"Frame {frame}: out_last at wrong bin {bin_num}"

        assert valid_count == 512, f"Frame {frame}: Expected 512 valid, got {valid_count}"
        assert last_seen, f"Frame {frame}: out_last not seen"
        dut.log.info(f"PASS: Frame {frame} correct")

    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await Timer(50, units="ns")
    dut.log.info("Multiple frames test passed!")


@cocotb.test()
async def test_fft_bin_filter_sparse_valid(dut):
    """Test FFT bin filter with gaps in valid signal"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.fft_data.value = 0
    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test 3: Send bins with gaps in valid signal")

    valid_count = 0
    bin_num = 0

    while bin_num < 1024:
        await FallingEdge(dut.clk)

        # Send valid every other cycle
        if bin_num % 2 == 0:
            dut.fft_data.value = bin_num
            dut.fft_valid.value = 1
            dut.fft_last.value = 1 if bin_num == 1023 else 0

            await RisingEdge(dut.clk)

            if dut.out_valid.value == 1:
                valid_count += 1
                out_data = dut.out_data.value.integer
                assert out_data == bin_num, f"Bin {bin_num}: got {out_data}"

            bin_num += 1
        else:
            # Gap - no valid
            dut.fft_valid.value = 0
            dut.fft_last.value = 0
            await RisingEdge(dut.clk)
            # Counter should not increment when valid=0
            bin_num += 1

    # We sent all 1024 bins, should get 512 valid
    assert valid_count == 512, f"Expected 512 valid outputs, got {valid_count}"
    dut.log.info(f"PASS: {valid_count} valid outputs with sparse valid")

    dut.fft_valid.value = 0
    await Timer(50, units="ns")
    dut.log.info("Sparse valid test passed!")


@cocotb.test()
async def test_fft_bin_filter_edge_cases(dut):
    """Test edge cases: bin 511 and bin 512"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.fft_data.value = 0
    dut.fft_valid.value = 0
    dut.fft_last.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    dut.log.info("Test 4: Check boundary at bins 511 and 512")

    # Send bins 0-514 to see boundary behavior
    for bin_num in range(515):
        await FallingEdge(dut.clk)
        dut.fft_data.value = bin_num
        dut.fft_valid.value = 1
        dut.fft_last.value = 0

        await RisingEdge(dut.clk)

        if bin_num < 512:
            # Should be valid
            assert dut.out_valid.value == 1, f"Bin {bin_num} should be valid"

            if bin_num == 511:
                assert dut.out_last.value == 1, "Bin 511 should have out_last=1"
                dut.log.info("PASS: Bin 511 has out_last=1")
            else:
                assert dut.out_last.value == 0, f"Bin {bin_num} should have out_last=0"
        else:
            # Should NOT be valid
            assert dut.out_valid.value == 0, f"Bin {bin_num} should NOT be valid"
            assert dut.out_last.value == 0, f"Bin {bin_num} should have out_last=0"
            if bin_num == 512:
                dut.log.info("PASS: Bin 512 is NOT valid")

    dut.fft_valid.value = 0
    await Timer(50, units="ns")
    dut.log.info("Edge cases test passed!")


def test_runner():
    """Simulate the FFT bin filter using the Python runner."""
    from cocotb.runner import get_runner

    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim"))

    sources = [proj_path / "hdl" / "fft_bin_filter.sv"]
    hdl_toplevel = "fft_bin_filter"
    build_test_args = ["-Wall"]
    parameters = {}

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
