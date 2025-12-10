module delay #
    (
        parameter integer DATA_WIDTH = 32,
        parameter integer BUFFER_SIZE = 4
    )
    (
        input wire signed [DATA_WIDTH-1 : 0] data_in,
        input wire [BUFFER_SIZE-1:0] delay_len,
        input wire [$clog2(DATA_WIDTH):0] decay_weight,
        input wire clk,
        input wire rst,
        output logic signed [DATA_WIDTH-1 : 0] data_out
    );

    //ram
    logic [DATA_WIDTH-1:0] delay_buf_out;
    logic [BUFFER_SIZE-1:0] delay_counter_w = 0;
    logic [BUFFER_SIZE-1:0] delay_counter_r = 2;

    assign data_out = $signed(data_in) + $signed(delay_buf_out);
    
    always_ff @(posedge clk) begin
        if (rst) begin
            delay_counter_w <= 0;
            delay_counter_r <= 2;
        end else begin
            if (delay_counter_w >= delay_len) begin
                delay_counter_w <= 0;
            end else begin
                delay_counter_w <= delay_counter_w + 1;
            end
            if (delay_counter_r >= delay_len) begin
                delay_counter_r <= 0;
            end else begin
                delay_counter_r <= delay_counter_r + 1;
            end
        end
    end

    xilinx_true_dual_port_read_first_2_clock_ram #(
        .RAM_WIDTH(32),                       // Specify RAM data width
        .RAM_DEPTH(1<<BUFFER_SIZE),                     // Specify RAM depth (number of entries)
        .RAM_PERFORMANCE("HIGH_PERFORMANCE"), // Select "HIGH_PERFORMANCE" or "LOW_LATENCY" 
        .INIT_FILE()          // Specify name/location of RAM initialization file if using one (leave blank if not)
    ) delay_buffer (
        .addra(delay_counter_w),  // Port A address bus, width determined from RAM_DEPTH
        .addrb(delay_counter_r),  // Port B address bus, width determined from RAM_DEPTH
        .dina($signed(data_out)>>>decay_weight),   // Port A RAM input data
        .dinb(),   // Port B RAM input data
        .clka(clk),   // Port A clock
        .clkb(clk),    // Port B clock
        .wea(1),    // Port A write enable
        .web(0),    // Port B write enable
        .ena(1),    // Port A RAM Enable, for additional power savings, disable port when not in use
        .enb(1),    // Port B RAM Enable, for additional power savings, disable port when not in use
        .rsta(rst),   // Port A output reset (does not affect memory contents)
        .rstb(rst),   // Port B output reset (does not affect memory contents)
        .regcea(1), // Port A output register enable
        .regceb(1), // Port B output register enable
        .douta(),  // Port A RAM output data
        .doutb(delay_buf_out)   // Port B RAM output data
    );

endmodule