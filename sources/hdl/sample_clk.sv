module sample_clk #(
        parameter integer CLK_FREQ = 100_000_000,  // System clock frequency in Hz
        parameter integer SAMPLE_RATE = 48_000     // Audio sample rate in Hz
    )
    (
        input wire clk,
        input wire rst,
        output logic sample_clk_en,
        output logic data_valid
    );

    localparam integer DIVIDER_VALUE = CLK_FREQ / SAMPLE_RATE;

    logic [$clog2(DIVIDER_VALUE)-1:0] sample_counter;

    always_ff @(posedge clk) begin
        if (rst) begin
            sample_counter <= 0;
            data_valid <= 0;
        end else begin
            if (sample_counter == DIVIDER_VALUE - 1) begin
                sample_counter <= 0;
                data_valid <= 1;
            end else begin
                sample_counter <= sample_counter + 1;
                data_valid <= 0;
            end
        end
    end

    assign sample_clk_en = (sample_counter == DIVIDER_VALUE - 1);

endmodule
