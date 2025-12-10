module hdmi_control_wrapper (
    input  wire       clk,        // 40 MHz
    input  wire       rst,

    // Pixel coordinates
    output wire [9:0] pixel_x,
    output wire [9:0] pixel_y,

    // Sync signals
    output wire       hsync,
    output wire       vsync,
    output wire       active
);

    hdmi_control u_hdmi_control (
        .clk(clk),
        .rst(rst),
        .pixel_x(pixel_x),
        .pixel_y(pixel_y),
        .hsync(hsync),
        .vsync(vsync),
        .active(active)
    );

endmodule
