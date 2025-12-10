import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, RisingEdge
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

def bits_lsb_first(num):
    """Convert byte to list of bits in LSB-first order (for UART transmission)"""
    return [(num >> i) & 1 for i in range(8)]

async def send_uart_byte(dut, byte_val, bit_period_ns=32000):
    """Send a single byte via UART with detailed logging"""
    dut._log.info(f"Sending byte 0x{byte_val:02X} = 0b{byte_val:08b}")
    bits = bits_lsb_first(byte_val)
    dut._log.info(f"  LSB-first bits: {bits}")

    # Start bit (low)
    dut._log.info(f"  START bit (0)")
    dut.data_in.value = 0
    await Timer(bit_period_ns, 'ns')

    # Data bits (LSB first)
    for i, bit in enumerate(bits):
        dut._log.info(f"  Data bit {i}: {bit}")
        dut.data_in.value = bit
        await Timer(bit_period_ns, 'ns')

    # Stop bit (high)
    dut._log.info(f"  STOP bit (1)")
    dut.data_in.value = 1
    await Timer(bit_period_ns, 'ns')

@cocotb.test()
async def test_single_byte(dut):
    """Test reception of a single byte with detailed state monitoring"""
    dut._log.info("=" * 60)
    dut._log.info("MIDI RX Debug Test - Single Byte Reception")
    dut._log.info("=" * 60)

    # Setup clock: 100MHz = 10ns period
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.data_in.value = 1  # Idle high
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    dut._log.info(f"BAUD_BIT_PERIOD = {100_000_000 // 31_250} cycles")
    dut._log.info("Reset complete.\n")

    # Monitor state changes
    async def state_monitor():
        last_state = -1
        while True:
            await RisingEdge(dut.clk)
            current_state = dut.uart_state.value.integer
            if current_state != last_state:
                dut._log.info(f"  [{cocotb.utils.get_sim_time('ns'):10.0f}ns] UART State: {last_state} -> {current_state}")
                last_state = current_state

    cocotb.start_soon(state_monitor())

    # Send a simple status byte (0x90 = Note On Channel 0)
    dut._log.info("\n--- Sending 0x90 (Note On status) ---")
    await send_uart_byte(dut, 0x90)

    await ClockCycles(dut.clk, 100)

    dut._log.info(f"\nReceived rx_data: 0x{dut.rx_data.value.integer:02X}")
    dut._log.info(f"last_status: 0x{dut.last_status.value.integer:02X}")
    dut._log.info(f"expecting_vel: {dut.expecting_vel.value}")

    # Send note byte (60 = Middle C)
    dut._log.info("\n--- Sending 0x3C (note 60) ---")
    await send_uart_byte(dut, 60)

    await ClockCycles(dut.clk, 100)

    dut._log.info(f"\nReceived rx_data: 0x{dut.rx_data.value.integer:02X}")
    dut._log.info(f"stored_note: {dut.stored_note.value.integer}")
    dut._log.info(f"expecting_vel: {dut.expecting_vel.value}")

    # Send velocity byte (127 = max velocity)
    dut._log.info("\n--- Sending 0x7F (velocity 127) ---")
    await send_uart_byte(dut, 127)

    await ClockCycles(dut.clk, 200)  # Wait longer for processing

    dut._log.info(f"\nFinal State:")
    dut._log.info(f"  on_out: 0b{dut.on_out.value.integer:08b}")

    # Extract voice 0 note and velocity from packed arrays
    # note_out is [7:0][6:0] - 7 bits per voice, 8 voices
    # velocity_out is [7:0][2:0] - 3 bits per voice, 8 voices
    note_out_full = dut.note_out.value.integer
    velocity_out_full = dut.velocity_out.value.integer

    voice0_note = note_out_full & 0x7F  # Extract lower 7 bits
    voice0_vel = velocity_out_full & 0x7  # Extract lower 3 bits

    dut._log.info(f"  note_out (full): 0x{note_out_full:X}")
    dut._log.info(f"  voice 0 note: {voice0_note}")
    dut._log.info(f"  velocity_out (full): 0x{velocity_out_full:X}")
    dut._log.info(f"  voice 0 velocity: {voice0_vel}")
    dut._log.info(f"  free_channel: {dut.free_channel.value.integer}")
    dut._log.info(f"  rx_done: {dut.rx_done.value.integer}")
    dut._log.info(f"  stored_note: {dut.stored_note.value.integer}")
    dut._log.info(f"  rx_data: 0x{dut.rx_data.value.integer:02X}")

    # Check if voice 0 is on (bit 0 of on_out)
    voice0_on = dut.on_out.value.integer & 0x1

    if voice0_on == 1 and voice0_note == 60 and voice0_vel == 3:
        dut._log.info("✓ SUCCESS: Voice 0 is ON with correct note and velocity!")
    elif voice0_on == 1:
        dut._log.error(f"✗ PARTIAL: Voice 0 is ON but note={voice0_note} (expected 60), vel={voice0_vel} (expected 3)")
    else:
        dut._log.error("✗ FAIL: Voice 0 should be ON but is OFF")


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
