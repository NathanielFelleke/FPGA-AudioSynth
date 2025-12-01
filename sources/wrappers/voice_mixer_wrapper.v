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

    // Create flattened packed array from individual inputs
    wire signed [(DATA_WIDTH * NUM_VOICES)-1:0] voice_in_flat;

    assign voice_in_flat[(0*DATA_WIDTH) +: DATA_WIDTH] = voice_0;
    assign voice_in_flat[(1*DATA_WIDTH) +: DATA_WIDTH] = voice_1;
    assign voice_in_flat[(2*DATA_WIDTH) +: DATA_WIDTH] = voice_2;
    assign voice_in_flat[(3*DATA_WIDTH) +: DATA_WIDTH] = voice_3;
    assign voice_in_flat[(4*DATA_WIDTH) +: DATA_WIDTH] = voice_4;
    assign voice_in_flat[(5*DATA_WIDTH) +: DATA_WIDTH] = voice_5;
    assign voice_in_flat[(6*DATA_WIDTH) +: DATA_WIDTH] = voice_6;
    assign voice_in_flat[(7*DATA_WIDTH) +: DATA_WIDTH] = voice_7;

    // Instantiate the SystemVerilog voice_mixer module
    voice_mixer #(
        .DATA_WIDTH(DATA_WIDTH),
        .NUM_VOICES(NUM_VOICES)
    ) voice_mixer_inst (
        .clk(clk),
        .rst(rst),
        .voice_in_flat(voice_in_flat),
        .data_in_valid(data_in_valid),
        .mixed_out(mixed_out),
        .data_out_valid(data_out_valid)
    );

endmodule

`default_nettype wire
