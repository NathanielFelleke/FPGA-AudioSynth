module adsr_envelope #
(
    parameter integer RATE_WIDTH = 16,
    parameter integer ENVELOPE_WIDTH = 32
)
(
    input wire clk,
    input wire rst,
    input wire [RATE_WIDTH-1:0] attack_time, //represents ms of attack time
    input wire [RATE_WIDTH-1:0] decay_time, //represents ms of decay time
    input wire [6:0] sustain_percent, //represents sustain percent (0 to max)
    input wire [RATE_WIDTH-1:0] release_time, //represents ms of release time 
    input wire note_on,

    output logic [ENVELOPE_WIDTH-1 : 0] envelope_out
);

    typedef enum {IDLE, ATTACK, DECAY, SUSTAIN, RELEASE} state_t;
    state_t state;

    logic prev_note_on;
    logic ms_pulse;
 
    // For simulation: use smaller divider (1000 = 10µs), for real HW: use 100_000 (1ms)
    localparam integer DIVIDER = 1000; //for simulation: 10µs pulse, change to 100_000 for real hardware
    //use clock divider to get millisecond pulses
    clk_divider #(
        .DIVIDER(DIVIDER)
    ) clk_div (
        .clk_100mhz(clk),
        .rst(rst),
        .pulse(ms_pulse)
);

 
    logic note_rising;
    logic note_falling;

    logic [RATE_WIDTH:0] counter;

    logic [ENVELOPE_WIDTH-1:0] attack_step;
    logic [ENVELOPE_WIDTH-1:0] decay_step;
    logic [ENVELOPE_WIDTH-1:0] release_step;

    localparam logic [ENVELOPE_WIDTH-1:0] MAX_ENVELOPE = {1'b0, {(ENVELOPE_WIDTH-1){1'b1}}}; // 0x7FFFFFFF for 32-bit

    logic [ENVELOPE_WIDTH-1:0] sustain_level;

    always_comb begin
        // Clamp to 0-100 range
        logic [6:0] percent_clamped;
        logic [63:0] temp_sustain;
        if (sustain_percent > 100)
            percent_clamped = 100;
        else
            percent_clamped = sustain_percent;

        // Calculate: (MAX_ENVELOPE * percent) / 100 using 64-bit intermediate to prevent overflow
        temp_sustain = ({32'b0, MAX_ENVELOPE} * {32'b0, percent_clamped}) / 64'd100;
        sustain_level = temp_sustain[ENVELOPE_WIDTH-1:0];
    end
    always_comb begin
        if (attack_time == 0)
            attack_step = MAX_ENVELOPE;
        else
            attack_step = MAX_ENVELOPE / attack_time;

        if (decay_time == 0)
            decay_step = MAX_ENVELOPE;
        else
            decay_step = (MAX_ENVELOPE - sustain_level) / decay_time;

        if (release_time == 0)
            release_step = MAX_ENVELOPE;
        else
            release_step = MAX_ENVELOPE / release_time;
    end

    always_ff @(posedge clk) begin
        if(rst) begin
            envelope_out <= 0;
            state <= IDLE;
            counter <= 0;
            prev_note_on <= 0;
            note_rising <= 0;
            note_falling <= 0;

        end
        else begin
            prev_note_on <= note_on;

            //used to detect rising and falling edge (latched)
            if (note_on & ~prev_note_on)
                note_rising <= 1;
                
            
            if (~note_on & prev_note_on)
                note_falling <= 1;
            if(ms_pulse) begin
                case(state)
                    IDLE: begin
                        envelope_out <= 0;
                        if(note_rising) begin
                            state <= ATTACK;
                            counter <= 0;
                            note_rising <= 0; //took care of rising edge
                        end
                    end
                    ATTACK: begin
                        //early release
                        if (note_falling) begin
                            state <= RELEASE;
                            counter <= 0;
                            note_falling <= 0; //took care of falling edge
                        end
                        else if (counter == attack_time - 1) begin
                            envelope_out <= MAX_ENVELOPE;
                            state <= DECAY;
                            counter <= 0;
                        end
                        else begin
                            envelope_out <= envelope_out + attack_step;
                            counter <= counter + 1;
                        end


                    end
                    DECAY: begin
                        if (note_falling) begin //early release
                            state <= RELEASE;
                            counter <= 0;
                            note_falling <= 0; //took care of falling edge
                        end
                        else if (counter == decay_time - 1 || envelope_out - decay_step <= sustain_level) begin
                            envelope_out <= sustain_level;
                            state <= SUSTAIN;
                            counter <= 0;
                        end
                        else begin
                            envelope_out <= envelope_out - decay_step;
                            counter <= counter + 1;
                        end
                    end
                    SUSTAIN: begin
                        envelope_out <= sustain_level;
                        //now wait for note to fall
                        if (note_falling) begin
                            state <= RELEASE;
                            counter <= 0;
                            note_falling <= 0; //took care of falling edge
                        end


                    end
                    RELEASE: begin
                        if (note_rising) begin //check if note is re pressed
                            state <= ATTACK;
                            counter <= 0;
                            note_rising <= 0; //took care of rising edge
                        end
                        else if (counter >= release_time - 1 || envelope_out <= release_step) begin
                            envelope_out <= 0;
                            state <= IDLE;
                            counter <= 0;
                        end
                        else begin
                            // Prevent underflow: use current envelope level as release step base
                            envelope_out <= envelope_out - release_step;
                            counter <= counter + 1;
                        end


                    end
                    default: begin
                        state <= IDLE;
                        envelope_out <= 0;
                        counter <= 0;
                    end
                endcase
            end

        end

    end



endmodule