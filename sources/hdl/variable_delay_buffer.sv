module variable_delay_buffer #(
    parameter ADDR_WIDTH = 16,  // 2^16 = 65536 samples
    parameter DATA_WIDTH = 32
)(
    input  wire                     clk,
    input  wire                     reset,

    input  wire                     sample_valid,
    input  wire [DATA_WIDTH-1:0]    in_sample,
    input  wire [ADDR_WIDTH-1:0]    delay_samples,

    output logic [DATA_WIDTH-1:0]   out_sample,
    output logic                    out_sample_valid
);

    localparam RAM_DEPTH = (1 << ADDR_WIDTH);

    // --- Internal pointers ---
    logic [ADDR_WIDTH-1:0] wr_ptr = 0;

    // Read pointer: compensate for BRAM 1-cycle latency by reading 1 address ahead
    // This makes the actual delay exactly 'delay_samples' cycles
    logic [ADDR_WIDTH-1:0] rd_ptr;
    assign rd_ptr = (wr_ptr + 1) - delay_samples;

    // --- RAM output ---
    logic [DATA_WIDTH-1:0] ram_out;

    // --- Xilinx dual port RAM ---
    xilinx_true_dual_port_read_first_2_clock_ram #(
        .RAM_WIDTH(DATA_WIDTH),
        .RAM_DEPTH(RAM_DEPTH),
        .RAM_PERFORMANCE("LOW_LATENCY")
    ) ram_inst (
        .addra (wr_ptr),
        .addrb (rd_ptr),

        .dina  (in_sample),
        .dinb  (0),

        .clka  (clk),
        .clkb  (clk),

        .wea   (sample_valid),
        .web   (1'b0),

        .ena   (1'b1),
        .enb   (1'b1),

        .rsta  (1'b0),
        .rstb  (1'b0),

        .regcea(1'b1),
        .regceb(1'b1),

        .douta (),
        .doutb (ram_out)
    );

    // --- Output registers ---
    always @(posedge clk) begin
        if (reset) begin
            out_sample <= 0;
            out_sample_valid <= 0;
        end else begin
            out_sample_valid <= sample_valid;  // valid delayed by 1 cycle to match output
            if (sample_valid)
                out_sample <= ram_out;
        end
    end

    // --- Write pointer increment ---
    always @(posedge clk) begin
        if (reset)
            wr_ptr <= 0;
        else if (sample_valid)
            wr_ptr <= wr_ptr + 1;
    end

endmodule
