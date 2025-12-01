module delay_effect #(
    parameter ADDR_WIDTH = 16,      // 2^16 = 65536 samples (~1.36s at 48kHz)
    parameter DATA_WIDTH = 16,      // 16-bit audio
    parameter FEEDBACK_WIDTH = 8    // 8-bit feedback control
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
    localparam signed MAX_POSITIVE = {1'b0, {(DATA_WIDTH-1){1'b1}}};  // 0x7FFF
    localparam signed MAX_NEGATIVE = {1'b1, {(DATA_WIDTH-1){1'b0}}};  // 0x8000

    // =========================================================================
    // Delayed signal from buffer
    // =========================================================================
    logic signed [DATA_WIDTH-1:0] delayed_sample;
    logic delayed_sample_valid;
    
    // =========================================================================
    // Feedback calculation
    // =========================================================================
    wire signed [DATA_WIDTH+FEEDBACK_WIDTH-1:0] feedback_scaled;
    assign feedback_scaled = delayed_sample * feedback_amount;
    
    wire signed [DATA_WIDTH-1:0] feedback_signal;
    assign feedback_signal = feedback_scaled >>> FEEDBACK_WIDTH;
    
    // Sum with overflow detection
    wire signed [DATA_WIDTH:0] feedback_sum;
    assign feedback_sum = audio_in + feedback_signal;
    
    // Saturate to prevent overflow
    wire signed [DATA_WIDTH-1:0] feedback_saturated;
    assign feedback_saturated = (feedback_sum > MAX_POSITIVE) ? MAX_POSITIVE :
                                (feedback_sum < MAX_NEGATIVE) ? MAX_NEGATIVE :
                                feedback_sum[DATA_WIDTH-1:0];
    
    // =========================================================================
    // Mode selection: feedback or feedforward
    // =========================================================================
    wire signed [DATA_WIDTH-1:0] buffer_input;
    assign buffer_input = mode ? feedback_saturated : audio_in;
    
    // =========================================================================
    // Variable delay buffer
    // =========================================================================
    variable_delay_buffer #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) delay_buf (
        .clk(clk),
        .reset(reset),
        
        .sample_valid(sample_valid),
        .in_sample(buffer_input),
        .delay_samples(delay_samples),
        
        .out_sample(delayed_sample),
        .out_sample_valid(delayed_sample_valid)
    );
    
    // =========================================================================
    // Output mixer: Single effect amount control
    // dry_amount = 255 - effect_amount
    // wet_amount = effect_amount
    // =========================================================================
    wire signed [DATA_WIDTH+8-1:0] dry_scaled;
    wire signed [DATA_WIDTH+8-1:0] wet_scaled;
    wire signed [DATA_WIDTH+8-1:0] mixed_output;
    
    // Scale dry and wet signals
    assign dry_scaled = audio_in * (8'd255 - effect_amount);
    assign wet_scaled = delayed_sample * effect_amount;
    
    // Mix together and scale down by 256
    assign mixed_output = (dry_scaled + wet_scaled) >>> 8;
    
    // =========================================================================
    // Output register
    // No saturation needed - mathematically cannot overflow with this mix scheme
    // =========================================================================
    always_ff @(posedge clk) begin
        if (reset) begin
            audio_out <= '0;
            audio_out_valid <= 1'b0;
        end else begin
            audio_out_valid <= delayed_sample_valid;
            audio_out <= mixed_output[DATA_WIDTH-1:0];
        end
    end

endmodule