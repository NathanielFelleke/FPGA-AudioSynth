import cocotb
import os
import random
import sys
import logging
from pathlib import Path
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge, ReadOnly,with_timeout, First, Join, ReadWrite, Edge
from cocotb.utils import get_sim_time as gst
from cocotb.runner import get_runner
from cocotb.clock import Clock
import numpy as np

from scipy.signal import lfilter
from matplotlib import pyplot as plt


 
#cheap way to get the name of current file for runner:
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
        result+=scaled_wave.astype(np.int8)
    return (time_points,result)
 

 
async def generate_clock(clock_wire):
    while True: # repeat forever
        clock_wire.value = 0
        await Timer(5,units="ns")
        clock_wire.value = 1
        await Timer(5,units="ns")




async def reset(rst_wire):
    rst_wire.value = 1
    await Timer(10,units="ns")
    rst_wire.value = 0


@cocotb.test()
async def fir_test(dut):
    #time and signal input:

    coeffs = [-2,-3,-4,0,9,21,32,36,32,21,9,0,-4,-3,-2]
    #coeffs = [-3,14,-20,6,16,-5,-41,68,-41,-5,16,6,-20,14,-3]
    coeffs = [0,0,0,0,0,0,0,0,0,0,0,0,0,-4,4]

    #coeffs = [1] + [0]*(NUM_COEFFS-1)
    t,si = generate_signed_8bit_sine_waves(
        sample_rate=100e6,
        duration=10e-6,
        frequencies=[46e6,20e6, 200e3],
        amplitudes=[0.1,0.1, 0.5]
    )


    filtered_signal = np.zeros(len(si))
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    await reset(dut.rst)
    for i in range(15):
        for b in range(8):
            dut.coeffs[b+8*i].value = (coeffs[i]>>b)&0x1 
    await Timer(10,units="ns")
    for i in range(len(si)):
        await FallingEdge(dut.clk)

        dut.data_in.value = int(si[i])
        dut.data_in_valid.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.data_out_valid.value == 1, f"data_valid_out should be 1 after"
        filtered_signal[i] = dut.data_out.value.signed_integer 
        await FallingEdge(dut.clk)
        dut.data_in_valid.value = 0
        await Timer(20, units="ns")
        #print(f"At time {gst(units='ns')} ns, input {si[i]} output {dut.sample_out.value}")
    model_output = lfilter(coeffs, [1.0], si)
    

    plt.figure()
    plt.subplot(3,1,1)
    plt.plot(t, si)
    plt.title("Input Signal")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.subplot(3,1,2)
    plt.plot(t, model_output)
    plt.title("FIR Filter Output (Model)")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.subplot(3,1,3)
    plt.plot(t, filtered_signal)
    plt.title("FIR Filter Output (HDL)")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.tight_layout()
    plt.show()
    plt.savefig("fir_output.png")





    



    
    
 
"""the code below should largely remain unchanged in structure, though the specific files and things
specified should get updated for different simulations.
"""

def spi_tx_runner():
    """Simulate the led_controller using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [proj_path / "hdl" / "audio_fir.sv"] #grow/modify this as needed.
    hdl_toplevel = "fir_15"
    build_test_args = ["-Wall"]#,"COCOTB_RESOLVE_X=ZEROS"]
    parameters = {} #!!!change these to do different versions
    sys.path.append(str(proj_path / "sim"))
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters=parameters,
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
    spi_tx_runner()