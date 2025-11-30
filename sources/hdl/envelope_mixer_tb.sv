module envelope_mixer_tb #(
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
    output logic [ENVELOPE_WIDTH-1:0] envelope_out,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic ms_pulse
);

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

    // Extract ms_pulse from ADSR for monitoring
    assign ms_pulse = adsr.ms_pulse;

    // Envelope Mixer
    envelope_mixer #(
        .DATA_WIDTH(DATA_WIDTH),
        .ENVELOPE_WIDTH(ENVELOPE_WIDTH)
    ) mixer (
        .clk(clk),
        .rst(rst),
        .audio_in(audio_in),
        .envelope_in(envelope_out),
        .audio_out(audio_out)
    );

endmodule
