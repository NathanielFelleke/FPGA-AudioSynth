module fft_bin_filter (
    //filter to take only the first half of bins 
    input  logic        clk,
    input  logic        rst,
    
    //data from the fft
    input  logic [31:0] fft_data,
    input  logic        fft_valid,
    input  logic        fft_last,
    
    // To magnitude
    output logic [31:0] out_data,
    output logic        out_valid,
    output logic        out_last
);

    logic [9:0] bin_count;

    always_ff @(posedge clk) begin
        if (rst) begin
            bin_count <= '0;
        end else if (fft_valid) begin
            if (fft_last)
                bin_count <= '0;
            else
                bin_count <= bin_count + 1;
        end
    end

    assign out_data  = fft_data;
    assign out_valid = fft_valid && (bin_count < 512);
    assign out_last  = fft_valid && (bin_count == 511);

endmodule