`timescale 1ns / 1ps

module synth_wrapper #(
    parameter integer AUDIO_WIDTH = 32,
    parameter integer NUM_VOICES = 8
)
(
    input wire clk,
    input wire rst,
    input wire midi_in,
    input wire octave_on,
    output wire signed [AUDIO_WIDTH-1:0] voice_1_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_2_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_3_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_4_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_5_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_6_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_7_out,
    output wire signed [AUDIO_WIDTH-1:0] voice_8_out,
    output wire [NUM_VOICES-1:0] note_on,
    output wire data_valid 
);

    synth #(
        .AUDIO_WIDTH(AUDIO_WIDTH),
        .NUM_VOICES(NUM_VOICES)
    ) synth_inst (
        .clk(clk),
        .rst(rst),
        .midi_in(midi_in),
        .octave_on(octave_on),
        .voice_1_out(voice_1_out),
        .voice_2_out(voice_2_out),
        .voice_3_out(voice_3_out),
        .voice_4_out(voice_4_out),
        .voice_5_out(voice_5_out),
        .voice_6_out(voice_6_out),
        .voice_7_out(voice_7_out),
        .voice_8_out(voice_8_out),
        .ons_out(note_on),
        .data_valid(data_valid)
    );

endmodule
