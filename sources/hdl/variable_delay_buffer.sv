module variable_delay_buffer #(
    parameter ADDR_WIDTH = 16,
    parameter DATA_WIDTH = 32
)(
    input  wire                      clk,
    input  wire                      rst,

    input  wire                      sample_valid,
    input  wire [DATA_WIDTH-1:0]     in_sample,
    input  wire [ADDR_WIDTH-1:0]     delay_samples,

    output logic [DATA_WIDTH-1:0]     out_sample,
    output logic                      out_sample_valid
);

    localparam RAM_DEPTH = (1 << ADDR_WIDTH);

    logic [ADDR_WIDTH-1:0] wr_ptr;
    logic [ADDR_WIDTH-1:0] rd_ptr;
    logic [DATA_WIDTH-1:0] ram_out; 
    logic [2:0] valid_pipe;

    //update the pointers when valid data
    always_ff @(posedge clk) begin
        if (rst) begin
            wr_ptr <= '0;
            rd_ptr <= '0;
        end else if (sample_valid) begin
            wr_ptr <= wr_ptr + 1'b1;
        
            rd_ptr <= wr_ptr - delay_samples;
        end
    end

    // Xilinx Dual Port BRAM Instantiation
    xilinx_true_dual_port_read_first_2_clock_ram #(
        .RAM_WIDTH(DATA_WIDTH),
        .RAM_DEPTH(RAM_DEPTH),
        .RAM_PERFORMANCE("HIGH_PERFORMANCE"), // Enforces 2-cycle latency with output register
        .INIT_FILE("")
    ) ram_inst (
        // Port A (Write)
        .addra  (wr_ptr),
        .dina   (in_sample),
        .wea    (sample_valid),
        .clka   (clk),
        .ena    (1'b1),
        .rsta   (1'b0),
        .regcea (1'b1),
        .douta  (),

        // Port B (Read)
        .addrb  (rd_ptr),
        .dinb   ('0),
        .web    (1'b0),
        .clkb   (clk),
        .enb    (1'b1),
        .rstb   (1'b0),
        .regceb (1'b1),
        .doutb  (ram_out)
    );

    //pipeline the output
    always_ff @(posedge clk) begin
        if (rst) begin
            out_sample       <= '0;
            valid_pipe       <= '0;
            out_sample_valid <= 1'b0;
        end else begin
            // output data
            out_sample <= ram_out;
            
            valid_pipe[0] <= sample_valid;
            valid_pipe[1] <= valid_pipe[0];
            valid_pipe[2] <= valid_pipe[1]; 

            out_sample_valid <= valid_pipe[2]; 
        end
    end

endmodule