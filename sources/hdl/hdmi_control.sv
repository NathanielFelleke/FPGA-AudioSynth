module hdmi_control (
    input  logic        clk,        // 40 MHz
    input  logic        rst,
    
    // Pixel coordinates
    output logic [9:0]  pixel_x,
    output logic [9:0]  pixel_y,
    
    // Sync signals
    output logic        hsync,
    output logic        vsync,
    output logic        active
);

    // 800x600 @ 60Hz timing
    localparam H_ACTIVE = 800;
    localparam H_FRONT  = 40;
    localparam H_SYNC   = 128;
    localparam H_BACK   = 88;
    localparam H_TOTAL  = 1056;

    localparam V_ACTIVE = 600;
    localparam V_FRONT  = 1;
    localparam V_SYNC   = 4;
    localparam V_BACK   = 23;
    localparam V_TOTAL  = 628;

    logic [10:0] h_count;
    logic [9:0]  v_count;

    // Horizontal counter
    always_ff @(posedge clk or negedge rst_n) begin
        if (rst) begin
            h_count <= '0;
        end else begin
            if (h_count == H_TOTAL - 1)
                h_count <= '0;
            else
                h_count <= h_count + 1;
        end
    end

    // Vertical counter
    always_ff @(posedge clk) begin
        if (rst) begin
            v_count <= '0;
        end else if (h_count == H_TOTAL - 1) begin
            if (v_count == V_TOTAL - 1)
                v_count <= '0;
            else
                v_count <= v_count + 1;
        end
    end

    // sync the signals
    assign hsync = ~((h_count >= H_ACTIVE + H_FRONT) && 
                     (h_count < H_ACTIVE + H_FRONT + H_SYNC));
    assign vsync = ~((v_count >= V_ACTIVE + V_FRONT) && 
                     (v_count < V_ACTIVE + V_FRONT + V_SYNC));

    // when it is in active region
    assign active = (h_count < H_ACTIVE) && (v_count < V_ACTIVE);

    // pixel coordinates to get from
    assign pixel_x = h_count[9:0];
    assign pixel_y = v_count;

endmodule