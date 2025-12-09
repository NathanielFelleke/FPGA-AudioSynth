// Behavioral model of Xilinx XPM_CDC_GRAY for simulation
// This is a simple 2-flop synchronizer for testbench use
// Does NOT perform actual gray code conversion (not needed for functional sim)

module xpm_cdc_gray #(
    parameter WIDTH = 8,
    parameter INIT_SYNC_FF = 0,
    parameter REG_OUTPUT = 0,
    parameter SIM_ASSERT_CHK = 0,
    parameter SIM_LOSSLESS_GRAY_CHK = 0
)(
    input  logic             src_clk,
    input  logic [WIDTH-1:0] src_in_bin,
    input  logic             dest_clk,
    output logic [WIDTH-1:0] dest_out_bin
);

    // Simple two-stage synchronizer for simulation
    // In real hardware, this would convert to/from gray code
    logic [WIDTH-1:0] sync_stage1, sync_stage2;

    always_ff @(posedge dest_clk) begin
        sync_stage1 <= src_in_bin;
        sync_stage2 <= sync_stage1;
    end

    assign dest_out_bin = sync_stage2;

endmodule
