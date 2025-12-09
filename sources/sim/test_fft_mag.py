import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_fft_magnitude(dut):
    """Test FFT magnitude calculation with expected values"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.rst.value = 1
    dut.s_axis_tvalid.value = 0
    dut.s_axis_tlast.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(20, units="ns")

    # Test 1: re=3, im=4 => mag^2 = 9+16 = 25
    dut.log.info("Test 1: re=3, im=4, expected mag^2=25")
    await FallingEdge(dut.clk)
    dut.s_axis_tdata.value = (4 << 16) | (3 & 0xFFFF)  # {im, re}
    dut.s_axis_tvalid.value = 1
    dut.s_axis_tlast.value = 0

    # Wait 2 cycles for pipeline
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.mag_squared.value.integer
    assert result == 25, f"FAIL: mag_squared = {result} (expected 25)"
    assert dut.mag_valid.value == 1, "mag_valid should be 1"
    dut.log.info(f"PASS: mag_squared = {result}")

    # Test 2: re=10, im=0 => mag^2 = 100
    dut.log.info("Test 2: re=10, im=0, expected mag^2=100")
    await FallingEdge(dut.clk)
    dut.s_axis_tdata.value = (0 << 16) | (10 & 0xFFFF)
    dut.s_axis_tvalid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.mag_squared.value.integer
    assert result == 100, f"FAIL: mag_squared = {result} (expected 100)"
    dut.log.info(f"PASS: mag_squared = {result}")

    # Test 3: re=0, im=5 => mag^2 = 25
    dut.log.info("Test 3: re=0, im=5, expected mag^2=25")
    await FallingEdge(dut.clk)
    dut.s_axis_tdata.value = (5 << 16) | (0 & 0xFFFF)
    dut.s_axis_tvalid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.mag_squared.value.integer
    assert result == 25, f"FAIL: mag_squared = {result} (expected 25)"
    dut.log.info(f"PASS: mag_squared = {result}")

    # Test 4: re=-3, im=-4 => mag^2 = 9+16 = 25
    dut.log.info("Test 4: re=-3, im=-4, expected mag^2=25")
    await FallingEdge(dut.clk)
    # Two's complement for -3 and -4 in 16-bit
    re_neg3 = ((-3) & 0xFFFF)
    im_neg4 = ((-4) & 0xFFFF)
    dut.s_axis_tdata.value = (im_neg4 << 16) | re_neg3
    dut.s_axis_tvalid.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.mag_squared.value.integer
    assert result == 25, f"FAIL: mag_squared = {result} (expected 25)"
    dut.log.info(f"PASS: mag_squared = {result}")

    # Test 5: re=100, im=100 => mag^2 = 20000, test tlast
    dut.log.info("Test 5: re=100, im=100, expected mag^2=20000")
    await FallingEdge(dut.clk)
    dut.s_axis_tdata.value = (100 << 16) | (100 & 0xFFFF)
    dut.s_axis_tvalid.value = 1
    dut.s_axis_tlast.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    result = dut.mag_squared.value.integer
    assert result == 20000, f"FAIL: mag_squared = {result} (expected 20000)"
    assert dut.mag_last.value == 1, "mag_last should be 1"
    dut.log.info(f"PASS: mag_squared = {result}, mag_last = {dut.mag_last.value}")

    dut.s_axis_tvalid.value = 0
    dut.s_axis_tlast.value = 0

    await Timer(50, units="ns")
    dut.log.info("All tests passed!")


def test_runner():
    """Simulate the FFT magnitude using the Python runner."""
    from cocotb.runner import get_runner

    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim"))

    sources = [proj_path / "hdl" / "fft_mag.sv"]
    hdl_toplevel = "fft_magnitude"
    build_test_args = ["-Wall"]
    parameters = {"DATA_WIDTH": 16}

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
