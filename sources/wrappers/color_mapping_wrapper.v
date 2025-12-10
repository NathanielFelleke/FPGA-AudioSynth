module color_mapping_wrapper (
    input  wire       clk,
    input  wire       rst,

    input  wire [7:0] log_val,
    input  wire       valid_in,

    output wire [23:0] rgb,
    output wire        valid_out
);

    color_map u_color_map (
        .clk(clk),
        .rst(rst),
        .log_val(log_val),
        .valid_in(valid_in),
        .rgb(rgb),
        .valid_out(valid_out)
    );

endmodule
