module video_handler #(
    parameter DELAY = 4,
    parameter WATERFALL_TOP = 300
)(
    input  logic        clk,
    input  logic        rst,
    
    // from video_timing module
    input  logic [9:0]  pixel_x,
    input  logic [9:0]  pixel_y,
    input  logic        hsync,
    input  logic        vsync,
    input  logic        active,
    
    // from color_map
    input  logic [23:0] rgb_in,
    
    // to the waterfall buffer module
    output logic [8:0]  rd_row,
    
    // to rgb2dvi ip
    output logic [23:0] rgb_out,
    output logic        hsync_out,
    output logic        vsync_out,
    output logic        active_out
);

    // detects in region of screen for waterfall and assigns the read row
    logic in_waterfall;

    logic [8:0] rd_row_comb; //need to add a combination before so we can delay rd_row by one cycle like logx
    assign in_waterfall = (pixel_y >= WATERFALL_TOP);
    assign rd_row_comb = pixel_y - WATERFALL_TOP;

    // pipelines to sync the signals
    logic [DELAY-1:0] hsync_pipe;
    logic [DELAY-1:0] vsync_pipe;
    logic [DELAY-1:0] active_pipe;
    logic [DELAY-1:0] in_waterfall_pipe;

    always_ff @(posedge clk) begin
        if (rst) begin
            hsync_pipe        <= '1;
            vsync_pipe        <= '1;
            active_pipe       <= '0;
            in_waterfall_pipe <= '0;

            rd_row <= '0;
        end else begin
            hsync_pipe        <= {hsync_pipe[DELAY-2:0], hsync};
            vsync_pipe        <= {vsync_pipe[DELAY-2:0], vsync};
            active_pipe       <= {active_pipe[DELAY-2:0], active};
            in_waterfall_pipe <= {in_waterfall_pipe[DELAY-2:0], in_waterfall};
            rd_row <= rd_row_comb;
        end
    end

    // output at the end of the pipeline
    assign hsync_out  = hsync_pipe[DELAY-1];
    assign vsync_out  = vsync_pipe[DELAY-1];
    assign active_out = active_pipe[DELAY-1];
    assign rgb_out    = in_waterfall_pipe[DELAY-1] ? rgb_in : 24'd0;

endmodule