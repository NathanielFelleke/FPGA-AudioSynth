module override (
        input wire clk,
        input wire rst,
        input wire [2:0] btns_in,
        output logic [7:0] on_out,
        output logic [7:0][6:0] note_out
    );

    logic [31:0] cycle_counter;
    logic [16:0][6:0] notes;
    assign notes[0] = 7'd64;//0,1,3,4,14,15
    assign notes[1] = 7'd62;
    assign notes[2] = 7'd60;//2,5,16
    assign notes[3] = 7'd64;
    assign notes[4] = 7'd62;
    assign notes[5] = 7'd60;
    assign notes[6] = 7'd60;//6-13
    assign notes[7] = 7'd60;
    assign notes[8] = 7'd60;
    assign notes[9] = 7'd60;
    assign notes[10] = 7'd62;
    assign notes[11] = 7'd62;
    assign notes[12] = 7'd62;
    assign notes[13] = 7'd62;
    assign notes[14] = 7'd64;
    assign notes[15] = 7'd62;
    assign notes[16] = 7'd60;

    logic [1:0] state;
    logic channel;
    logic [7:0] current_note;
    logic [31:0] note_len;

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= 0;
            on_out <= 0;
            for (int i=0; i<8; i=i+1) begin
                note_out[i] <= 0;
            end
            cycle_counter <= 0;
            channel <= 0;
            current_note <= 0;
        end else begin
            if (state == 0) begin
                if (btns_in[0]) begin
                    note_out[0] <= notes[0];
                    on_out[0] <= 1;
                    state <= 1;
                    cycle_counter <= 0;
                    channel <= 1;
                    current_note <= 1;
                    note_len <= 32'd50000000;
                end
            end else if (state == 1) begin
                if (cycle_counter == note_len-1) begin
                    if (current_note == 17) begin
                        on_out <= 0;
                        state <= 0;
                    end else begin
                        note_out[channel] <= notes[current_note];
                        cycle_counter <= 0;
                        channel <= ~channel;
                        on_out[1:0] <= ~on_out[1:0];
                        current_note <= current_note + 1;
                        //note_len <= (current_note>=6 && current_note<=13)? 32'd1: (current_note==1 && current_note==4 && current_note==15)? 32'b100 : 32'b10;
                        note_len <= (current_note>=5 && current_note<=12)? 32'd25000000: (current_note==2 && current_note==4 && current_note==15)? 32'd100000000 : 32'50000000;
                    end
                end else begin
                    cycle_counter <= cycle_counter + 1;
                end
            end
        end
    end

endmodule