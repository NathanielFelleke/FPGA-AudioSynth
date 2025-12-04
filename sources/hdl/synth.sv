module synth #(
        parameter integer AUDIO_WIDTH = 32,
        parameter integer NUM_VOICES = 8
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
        output logic signed [NUM_VOICES-1:0] ons_out
    );

    logic [NUM_VOICES-1:0][2:0] note_vels;
    logic [NUM_VOICES-1:0][6:0] note_notes;
    logic [1:0] wave_type;

    midi_rx midi_receiver(.clk(clk), .rst(rst), .data_in(midi_in), .on_out(ons_out), .velocity_out(note_vels), .wave_out(wave_type), .note_out(note_notes));

    logic [127:0][32:0] note_freqs;
    assign note_freqs[0] = 32'd702;
    assign note_freqs[1] = 32'd743;
    assign note_freqs[2] = 32'd788;
    assign note_freqs[3] = 32'd835;
    assign note_freqs[4] = 32'd884;
    assign note_freqs[5] = 32'd937;
    assign note_freqs[6] = 32'd993;
    assign note_freqs[7] = 32'd1052;
    assign note_freqs[8] = 32'd1114;
    assign note_freqs[9] = 32'd1181;
    assign note_freqs[10] = 32'd1251;
    assign note_freqs[11] = 32'd1325;
    assign note_freqs[12] = 32'd1404;
    assign note_freqs[13] = 32'd1487;
    assign note_freqs[14] = 32'd1576;
    assign note_freqs[15] = 32'd1670;
    assign note_freqs[16] = 32'd1769;
    assign note_freqs[17] = 32'd1874;
    assign note_freqs[18] = 32'd1986;
    assign note_freqs[19] = 32'd2104;
    assign note_freqs[20] = 32'd2229;
    assign note_freqs[21] = 32'd2362;
    assign note_freqs[22] = 32'd2502;
    assign note_freqs[23] = 32'd2651;
    assign note_freqs[24] = 32'd2808;
    assign note_freqs[25] = 32'd2975;
    assign note_freqs[26] = 32'd3152;
    assign note_freqs[27] = 32'd3340;
    assign note_freqs[28] = 32'd3539;
    assign note_freqs[29] = 32'd3749;
    assign note_freqs[30] = 32'd3972;
    assign note_freqs[31] = 32'd4208;
    assign note_freqs[32] = 32'd4458;
    assign note_freqs[33] = 32'd4724;
    assign note_freqs[34] = 32'd5004;
    assign note_freqs[35] = 32'd5302;
    assign note_freqs[36] = 32'd5617;
    assign note_freqs[37] = 32'd5951;
    assign note_freqs[38] = 32'd6305;
    assign note_freqs[39] = 32'd6680;
    assign note_freqs[40] = 32'd7078;
    assign note_freqs[41] = 32'd7498;
    assign note_freqs[42] = 32'd7944;
    assign note_freqs[43] = 32'd8417;
    assign note_freqs[44] = 32'd8917;
    assign note_freqs[45] = 32'd9448;
    assign note_freqs[46] = 32'd10009;
    assign note_freqs[47] = 32'd10605;
    assign note_freqs[48] = 32'd11235;
    assign note_freqs[49] = 32'd11903;
    assign note_freqs[50] = 32'd12611;
    assign note_freqs[51] = 32'd13361;
    assign note_freqs[52] = 32'd14156;
    assign note_freqs[53] = 32'd14997;
    assign note_freqs[54] = 32'd15889;
    assign note_freqs[55] = 32'd16834;
    assign note_freqs[56] = 32'd17835;
    assign note_freqs[57] = 32'd18896;
    assign note_freqs[58] = 32'd20019;
    assign note_freqs[59] = 32'd21210;
    assign note_freqs[60] = 32'd22471;
    assign note_freqs[61] = 32'd23807;
    assign note_freqs[62] = 32'd25223;
    assign note_freqs[63] = 32'd26722;
    assign note_freqs[64] = 32'd28312;
    assign note_freqs[65] = 32'd29995;
    assign note_freqs[66] = 32'd31779;
    assign note_freqs[67] = 32'd33668;
    assign note_freqs[68] = 32'd35670;
    assign note_freqs[69] = 32'd37792;
    assign note_freqs[70] = 32'd40039;
    assign note_freqs[71] = 32'd42420;
    assign note_freqs[72] = 32'd44942;
    assign note_freqs[73] = 32'd47614;
    assign note_freqs[74] = 32'd50446;
    assign note_freqs[75] = 32'd53445;
    assign note_freqs[76] = 32'd56624;
    assign note_freqs[77] = 32'd59991;
    assign note_freqs[78] = 32'd63558;
    assign note_freqs[79] = 32'd67337;
    assign note_freqs[80] = 32'd71341;
    assign note_freqs[81] = 32'd75584;
    assign note_freqs[82] = 32'd80078;
    assign note_freqs[83] = 32'd84840;
    assign note_freqs[84] = 32'd89885;
    assign note_freqs[85] = 32'd95229;
    assign note_freqs[86] = 32'd100892;
    assign note_freqs[87] = 32'd106891;
    assign note_freqs[88] = 32'd113248;
    assign note_freqs[89] = 32'd119982;
    assign note_freqs[90] = 32'd127116;
    assign note_freqs[91] = 32'd134675;
    assign note_freqs[92] = 32'd142683;
    assign note_freqs[93] = 32'd151168;
    assign note_freqs[94] = 32'd160156;
    assign note_freqs[95] = 32'd169680;
    assign note_freqs[96] = 32'd179770;
    assign note_freqs[97] = 32'd190459;
    assign note_freqs[98] = 32'd201785;
    assign note_freqs[99] = 32'd213783;
    assign note_freqs[100] = 32'd226496;
    assign note_freqs[101] = 32'd239964;
    assign note_freqs[102] = 32'd254233;
    assign note_freqs[103] = 32'd269350;
    assign note_freqs[104] = 32'd285367;
    assign note_freqs[105] = 32'd302336;
    assign note_freqs[106] = 32'd320313;
    assign note_freqs[107] = 32'd339360;
    assign note_freqs[108] = 32'd359540;
    assign note_freqs[109] = 32'd380919;
    assign note_freqs[110] = 32'd403570;
    assign note_freqs[111] = 32'd427567;
    assign note_freqs[112] = 32'd452992;
    assign note_freqs[113] = 32'd479928;
    assign note_freqs[114] = 32'd508466;
    assign note_freqs[115] = 32'd538701;
    assign note_freqs[116] = 32'd570734;
    assign note_freqs[117] = 32'd604672;
    assign note_freqs[118] = 32'd640627;
    assign note_freqs[119] = 32'd678721;
    assign note_freqs[120] = 32'd719080;
    assign note_freqs[121] = 32'd761839;
    assign note_freqs[122] = 32'd807140;
    assign note_freqs[123] = 32'd855135;
    assign note_freqs[124] = 32'd905984;
    assign note_freqs[125] = 32'd959857;
    assign note_freqs[126] = 32'd1016933;
    assign note_freqs[127] = 32'd1077403;

    logic signed [7:0][AUDIO_WIDTH-1:0] osc_out;
    logic signed [7:0][AUDIO_WIDTH-1:0] oct_osc_out;
    logic signed [7:0][AUDIO_WIDTH-1:0] notes_xvel;

    genvar i;
    generate
        for (i=0; i < 16; i++) begin
            oscillator osc_inst(.clk(clk), .rst(rst), .wave_type(wave_type), .step_in(1), .PHASE_INCR(note_freqs[note_notes[i]]), .data_out(osc_out[i]));
            oscillator oct_osc_inst(.clk(clk), .rst(rst), .wave_type(wave_type), .step_in(1), .PHASE_INCR(note_freqs[note_notes[i]]<<1), .data_out(oct_osc_out[i]));
        end
    endgenerate

    assign voice_1_out = (octave_on)? $signed(osc_out[0])*(note_vels[0]+1)+$signed(oct_osc_out[0])*(note_vels[0]+1) : $signed(osc_out[0])*(note_vels[0]+1);
    assign voice_2_out = (octave_on)? $signed(osc_out[1])*(note_vels[1]+1)+$signed(oct_osc_out[1])*(note_vels[1]+1) : $signed(osc_out[1])*(note_vels[1]+1);
    assign voice_3_out = (octave_on)? $signed(osc_out[2])*(note_vels[2]+1)+$signed(oct_osc_out[2])*(note_vels[2]+1) : $signed(osc_out[2])*(note_vels[2]+1);
    assign voice_4_out = (octave_on)? $signed(osc_out[3])*(note_vels[3]+1)+$signed(oct_osc_out[3])*(note_vels[3]+1) : $signed(osc_out[3])*(note_vels[3]+1);
    assign voice_5_out = (octave_on)? $signed(osc_out[4])*(note_vels[4]+1)+$signed(oct_osc_out[4])*(note_vels[4]+1) : $signed(osc_out[4])*(note_vels[4]+1);
    assign voice_6_out = (octave_on)? $signed(osc_out[5])*(note_vels[5]+1)+$signed(oct_osc_out[5])*(note_vels[5]+1) : $signed(osc_out[5])*(note_vels[5]+1);
    assign voice_7_out = (octave_on)? $signed(osc_out[6])*(note_vels[6]+1)+$signed(oct_osc_out[6])*(note_vels[6]+1) : $signed(osc_out[6])*(note_vels[6]+1);
    assign voice_8_out = (octave_on)? $signed(osc_out[7])*(note_vels[7]+1)+$signed(oct_osc_out[7])*(note_vels[7]+1) : $signed(osc_out[7])*(note_vels[7]+1);

endmodule