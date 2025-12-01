`timescale 1ns / 1ps
`default_nettype none

module voice_mixer_wrapper #(
    parameter DATA_WIDTH = 32,
    parameter NUM_VOICES = 8
)
(
    input wire clk,
    input wire rst,

    // Individual voice inputs for easy Vivado IP Integrator connectivity
    input wire signed [DATA_WIDTH-1:0] voice_0,
    input wire signed [DATA_WIDTH-1:0] voice_1,
    input wire signed [DATA_WIDTH-1:0] voice_2,
    input wire signed [DATA_WIDTH-1:0] voice_3,
    input wire signed [DATA_WIDTH-1:0] voice_4,
    input wire signed [DATA_WIDTH-1:0] voice_5,
    input wire signed [DATA_WIDTH-1:0] voice_6,
    input wire signed [DATA_WIDTH-1:0] voice_7,

    input wire data_in_valid,

    output wire signed [DATA_WIDTH-1:0] mixed_out,
    output wire data_out_valid
);

    // Create array from individual inputs
    wire signed [DATA_WIDTH-1:0] voice_array [0:NUM_VOICES-1];

    assign voice_array[0] = voice_0;
    assign voice_array[1] = voice_1;
    assign voice_array[2] = voice_2;
    assign voice_array[3] = voice_3;
    assign voice_array[4] = voice_4;
    assign voice_array[5] = voice_5;
    assign voice_array[6] = voice_6;
    assign voice_array[7] = voice_7;

    // Instantiate the SystemVerilog voice_mixer module
    voice_mixer #(
        .DATA_WIDTH(DATA_WIDTH),
        .NUM_VOICES(NUM_VOICES)
    ) voice_mixer_inst (
        .clk(clk),
        .rst(rst),
        .voice_in(voice_array),
        .data_in_valid(data_in_valid),
        .mixed_out(mixed_out),
        .data_out_valid(data_out_valid)
    );

endmodule

`default_nettype wire
