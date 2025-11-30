import os
import sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.runner import get_runner

test_file = os.path.basename(__file__).replace(".py", "")


@cocotb.test()
async def test_voice_mixer_simple(dut):
    """Simple test of voice mixer summing functionality"""
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

    # Test 1: All voices = 100, expected sum = 800
    print("\nTest 1: All voices = 100")
    dut.data_in_valid.value = 1
    for i in range(8):
        dut.voice_in[i].value = 100
    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 0

    # Wait for output valid (3 cycles for 8 voices)
    for _ in range(5):
        await RisingEdge(dut.clk)
        if dut.data_out_valid.value == 1:
            result = dut.mixed_out.value.signed_integer
            print(f"  Result: {result}, Expected: 800")
            assert result == 800, f"Expected 800, got {result}"
            break

    # Test 2: Alternating +1000/-1000, expected sum = 0
    print("\nTest 2: Alternating +1000/-1000")
    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 1
    for i in range(8):
        dut.voice_in[i].value = 1000 if i % 2 == 0 else -1000
    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)
        if dut.data_out_valid.value == 1:
            result = dut.mixed_out.value.signed_integer
            print(f"  Result: {result}, Expected: 0")
            assert result == 0, f"Expected 0, got {result}"
            break

    # Test 3: Mixed values
    print("\nTest 3: Mixed values")
    test_values = [1000, 2000, -500, 3000, -1000, 500, 0, 1500]
    expected_sum = sum(test_values)

    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 1
    for i in range(8):
        dut.voice_in[i].value = test_values[i]
    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)
        if dut.data_out_valid.value == 1:
            result = dut.mixed_out.value.signed_integer
            print(f"  Result: {result}, Expected: {expected_sum}")
            assert result == expected_sum, f"Expected {expected_sum}, got {result}"
            break

    print("\nAll tests passed!")


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
