// Verilog wrapper for effect_mux SystemVerilog module
// Converts SystemVerilog logic to wire for IP integration

module effect_mux_wrapper #(
    parameter DATA_WIDTH = 32
)(
    input wire                         clk,
    input wire                         reset,

    // Audio stream
    input wire                         sample_valid,
    input wire signed [DATA_WIDTH-1:0] audio_in,
    output wire signed [DATA_WIDTH-1:0] audio_out,
    output wire                        audio_out_valid,

    // Effect enable/bypass controls
    input wire                         enable_bitcrush,
    input wire                         enable_delay,

    // Bitcrush parameters
    input wire [4:0]                   bit_depth,

    // Delay parameters
    input wire [15:0]                  delay_samples,
    input wire [7:0]                   feedback_amount
);

    // Internal signals
    wire signed [DATA_WIDTH-1:0] audio_out_internal;
    wire audio_out_valid_internal;

    // Instantiate the effect_mux module
    effect_mux #(
        .DATA_WIDTH(DATA_WIDTH)
    ) effect_mux_inst (
        .clk(clk),
        .reset(reset),
        .sample_valid(sample_valid),
        .audio_in(audio_in),
        .audio_out(audio_out_internal),
        .audio_out_valid(audio_out_valid_internal),
        .enable_bitcrush(enable_bitcrush),
        .enable_delay(enable_delay),
        .bit_depth(bit_depth),
        .delay_samples(delay_samples),
        .feedback_amount(feedback_amount)
    );

    // Assign internal signals to outputs
    assign audio_out = audio_out_internal;
    assign audio_out_valid = audio_out_valid_internal;

endmodule
