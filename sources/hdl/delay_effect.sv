module delay_effect #(
    parameter ADDR_WIDTH = 16,      // 2^16 = 65536 samples (~1.36s at 48kHz)
    parameter DATA_WIDTH = 32,      // 32-bit internal data width
    parameter FEEDBACK_WIDTH = 8,   // 8-bit feedback control
    parameter LATENCY = 8           // Pipeline latency in cycles (2 feedback + 3 buffer + 3 mixer)
)(
    input  wire                         clk,
    input  wire                         reset,
    
    // Audio stream
    input  wire                         sample_valid,
    input  wire signed [DATA_WIDTH-1:0] audio_in,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic                        audio_out_valid,
    
    // Control parameters
    input  wire [ADDR_WIDTH-1:0]        delay_samples,      // Delay time in samples
    input  wire [FEEDBACK_WIDTH-1:0]    feedback_amount,    // 0-255 (0.0 to ~1.0)
    input  wire [7:0]                   effect_amount,      // 0-255 (dry to wet mix)
    input  wire                         mode                // 0=feedforward, 1=feedback
);

    // =========================================================================
    // Constants
    // =========================================================================
    localparam signed MAX_POSITIVE = {1'b0, {(DATA_WIDTH-1){1'b1}}};  // Largest positive value
    localparam signed MAX_NEGATIVE = {1'b1, {(DATA_WIDTH-1){1'b0}}};  // Most negative value

    // =========================================================================
    // Delayed signal from buffer
    // =========================================================================
    logic signed [DATA_WIDTH-1:0] delayed_sample;
    logic delayed_sample_valid;

    // =========================================================================
    // Feedback calculation - PIPELINED
    // =========================================================================
    // Stage 1: Multiply
    logic signed [DATA_WIDTH+FEEDBACK_WIDTH-1:0] feedback_scaled;
    logic signed [DATA_WIDTH-1:0] audio_in_stage1;
    logic sample_valid_stage1;
    logic mode_stage1;

    always_ff @(posedge clk) begin
        if (reset) begin
            feedback_scaled <= '0;
            audio_in_stage1 <= '0;
            sample_valid_stage1 <= 1'b0;
            mode_stage1 <= 1'b0;
        end else begin
            feedback_scaled <= delayed_sample * $signed({1'b0, feedback_amount});
            audio_in_stage1 <= audio_in;
            sample_valid_stage1 <= sample_valid;
            mode_stage1 <= mode;
        end
    end

    // Stage 2: Shift and add with saturation
    logic signed [DATA_WIDTH-1:0] feedback_signal;
    logic signed [DATA_WIDTH:0] feedback_sum;
    logic signed [DATA_WIDTH-1:0] feedback_saturated;
    logic signed [DATA_WIDTH-1:0] buffer_input;
    logic signed [DATA_WIDTH-1:0] audio_in_stage2;
    logic sample_valid_stage2;

    always_ff @(posedge clk) begin
        if (reset) begin
            feedback_signal <= '0;
            feedback_sum <= '0;
            feedback_saturated <= '0;
            buffer_input <= '0;
            audio_in_stage2 <= '0;
            sample_valid_stage2 <= 1'b0;
        end else begin
            // Shift down feedback
            feedback_signal <= feedback_scaled >>> FEEDBACK_WIDTH;

            // Add with overflow detection
            feedback_sum <= audio_in_stage1 + (feedback_scaled >>> FEEDBACK_WIDTH);

            // Saturate
            if (feedback_sum > MAX_POSITIVE)
                feedback_saturated <= MAX_POSITIVE;
            else if (feedback_sum < MAX_NEGATIVE)
                feedback_saturated <= MAX_NEGATIVE;
            else
                feedback_saturated <= feedback_sum[DATA_WIDTH-1:0];

            // Mode selection: feedback or feedforward
            buffer_input <= mode_stage1 ? feedback_saturated : audio_in_stage1;

            audio_in_stage2 <= audio_in_stage1;
            sample_valid_stage2 <= sample_valid_stage1;
        end
    end
    
    // =========================================================================
    // Variable delay buffer
    // =========================================================================
    variable_delay_buffer #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) delay_buf (
        .clk(clk),
        .reset(reset),

        .sample_valid(sample_valid_stage2),
        .in_sample(buffer_input),
        .delay_samples(delay_samples),

        .out_sample(delayed_sample),
        .out_sample_valid(delayed_sample_valid)
    );
    
    // =========================================================================
    // Output mixer: Single effect amount control - PIPELINED
    // dry_amount = 255 - effect_amount
    // wet_amount = effect_amount
    // =========================================================================
    // Stage 1: Multiply dry and wet
    logic signed [DATA_WIDTH+8-1:0] dry_scaled;
    logic signed [DATA_WIDTH+8-1:0] wet_scaled;
    logic delayed_sample_valid_stage1;

    always_ff @(posedge clk) begin
        if (reset) begin
            dry_scaled <= '0;
            wet_scaled <= '0;
            delayed_sample_valid_stage1 <= 1'b0;
        end else begin
            dry_scaled <= audio_in_stage2 * (8'd255 - effect_amount);
            wet_scaled <= delayed_sample * effect_amount;
            delayed_sample_valid_stage1 <= delayed_sample_valid;
        end
    end

    // Stage 2: Mix and scale
    logic signed [DATA_WIDTH+8:0] mixed_sum;
    logic signed [DATA_WIDTH+8-1:0] mixed_output;

    always_ff @(posedge clk) begin
        if (reset) begin
            mixed_sum <= '0;
            mixed_output <= '0;
            audio_out_valid <= 1'b0;
        end else begin
            mixed_sum <= dry_scaled + wet_scaled;
            mixed_output <= (dry_scaled + wet_scaled) >>> 8;
            audio_out_valid <= delayed_sample_valid_stage1;
        end
    end

    // =========================================================================
    // Output register
    // =========================================================================
    always_ff @(posedge clk) begin
        if (reset) begin
            audio_out <= '0;
        end else begin
            audio_out <= mixed_output[DATA_WIDTH-1:0];
        end
    end

endmodule