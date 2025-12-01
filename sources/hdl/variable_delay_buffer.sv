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
    logic [ADDR_WIDTH-1:0] wr_ptr;

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

    // --- Output registers and valid tracking ---
    // Track how many samples have been written to know when buffer is "full"
    logic [ADDR_WIDTH-1:0] write_count;

    always @(posedge clk) begin
        if (reset) begin
            out_sample <= 0;
            out_sample_valid <= 0;
            write_count <= 0;
        end else begin
            out_sample <= ram_out;

            // Increment write_count only when a sample is actually written
            if (sample_valid) begin
                // Once we've written enough samples, keep write_count saturated
                // (we only care if write_count >= delay_samples)
                if (write_count < (1 << ADDR_WIDTH) - 1) begin
                    write_count <= write_count + 1;
                end
            end

            // Output is valid once we have written at least delay_samples samples
            // Once "full", it stays valid (the read pointer always provides valid delayed data)
            // Account for the fact that write_count will increment this cycle,
            // so check against delay_samples-1 if we're about to write
            if (sample_valid) begin
                // About to increment write_count, so check if it will reach delay_samples
                if (write_count + 1 >= delay_samples) begin
                    out_sample_valid <= 1'b1;
                end else begin
                    out_sample_valid <= 1'b0;
                end
            end else begin
                // Not writing, keep current state (once valid, stays valid)
                if (write_count >= delay_samples) begin
                    out_sample_valid <= 1'b1;
                end else begin
                    out_sample_valid <= 1'b0;
                end
            end
        end
    end

    // --- Write pointer increment ---
    logic [ADDR_WIDTH-1:0] wr_ptr_next;
    assign wr_ptr_next = wr_ptr + 1;

    always @(posedge clk) begin
        if (reset)
            wr_ptr <= 0;
        else if (sample_valid)
            wr_ptr <= wr_ptr_next;
    end

endmodule
