import cocotb
import os
import random
import sys
from math import log
import logging
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge
from cocotb.triggers import ReadOnly,with_timeout, Edge, ReadWrite, NextTimeStep, First
from cocotb.utils import get_sim_time as gst
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

def bits(num):
    num_copy = num+0
    bit = 0
    out = [0,0,0,0,0,0,0,0]
    while num_copy:
        if num_copy%2:
            out[7-bit] = 1
        num_copy = num_copy>>1
        bit += 1
    return out

@cocotb.test()
async def test_a(dut):
    """cocotb test for messing with verilog simulation"""
    dut._log.info("Starting...")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.data_in.value = 1
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    await Timer(10, 'ns')
    await FallingEdge(dut.clk)
    for _ in range(20):
        print(dut.free_channel.value, dut.on_out.value.integer)
        command = random.randint(0,2)
        if command == 2:
            input = [[1,1,0,0,0,0,0,0],[0,0,0,0,0,0,random.randint(0,1),random.randint(0,1)]]
            dut._log.info(f"Sending Channel: {input[1]}")
        else: 
            input = [[1,0,0,command,0,0,0,0],[0,random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1),random.randint(0,1)], [0,0,0,command,command,1,1,1]]
            if command:
                dut._log.info(f"Sending On: {input[1]}")
            else:
                dut._log.info(f"Sending Off: {input[1]}")
        for byte in input:
            dut.data_in.value = 0
            await Timer(32000, 'ns')
            for i in range(8):
                dut.data_in.value = byte[7-i]
                await Timer(32000, 'ns')
            dut.data_in.value = 1
            await Timer(32000, 'ns')
        if command == 2:
            dut._log.info(f"Recieved {dut.last_byte.value} {dut.current_byte.value}. Waveform = {dut.wave_out.value.integer}")
        else:
            dut._log.info(f"Recieved {dut.second_last_byte.value} {dut.last_byte.value} {dut.current_byte.value}.")   
    # for i in range(8):
    #     if (dut.on_out.value.integer>>i)%2:
    #         input = [[1,0,0,0,0,0,0,0], bits(dut.note_out.value[i].integer), [0,0,0,0,0,1,1,1]]
    #         dut._log.info(f"Sending Off: {input[1]}")
    #         for byte in input:
    #             dut.data_in.value = 0
    #             await Timer(32000, 'ns')
    #             for i in range(8):
    #                 dut.data_in.value = byte[7-i]
    #                 await Timer(32000, 'ns')
    #             dut.data_in.value = 1
    #             await Timer(32000, 'ns')
    #             dut._log.info(f"Recieved {dut.second_last_byte.value} {dut.last_byte.value} {dut.current_byte.value}. Velocity[{dut.last_byte.value.integer}] = {dut.velocity_out[dut.last_byte.value.integer].value}")
    # assert dut.on_out.value == 0


 
def test_runner():
    """Simulate the counter using the Python runner."""
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim" / "model"))
    sources = [proj_path / "hdl" / "midi_rx.sv"]
    build_test_args = ["-Wall"]
    sys.path.append(str(proj_path / "sim"))
    hdl_toplevel = "midi_rx"
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