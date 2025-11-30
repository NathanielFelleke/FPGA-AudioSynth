module midi_rx
    (
        input wire clk,
        input wire rst,
        input wire data_in,
        output logic [127:0] note_out,
        output logic [127:0][2:0] velocity_out,
        output logic [1:0] wave_out
    );
    logic state;
    logic [7:0] current_byte;
    logic [7:0] last_byte;
    logic [7:0] second_last_byte;

    logic [11:0] cycle_counter;
    logic [3:0] bit_counter;
    
    always_ff @(posedge clk) begin
        if (rst) begin
            note_out <= 0;
            for (int i=1; i<128; i=i+1) begin
                velocity_out[i] <= 0;
            end
            wave_out <= 0;
            current_byte <= 0;
            last_byte <= 0;
            bit_counter <= 0;
            cycle_counter <= 0;
            state <= 0;
        end else begin
            if (state == 0) begin
                if (data_in == 0) begin
                    state <= 1;
                    bit_counter <= 0;
                    cycle_counter <= 0;
                    second_last_byte <= last_byte;
                    last_byte <= current_byte;
                end
            end else begin
                if (cycle_counter == 3199) begin
                    if (bit_counter == 8) begin
                        state <= 0;
                        if (data_in == 1) begin
                            if (last_byte[7:4] == 4'b1100) begin
                                wave_out <= current_byte[1:0];
                            end else if (second_last_byte[7:5] == 4'b100) begin//1001: note on. 1000: note off
                                note_out[last_byte] <= second_last_byte[4];
                                velocity_out[last_byte] <= current_byte[7:5];
                            end
                        end
                    end else begin
                        cycle_counter <= 0;
                        current_byte[7-bit_counter] <= data_in;
                        bit_counter <= bit_counter + 1;
                    end
                end else begin
                    cycle_counter <= cycle_counter + 1;
                end
            end
        end
    end
endmodule
