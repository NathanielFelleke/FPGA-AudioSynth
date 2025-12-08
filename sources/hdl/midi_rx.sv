module midi_rx
    (
        input wire clk,
        input wire rst,
        input wire data_in,
        output logic [7:0] on_out,
        output logic [7:0][2:0] velocity_out,
        output logic [7:0][6:0] note_out,
        output logic [1:0] wave_out
    );
    logic state;
    logic [7:0] current_byte;
    logic [7:0] last_byte;
    logic [7:0] second_last_byte;

    logic [11:0] cycle_counter;
    logic [3:0] bit_counter;

    logic [2:0] free_channel;
    assign free_channel = (~on_out[0])? 3'd0: (~on_out[1])? 3'd1: (~on_out[2])? 3'd2: (~on_out[3])? 3'd3: (~on_out[4])? 3'd4: (~on_out[5])? 3'd5: (~on_out[6])? 3'd6: (~on_out[7])? 3'd7: 3'd7; 

    always_ff @(posedge clk) begin
        if (rst) begin
            on_out <= 0;
            for (int i=0; i<8; i=i+1) begin
                velocity_out[i] <= 0;
                note_out[i] <= 0;
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
                            if (last_byte[7:4] == 4'b1100) begin//change wave type
                                wave_out <= current_byte[1:0];
                            end else if (second_last_byte[7:4] == 9) begin//note on
                                on_out[free_channel] <= 1;
                                velocity_out[free_channel] <= current_byte[7:5];
                                note_out[free_channel] <= last_byte[6:0];
                            end else if (second_last_byte[7:4] == 8) begin//note off
                                for (int i=0; i<8; i=i+1) begin
                                    if (on_out[i] && note_out[i]==last_byte) begin
                                        on_out[i] <= 0;
                                    end
                                end
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
