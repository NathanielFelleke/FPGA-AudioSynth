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

coeffs = [-2,-3,-4,0,9,21,32,36,32,21,9,0,-4,-3,-2] #low pass
# coeffs = [-3,14,-20,6,16,-5,-41,68,-41,-5,16,6,-20,14,-3] #high pass
#time and signal input:
t,si = generate_signed_8bit_sine_waves(
    sample_rate=100e6,
    duration=10e-6,
    frequencies=[100e5],
    amplitudes=[4]
)

plays = []
for i in range(1000):
    if (i>200 and i<600) or (i>925 and i<950):
        plays.append(1)
    else:
        plays.append(0)            


# #print(si)
# model_output = lfilter(coeffs, [1.0], si)
# #my_output = np.zeros(1000)

@cocotb.test()
async def test_a(dut):
    my_output = np.zeros(1000)
    """cocotb test for messing with verilog simulation"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.attack_len.value = 200
    dut.release_len.value = 300
    for i in range(1000):
        dut.play.value = plays[i]
        dut.data_in.value = int(si[i])
        if i != 0:
            my_output[i-1] += dut.data_out.value.signed_integer
        await Timer(10,'ns')
    my_output[999] += dut.data_out.value.signed_integer
    plt.figure()
    plt.plot(t,[int(i) for i in si])
    plt.plot(t,my_output)
    plt.show()


def test_runner():
    """Simulate the counter using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "envelope" / "model"))
    sources = [proj_path / "hdl" / "envelope.sv"]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "envelope"
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