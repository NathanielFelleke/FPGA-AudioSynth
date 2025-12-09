`timescale 1ns / 1ps

module fft_input_wrapper #(
    parameter INPUT_WIDTH = 32,
    parameter FFT_WIDTH   = 16,
    parameter FFT_SIZE    = 1024
)(
    input  wire                      clk,
    input  wire                      rst,

    input  wire signed [INPUT_WIDTH-1:0] audio_in,
    input  wire                          audio_valid,

    output wire [2*FFT_WIDTH-1:0] m_axis_tdata,
    output wire                   m_axis_tvalid,
    output wire                   m_axis_tlast,
    input  wire                   m_axis_tready
);

    fft_input_handler #(
        .INPUT_WIDTH(INPUT_WIDTH),
        .FFT_WIDTH(FFT_WIDTH),
        .FFT_SIZE(FFT_SIZE)
    ) fft_input_handler_inst (
        .clk(clk),
        .rst(rst),
        .audio_in(audio_in),
        .audio_valid(audio_valid),
        .m_axis_tdata(m_axis_tdata),
        .m_axis_tvalid(m_axis_tvalid),
        .m_axis_tlast(m_axis_tlast),
        .m_axis_tready(m_axis_tready)
    );

endmodule