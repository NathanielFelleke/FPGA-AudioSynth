import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_log_scale(dut):
    """Test log scale with expected values"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.mag_valid.value = 0
    dut.mag_last.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    # Test 1: mag_squared = 0x80000000 (bit 31 set)
    # Expected: leading_one=31, normalized has top bits 100 => log_out = {31, 3'b100} = 0xFC
    dut.log.info("Test 1: mag_squared=0x80000000, expected log_out=0xFC")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x80000000
    dut.mag_valid.value = 1
    dut.mag_last.value = 0

    # Wait 2 cycles for pipeline
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0xFC, f"FAIL: log_out = 0x{result:02X} (expected 0xFC)"
    assert dut.log_valid.value == 1, "log_valid should be 1"
    dut.log.info(f"PASS: log_out = 0x{result:02X}")

    # Test 2: mag_squared = 0x00000100 (bit 8 set)
    # Expected: leading_one=8, normalized = 0x100 << 23 = 0x80000000 => {8, 3'b100} = 0x44
    dut.log.info("Test 2: mag_squared=0x00000100, expected log_out=0x44")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x00000100
    dut.mag_valid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0x44, f"FAIL: log_out = 0x{result:02X} (expected 0x44)"
    dut.log.info(f"PASS: log_out = 0x{result:02X}")

    # Test 3: mag_squared = 0x40000000 (bit 30 set)
    # Expected: leading_one=30, normalized = 0x40000000 << 1 = 0x80000000 => {30, 3'b100} = 0xF4
    dut.log.info("Test 3: mag_squared=0x40000000, expected log_out=0xF4")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x40000000
    dut.mag_valid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0xF4, f"FAIL: log_out = 0x{result:02X} (expected 0xF4)"
    dut.log.info(f"PASS: log_out = 0x{result:02X}")

    # Test 4: mag_squared = 0x00000001 (bit 0 set)
    # Expected: leading_one=0, normalized = 0x1 << 31 = 0x80000000 => {0, 3'b100} = 0x04
    dut.log.info("Test 4: mag_squared=0x00000001, expected log_out=0x04")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x00000001
    dut.mag_valid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0x04, f"FAIL: log_out = 0x{result:02X} (expected 0x04)"
    dut.log.info(f"PASS: log_out = 0x{result:02X}")

    # Test 5: mag_squared = 0x00100000 (bit 20 set)
    # Expected: leading_one=20, normalized = 0x100000 << 11 = 0x80000000 => {20, 3'b100} = 0xA4
    dut.log.info("Test 5: mag_squared=0x00100000, expected log_out=0xA4")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x00100000
    dut.mag_valid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0xA4, f"FAIL: log_out = 0x{result:02X} (expected 0xA4)"
    dut.log.info(f"PASS: log_out = 0x{result:02X}")

    # Test 6: mag_squared = 0xC0000000 (bits 31,30 set)
    # Expected: leading_one=31, normalized = 0xC0000000 << 0 => {31, 3'b110} = 0xFE
    dut.log.info("Test 6: mag_squared=0xC0000000, expected log_out=0xFE")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0xC0000000
    dut.mag_valid.value = 1
    dut.mag_last.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    assert result == 0xFE, f"FAIL: log_out = 0x{result:02X} (expected 0xFE)"
    assert dut.log_last.value == 1, "log_last should be 1"
    dut.log.info(f"PASS: log_out = 0x{result:02X}, log_last = {dut.log_last.value}")

    # Test 7: Zero input (edge case)
    dut.log.info("Test 7: mag_squared=0x00000000 (zero - edge case)")
    await FallingEdge(dut.clk)
    dut.mag_squared.value = 0x00000000
    dut.mag_valid.value = 1
    dut.mag_last.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.log_out.value.integer
    dut.log.info(f"INFO: log_out = 0x{result:02X} (zero input case)")

    dut.mag_valid.value = 0
    dut.mag_last.value = 0

    await Timer(50, units="ns")
    dut.log.info("All tests passed!")


def test_runner():
    """Simulate the log scale using the Python runner."""
    from cocotb.runner import get_runner

    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim"))

    sources = [proj_path / "hdl" / "log_scale.sv"]
    hdl_toplevel = "log_scale"
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
