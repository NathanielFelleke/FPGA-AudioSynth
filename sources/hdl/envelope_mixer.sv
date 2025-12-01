module envelope_mixer #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ENVELOPE_WIDTH = 32
)
(
    input wire clk,
    input wire rst,
    input wire signed [DATA_WIDTH-1:0] audio_in,              // 32-bit audio signal (oscillator output)
    input wire data_in_valid,
    input wire [ENVELOPE_WIDTH-1:0] envelope_in,              // 32-bit envelope value (ADSR output)
    output logic signed [DATA_WIDTH-1:0] audio_out,            // 32-bit modulated output
    output logic data_out_valid
);

    // Intermediate product: audio * envelope
    // Treating envelope as a fixed-point value from 0.0 to ~1.0 (where 2^31-1 = 1.0)
    logic signed [DATA_WIDTH + ENVELOPE_WIDTH - 1:0] product;

    // Combinational multiplication
    always_comb begin
        product = audio_in * signed'(envelope_in);
    end

    // Register output: scale down by dividing by 2^31 to get back to audio range
    always_ff @(posedge clk) begin
        if (rst) begin
            audio_out <= 0;
            data_out_valid <= 0;
        end else begin
            // For signed * signed multiplication, extract bits [62:31] to get 32-bit result
            // This is equivalent to right-shifting by 31 bits
            // Since envelope ranges from 0 to 2^31-1 (fixed point 0.0 to ~1.0),
            // the product ranges from -audio_max to +audio_max as desired
            audio_out <= product[62:31];
            data_out_valid <= data_in_valid;
        end
    end

endmodule
