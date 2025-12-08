module fft_magnitude #(
    parameter DATA_WIDTH = 16
)(
    input  logic        clk,
    input  logic        rst,
    

    input  logic [2*DATA_WIDTH-1:0] s_axis_tdata,
    input  logic                    s_axis_tvalid,
    input  logic                    s_axis_tlast,
    output logic                    s_axis_tready,
    
    output logic [2*DATA_WIDTH-1:0] mag_squared,
    output logic                    mag_valid,
    output logic                    mag_last
);
    //stage 1 of pipeline is square both components
    //stage 2 of pipeline is summing the squares


    // Unpack data
    logic signed [DATA_WIDTH-1:0] re, im;
    assign re = $signed(s_axis_tdata[DATA_WIDTH-1:0]);
    assign im = $signed(s_axis_tdata[2*DATA_WIDTH-1:DATA_WIDTH]);
    
    //just assign tready to 1 for now as not expecting to backpressure (FOR NOW)
    assign s_axis_tready = 1'b1;

    // Pipeline stage 1: square both components
    logic signed [2*DATA_WIDTH-1:0] re_sq, im_sq;
    logic                           valid_p1, last_p1;
    
    always_ff @(posedge clk) begin
        if (rst) begin
            re_sq    <= '0;
            im_sq    <= '0;
            valid_p1 <= 1'b0;
            last_p1  <= 1'b0;

            mag_squared <= '0;
            mag_valid   <= 1'b0;
            mag_last    <= 1'b0;
        end else begin
            //first pipeline
            re_sq    <= re * re;
            im_sq    <= im * im;
            valid_p1 <= s_axis_tvalid;
            last_p1  <= s_axis_tlast;

            //second pipeline
            mag_squared <= re_sq + im_sq;
            mag_valid   <= valid_p1;
            mag_last    <= last_p1;
        end
    end


endmodule