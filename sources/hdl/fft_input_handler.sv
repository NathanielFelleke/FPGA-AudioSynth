module fft_input_handler #(
    parameter INPUT_WIDTH = 32,
    parameter FFT_WIDTH   = 16,
    parameter FFT_SIZE    = 1024
)(
    input  logic        clk,
    input  logic        rst,
    
    // Audio input
    input  logic signed [INPUT_WIDTH-1:0] audio_in,
    input  logic                          audio_valid,
    
    // AXI-Stream to FFT IP
    output logic [2*FFT_WIDTH-1:0] m_axis_tdata,
    output logic                   m_axis_tvalid,
    output logic                   m_axis_tlast,
    input  logic                   m_axis_tready
);

    localparam SHIFT = INPUT_WIDTH - FFT_WIDTH;
    localparam CTR_WIDTH = $clog2(FFT_SIZE);

    logic [CTR_WIDTH-1:0] sample_ctr;
    logic                 last_sample;

    assign last_sample = (sample_ctr == FFT_SIZE - 1);

    logic signed [FFT_WIDTH-1:0] audio_scaled;
    assign audio_scaled  = $signed(audio_in >>> SHIFT); //SCALES THE AUDIO

    

    always_ff @(posedge clk) begin
        if (rst) begin
            m_axis_tdata  <= '0;
            m_axis_tvalid <= 1'b0;
            m_axis_tlast  <= 1'b0;

            //counter for tlast
            sample_ctr <= '0;
        end else begin
            m_axis_tvalid <= audio_valid;
            m_axis_tlast  <= audio_valid && last_sample;
            m_axis_tdata  <= {{FFT_WIDTH{1'b0}}, audio_scaled};

            if (audio_valid && m_axis_tready) begin
                if (last_sample)
                    sample_ctr <= '0;
                else
                    sample_ctr <= sample_ctr + 1;
        end
        end
    end
endmodule