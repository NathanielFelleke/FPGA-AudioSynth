module triangle_generator (
  input wire clk_in,
  input wire rst_in,
  input wire step_in,
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out);

  logic [31:0] phase;
  logic signed [31:0] triangle;

  // True 32-bit triangle wave
  // First half (0 to π): rising from -max to +max
  // Second half (π to 2π): falling from +max to -max
  always_comb begin
    if (phase[31] == 1'b0) begin
      // First half: 0 to 0x7FFFFFFF
      // Map to -2^31 to +2^31-1 by shifting and inverting
      triangle = {phase[30:0], 1'b0} - 32'sd2147483648;
    end else begin
      // Second half: 0x80000000 to 0xFFFFFFFF
      // Map to +2^31-1 down to -2^31
      triangle = 32'sd2147483647 - {phase[30:0], 1'b0};
    end
  end

  assign amp_out = triangle;

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule