module envelope #
    (
        parameter integer DATA_WIDTH = 32,
        parameter integer AR_WIDTH = 32
    )
    (
        input wire clk,
        input wire rst,
        input wire signed [DATA_WIDTH-1 : 0] data_in,
        input wire play,
        input wire [AR_WIDTH-1:0] attack_len,
        input wire [AR_WIDTH-1:0] decay_len,
        input wire [4:0] sustain_level,
        input wire [AR_WIDTH-1:0] release_len,
        output logic signed [DATA_WIDTH-1 : 0] data_out
    );
    enum {IDLE, ATTACK, DECAY, SUSTAIN, RELEASE} state;
    logic [AR_WIDTH-1:0] ar_counter;
    logic [$clog2(DATA_WIDTH):0] t_phase;
    logic signed [DATA_WIDTH-1:0] sustain_data, decay_data;

    always_ff @(posedge clk) begin
        if (rst) begin
            data_out <= 0;
            state <= IDLE;
            ar_counter <= 0;
            t_phase <= 0;
        end else begin
            case (state)
                IDLE: begin
                    data_out <= 0;
                    if (play == 1) begin
                        state <= (attack_len != 0)? ATTACK : (decay_len == 0)? SUSTAIN : DECAY;
                        ar_counter <= 0;
                        t_phase = 0;
                    end
                end
                ATTACK: begin
                    data_out <= $signed(-$signed(data_in)>>>t_phase)+$signed(data_in);
                    if (t_phase != 16) begin
                        if (ar_counter == attack_len[31:4]) begin
                            t_phase <= t_phase + 1;
                            ar_counter <= 0;
                        end else begin
                            if (~play) begin
                                state <= (release_len == 0)? IDLE : RELEASE;
                                t_phase <= 16-t_phase;
                            end else begin
                                ar_counter <= ar_counter + 1;
                            end
                        end
                    end else begin
                        state <= (decay_len == 0)? SUSTAIN : DECAY;
                        t_phase <= 0;
                    end
                end
                DECAY: begin
                    data_out <= $signed($signed(decay_data)>>>t_phase)+$signed(sustain_data);
                    if (t_phase != 16) begin
                        if (ar_counter == decay_len[31:4]) begin
                            t_phase <= t_phase + 1;
                            ar_counter <= 0;
                        end else begin
                            if (~play) begin
                                state <= (release_len == 0)? IDLE : RELEASE;
                                t_phase <= 16-t_phase;
                            end else begin
                                ar_counter <= ar_counter + 1;
                            end
                        end
                    end else begin
                        state <= SUSTAIN;
                    end
                end
                SUSTAIN: begin
                    data_out <= sustain_data;
                    if (play == 0) begin
                        state <= (release_len == 0)? IDLE : RELEASE;
                        ar_counter <= 0;
                        t_phase = 0;
                    end
                end
                RELEASE: begin
                    data_out <= $signed(sustain_data)>>>t_phase;
                    if (t_phase != 16) begin
                        if (ar_counter == release_len[31:4]) begin
                            t_phase <= t_phase + 1;
                            ar_counter <= 0;
                        end else begin
                            if (play) begin
                                state <= (attack_len != 0)? ATTACK : (decay_len == 0)? SUSTAIN : DECAY;
                                t_phase <= 16-t_phase;
                            end else begin
                                ar_counter <= ar_counter + 1;
                            end
                        end
                    end else begin
                        state <= IDLE;
                    end
                end
            endcase
        end
        sustain_data <= $signed($signed(data_in)*sustain_level)>>>7;
        decay_data <= $signed($signed(data_in)*(128-sustain_level))>>>7;
    end
    
    

endmodule