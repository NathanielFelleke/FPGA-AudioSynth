module square_generator (
  input wire clk_in,
  input wire rst_in, //clock and reset
  input wire step_in, //trigger a phase step (rate at which you run sine generator)
  input wire [31:0] PHASE_INCR,
  output logic signed [7:0] amp_out); //output phase in 2's complement

  logic [31:0] phase;
  logic [7:0] amp;
  logic [7:0] amp_pre;

  assign amp_out = (phase[31])? 32'h0000007F: 32'hFFFFFF80;

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule