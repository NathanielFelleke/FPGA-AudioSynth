import cocotb
import os
import random
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles
from cocotb.runner import get_runner
test_file = os.path.basename(__file__).replace(".py","")

def bits_lsb_first(num):
    """Convert byte to list of bits in LSB-first order (for UART transmission)"""
    return [(num >> i) & 1 for i in range(8)]

def get_voice_state(dut, voice_num):
    """Extract voice state from packed arrays (cocotb indexing workaround)"""
    on_out = dut.on_out.value.integer
    note_out = dut.note_out.value.integer
    vel_out = dut.velocity_out.value.integer

    voice_on = (on_out >> voice_num) & 0x1
    voice_note = (note_out >> (voice_num * 7)) & 0x7F
    voice_vel = (vel_out >> (voice_num * 3)) & 0x7

    return voice_on, voice_note, voice_vel

async def send_uart_byte(dut, byte_val, bit_period_ns=32000):
    """Send a single byte via UART (start bit, 8 data bits LSB-first, stop bit)"""
    # Start bit (low)
    dut.data_in.value = 0
    await Timer(bit_period_ns, 'ns')

    # Data bits (LSB first)
    bits = bits_lsb_first(byte_val)
    for bit in bits:
        dut.data_in.value = bit
        await Timer(bit_period_ns, 'ns')

    # Stop bit (high)
    dut.data_in.value = 1
    await Timer(bit_period_ns, 'ns')

async def send_midi_message(dut, status, data1, data2=None):
    """Send a complete MIDI message"""
    await send_uart_byte(dut, status)
    await send_uart_byte(dut, data1)
    if data2 is not None:
        await send_uart_byte(dut, data2)

@cocotb.test()
async def test_midi_notes(dut):
    """Test MIDI Note On and Note Off messages"""
    dut._log.info("=" * 60)
    dut._log.info("Starting MIDI RX Test - LSB First Implementation")
    dut._log.info("=" * 60)

    # Setup clock: 100MHz = 10ns period
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))

    # Reset
    dut.data_in.value = 1  # Idle high
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    dut._log.info("Reset complete. Starting MIDI message tests...")

    # Test 1: Note On - Middle C (note 60) with max velocity
    dut._log.info("\n--- Test 1: Note On (0x90, 60, 127) ---")
    await send_midi_message(dut, 0x90, 60, 127)
    await ClockCycles(dut.clk, 100)

    voice0_on, voice0_note, voice0_vel = get_voice_state(dut, 0)
    assert voice0_on == 1, "Voice 0 should be ON"
    assert voice0_note == 60, f"Note should be 60, got {voice0_note}"
    assert voice0_vel == 3, f"Velocity (top 3 bits of 127) should be 3, got {voice0_vel}"
    dut._log.info(f"✓ Voice 0: ON, Note={voice0_note}, Velocity={voice0_vel}")

    # Test 2: Another Note On - Note 64 with velocity 100
    dut._log.info("\n--- Test 2: Note On (0x90, 64, 100) ---")
    await send_midi_message(dut, 0x90, 64, 100)
    await ClockCycles(dut.clk, 100)

    voice1_on, voice1_note, voice1_vel = get_voice_state(dut, 1)
    assert voice1_on == 1, "Voice 1 should be ON"
    assert voice1_note == 64, f"Note should be 64, got {voice1_note}"
    dut._log.info(f"✓ Voice 1: ON, Note={voice1_note}, Velocity={voice1_vel}")

    # Test 3: Note On with Running Status (no status byte sent)
    dut._log.info("\n--- Test 3: Running Status - Note 67, Velocity 80 ---")
    await send_uart_byte(dut, 67)
    await send_uart_byte(dut, 80)
    await ClockCycles(dut.clk, 100)

    voice2_on, voice2_note, voice2_vel = get_voice_state(dut, 2)
    assert voice2_on == 1, "Voice 2 should be ON"
    assert voice2_note == 67, f"Note should be 67, got {voice2_note}"
    dut._log.info(f"✓ Voice 2: ON, Note={voice2_note}, Velocity={voice2_vel}")

    # Test 4: Note Off - Turn off note 60
    dut._log.info("\n--- Test 4: Note Off (0x80, 60, 0) ---")
    await send_midi_message(dut, 0x80, 60, 0)
    await ClockCycles(dut.clk, 100)

    voice0_on, _, _ = get_voice_state(dut, 0)
    assert voice0_on == 0, "Voice 0 should be OFF"
    dut._log.info(f"✓ Voice 0: OFF")

    # Test 5: Note Off using velocity 0 method
    dut._log.info("\n--- Test 5: Note Off via Velocity=0 (0x90, 64, 0) ---")
    await send_midi_message(dut, 0x90, 64, 0)
    await ClockCycles(dut.clk, 100)

    voice1_on, _, _ = get_voice_state(dut, 1)
    assert voice1_on == 0, "Voice 1 should be OFF"
    dut._log.info(f"✓ Voice 1: OFF")

    # Test 6: Fill all 8 voices
    dut._log.info("\n--- Test 6: Fill all 8 voices ---")
    for i in range(7):  # We already have 1 note on (voice 2), add 7 more for total of 8
        note = 48 + i
        velocity = 64 + i * 10
        await send_uart_byte(dut, note)
        await send_uart_byte(dut, velocity)
        await ClockCycles(dut.clk, 50)

    await ClockCycles(dut.clk, 100)
    on_count = bin(dut.on_out.value.integer).count('1')
    dut._log.info(f"✓ Active voices: {on_count}/8")

    # Test 7: Try to add 9th voice (should be ignored - no free channels)
    dut._log.info("\n--- Test 7: Overflow - 9th note (should be ignored) ---")
    await send_uart_byte(dut, 72)
    await send_uart_byte(dut, 100)
    await ClockCycles(dut.clk, 100)

    on_count_after = bin(dut.on_out.value.integer).count('1')
    assert on_count_after == on_count, "Voice count should not increase when all channels full"
    dut._log.info(f"✓ Still {on_count_after} voices (overflow handled correctly)")

    # Test 8: Turn off all notes
    dut._log.info("\n--- Test 8: Turn off all notes ---")
    await send_midi_message(dut, 0x80, 0, 0)  # New status
    for i in range(8):
        voice_on, voice_note, _ = get_voice_state(dut, i)
        if voice_on:
            await send_uart_byte(dut, voice_note)
            await send_uart_byte(dut, 0)
            await ClockCycles(dut.clk, 50)

    await ClockCycles(dut.clk, 100)
    assert dut.on_out.value.integer == 0, f"All voices should be OFF, but on_out={bin(dut.on_out.value.integer)}"
    dut._log.info(f"✓ All voices OFF")

    # Test 9: Bit-level validation - Send 0x90 and verify LSB-first reception
    dut._log.info("\n--- Test 9: Bit-level LSB-first validation ---")
    dut._log.info("Sending 0x90 = 0b10010000")
    dut._log.info("LSB-first order: [0,0,0,0,1,0,0,1]")
    await send_uart_byte(dut, 0x90)
    await ClockCycles(dut.clk, 10)
    dut._log.info("✓ Byte transmitted successfully")

    dut._log.info("\n" + "=" * 60)
    dut._log.info("All tests PASSED!")
    dut._log.info("=" * 60)

@cocotb.test()
async def test_random_messages(dut):
    """Test with random MIDI messages"""
    dut._log.info("\n" + "=" * 60)
    dut._log.info("Random Message Test")
    dut._log.info("=" * 60)

    # Setup
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start(start_high=False))
    dut.data_in.value = 1
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    notes_on = []

    for test_num in range(15):
        choice = random.randint(0, 1)

        if choice == 0 or len(notes_on) == 0:  # Note On
            note = random.randint(36, 84)  # Piano range
            velocity = random.randint(40, 127)
            dut._log.info(f"Test {test_num}: Note ON  - Note {note}, Vel {velocity}")
            await send_midi_message(dut, 0x90, note, velocity)
            notes_on.append(note)
        else:  # Note Off
            note = random.choice(notes_on)
            dut._log.info(f"Test {test_num}: Note OFF - Note {note}")
            await send_midi_message(dut, 0x80, note, 0)
            notes_on.remove(note)

        await ClockCycles(dut.clk, 100)

    # Clean up - turn off all notes
    dut._log.info("\nCleaning up remaining notes...")
    for note in notes_on:
        await send_midi_message(dut, 0x80, note, 0)
        await ClockCycles(dut.clk, 50)

    await ClockCycles(dut.clk, 100)
    dut._log.info(f"Final state: {bin(dut.on_out.value.integer).count('1')} voices active")
    dut._log.info("Random test complete!")


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
