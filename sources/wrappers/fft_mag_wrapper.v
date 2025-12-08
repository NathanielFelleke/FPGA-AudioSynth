`timescale 1ns / 1ps

module fft_mag_wrapper #(
    parameter DATA_WIDTH = 16
)(
    input  wire                      clk,
    input  wire                      rst,

    input  wire [2*DATA_WIDTH-1:0] s_axis_tdata,
    input  wire                    s_axis_tvalid,
    input  wire                    s_axis_tlast,
    output wire                    s_axis_tready,

    output wire [2*DATA_WIDTH-1:0] mag_squared,
    output wire                    mag_valid,
    output wire                    mag_last
);

    fft_magnitude #(
        .DATA_WIDTH(DATA_WIDTH)
    ) fft_magnitude_inst (
        .clk(clk),
        .rst(rst),
        .s_axis_tdata(s_axis_tdata),
        .s_axis_tvalid(s_axis_tvalid),
        .s_axis_tlast(s_axis_tlast),
        .s_axis_tready(s_axis_tready),
        .mag_squared(mag_squared),
        .mag_valid(mag_valid),
        .mag_last(mag_last)
    );

endmodule
