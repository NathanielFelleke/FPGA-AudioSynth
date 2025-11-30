module clk_divider #(
    parameter DIVIDER = 100_000
) (
    input clk_100mhz,
    input rst,
    output logic pulse
);

    // To generate a pulse every 1 ms using a 100 MHz clock:
    // 100 MHz = 100,000,000 cycles per second
    // 1 ms = 100,000 clock cycles
    // Set DIVIDER to the desired number of cycles per pulse

    localparam COUNTER_WIDTH = $clog2(DIVIDER);

    logic [COUNTER_WIDTH-1:0] counter;

    always_ff @(posedge clk_100mhz) begin
        if (rst) begin
            counter <= 0;
            pulse <= 0;
        end else begin
            pulse <= (counter == DIVIDER - 1);

            if (counter == DIVIDER - 1) begin
                counter <= 0;
            end else begin
                counter <= counter + 1;
            end
        end
    end

endmodule
