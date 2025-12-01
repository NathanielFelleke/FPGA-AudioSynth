module bypass_effect #(  //a module that can passthrough with same latency as an effect
    parameter DATA_WIDTH = 32,
    parameter LATENCY = 1
)(
    input  wire                         clk,
    input  wire                         reset,
    input  wire                         sample_valid,
    input  wire signed [DATA_WIDTH-1:0] audio_in,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic                        audio_out_valid
);

    generate
        if (LATENCY == 0) begin
            // No latency, a comb through
            assign audio_out = audio_in;
            assign audio_out_valid = sample_valid;
        end
        else begin
            // pipeline with latency cycles
            logic signed [DATA_WIDTH-1:0] pipeline [LATENCY];
            logic valid_pipeline [LATENCY];

            always_ff @(posedge clk) begin
                if (reset) begin
                    for (int i = 0; i < LATENCY; i++) begin
                        pipeline[i] <= '0;
                        valid_pipeline[i] <= 1'b0;
                    end
                end
                else begin
                    //shifting data through
                    pipeline[0] <= audio_in;
                    valid_pipeline[0] <= sample_valid;

                    for (int i = 1; i < LATENCY; i++) begin
                        pipeline[i] <= pipeline[i-1];
                        valid_pipeline[i] <= valid_pipeline[i-1];
                    end
                end
            end
            //output the data out
            assign audio_out = pipeline[LATENCY-1];
            assign audio_out_valid = valid_pipeline[LATENCY-1];
        end
    endgenerate

endmodule
