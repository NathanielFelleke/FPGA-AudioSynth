module color_map (
    input  logic        clk,
    input  logic        rst,
    
    input  logic [7:0]  log_val,
    input  logic        valid_in,
    
    output logic [23:0] rgb,
    output logic        valid_out
);

    logic [7:0] r, g, b;

    // Jet: blue → cyan → green → yellow → red
    always_comb begin
        if (log_val < 64) begin
            // Blue to cyan
            r = 0;
            g = log_val << 2;
            b = 255;
        end else if (log_val < 128) begin
            // Cyan to green
            r = 0;
            g = 255;
            b = 255 - ((log_val - 64) << 2);
        end else if (log_val < 192) begin
            // Green to yellow
            r = (log_val - 128) << 2;
            g = 255;
            b = 0;
        end else begin
            // Yellow to red
            r = 255;
            g = 255 - ((log_val - 192) << 2);
            b = 0;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            rgb       <= '0;
            valid_out <= 1'b0;
        end else begin
            rgb       <= {r, g, b};
            valid_out <= valid_in;
        end
    end

endmodule