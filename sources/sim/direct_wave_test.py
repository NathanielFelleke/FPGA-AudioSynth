import cocotb
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from cocotb.runner import get_runner

@cocotb.test()
async def test_sine_direct(dut):
    """Direct test of sine generator"""
    cocotb.start_soon(Clock(dut.clk_in, 10, units="ns").start())

    dut.rst_in.value = 1
    dut.step_in.value = 0
    dut.PHASE_INCR.value = 23409859  # Middle C
    await RisingEdge(dut.clk_in)
    dut.rst_in.value = 0
    dut.step_in.value = 1
    await RisingEdge(dut.clk_in)

    # Collect 200 samples
    samples = []
    for _ in range(200):
        await RisingEdge(dut.clk_in)
        val = dut.amp_out.value.signed_integer
        samples.append(val)

    data = np.array(samples, dtype=np.int64)
    dut._log.info(f"Sine: min={np.min(data):e}, max={np.max(data):e}, mean={np.mean(data):.2e}")

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(data)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('Direct Sine Generator Test')
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.savefig('direct_sine_test.png', dpi=150)

def test_runner():
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "hdl" / "sine.sv"]

    hdl_toplevel = "sine_generator"
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=["-Wall"],
        timescale=('1ns','1ps'),
        waves=True
    )
    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=os.path.basename(__file__).replace(".py",""),
        waves=True
    )

if __name__ == "__main__":
    test_runner()
