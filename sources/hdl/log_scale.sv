module log_scale (
    input  logic        clk,
    input  logic        rst,
    
    input  logic [31:0] mag_squared,
    input  logic        mag_valid,
    input  logic        mag_last,
    
    output logic [7:0]  log_out,
    output logic        log_valid,
    output logic        log_last
);

    //LOGIC TO FIND THE LEADING ONE
    logic [4:0] leading_one;
    
    always_comb begin
        if      (mag_squared[31]) leading_one = 31;
        else if (mag_squared[30]) leading_one = 30;
        else if (mag_squared[29]) leading_one = 29;
        else if (mag_squared[28]) leading_one = 28;
        else if (mag_squared[27]) leading_one = 27;
        else if (mag_squared[26]) leading_one = 26;
        else if (mag_squared[25]) leading_one = 25;
        else if (mag_squared[24]) leading_one = 24;
        else if (mag_squared[23]) leading_one = 23;
        else if (mag_squared[22]) leading_one = 22;
        else if (mag_squared[21]) leading_one = 21;
        else if (mag_squared[20]) leading_one = 20;
        else if (mag_squared[19]) leading_one = 19;
        else if (mag_squared[18]) leading_one = 18;
        else if (mag_squared[17]) leading_one = 17;
        else if (mag_squared[16]) leading_one = 16;
        else if (mag_squared[15]) leading_one = 15;
        else if (mag_squared[14]) leading_one = 14;
        else if (mag_squared[13]) leading_one = 13;
        else if (mag_squared[12]) leading_one = 12;
        else if (mag_squared[11]) leading_one = 11;
        else if (mag_squared[10]) leading_one = 10;
        else if (mag_squared[9])  leading_one = 9;
        else if (mag_squared[8])  leading_one = 8;
        else if (mag_squared[7])  leading_one = 7;
        else if (mag_squared[6])  leading_one = 6;
        else if (mag_squared[5])  leading_one = 5;
        else if (mag_squared[4])  leading_one = 4;
        else if (mag_squared[3])  leading_one = 3;
        else if (mag_squared[2])  leading_one = 2;
        else if (mag_squared[1])  leading_one = 1;
        else                      leading_one = 0;
end

    // Pipeline stage 1: normalize and register
    logic [4:0]  log_int_p1;
    logic [31:0] mag_norm_p1;
    logic        valid_p1, last_p1;
    
    always_ff @(posedge clk) begin
        if (rst) begin
            log_int_p1  <= '0;
            mag_norm_p1 <= '0;
            valid_p1    <= 1'b0;
            last_p1     <= 1'b0;

            log_out   <= '0;
            log_valid <= 1'b0;
            log_last  <= 1'b0;
        end else begin
            //stage 1
            log_int_p1  <= leading_one;
            mag_norm_p1 <= mag_squared << (31 - leading_one);
            valid_p1    <= mag_valid;
            last_p1     <= mag_last;

            //stage 2
            log_out   <= {log_int_p1, mag_norm_p1[31:29]};
            log_valid <= valid_p1;
            log_last  <= last_p1;
        end
    end

endmodule