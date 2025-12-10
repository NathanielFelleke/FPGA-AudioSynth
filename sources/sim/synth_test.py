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
    my_output = []
    """cocotb test for messing with verilog simulation"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(100, 'ns')
    note1 = [0,random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1)]
    note2 = [0,random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1)]
    for i in range(2):
        input = [[1,1,0,0,0,0,0,0],[0,0,0,0,0,0,random.randint(0,1),random.randint(0,1)]]
        dut._log.info(f"Sending Channel: {input[1]}")
        for byte in input:
            print('b')
            dut.midi_in.value = 0
            await Timer(32000, 'ns')
            for i in range(8):
                dut.midi_in.value = byte[7-i]
                await Timer(32000, 'ns')
            dut.midi_in.value = 1
            await Timer(32000, 'ns')
        dut.wave_type.value = i
        vel = [0,0,0,0,0,0,0,0]
        input_on = [[1,0,0,(i+1)%2,0,0,0,0], note1, vel]
        input_off = [[1,0,0,(i+1)%2,0,0,0,0], note2, vel]
        for byte in input_on:
            print('b1')
            dut.midi_in.value = 0
            await Timer(32000, 'ns')
            for i in range(8):
                dut.midi_in.value = byte[7-i]
                await Timer(32000, 'ns')
            dut.midi_in.value = 1
            await Timer(32000, 'ns')
        print(dut.note_plays.value)
        for _ in range(1000000):
            await Timer(10, 'ns')
            my_output.append(dut.audio_out.value.signed_integer)
        for byte in input_off:
            print('b0')
            dut.midi_in.value = 0
            await Timer(32000, 'ns')
            for i in range(8):
                dut.midi_in.value = byte[7-i]
                await Timer(32000, 'ns')
            dut.midi_in.value = 1
            await Timer(32000, 'ns')
        print(dut.note_plays.value)
        for _ in range(1000000):
            await Timer(10, 'ns')
            my_output.append(dut.audio_out.value.signed_integer)
    
    plt.figure()
    plt.plot(np.array(my_output))
    plt.show()


def test_runner():
    """Simulate the counter using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [proj_path / "hdl" / "synth.sv", proj_path / "hdl" / "oscillator.sv", proj_path / "hdl" / "sine.sv",proj_path / "hdl" / "square.sv",proj_path / "hdl" / "sawtooth.sv",proj_path / "hdl" / "triangle.sv",proj_path / "hdl" / "midi_rx.sv",proj_path / "hdl" / "envelope.sv"]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "synth"
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