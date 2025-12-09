module log_scale_wrapper (
    input  wire        clk,
    input  wire        rst,

    input  wire [31:0] mag_squared,
    input  wire        mag_valid,
    input  wire        mag_last,

    output wire [7:0]  log_out,
    output wire        log_valid,
    output wire        log_last
);

    log_scale u_log_scale (
        .clk(clk),
        .rst(rst),
        .mag_squared(mag_squared),
        .mag_valid(mag_valid),
        .mag_last(mag_last),
        .log_out(log_out),
        .log_valid(log_valid),
        .log_last(log_last)
    );

endmodule
