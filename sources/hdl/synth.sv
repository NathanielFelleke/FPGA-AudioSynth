module synth #(
        parameter integer AUDIO_WIDTH = 32,
        parameter integer NUM_VOICES = 8,
        parameter integer CLK_FREQ = 100_000_000,  // System clock frequency in Hz
        parameter integer SAMPLE_RATE = 48_000     // Audio sample rate in Hz
    )
    (
        input wire clk,
        input wire rst,
        input wire midi_in,
        input wire octave_on,
        output logic signed [AUDIO_WIDTH-1:0] voice_1_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_2_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_3_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_4_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_5_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_6_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_7_out,
        output logic signed [AUDIO_WIDTH-1:0] voice_8_out,
        output logic signed [NUM_VOICES-1:0] ons_out,
        output logic data_valid
    );

    // Sample rate divider - generates 48kHz enable signal
    logic sample_clk_en;
    sample_clk #(.CLK_FREQ(CLK_FREQ), .SAMPLE_RATE(SAMPLE_RATE))
        sample_divider(.clk(clk), .rst(rst), .sample_clk_en(sample_clk_en), .data_valid(data_valid));

    logic [NUM_VOICES-1:0][2:0] note_vels;
    logic [NUM_VOICES-1:0][6:0] note_notes;
    logic [1:0] wave_type;

    midi_rx midi_receiver(.clk(clk), .rst(rst), .data_in(midi_in), .on_out(ons_out), .velocity_out(note_vels), .wave_out(wave_type), .note_out(note_notes));

    // Phase increment values for 48kHz sample rate
    // Formula: PHASE_INCR = (frequency * 2^32) / 48000
    logic [127:0][31:0] note_freqs;
    assign note_freqs[0] = 32'd731558;
    assign note_freqs[1] = 32'd775059;
    assign note_freqs[2] = 32'd821146;
    assign note_freqs[3] = 32'd869974;
    assign note_freqs[4] = 32'd921705;
    assign note_freqs[5] = 32'd976513;
    assign note_freqs[6] = 32'd1034579;
    assign note_freqs[7] = 32'd1096099;
    assign note_freqs[8] = 32'd1161276;
    assign note_freqs[9] = 32'd1230329;
    assign note_freqs[10] = 32'd1303488;
    assign note_freqs[11] = 32'd1380998;
    assign note_freqs[12] = 32'd1463116;
    assign note_freqs[13] = 32'd1550118;
    assign note_freqs[14] = 32'd1642292;
    assign note_freqs[15] = 32'd1739948;
    assign note_freqs[16] = 32'd1843411;
    assign note_freqs[17] = 32'd1953026;
    assign note_freqs[18] = 32'd2069159;
    assign note_freqs[19] = 32'd2192197;
    assign note_freqs[20] = 32'd2322552;
    assign note_freqs[21] = 32'd2460658;
    assign note_freqs[22] = 32'd2606977;
    assign note_freqs[23] = 32'd2761996;
    assign note_freqs[24] = 32'd2926232;
    assign note_freqs[25] = 32'd3100235;
    assign note_freqs[26] = 32'd3284585;
    assign note_freqs[27] = 32'd3479896;
    assign note_freqs[28] = 32'd3686822;
    assign note_freqs[29] = 32'd3906052;
    assign note_freqs[30] = 32'd4138318;
    assign note_freqs[31] = 32'd4384395;
    assign note_freqs[32] = 32'd4645104;
    assign note_freqs[33] = 32'd4921317;
    assign note_freqs[34] = 32'd5213953;
    assign note_freqs[35] = 32'd5523991;
    assign note_freqs[36] = 32'd5852465;
    assign note_freqs[37] = 32'd6200470;
    assign note_freqs[38] = 32'd6569170;
    assign note_freqs[39] = 32'd6959793;
    assign note_freqs[40] = 32'd7373644;
    assign note_freqs[41] = 32'd7812103;
    assign note_freqs[42] = 32'd8276635;
    assign note_freqs[43] = 32'd8768789;
    assign note_freqs[44] = 32'd9290209;
    assign note_freqs[45] = 32'd9842633;
    assign note_freqs[46] = 32'd10427907;
    assign note_freqs[47] = 32'd11047982;
    assign note_freqs[48] = 32'd11704930;
    assign note_freqs[49] = 32'd12400941;
    assign note_freqs[50] = 32'd13138339;
    assign note_freqs[51] = 32'd13919586;
    assign note_freqs[52] = 32'd14747287;
    assign note_freqs[53] = 32'd15624207;
    assign note_freqs[54] = 32'd16553270;
    assign note_freqs[55] = 32'd17537579;
    assign note_freqs[56] = 32'd18580418;
    assign note_freqs[57] = 32'd19685267;
    assign note_freqs[58] = 32'd20855814;
    assign note_freqs[59] = 32'd22095965;
    assign note_freqs[60] = 32'd23409859;
    assign note_freqs[61] = 32'd24801882;
    assign note_freqs[62] = 32'd26276679;
    assign note_freqs[63] = 32'd27839171;
    assign note_freqs[64] = 32'd29494575;
    assign note_freqs[65] = 32'd31248413;
    assign note_freqs[66] = 32'd33106541;
    assign note_freqs[67] = 32'd35075158;
    assign note_freqs[68] = 32'd37160835;
    assign note_freqs[69] = 32'd39370534;
    assign note_freqs[70] = 32'd41711627;
    assign note_freqs[71] = 32'd44191930;
    assign note_freqs[72] = 32'd46819719;
    assign note_freqs[73] = 32'd49603764;
    assign note_freqs[74] = 32'd52553357;
    assign note_freqs[75] = 32'd55678342;
    assign note_freqs[76] = 32'd58989149;
    assign note_freqs[77] = 32'd62496826;
    assign note_freqs[78] = 32'd66213081;
    assign note_freqs[79] = 32'd70150316;
    assign note_freqs[80] = 32'd74321671;
    assign note_freqs[81] = 32'd78741067;
    assign note_freqs[82] = 32'd83423255;
    assign note_freqs[83] = 32'd88383859;
    assign note_freqs[84] = 32'd93639437;
    assign note_freqs[85] = 32'd99207528;
    assign note_freqs[86] = 32'd105106715;
    assign note_freqs[87] = 32'd111356685;
    assign note_freqs[88] = 32'd117978298;
    assign note_freqs[89] = 32'd124993653;
    assign note_freqs[90] = 32'd132426162;
    assign note_freqs[91] = 32'd140300631;
    assign note_freqs[92] = 32'd148643341;
    assign note_freqs[93] = 32'd157482134;
    assign note_freqs[94] = 32'd166846509;
    assign note_freqs[95] = 32'd176767719;
    assign note_freqs[96] = 32'd187278874;
    assign note_freqs[97] = 32'd198415056;
    assign note_freqs[98] = 32'd210213429;
    assign note_freqs[99] = 32'd222713370;
    assign note_freqs[100] = 32'd235956596;
    assign note_freqs[101] = 32'd249987305;
    assign note_freqs[102] = 32'd264852324;
    assign note_freqs[103] = 32'd280601263;
    assign note_freqs[104] = 32'd297286682;
    assign note_freqs[105] = 32'd314964268;
    assign note_freqs[106] = 32'd333693018;
    assign note_freqs[107] = 32'd353535438;
    assign note_freqs[108] = 32'd374557749;
    assign note_freqs[109] = 32'd396830112;
    assign note_freqs[110] = 32'd420426858;
    assign note_freqs[111] = 32'd445426740;
    assign note_freqs[112] = 32'd471913192;
    assign note_freqs[113] = 32'd499974611;
    assign note_freqs[114] = 32'd529704648;
    assign note_freqs[115] = 32'd561202526;
    assign note_freqs[116] = 32'd594573365;
    assign note_freqs[117] = 32'd629928537;
    assign note_freqs[118] = 32'd667386037;
    assign note_freqs[119] = 32'd707070876;
    assign note_freqs[120] = 32'd749115498;
    assign note_freqs[121] = 32'd793660223;
    assign note_freqs[122] = 32'd840853716;
    assign note_freqs[123] = 32'd890853480;
    assign note_freqs[124] = 32'd943826385;
    assign note_freqs[125] = 32'd999949222;
    assign note_freqs[126] = 32'd1059409297;
    assign note_freqs[127] = 32'd1122405052;

    logic signed [7:0][AUDIO_WIDTH-1:0] osc_out;
    logic signed [7:0][AUDIO_WIDTH-1:0] oct_osc_out;
    logic signed [7:0][AUDIO_WIDTH-1:0] notes_xvel;

    genvar i;
    generate
        for (i=0; i < 8; i++) begin
            oscillator osc_inst(.clk(clk), .rst(rst), .wave_type(wave_type), .step_in(sample_clk_en), .PHASE_INCR(note_freqs[note_notes[i]]), .data_out(osc_out[i]));
            oscillator oct_osc_inst(.clk(clk), .rst(rst), .wave_type(wave_type), .step_in(sample_clk_en), .PHASE_INCR(note_freqs[note_notes[i]]<<1), .data_out(oct_osc_out[i]));
        end
    endgenerate

    // velocity scaling with with gain compensation for 32-bit oscillators (to prevent overflow)
    //right shift by 3 bits so it can fit
    //if both oscillators (need to shift by 1 as well)
    assign voice_1_out = (octave_on)? ((osc_out[0] + oct_osc_out[0]) >>> 1) * $signed({1'b0, note_vels[0]+1'b1}) >>> 3 : (osc_out[0] * $signed({1'b0, note_vels[0]+1'b1})) >>> 3;
    assign voice_2_out = (octave_on)? ((osc_out[1] + oct_osc_out[1]) >>> 1) * $signed({1'b0, note_vels[1]+1'b1}) >>> 3 : (osc_out[1] * $signed({1'b0, note_vels[1]+1'b1})) >>> 3;
    assign voice_3_out = (octave_on)? ((osc_out[2] + oct_osc_out[2]) >>> 1) * $signed({1'b0, note_vels[2]+1'b1}) >>> 3 : (osc_out[2] * $signed({1'b0, note_vels[2]+1'b1})) >>> 3;
    assign voice_4_out = (octave_on)? ((osc_out[3] + oct_osc_out[3]) >>> 1) * $signed({1'b0, note_vels[3]+1'b1}) >>> 3 : (osc_out[3] * $signed({1'b0, note_vels[3]+1'b1})) >>> 3;
    assign voice_5_out = (octave_on)? ((osc_out[4] + oct_osc_out[4]) >>> 1) * $signed({1'b0, note_vels[4]+1'b1}) >>> 3 : (osc_out[4] * $signed({1'b0, note_vels[4]+1'b1})) >>> 3;
    assign voice_6_out = (octave_on)? ((osc_out[5] + oct_osc_out[5]) >>> 1) * $signed({1'b0, note_vels[5]+1'b1}) >>> 3 : (osc_out[5] * $signed({1'b0, note_vels[5]+1'b1})) >>> 3;
    assign voice_7_out = (octave_on)? ((osc_out[6] + oct_osc_out[6]) >>> 1) * $signed({1'b0, note_vels[6]+1'b1}) >>> 3 : (osc_out[6] * $signed({1'b0, note_vels[6]+1'b1})) >>> 3;
    assign voice_8_out = (octave_on)? ((osc_out[7] + oct_osc_out[7]) >>> 1) * $signed({1'b0, note_vels[7]+1'b1}) >>> 3 : (osc_out[7] * $signed({1'b0, note_vels[7]+1'b1})) >>> 3;

endmodule