module effect_mux #(
    parameter DATA_WIDTH = 32
)(
    input  wire clk,
    input  wire rst,

    input  wire sample_valid, //AXI STREAM IN
    input  wire signed [DATA_WIDTH-1:0] audio_in,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic audio_out_valid,

    // ENABLE CONTROLS
    input  wire  enable_bitcrush,
    input  wire  enable_delay,

    // BITCRUSH PARAMETERS
    input  wire [4:0] bit_depth,

    // DELAY PARAMETERS
    input  wire [15:0]  delay_samples,
    input  wire [7:0]  feedback_amount
);

    // Stage 1: Bitcrush effect (optional)
    logic signed [DATA_WIDTH-1:0] stage1_out;
    logic stage1_valid;

    logic signed [DATA_WIDTH-1:0] bitcrush_out;
    logic bitcrush_valid;

    bitcrush_effect #(
        .DATA_WIDTH(DATA_WIDTH),
        .LATENCY(1)
    ) bitcrush_inst (
        .clk(clk),
        .rst(rst),
        .sample_valid(sample_valid),
        .audio_in(audio_in),
        .audio_out(bitcrush_out),
        .audio_out_valid(bitcrush_valid),
        .bit_depth(bit_depth)
    );

    // Bypass path with latency compensation
    logic signed [DATA_WIDTH-1:0] bitcrush_bypass_out;
    logic bitcrush_bypass_valid;

    bypass_effect #(
        .DATA_WIDTH(DATA_WIDTH),
        .LATENCY(1)
    ) bitcrush_bypass_inst (
        .clk(clk),
        .rst(rst),
        .sample_valid(sample_valid),
        .audio_in(audio_in),
        .audio_out(bitcrush_bypass_out),
        .audio_out_valid(bitcrush_bypass_valid)
    );

    //mux if to use bitcrush or bypass
    assign stage1_out = enable_bitcrush ? bitcrush_out : bitcrush_bypass_out;
    assign stage1_valid = enable_bitcrush ? bitcrush_valid : bitcrush_bypass_valid;

    // Stage 2: Delay effect (optional)
    logic signed [DATA_WIDTH-1:0] stage2_out;
    logic stage2_valid;

    logic signed [DATA_WIDTH-1:0] delay_out;
    logic delay_valid;

    delay_effect #(
        .ADDR_WIDTH(16),
        .DATA_WIDTH(DATA_WIDTH),
        .FEEDBACK_WIDTH(8),
        .LATENCY(7)
    ) delay_inst (
        .clk(clk),
        .rst(rst),
        .sample_valid(stage1_valid),
        .audio_in(stage1_out),
        .audio_out(delay_out),
        .audio_out_valid(delay_valid),
        .delay_samples(delay_samples),
        .feedback_amount(feedback_amount),
        .effect_amount(8'd255),  // Always 100% wet (effect is the processed signal)
        .mode(1'b1)              // Feedback mode
    );

    // Bypass path with latency compensation
    logic signed [DATA_WIDTH-1:0] delay_bypass_out;
    logic delay_bypass_valid;

    bypass_effect #(
        .DATA_WIDTH(DATA_WIDTH),
        .LATENCY(7)
    ) delay_bypass_inst (
        .clk(clk),
        .rst(rst),
        .sample_valid(stage1_valid),
        .audio_in(stage1_out),
        .audio_out(delay_bypass_out),
        .audio_out_valid(delay_bypass_valid)
    );

    // Mux: use delay if enabled, otherwise use bypass
    assign stage2_out = enable_delay ? delay_out : delay_bypass_out;
    assign stage2_valid = enable_delay ? delay_valid : delay_bypass_valid;

    // =========================================================================
    // Output register
    // =========================================================================
    always_ff @(posedge clk) begin
        if (rst) begin
            audio_out <= '0;
            audio_out_valid <= 1'b0;
        end else begin
            audio_out_valid <= stage2_valid;
            audio_out <= stage2_out;
        end
    end

endmodule
