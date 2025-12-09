module waterfall_buffer (
    //main clock writing into it
    input  logic        wr_clk,
    input  logic        wr_rst,
    input  logic [7:0]  log_in,
    input  logic        log_valid,
    input  logic        log_last,
    
    //25 Mhz clock (which runs video logic) reading from
    input  logic        rd_clk,
    input  logic        rd_rst,
    input  logic [8:0]  rd_bin,
    input  logic [7:0]  rd_row,
    output logic [7:0]  rd_data
);

    //counters for bin and row for the writing side
    logic [8:0] wr_bin;
    logic [7:0] wr_row;

    always_ff @(posedge wr_clk) begin
        if (wr_rst) begin
            wr_bin <= '0;
            wr_row <= '0;
        end else if (log_valid) begin
            if (log_last) begin

                wr_bin <= '0;

                wr_row <= wr_row + 1;
            end else begin


                wr_bin <= wr_bin + 1;
            end
        end
    end

    //Using gray code to sync the write row to the read row (safely)
    logic [7:0] wr_row_rd;

    xpm_cdc_gray #( //vivado ip for gray code
        .WIDTH(8)
    ) row_sync (
        .src_clk(wr_clk),
        .src_in_bin(wr_row),
        .dest_clk(rd_clk),
        .dest_out_bin(wr_row_rd)
    );

    //read address based on the wr_row
    logic [7:0] rd_row_addr;
    assign rd_row_addr = wr_row_rd - rd_row - 1;

    // using bram for storing this data
    xilinx_true_dual_port_read_first_2_clock_ram #(
        .RAM_WIDTH(8),
        .RAM_DEPTH(512 * 256),
        .RAM_PERFORMANCE("HIGH_PERFORMANCE")
    ) frame_mem (
        .clka(wr_clk),
        .clkb(rd_clk),
        .addra({wr_row, wr_bin}),
        .addrb({rd_row_addr, rd_bin}),
        .dina(log_in),
        .dinb(8'b0),
        .wea(log_valid),
        .web(1'b0),
        .ena(1'b1),
        .enb(1'b1),
        .rsta(wr_rst),
        .rstb(rd_rst),
        .regcea(1'b1),
        .regceb(1'b1),
        .douta(),
        .doutb(rd_data)
    );

endmodule