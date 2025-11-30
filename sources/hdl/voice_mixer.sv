module voice_mixer #(
    parameter integer DATA_WIDTH = 32,
    parameter integer NUM_VOICES = 8  // Must be a power of 2
)
(
    input wire clk,
    input wire rst,
    input wire signed [DATA_WIDTH-1:0] voice_in [NUM_VOICES-1:0],  // Array of voice inputs
    input wire data_in_valid,                                       // High when input data is valid
    output logic signed [DATA_WIDTH-1:0] mixed_out,                 // Mixed output
    output logic data_out_valid                                     // High when output is valid
);

    // Calculate number of tree stages needed (log2 of NUM_VOICES)
    localparam NUM_STAGES = $clog2(NUM_VOICES);

    // Create arrays for each stage of the adder tree
    // Stage 0 is the input, each subsequent stage has half the signals
    logic signed [DATA_WIDTH-1:0] stage [NUM_STAGES:0][NUM_VOICES-1:0];

    // Valid signal pipeline - tracks data_in_valid through the pipeline stages
    logic valid_pipe [NUM_STAGES:0];

    // Stage 0: Connect inputs directly
    always_comb begin
        for (int i = 0; i < NUM_VOICES; i++) begin
            stage[0][i] = voice_in[i];
        end
        valid_pipe[0] = data_in_valid;
    end

    // Generate adder tree stages
    genvar s, i;
    generate
        for (s = 0; s < NUM_STAGES; s++) begin : stage_gen
            // Number of valid signals at this stage
            localparam NUM_SIGNALS = NUM_VOICES >> s;
            localparam NEXT_NUM_SIGNALS = NUM_SIGNALS >> 1;

            for (i = 0; i < NEXT_NUM_SIGNALS; i++) begin : adder_gen
                // Each adder sums two adjacent signals
                always_ff @(posedge clk) begin
                    if (rst) begin
                        stage[s+1][i] <= 0;
                    end else if (valid_pipe[s]) begin
                        // Only update when valid data is present
                        // Add two signals with saturation protection
                        // Extra bit for overflow detection
                        logic signed [DATA_WIDTH:0] sum_temp;
                        sum_temp = stage[s][2*i] + stage[s][2*i + 1];

                        // Saturation logic
                        if (sum_temp > $signed({1'b0, {(DATA_WIDTH-1){1'b1}}})) begin
                            // Positive overflow: saturate to max positive
                            stage[s+1][i] <= {1'b0, {(DATA_WIDTH-1){1'b1}}};
                        end else if (sum_temp < $signed({1'b1, {(DATA_WIDTH-1){1'b0}}})) begin
                            // Negative overflow: saturate to max negative
                            stage[s+1][i] <= {1'b1, {(DATA_WIDTH-1){1'b0}}};
                        end else begin
                            // No overflow: use lower bits
                            stage[s+1][i] <= sum_temp[DATA_WIDTH-1:0];
                        end
                    end
                end
            end

            // Pipeline the valid signal
            always_ff @(posedge clk) begin
                if (rst) begin
                    valid_pipe[s+1] <= 0;
                end else begin
                    valid_pipe[s+1] <= valid_pipe[s];
                end
            end
        end
    endgenerate

    // Final output is the result of the last stage
    assign mixed_out = stage[NUM_STAGES][0];
    assign data_out_valid = valid_pipe[NUM_STAGES];

endmodule
