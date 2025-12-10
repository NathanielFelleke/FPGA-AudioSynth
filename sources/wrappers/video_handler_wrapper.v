module video_handler_wrapper #(
    parameter DELAY = 4,
    parameter WATERFALL_TOP = 300
)(
    input  wire        clk,
    input  wire        rst,

    // from video_timing module
    input  wire [9:0]  pixel_x,
    input  wire [9:0]  pixel_y,
    input  wire        hsync,
    input  wire        vsync,
    input  wire        active,

    // from color_map
    input  wire [23:0] rgb_in,

    // to the waterfall buffer module
    output wire [8:0]  rd_row,

    // to rgb2dvi ip
    output wire [23:0] rgb_out,
    output wire        hsync_out,
    output wire        vsync_out,
    output wire        active_out
);

    video_handler #(
        .DELAY(DELAY),
        .WATERFALL_TOP(WATERFALL_TOP)
    ) u_video_handler (
        .clk(clk),
        .rst(rst),
        .pixel_x(pixel_x),
        .pixel_y(pixel_y),
        .hsync(hsync),
        .vsync(vsync),
        .active(active),
        .rgb_in(rgb_in),
        .rd_row(rd_row),
        .rgb_out(rgb_out),
        .hsync_out(hsync_out),
        .vsync_out(vsync_out),
        .active_out(active_out)
    );

endmodule
