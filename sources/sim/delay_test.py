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

def generate_signed_8bit_sine_waves(sample_rate, duration,frequencies, amplitudes):
    """
    frequencies (float): The frequency of the sine waves in Hz.
    relative amplitudes (float) of the sinewaves (0 to 1.0).
    sample_rate (int): The number of samples per second.
    duration (float): The duration of the time series in seconds.
    """
    num_samples = int(sample_rate * duration)
    time_points = np.arange(num_samples) / sample_rate
    # Generate a sine wave with amplitude 1.0
    result = np.zeros(num_samples, dtype=int)
    assert len(frequencies) == len(amplitudes), "frequencies must match amplitudes"
    for i in range(len(frequencies)):
        sine_wave = amplitudes[i]*np.sin(2 * np.pi * frequencies[i] * time_points)
        # Scale the sine wave to the 8-bit signed range [-128, 127]
        scaled_wave = sine_wave * 127
        # make 8bit signed integers:
        result+=scaled_wave.astype(np.int32)
    return (time_points,result)

t,si = generate_signed_8bit_sine_waves(
    sample_rate=100e6,
    duration=10e-6,
    frequencies=[400e5],
    amplitudes=[4]
)

plays = []
for i in range(100):
    if (i>10 and i<18):
        plays.append(int(si[i]))
    else:
        plays.append(0)            

@cocotb.test()
async def test_a(dut):
    my_output = np.zeros(100)
    """cocotb test for messing with verilog simulation"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.decay_weight.value = 1
    dut.delay_len.value = 10
    for i in range(100):
        dut.data_in.value = plays[i]
        if i != 0:
            my_output[i-1] += dut.data_out.value.signed_integer
        await Timer(10,'ns')
    my_output[99] += dut.data_out.value.signed_integer
    plt.figure()
    plt.plot(my_output)
    plt.show()

def test_runner():
    """Simulate the counter using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "delay" / "model"))
    sources = [proj_path / "hdl" / "delay.sv", proj_path / "hdl" / "xilinx_true_dual_port_read_first_2_clock_ram.sv"]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "delay"
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