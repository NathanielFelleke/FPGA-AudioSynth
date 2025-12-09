module waterfall_buffer_wrapper (
    input  wire        wr_clk,
    input  wire        wr_rst,
    input  wire [7:0]  log_in,
    input  wire        log_valid,
    input  wire        log_last,

    input  wire        rd_clk,
    input  wire        rd_rst,
    input  wire [8:0]  rd_bin,
    input  wire [7:0]  rd_row,
    output wire [7:0]  rd_data
);

    waterfall_buffer u_waterfall_buffer (
        .wr_clk(wr_clk),
        .wr_rst(wr_rst),
        .log_in(log_in),
        .log_valid(log_valid),
        .log_last(log_last),
        .rd_clk(rd_clk),
        .rd_rst(rd_rst),
        .rd_bin(rd_bin),
        .rd_row(rd_row),
        .rd_data(rd_data)
    );

endmodule
