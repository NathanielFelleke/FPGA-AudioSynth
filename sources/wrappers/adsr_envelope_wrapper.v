`timescale 1ns / 1ps
`default_nettype none

module adsr_envelope_wrapper #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ENVELOPE_WIDTH = 32,
    parameter integer RATE_WIDTH = 16
)
(
    input wire clk,
    input wire rst,
    input wire note_on,
    input wire [RATE_WIDTH-1:0] attack_time,
    input wire [RATE_WIDTH-1:0] decay_time,
    input wire [6:0] sustain_percent,
    input wire [RATE_WIDTH-1:0] release_time,
    input wire signed [DATA_WIDTH-1:0] audio_in,
    input wire data_in_valid,
    output wire signed [DATA_WIDTH-1:0] audio_out,
    output wire data_out_valid
);

    // Internal wire to connect ADSR output to mixer input
    wire [ENVELOPE_WIDTH-1:0] envelope_out;

    // ADSR Envelope Generator
    adsr_envelope #(
        .RATE_WIDTH(RATE_WIDTH),
        .ENVELOPE_WIDTH(ENVELOPE_WIDTH)
    ) adsr (
        .clk(clk),
        .rst(rst),
        .attack_time(attack_time),
        .decay_time(decay_time),
        .sustain_percent(sustain_percent),
        .release_time(release_time),
        .note_on(note_on),
        .envelope_out(envelope_out)
    );

    // Envelope Mixer
    envelope_mixer #(
        .DATA_WIDTH(DATA_WIDTH),
        .ENVELOPE_WIDTH(ENVELOPE_WIDTH)
    ) mixer (
        .clk(clk),
        .rst(rst),
        .audio_in(audio_in),
        .data_in_valid(data_in_valid),
        .envelope_in(envelope_out),
        .audio_out(audio_out),
        .data_out_valid(data_out_valid)
    );

endmodule

`default_nettype wire
