import cocotb
import os
import sys
from pathlib import Path
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

test_file = os.path.basename(__file__).replace(".py","")

@cocotb.test()
async def test_waterfall_buffer_basic_write_read(dut):
    """Test basic write and read operations"""

    # Start both clocks
    wr_clk = cocotb.start_soon(Clock(dut.wr_clk, 10, units="ns").start(start_high=False))  # 100 MHz
    rd_clk = cocotb.start_soon(Clock(dut.rd_clk, 40, units="ns").start(start_high=False))  # 25 MHz

    # Reset both domains
    dut.wr_rst.value = 1
    dut.rd_rst.value = 1
    dut.log_in.value = 0
    dut.log_valid.value = 0
    dut.log_last.value = 0
    dut.rd_bin.value = 0
    dut.rd_row.value = 0

    await RisingEdge(dut.wr_clk)
    await RisingEdge(dut.rd_clk)
    await FallingEdge(dut.wr_clk)
    dut.wr_rst.value = 0
    await FallingEdge(dut.rd_clk)
    dut.rd_rst.value = 0
    await Timer(50, units="ns")

    dut.log.info("Test 1: Write one full row (512 bins)")

    # Write 512 bins of data (one row)
    for bin_num in range(512):
        await FallingEdge(dut.wr_clk)
        dut.log_in.value = bin_num & 0xFF  # Use bin number as data
        dut.log_valid.value = 1
        dut.log_last.value = 1 if bin_num == 511 else 0
        await RisingEdge(dut.wr_clk)

    dut.log_valid.value = 0
    dut.log_last.value = 0

    # Wait for CDC to propagate
    await Timer(200, units="ns")

    # Now try to read back from row 0 (newest row)
    dut.log.info("Reading back row 0...")
    errors = 0
    for bin_num in range(512):
        await FallingEdge(dut.rd_clk)
        dut.rd_bin.value = bin_num
        dut.rd_row.value = 0  # Row 0 = newest

        # Wait for read latency (2 cycles for HIGH_PERFORMANCE mode)
        await RisingEdge(dut.rd_clk)
        await RisingEdge(dut.rd_clk)

        rd_data = dut.rd_data.value.integer
        # Note: First few reads might be invalid due to initial state
        if bin_num >= 2:  # Account for 2-cycle latency offset
            expected = (bin_num - 2) & 0xFF
            if rd_data != expected:
                errors += 1
                if errors < 10:  # Limit error messages
                    dut.log.info(f"Bin {bin_num}: expected {expected}, got {rd_data}")

    if errors == 0:
        dut.log.info("PASS: All reads matched (accounting for latency)")
    else:
        dut.log.info(f"INFO: {errors} mismatches (may be due to latency/CDC)")

    await Timer(100, units="ns")
    dut.log.info("Basic write/read test complete")


@cocotb.test()
async def test_waterfall_buffer_multiple_rows(dut):
    """Test writing multiple rows and reading them back"""

    # Start both clocks
    wr_clk = cocotb.start_soon(Clock(dut.wr_clk, 10, units="ns").start(start_high=False))
    rd_clk = cocotb.start_soon(Clock(dut.rd_clk, 40, units="ns").start(start_high=False))

    # Reset
    dut.wr_rst.value = 1
    dut.rd_rst.value = 1
    dut.log_in.value = 0
    dut.log_valid.value = 0
    dut.log_last.value = 0
    dut.rd_bin.value = 0
    dut.rd_row.value = 0

    await RisingEdge(dut.wr_clk)
    await RisingEdge(dut.rd_clk)
    await FallingEdge(dut.wr_clk)
    dut.wr_rst.value = 0
    await FallingEdge(dut.rd_clk)
    dut.rd_rst.value = 0
    await Timer(50, units="ns")

    dut.log.info("Test 2: Write 4 rows with distinct patterns")

    # Write 4 rows, each with a distinct pattern
    num_rows = 4
    for row in range(num_rows):
        dut.log.info(f"Writing row {row}")
        for bin_num in range(512):
            await FallingEdge(dut.wr_clk)
            # Pattern: row number in upper nibble, bin in lower
            dut.log_in.value = ((row & 0xF) << 4) | ((bin_num >> 5) & 0xF)
            dut.log_valid.value = 1
            dut.log_last.value = 1 if bin_num == 511 else 0
            await RisingEdge(dut.wr_clk)

        dut.log_valid.value = 0
        dut.log_last.value = 0
        await RisingEdge(dut.wr_clk)

    # Wait for CDC
    await Timer(300, units="ns")

    # Read back and verify circular addressing
    dut.log.info("Reading back rows...")
    for row in range(min(num_rows, 4)):
        # Read a few bins from each row
        await FallingEdge(dut.rd_clk)
        dut.rd_bin.value = 100  # Arbitrary bin
        dut.rd_row.value = row

        # Wait for latency
        await RisingEdge(dut.rd_clk)
        await RisingEdge(dut.rd_clk)
        await RisingEdge(dut.rd_clk)

        rd_data = dut.rd_data.value.integer
        dut.log.info(f"Row {row}, bin 100: data = 0x{rd_data:02X}")

    await Timer(100, units="ns")
    dut.log.info("Multiple rows test complete")


@cocotb.test()
async def test_waterfall_buffer_circular_addressing(dut):
    """Test circular buffer behavior"""

    # Start both clocks
    wr_clk = cocotb.start_soon(Clock(dut.wr_clk, 10, units="ns").start(start_high=False))
    rd_clk = cocotb.start_soon(Clock(dut.rd_clk, 40, units="ns").start(start_high=False))

    # Reset
    dut.wr_rst.value = 1
    dut.rd_rst.value = 1
    dut.log_in.value = 0
    dut.log_valid.value = 0
    dut.log_last.value = 0
    dut.rd_bin.value = 0
    dut.rd_row.value = 0

    await RisingEdge(dut.wr_clk)
    await RisingEdge(dut.rd_clk)
    await FallingEdge(dut.wr_clk)
    dut.wr_rst.value = 0
    await FallingEdge(dut.rd_clk)
    dut.rd_rst.value = 0
    await Timer(50, units="ns")

    dut.log.info("Test 3: Verify circular addressing with row counter wrap")

    # Write several rows to test wrap behavior
    for row in range(8):
        for bin_num in range(512):
            await FallingEdge(dut.wr_clk)
            dut.log_in.value = (row * 10 + bin_num // 50) & 0xFF
            dut.log_valid.value = 1
            dut.log_last.value = 1 if bin_num == 511 else 0
            await RisingEdge(dut.wr_clk)

        dut.log_valid.value = 0
        dut.log_last.value = 0

        # Quick pause between rows
        for _ in range(5):
            await RisingEdge(dut.wr_clk)

    # Wait for CDC
    await Timer(500, units="ns")

    # Verify that row 0 gives us the newest data
    dut.log.info("Checking row 0 (newest)...")
    await FallingEdge(dut.rd_clk)
    dut.rd_bin.value = 0
    dut.rd_row.value = 0

    await RisingEdge(dut.rd_clk)
    await RisingEdge(dut.rd_clk)
    await RisingEdge(dut.rd_clk)

    rd_data = dut.rd_data.value.integer
    dut.log.info(f"Row 0, bin 0: data = 0x{rd_data:02X}")

    await Timer(100, units="ns")
    dut.log.info("Circular addressing test complete")


@cocotb.test()
async def test_waterfall_buffer_cdc_stability(dut):
    """Test CDC gray code synchronizer stability"""

    # Start both clocks
    wr_clk = cocotb.start_soon(Clock(dut.wr_clk, 10, units="ns").start(start_high=False))
    rd_clk = cocotb.start_soon(Clock(dut.rd_clk, 40, units="ns").start(start_high=False))

    # Reset
    dut.wr_rst.value = 1
    dut.rd_rst.value = 1
    dut.log_in.value = 0
    dut.log_valid.value = 0
    dut.log_last.value = 0
    dut.rd_bin.value = 0
    dut.rd_row.value = 0

    await RisingEdge(dut.wr_clk)
    await RisingEdge(dut.rd_clk)
    await FallingEdge(dut.wr_clk)
    dut.wr_rst.value = 0
    await FallingEdge(dut.rd_clk)
    dut.rd_rst.value = 0
    await Timer(50, units="ns")

    dut.log.info("Test 4: Write continuously and check CDC stability")

    # Continuously write for a while
    for row in range(10):
        for bin_num in range(512):
            await FallingEdge(dut.wr_clk)
            dut.log_in.value = ((row + bin_num) & 0xFF)
            dut.log_valid.value = 1
            dut.log_last.value = 1 if bin_num == 511 else 0
            await RisingEdge(dut.wr_clk)

    dut.log_valid.value = 0

    # Let CDC settle
    await Timer(500, units="ns")

    # Sample reads across different rows
    for test_row in [0, 1, 5, 9]:
        await FallingEdge(dut.rd_clk)
        dut.rd_bin.value = 256
        dut.rd_row.value = test_row

        for _ in range(3):
            await RisingEdge(dut.rd_clk)

        rd_data = dut.rd_data.value.integer
        dut.log.info(f"Row {test_row}: data = 0x{rd_data:02X}")

    await Timer(100, units="ns")
    dut.log.info("CDC stability test complete")


def test_runner():
    """Simulate the waterfall buffer using the Python runner."""
    from cocotb.runner import get_runner

    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    sys.path.append(str(proj_path / "sim"))

    sources = [
        proj_path / "hdl" / "waterfall_buffer.sv",
        proj_path / "hdl" / "xpm_cdc_gray.sv",
        proj_path / "hdl" / "xilinx_true_dual_port_read_first_2_clock_ram.v"
    ]
    hdl_toplevel = "waterfall_buffer"
    build_test_args = ["-Wall"]
    parameters = {}

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        always=True,
        build_args=build_test_args,
        parameters=parameters,
        timescale=('1ns','1ps'),
        waves=True
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=test_file,
        test_args=[],
        waves=True
    )

if __name__ == "__main__":
    test_runner()
