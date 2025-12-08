module sawtooth_generator (
  input wire clk_in,
  input wire rst_in,
  input wire step_in,
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out);

  logic [31:0] phase;

  // True 32-bit sawtooth centered at zero
  // Phase goes from 0 to 2^32-1, we want -2^31 to +2^31-1
  // XOR with 0x80000000 to flip the MSB, effectively subtracting 2^31
  assign amp_out = $signed(phase ^ 32'h80000000);

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule