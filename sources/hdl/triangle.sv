module triangle_generator (
  input wire clk_in,
  input wire rst_in, //clock and reset
  input wire step_in, //trigger a phase step (rate at which you run sine generator)
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out); //output phase in 2's complement

  logic [31:0] phase;
  logic [7:0] amp;
  logic [31:0] amp_pre;
  assign amp = (phase[31])? {phase[30:24], 1'b0}: 8'hFF-(phase[30:24]<<1);
  assign amp_pre = (amp[7])? ({24'b0,~amp[7],amp[6:0]}) : ({24'hFFFFFF,~amp[7],amp[6:0]});
  assign amp_out = $signed(amp_pre); //decrease volume so it isn't too loud!

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule