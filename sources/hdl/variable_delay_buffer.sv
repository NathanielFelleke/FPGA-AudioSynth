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

    // --- Write pointer: points to next write location ---
    logic [ADDR_WIDTH-1:0] wr_ptr;

    // --- Read pointer: wr_ptr - delay_samples ---
    // Modular arithmetic handles wrap naturally for circular buffer
    logic [ADDR_WIDTH-1:0] rd_ptr;
    assign rd_ptr = wr_ptr - delay_samples;

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
        .dinb  ({DATA_WIDTH{1'b0}}),
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

    // --- Track total samples written ---
    logic [ADDR_WIDTH-1:0] write_count;

    // --- Write pointer management ---
    always_ff @(posedge clk) begin
        if (reset) begin
            wr_ptr <= '0;
        end else if (sample_valid) begin
            wr_ptr <= wr_ptr + 1'b1;
        end
    end

    // --- Output and valid logic ---
    always_ff @(posedge clk) begin
        if (reset) begin
            out_sample       <= '0;
            out_sample_valid <= 1'b0;
            write_count      <= '0;
        end else begin
            // Always capture RAM output (continuously reading from rd_ptr)
            out_sample <= ram_out;

            // Track samples written (saturate at max to prevent overflow)
            if (sample_valid && write_count < {ADDR_WIDTH{1'b1}}) begin
                write_count <= write_count + 1'b1;
            end

            // FIX: Valid is computed fresh each cycle, not "set and forget"
            // Output is valid when:
            // 1. We're actively processing a sample (sample_valid), AND
            // 2. We have enough samples buffered for the requested delay
            out_sample_valid <= sample_valid && (write_count >= delay_samples);
        end
    end

endmodule