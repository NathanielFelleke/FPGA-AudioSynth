module triangle_generator (
  input wire clk_in,
  input wire rst_in,
  input wire step_in,
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out);

  logic [31:0] phase;
  logic [31:0] triangle_unsigned;

  // True 32-bit triangle wave centered at zero
  // First half (phase[31]=0): rising from 0 to max
  // Second half (phase[31]=1): falling from max to 0
  always_comb begin
    if (phase[31] == 1'b0) begin
      // Rising: use phase[30:0] shifted left
      triangle_unsigned = {phase[30:0], 1'b0};
    end else begin
      // Falling: invert phase[30:0] and shift left
      triangle_unsigned = {~phase[30:0], 1'b0};
    end
  end

  // Center around zero by XORing with 0x80000000 (flip sign bit)
  assign amp_out = $signed(triangle_unsigned ^ 32'h80000000);

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule