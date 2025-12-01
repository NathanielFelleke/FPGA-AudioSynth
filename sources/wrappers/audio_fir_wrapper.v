`timescale 1ns / 1ps
`default_nettype none

module audio_fir_wrapper #(
    parameter DATA_WIDTH = 32,
    parameter NUM_COEFFS = 64,
    parameter COEFF_WIDTH = 16
)
(
    input wire clk,
    input wire rst,
    input wire signed [DATA_WIDTH-1:0] data_in,
    input wire data_in_valid,
    input wire signed [NUM_COEFFS-1:0][COEFF_WIDTH-1:0] coeffs,
    input wire [COEFF_WIDTH-1:0] scaler,  // Right shift amount for scaling output
    input wire enable,  // When 1: use FIR, when 0: passthrough
    output wire signed [DATA_WIDTH-1:0] data_out,
    output wire data_out_valid
);

    // FIR filter output
    wire signed [DATA_WIDTH-1:0] fir_out;
    wire fir_out_valid;

    // Instantiate the FIR filter
    audio_fir #(
        .DATA_WIDTH(DATA_WIDTH),
        .NUM_COEFFS(NUM_COEFFS),
        .COEFF_WIDTH(COEFF_WIDTH)
    ) fir_inst (
        .clk(clk),
        .rst(rst),
        .data_in(data_in),
        .data_in_valid(data_in_valid),
        .coeffs(coeffs),
        .data_out(fir_out),
        .data_out_valid(fir_out_valid)
    );

    // Scale the FIR output by right-shifting
    reg signed [DATA_WIDTH-1:0] scaled_fir_out;
    reg scaled_fir_valid;

    always @(posedge clk) begin
        if (rst) begin
            scaled_fir_out <= 0;
            scaled_fir_valid <= 0;
        end else begin
            scaled_fir_out <= fir_out >>> scaler;
            scaled_fir_valid <= fir_out_valid;
        end
    end

    // Passthrough path (2-cycle latency to match FIR + scaler)
    reg signed [DATA_WIDTH-1:0] passthrough_pipe [1:0];
    reg passthrough_valid_pipe [1:0];

    always @(posedge clk) begin
        if (rst) begin
            passthrough_pipe[0] <= 0;
            passthrough_pipe[1] <= 0;
            passthrough_valid_pipe[0] <= 0;
            passthrough_valid_pipe[1] <= 0;
        end else begin
            passthrough_pipe[0] <= data_in;
            passthrough_pipe[1] <= passthrough_pipe[0];
            passthrough_valid_pipe[0] <= data_in_valid;
            passthrough_valid_pipe[1] <= passthrough_valid_pipe[0];
        end
    end

    // Mux between FIR and passthrough based on enable
    assign data_out = enable ? scaled_fir_out : passthrough_pipe[1];
    assign data_out_valid = enable ? scaled_fir_valid : passthrough_valid_pipe[1];

endmodule

`default_nettype wire
