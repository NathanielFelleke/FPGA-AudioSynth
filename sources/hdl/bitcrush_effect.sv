module bitcrush_effect #(
    parameter DATA_WIDTH = 32,       // 32-bit internal data width
    parameter LATENCY = 1            // Pipeline latency in cycles
)(
    input  wire                         clk,
    input  wire                         reset,

    // Audio stream
    input  wire                         sample_valid,
    input  wire signed [DATA_WIDTH-1:0] audio_in,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic                        audio_out_valid,

    // Control parameters
    input  wire [4:0]                   bit_depth           // (number of bits to keep) -1
);

    //calculates the amount to shift by
    logic [4:0] shift_amount;
    assign shift_amount = (DATA_WIDTH - 1) - bit_depth;  // Keep bit_depth bits

    
    logic signed [DATA_WIDTH-1:0] crushed_sample;
    assign crushed_sample = $signed(audio_in >>> shift_amount) << shift_amount;

    always_ff @(posedge clk) begin
        if (reset) begin
            audio_out <= '0;
            audio_out_valid <= 1'b0;
        end else begin
            audio_out_valid <= sample_valid;
            audio_out <= crushed_sample;
        end
    end

endmodule
