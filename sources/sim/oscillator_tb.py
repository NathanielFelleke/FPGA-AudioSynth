import cocotb
import os
import random
import sys
from math import log
import logging
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge
from cocotb.triggers import ReadOnly,with_timeout, Edge, ReadWrite, NextTimeStep, First
from cocotb.utils import get_sim_time as gst
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_a(dut):
    my_output = np.zeros(4000)
    """cocotb test for messing with verilog simulation"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.PHASE_INCR.value = 19777216
    dut.step_in.value = 1
    dut.wave_type.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')
    for i in range(1000):
        my_output[i] = dut.data_out.value.signed_integer
        await FallingEdge(dut.clk)
    dut.wave_type.value = 1
    for i in range(1000):
        my_output[i+1000] = dut.data_out.value.signed_integer
        await FallingEdge(dut.clk)
    dut.wave_type.value = 2
    for i in range(1000):
        my_output[i+2000] = dut.data_out.value.signed_integer
        await FallingEdge(dut.clk)
    dut.wave_type.value = 3
    for i in range(1000):
        my_output[i+3000] = dut.data_out.value.signed_integer
        await FallingEdge(dut.clk)
    
    plt.figure()
    plt.plot(np.array(my_output))
    plt.show()


def test_runner():
    """Simulate the counter using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [proj_path / "hdl" / "oscillator.sv", proj_path / "hdl" / "sine.sv",proj_path / "hdl" / "square.sv",proj_path / "hdl" / "sawtooth.sv",proj_path / "hdl" / "triangle.sv"]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "oscillator"
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters={},
        timescale = ('1ns','1ps'),
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