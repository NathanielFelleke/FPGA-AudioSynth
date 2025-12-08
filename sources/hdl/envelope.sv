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
    logic [AR_WIDTH-1:0] ar_counter, ar_counter_next;
    logic [$clog2(DATA_WIDTH):0] a_phase, r_phase;

    // Compute next counter value
    always_comb begin
        case (state)
            IDLE: ar_counter_next = 0;
            ATTACK: ar_counter_next = (play == 0)? release_len : ar_counter + 1;
            SUSTAIN: ar_counter_next = ar_counter;
            RELEASE: ar_counter_next = (play == 1)? 0 : ar_counter - 1;
            default: ar_counter_next = 0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            data_out <= 0;
            state <= IDLE;
            ar_counter <= 0;
            a_phase <= 0;
            r_phase <= 0;
        end else begin
            // Update counter
            ar_counter <= ar_counter_next;

            // Pipeline the division operations using NEXT counter value
            a_phase <= DATA_WIDTH*ar_counter_next/attack_len;
            r_phase <= DATA_WIDTH*(release_len-ar_counter_next)/release_len;

            case (state)
                IDLE: begin
                    data_out <= 0;
                    if (play == 1) begin
                        state <= (attack_len == 0)? SUSTAIN : ATTACK;
                    end
                end
                ATTACK: begin
                    state <= (play == 0)? (release_len == 0)? IDLE : RELEASE: (ar_counter == attack_len-1)? SUSTAIN : ATTACK;
                    data_out <= $signed(-$signed(data_in)>>>a_phase)+$signed(data_in);
                end
                SUSTAIN: begin
                    data_out <= data_in;
                    if (play == 0) begin
                        state <= (release_len == 0)? IDLE : RELEASE;
                    end
                end
                RELEASE: begin
                    state <= (play == 1)? (attack_len == 0)? SUSTAIN : ATTACK: (ar_counter == 1)? IDLE : RELEASE;
                    data_out <= $signed(data_in)>>>r_phase;
                end
            endcase
        end
    end
    
    

endmodule