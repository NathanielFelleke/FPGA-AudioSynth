module audio_fir #(
    parameter DATA_WIDTH = 32,
    parameter NUM_COEFFS = 64,
    parameter COEFF_WIDTH = 16
)
(
    input wire clk,
    input wire rst,
    input wire signed [DATA_WIDTH-1:0] data_in,
    input wire data_in_valid, //high when input data is valid (most likely poseedge of audio clock)
    input wire signed [NUM_COEFFS-1:0][COEFF_WIDTH-1:0] coeffs,
    output logic signed [DATA_WIDTH-1:0] data_out,
    output logic data_out_valid
);
    logic signed[DATA_WIDTH+COEFF_WIDTH-1:0] sums [NUM_COEFFS - 1:0];
    always_comb begin
        data_out = sums[0][DATA_WIDTH-1:0]; //get the right portion of the sum
    end
    always_ff @(posedge clk)begin
        if(rst)begin //reset all the values
             for (int i=0; i<NUM_COEFFS; i=i+1) begin
                sums[i] <= 0;
             end
            
            data_out_valid <= 0;
        end else begin
            if(data_in_valid) begin
                sums[NUM_COEFFS-1] <= $signed(data_in) * $signed(coeffs[NUM_COEFFS-1]);  // get sum of n-15 term
                for(int i = NUM_COEFFS-2; i >= 0; i = i - 1) begin //get all sums
                    sums[i] <= $signed(sums[i+1]) + $signed(data_in) * $signed(coeffs[i]);
                end
                data_out_valid <= 1'b1; //data is valid
            end
            else begin
                data_out_valid <= 1'b0;

            end
        end
    end
endmodule