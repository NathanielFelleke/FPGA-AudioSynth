module square_generator (
  input wire clk_in,
  input wire rst_in,
  input wire step_in,
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out);

  logic [31:0] phase;

  // True 32-bit square wave: full positive or full negative
  assign amp_out = (phase[31])? -32'sd2147483647 : 32'sd2147483647;

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule