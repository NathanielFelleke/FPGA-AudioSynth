module delay_effect #(
    parameter ADDR_WIDTH = 16,
    parameter DATA_WIDTH = 32,
    parameter FEEDBACK_WIDTH = 8,
    parameter LATENCY = 8 // Total calculated latency will be used for valid signal
)(
    input  wire                       clk,
    input  wire                       rst,
    
    // Audio stream
    input  wire                       sample_valid,
    input  wire signed [DATA_WIDTH-1:0] audio_in,
    output logic signed [DATA_WIDTH-1:0] audio_out,
    output logic                      audio_out_valid,
    
    // Control parameters
    input  wire [ADDR_WIDTH-1:0]      delay_samples,
    input  wire [FEEDBACK_WIDTH-1:0]  feedback_amount,
    input  wire [7:0]                 effect_amount,
    input  wire                       mode // 0=feedforward, 1=feedback
);

    localparam signed MAX_POSITIVE = {1'b0, {(DATA_WIDTH-1){1'b1}}};
    localparam signed MAX_NEGATIVE = {1'b1, {(DATA_WIDTH-1){1'b0}}};
    localparam TOTAL_PIPELINE_STAGES = 6; // 3 (Feedback/Dry Sync) + 3 (Delay Buffer + Mixer)

    // Signals from Delay Buffer
    logic signed [DATA_WIDTH-1:0] delayed_sample;
    logic delayed_sample_valid;

    // Dry Path Alignment (3 stages required for total path synchronization)
    logic signed [DATA_WIDTH-1:0] dry_aligned_stg[0:TOTAL_PIPELINE_STAGES-1];
    logic [TOTAL_PIPELINE_STAGES-1:0] valid_pipe_stg;

    // =========================================================================
    // 1. INPUT, DRY ALIGNMENT, & FEEDBACK PREPARATION
    // Total stages here must match the latency of the combined Delay Buffer and Mixer.
    // Delay Buffer Latency: 3 cycles. Mixer Latency: 3 cycles. Total: 6 cycles.
    // We synchronize the dry path to the final mixer stage.
    // =========================================================================
    
    // Feedback: Wet signal scaled (requires DATA_WIDTH + FEEDBACK_WIDTH bits)
    logic signed [DATA_WIDTH+FEEDBACK_WIDTH-1:0] feedback_scaled;
    logic signed [DATA_WIDTH-1:0] feedback_signal;
    logic signed [DATA_WIDTH:0] feedback_sum;
    logic signed [DATA_WIDTH-1:0] buffer_input;
    
    // Feedback path stage 1: Scale delayed sample
    always_ff @(posedge clk) begin
        if (rst) begin
            feedback_scaled <= '0;
            valid_pipe_stg[0] <= 1'b0;
        end else begin
            // Scale delayed sample for potential feedback addition
            feedback_scaled <= delayed_sample * $signed({1'b0, feedback_amount});
            
            // Align input and valid signal (Stage 1)
            dry_aligned_stg[0] <= audio_in;
            valid_pipe_stg[0] <= sample_valid;
        end
    end

    // Feedback path stage 2: Shift and Add/Saturate
    always_ff @(posedge clk) begin
        if (rst) begin
            buffer_input <= '0;
            valid_pipe_stg[1] <= 1'b0;
        end else begin
            // Shift down the scaled feedback
            feedback_signal <= feedback_scaled >>> FEEDBACK_WIDTH;

            // Add new input (dry_aligned_stg[0]) with feedback_signal
            feedback_sum <= $signed(dry_aligned_stg[0]) + $signed(feedback_signal);

            // Saturate and select buffer input
            if (mode == 1'b1) begin // Feedback Mode
                if (feedback_sum > MAX_POSITIVE)
                    buffer_input <= MAX_POSITIVE;
                else if (feedback_sum < MAX_NEGATIVE)
                    buffer_input <= MAX_NEGATIVE;
                else
                    buffer_input <= feedback_sum[DATA_WIDTH-1:0];
            end else begin // Feedforward Mode (no feedback)
                buffer_input <= dry_aligned_stg[0];
            end
            
            // Align dry path and valid signal (Stage 2)
            dry_aligned_stg[1] <= dry_aligned_stg[0];
            valid_pipe_stg[1] <= valid_pipe_stg[0];
        end
    end

    // =========================================================================
    // 2. VARIABLE DELAY BUFFER (3 cycles latency)
    // The buffer input signal is 'buffer_input'
    // =========================================================================
    variable_delay_buffer #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) delay_buf (
        .clk(clk),
        .rst(rst),
        .sample_valid(valid_pipe_stg[1]), // Valid from Stage 2
        .in_sample(buffer_input),
        .delay_samples(delay_samples),
        .out_sample(delayed_sample),
        .out_sample_valid(delayed_sample_valid)
    );
    
    // =========================================================================
    // 3. MIXER (3 cycles pipeline)
    // The delay buffer introduces 3 cycles of latency. The dry path must catch up.
    // =========================================================================
    
    // Stage 1: Align dry path with delayed sample (Buffer output is ready now)
    logic signed [DATA_WIDTH-1:0] dry_mixer_input;

    always_ff @(posedge clk) begin
        if (rst) begin
            dry_mixer_input <= '0;
            valid_pipe_stg[2] <= 1'b0;
        end else begin
            dry_mixer_input <= dry_aligned_stg[1];
            
            // Align valid signal (Stage 3 - end of buffer path)
            valid_pipe_stg[2] <= valid_pipe_stg[1];
        end
    end
    
    // Stage 2: Multiply dry and wet
    logic signed [DATA_WIDTH+8-1:0] dry_scaled;
    logic signed [DATA_WIDTH+8-1:0] wet_scaled;
    
    always_ff @(posedge clk) begin
        if (rst) begin
            dry_scaled <= '0;
            wet_scaled <= '0;
            valid_pipe_stg[3] <= 1'b0;
        end else begin
            // delayed_sample_valid is delayed sample's valid signal (3 cycles delay)
            if (delayed_sample_valid) begin
                dry_scaled <= dry_mixer_input * (8'd255 - effect_amount);
                wet_scaled <= delayed_sample * effect_amount;
            end else begin
                dry_scaled <= '0;
                wet_scaled <= '0;
            end

            // Align dry path and valid signal (Stage 4)
            dry_aligned_stg[2] <= dry_mixer_input;
            valid_pipe_stg[3] <= delayed_sample_valid;
        end
    end

    // Stage 3: Mix, Scale, and Register Output
    logic signed [DATA_WIDTH+8-1:0] mixed_output;

    always_ff @(posedge clk) begin
        if (rst) begin
            audio_out <= '0;
            audio_out_valid <= 1'b0;
            valid_pipe_stg[4] <= 1'b0;
        end else begin
            // Sum and divide by 256 (shift right by 8)
            mixed_output <= (dry_scaled + wet_scaled) >>> 8;
            
            // Final output stage (Stage 5)
            audio_out <= mixed_output[DATA_WIDTH-1:0];
            
            // Align valid signal (Stage 5)
            valid_pipe_stg[4] <= valid_pipe_stg[3];
            audio_out_valid <= valid_pipe_stg[4];
        end
    end

endmodule