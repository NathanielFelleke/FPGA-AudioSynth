module oscillator #
    (
        parameter integer DATA_WIDTH = 32
    )
    (
        input wire clk,
        input wire rst,
        input wire [1:0] wave_type,
        input wire step_in,
        input wire [31:0] PHASE_INCR,
        output logic signed [DATA_WIDTH-1 : 0] data_out
    );

    logic [DATA_WIDTH-1:0] sin_out, sq_out, saw_out, tri_out;
    sine_generator my_sine(.clk_in(clk), .rst_in(rst), .step_in(step_in), .PHASE_INCR(PHASE_INCR), .amp_out(sin_out));
    square_generator my_square(.clk_in(clk), .rst_in(rst), .step_in(step_in), .PHASE_INCR(PHASE_INCR), .amp_out(sq_out));
    sawtooth_generator my_sawtooth(.clk_in(clk), .rst_in(rst), .step_in(step_in), .PHASE_INCR(PHASE_INCR), .amp_out(saw_out));
    triangle_generator my_triangle(.clk_in(clk), .rst_in(rst), .step_in(step_in), .PHASE_INCR(PHASE_INCR), .amp_out(tri_out));

    always_ff @(posedge clk) begin
        if (rst) begin
            data_out <= 0;
        end else begin
            case (wave_type)
                2'b00: begin
                    data_out <= sin_out;
                end
                2'b01: begin
                    data_out <= sq_out;
                end
                2'b10: begin
                    data_out <= saw_out;
                end
                2'b11: begin
                    data_out <= tri_out;
                end
            endcase
        end
    end
    
    

endmodule