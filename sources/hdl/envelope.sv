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
        input wire [AR_WIDTH-1:0] release_len,
        output logic signed [DATA_WIDTH-1 : 0] data_out
    );
    enum {IDLE, ATTACK, SUSTAIN, RELEASE} state;
    logic [AR_WIDTH-1:0] ar_counter;
    logic [$clog2(DATA_WIDTH):0] a_phase, r_phase;
    assign a_phase = DATA_WIDTH*ar_counter/attack_len;
    assign r_phase = DATA_WIDTH*(release_len-ar_counter)/release_len;

    always_ff @(posedge clk) begin
        if (rst) begin
            data_out <= 0;
            state <= IDLE;
            ar_counter <= 0;
        end else begin
            case (state)
                IDLE: begin
                    data_out <= 0;
                    if (play == 1) begin
                        state <= (release_len == 0)? SUSTAIN : ATTACK;
                        ar_counter <= 0;
                    end
                end
                ATTACK: begin
                    state <= (play == 0)? (release_len == 0)? IDLE : RELEASE: (ar_counter == attack_len-1)? SUSTAIN : ATTACK;
                    data_out <= $signed(-$signed(data_in)>>>a_phase)+$signed(data_in);
                    ar_counter <= (play == 0)? (DATA_WIDTH-r_phase)*release_len/DATA_WIDTH: ar_counter + 1;
                end
                SUSTAIN: begin
                    data_out <= data_in;
                    if (play == 0) begin
                        state <= (release_len == 0)? IDLE : RELEASE;
                        ar_counter <= release_len;
                    end
                end
                RELEASE: begin
                    state <= (play == 1)? (attack_len == 0)? SUSTAIN : ATTACK: (ar_counter == 1)? IDLE : RELEASE;
                    data_out <= $signed(data_in)>>>r_phase;
                    ar_counter <= (play == 1)? (DATA_WIDTH-a_phase)*attack_len/DATA_WIDTH: ar_counter - 1;
                end
            endcase
        end
    end
    
    

endmodule