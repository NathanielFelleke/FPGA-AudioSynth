module x_mapping_wrapper (
    input  wire       clk,
    input  wire       rst,

    input  wire [9:0] pixel_x,
    input  wire       active,

    output wire [8:0] bin_index,
    output wire       bin_valid
);

    log_x_map u_log_x_map (
        .clk(clk),
        .rst(rst),
        .pixel_x(pixel_x),
        .active(active),
        .bin_index(bin_index),
        .bin_valid(bin_valid)
    );

endmodule
