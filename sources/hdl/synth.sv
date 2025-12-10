module synth #( 
    parameter integer AUDIO_WIDTH = 32, 
    parameter integer NUM_VOICES = 8, 
    parameter integer CLK_FREQ = 100_000_000, 
    parameter integer SAMPLE_RATE = 48_000     
) 
( 
    input wire clk, 
    input wire rst, 
    input wire midi_in, 
    input wire octave_on, 
    
    // Audio Outputs
    output logic signed [AUDIO_WIDTH-1:0] voice_1_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_2_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_3_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_4_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_5_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_6_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_7_out, 
    output logic signed [AUDIO_WIDTH-1:0] voice_8_out, 
    
    // Debug
    output logic [NUM_VOICES-1:0] ons_out, 
    output logic data_valid 
); 

    // Sample rate divider
    logic sample_clk_en; 
    sample_clk #(.CLK_FREQ(CLK_FREQ), .SAMPLE_RATE(SAMPLE_RATE)) 
        sample_divider(.clk(clk), .rst(rst), .sample_clk_en(sample_clk_en), .data_valid(data_valid)); 

    logic [NUM_VOICES-1:0][2:0] note_vels; 
    logic [NUM_VOICES-1:0][6:0] note_notes; 
    
    // Default Wave Type (Since MIDI no longer controls it)
    // 0 = Sawtooth, 1 = Square, etc. Change this manually if needed.
    logic [1:0] wave_type; 
    assign wave_type = 2'b00; 

    // =============================================================
    // FIX: Instantiation now matches the 6-port midi_rx
    // =============================================================
    midi_rx midi_receiver (
        .clk(clk), 
        .rst(rst), 
        .data_in(midi_in), 
        .on_out(ons_out), 
        .velocity_out(note_vels), 
        // REMOVED: .wave_out(wave_type) <-- This was causing the error
        .note_out(note_notes)
    ); 

    // Frequency Lookup
    logic [127:0][31:0] note_freqs; 
    assign note_freqs[0] = 32'd731558; 
    assign note_freqs[1] = 32'd775059; 
    // ... (Your frequency list continues here) ...
    assign note_freqs[127] = 32'd1122405052; // Ensure full list is in your file

    logic signed [7:0][AUDIO_WIDTH-1:0] osc_out; 
    logic signed [7:0][AUDIO_WIDTH-1:0] oct_osc_out; 

    // Oscillator Bank
    genvar i; 
    generate 
        for (i=0; i < 8; i++) begin : voices
            oscillator osc_inst(
                .clk(clk), 
                .rst(rst), 
                .wave_type(wave_type), 
                .step_in(sample_clk_en), 
                .PHASE_INCR(note_freqs[note_notes[i]]), 
                .data_out(osc_out[i])
            ); 
            oscillator oct_osc_inst(
                .clk(clk), 
                .rst(rst), 
                .wave_type(wave_type), 
                .step_in(sample_clk_en), 
                .PHASE_INCR(note_freqs[note_notes[i]]<<1), 
                .data_out(oct_osc_out[i])
            ); 
        end 
    endgenerate 

    // Audio Output Assignment
    assign voice_1_out = (octave_on)? ((osc_out[0] + oct_osc_out[0]) >>> 1) : osc_out[0]; 
    assign voice_2_out = (octave_on)? ((osc_out[1] + oct_osc_out[1]) >>> 1) : osc_out[1]; 
    assign voice_3_out = (octave_on)? ((osc_out[2] + oct_osc_out[2]) >>> 1) : osc_out[2]; 
    assign voice_4_out = (octave_on)? ((osc_out[3] + oct_osc_out[3]) >>> 1) : osc_out[3]; 
    assign voice_5_out = (octave_on)? ((osc_out[4] + oct_osc_out[4]) >>> 1) : osc_out[4]; 
    assign voice_6_out = (octave_on)? ((osc_out[5] + oct_osc_out[5]) >>> 1) : osc_out[5]; 
    assign voice_7_out = (octave_on)? ((osc_out[6] + oct_osc_out[6]) >>> 1) : osc_out[6]; 
    assign voice_8_out = (octave_on)? ((osc_out[7] + oct_osc_out[7]) >>> 1) : osc_out[7]; 

endmodule