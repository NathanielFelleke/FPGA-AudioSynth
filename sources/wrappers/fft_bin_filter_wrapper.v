module fft_bin_filter_wrapper (
    //filter to take only the first half of bins
    input  wire        clk,
    input  wire        rst,

    //data from the fft
    input  wire [31:0] fft_data,
    input  wire        fft_valid,
    input  wire        fft_last,

    // To magnitude
    output wire [31:0] out_data,
    output wire        out_valid,
    output wire        out_last
);

    fft_bin_filter u_fft_bin_filter (
        .clk(clk),
        .rst(rst),
        .fft_data(fft_data),
        .fft_valid(fft_valid),
        .fft_last(fft_last),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_last(out_last)
    );

endmodule
