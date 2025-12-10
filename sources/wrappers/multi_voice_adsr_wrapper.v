`timescale 1ns / 1ps
`default_nettype none

module multi_voice_adsr_wrapper #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ENVELOPE_WIDTH = 32,
    parameter integer RATE_WIDTH = 16,
    parameter integer NUM_VOICES = 8
)
(
    input wire clk,
    input wire rst,

    // Shared ADSR parameters for all voices
    input wire [RATE_WIDTH-1:0] attack_time,
    input wire [RATE_WIDTH-1:0] decay_time,
    input wire [6:0] sustain_percent,
    input wire [RATE_WIDTH-1:0] release_time,

    // Individual note_on signals for each voice
    input wire [NUM_VOICES-1:0] note_on,

    // Individual voice audio inputs
    input wire signed [DATA_WIDTH-1:0] voice_0_in,
    input wire signed [DATA_WIDTH-1:0] voice_1_in,
    input wire signed [DATA_WIDTH-1:0] voice_2_in,
    input wire signed [DATA_WIDTH-1:0] voice_3_in,
    input wire signed [DATA_WIDTH-1:0] voice_4_in,
    input wire signed [DATA_WIDTH-1:0] voice_5_in,
    input wire signed [DATA_WIDTH-1:0] voice_6_in,
    input wire signed [DATA_WIDTH-1:0] voice_7_in,

    input wire data_in_valid,

    // Individual voice audio outputs
    output wire signed [DATA_WIDTH-1:0] voice_0_out,
    output wire signed [DATA_WIDTH-1:0] voice_1_out,
    output wire signed [DATA_WIDTH-1:0] voice_2_out,
    output wire signed [DATA_WIDTH-1:0] voice_3_out,
    output wire signed [DATA_WIDTH-1:0] voice_4_out,
    output wire signed [DATA_WIDTH-1:0] voice_5_out,
    output wire signed [DATA_WIDTH-1:0] voice_6_out,
    output wire signed [DATA_WIDTH-1:0] voice_7_out,

    output wire data_out_valid
);

    // Create arrays from individual inputs
    wire signed [DATA_WIDTH-1:0] voice_in [0:NUM_VOICES-1];
    wire signed [DATA_WIDTH-1:0] voice_out [0:NUM_VOICES-1];
    wire [NUM_VOICES-1:0] voice_valid_out;

    assign voice_in[0] = voice_0_in;
    assign voice_in[1] = voice_1_in;
    assign voice_in[2] = voice_2_in;
    assign voice_in[3] = voice_3_in;
    assign voice_in[4] = voice_4_in;
    assign voice_in[5] = voice_5_in;
    assign voice_in[6] = voice_6_in;
    assign voice_in[7] = voice_7_in;

    assign voice_0_out = voice_out[0];
    assign voice_1_out = voice_out[1];
    assign voice_2_out = voice_out[2];
    assign voice_3_out = voice_out[3];
    assign voice_4_out = voice_out[4];
    assign voice_5_out = voice_out[5];
    assign voice_6_out = voice_out[6];
    assign voice_7_out = voice_out[7];

    // All voices should have same valid output (same pipeline delay)
    assign data_out_valid = voice_valid_out[0];

    // Generate ADSR envelope wrapper for each voice
    genvar i;
    generate
        for (i = 0; i < NUM_VOICES; i = i + 1) begin : adsr_voice
            adsr_envelope_wrapper #(
                .DATA_WIDTH(DATA_WIDTH),
                .ENVELOPE_WIDTH(ENVELOPE_WIDTH),
                .RATE_WIDTH(RATE_WIDTH)
            ) adsr_wrapper_inst (
                .clk(clk),
                .rst(rst),
                .note_on(note_on[i]),
                .attack_time(attack_time),
                .decay_time(decay_time),
                .sustain_percent(sustain_percent),
                .release_time(release_time),
                .audio_in(voice_in[i]),
                .data_in_valid(data_in_valid),
                .audio_out(voice_out[i]),
                .data_out_valid(voice_valid_out[i])
            );
        end
    endgenerate

endmodule

`default_nettype wire