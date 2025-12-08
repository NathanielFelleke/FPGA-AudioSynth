module sine_generator (
  input wire clk_in,
  input wire rst_in,
  input wire step_in,
  input wire [31:0] PHASE_INCR,
  output logic signed [31:0] amp_out);

  logic [31:0] phase;
  logic signed [31:0] lut_out;

  // Use top 10 bits for 1024-point resolution (high quality audio)
  sine_lut lut_1(.clk_in(clk_in), .phase_in(phase[31:22]), .amp_out(lut_out));

  assign amp_out = lut_out;

  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      phase <= 32'b0;
    end else if (step_in)begin
      phase <= phase+PHASE_INCR;
    end
  end
endmodule

// 10-bit sine lookup with quarter-wave symmetry, 32-bit output
module sine_lut(input wire [9:0] phase_in, input wire clk_in, output logic signed [31:0] amp_out);
  logic [7:0] quarter_phase;
  logic signed [31:0] quarter_amp;
  logic [1:0] quadrant;

  // Quarter-wave ROM - 256 entries with 32-bit signed values
  logic signed [31:0] sine_rom [0:255];

  assign quadrant = phase_in[9:8];
  assign quarter_phase = (quadrant[0]) ? ~phase_in[7:0] : phase_in[7:0];

  // Initialize ROM with sine values (0 to π/2)
  // Values calculated as: round(sin(i * π / 512) * 2^31-1)
  initial begin
     sine_rom[0] = 32'sd0; sine_rom[1] = 32'sd13176712; sine_rom[2] = 32'sd26352928; sine_rom[3] = 32'sd39528151;
    sine_rom[4] = 32'sd52701887; sine_rom[5] = 32'sd65873638; sine_rom[6] = 32'sd79042909; sine_rom[7] = 32'sd92209205;        
    sine_rom[8] = 32'sd105372028; sine_rom[9] = 32'sd118530885; sine_rom[10] = 32'sd131685278; sine_rom[11] = 32'sd144834714;  
    sine_rom[12] = 32'sd157978697; sine_rom[13] = 32'sd171116732; sine_rom[14] = 32'sd184248325; sine_rom[15] = 32'sd197372981;
    sine_rom[16] = 32'sd210490206; sine_rom[17] = 32'sd223599506; sine_rom[18] = 32'sd236700388; sine_rom[19] = 32'sd249792358;
    sine_rom[20] = 32'sd262874923; sine_rom[21] = 32'sd275947592; sine_rom[22] = 32'sd289009871; sine_rom[23] = 32'sd302061269;
    sine_rom[24] = 32'sd315101294; sine_rom[25] = 32'sd328129457; sine_rom[26] = 32'sd341145265; sine_rom[27] = 32'sd354148229;
    sine_rom[28] = 32'sd367137860; sine_rom[29] = 32'sd380113669; sine_rom[30] = 32'sd393075166; sine_rom[31] = 32'sd406021864;
    sine_rom[32] = 32'sd418953276; sine_rom[33] = 32'sd431868915; sine_rom[34] = 32'sd444768293; sine_rom[35] = 32'sd457650927;
    sine_rom[36] = 32'sd470516330; sine_rom[37] = 32'sd483364019; sine_rom[38] = 32'sd496193509; sine_rom[39] = 32'sd509004318;
    sine_rom[40] = 32'sd521795963; sine_rom[41] = 32'sd534567963; sine_rom[42] = 32'sd547319836; sine_rom[43] = 32'sd560051103;
    sine_rom[44] = 32'sd572761285; sine_rom[45] = 32'sd585449903; sine_rom[46] = 32'sd598116478; sine_rom[47] = 32'sd610760535;
    sine_rom[48] = 32'sd623381597; sine_rom[49] = 32'sd635979190; sine_rom[50] = 32'sd648552837; sine_rom[51] = 32'sd661102068;
    sine_rom[52] = 32'sd673626408; sine_rom[53] = 32'sd686125386; sine_rom[54] = 32'sd698598533; sine_rom[55] = 32'sd711045377;
    sine_rom[56] = 32'sd723465451; sine_rom[57] = 32'sd735858287; sine_rom[58] = 32'sd748223418; sine_rom[59] = 32'sd760560379;
    sine_rom[60] = 32'sd772868706; sine_rom[61] = 32'sd785147934; sine_rom[62] = 32'sd797397602; sine_rom[63] = 32'sd809617248;
    sine_rom[64] = 32'sd821806413; sine_rom[65] = 32'sd833964637; sine_rom[66] = 32'sd846091463; sine_rom[67] = 32'sd858186434;
    sine_rom[68] = 32'sd870249095; sine_rom[69] = 32'sd882278991; sine_rom[70] = 32'sd894275670; sine_rom[71] = 32'sd906238681;
    sine_rom[72] = 32'sd918167571; sine_rom[73] = 32'sd930061894; sine_rom[74] = 32'sd941921200; sine_rom[75] = 32'sd953745043;
    sine_rom[76] = 32'sd965532978; sine_rom[77] = 32'sd977284561; sine_rom[78] = 32'sd988999351; sine_rom[79] = 32'sd1000676905;
    sine_rom[80] = 32'sd1012316784; sine_rom[81] = 32'sd1023918549; sine_rom[82] = 32'sd1035481765; sine_rom[83] = 32'sd1047005996;
    sine_rom[84] = 32'sd1058490807; sine_rom[85] = 32'sd1069935767; sine_rom[86] = 32'sd1081340445; sine_rom[87] = 32'sd1092704410;
    sine_rom[88] = 32'sd1104027236; sine_rom[89] = 32'sd1115308496; sine_rom[90] = 32'sd1126547765; sine_rom[91] = 32'sd1137744620;
    sine_rom[92] = 32'sd1148898640; sine_rom[93] = 32'sd1160009404; sine_rom[94] = 32'sd1171076495; sine_rom[95] = 32'sd1182099495;
    sine_rom[96] = 32'sd1193077990; sine_rom[97] = 32'sd1204011566; sine_rom[98] = 32'sd1214899812; sine_rom[99] = 32'sd1225742318;
    sine_rom[100] = 32'sd1236538675; sine_rom[101] = 32'sd1247288477; sine_rom[102] = 32'sd1257991319; sine_rom[103] = 32'sd1268646799;
    sine_rom[104] = 32'sd1279254515; sine_rom[105] = 32'sd1289814068; sine_rom[106] = 32'sd1300325059; sine_rom[107] = 32'sd1310787095;
    sine_rom[108] = 32'sd1321199780; sine_rom[109] = 32'sd1331562722; sine_rom[110] = 32'sd1341875532; sine_rom[111] = 32'sd1352137822;
    sine_rom[112] = 32'sd1362349204; sine_rom[113] = 32'sd1372509294; sine_rom[114] = 32'sd1382617710; sine_rom[115] = 32'sd1392674071;
    sine_rom[116] = 32'sd1402677999; sine_rom[117] = 32'sd1412629117; sine_rom[118] = 32'sd1422527050; sine_rom[119] = 32'sd1432371426;
    sine_rom[120] = 32'sd1442161874; sine_rom[121] = 32'sd1451898025; sine_rom[122] = 32'sd1461579513; sine_rom[123] = 32'sd1471205973;
    sine_rom[124] = 32'sd1480777044; sine_rom[125] = 32'sd1490292364; sine_rom[126] = 32'sd1499751575; sine_rom[127] = 32'sd1509154322;
    sine_rom[128] = 32'sd1518500249; sine_rom[129] = 32'sd1527789006; sine_rom[130] = 32'sd1537020243; sine_rom[131] = 32'sd1546193612;
    sine_rom[132] = 32'sd1555308767; sine_rom[133] = 32'sd1564365366; sine_rom[134] = 32'sd1573363067; sine_rom[135] = 32'sd1582301533;
    sine_rom[136] = 32'sd1591180425; sine_rom[137] = 32'sd1599999410; sine_rom[138] = 32'sd1608758157; sine_rom[139] = 32'sd1617456334;
    sine_rom[140] = 32'sd1626093615; sine_rom[141] = 32'sd1634669675; sine_rom[142] = 32'sd1643184190; sine_rom[143] = 32'sd1651636840;
    sine_rom[144] = 32'sd1660027308; sine_rom[145] = 32'sd1668355276; sine_rom[146] = 32'sd1676620431; sine_rom[147] = 32'sd1684822463;
    sine_rom[148] = 32'sd1692961061; sine_rom[149] = 32'sd1701035921; sine_rom[150] = 32'sd1709046738; sine_rom[151] = 32'sd1716993211;
    sine_rom[152] = 32'sd1724875039; sine_rom[153] = 32'sd1732691927; sine_rom[154] = 32'sd1740443580; sine_rom[155] = 32'sd1748129706;
    sine_rom[156] = 32'sd1755750016; sine_rom[157] = 32'sd1763304223; sine_rom[158] = 32'sd1770792043; sine_rom[159] = 32'sd1778213194;
    sine_rom[160] = 32'sd1785567395; sine_rom[161] = 32'sd1792854372; sine_rom[162] = 32'sd1800073848; sine_rom[163] = 32'sd1807225552;
    sine_rom[164] = 32'sd1814309215; sine_rom[165] = 32'sd1821324571; sine_rom[166] = 32'sd1828271355; sine_rom[167] = 32'sd1835149305;
    sine_rom[168] = 32'sd1841958164; sine_rom[169] = 32'sd1848697673; sine_rom[170] = 32'sd1855367580; sine_rom[171] = 32'sd1861967633;
    sine_rom[172] = 32'sd1868497585; sine_rom[173] = 32'sd1874957188; sine_rom[174] = 32'sd1881346201; sine_rom[175] = 32'sd1887664382;
    sine_rom[176] = 32'sd1893911493; sine_rom[177] = 32'sd1900087300; sine_rom[178] = 32'sd1906191569; sine_rom[179] = 32'sd1912224072;
    sine_rom[180] = 32'sd1918184580; sine_rom[181] = 32'sd1924072870; sine_rom[182] = 32'sd1929888719; sine_rom[183] = 32'sd1935631909;
    sine_rom[184] = 32'sd1941302224; sine_rom[185] = 32'sd1946899450; sine_rom[186] = 32'sd1952423376; sine_rom[187] = 32'sd1957873795;
    sine_rom[188] = 32'sd1963250500; sine_rom[189] = 32'sd1968553291; sine_rom[190] = 32'sd1973781966; sine_rom[191] = 32'sd1978936330;
    sine_rom[192] = 32'sd1984016188; sine_rom[193] = 32'sd1989021349; sine_rom[194] = 32'sd1993951624; sine_rom[195] = 32'sd1998806828;
    sine_rom[196] = 32'sd2003586778; sine_rom[197] = 32'sd2008291295; sine_rom[198] = 32'sd2012920200; sine_rom[199] = 32'sd2017473320;
    sine_rom[200] = 32'sd2021950483; sine_rom[201] = 32'sd2026351521; sine_rom[202] = 32'sd2030676268; sine_rom[203] = 32'sd2034924561;
    sine_rom[204] = 32'sd2039096240; sine_rom[205] = 32'sd2043191149; sine_rom[206] = 32'sd2047209132; sine_rom[207] = 32'sd2051150040;
    sine_rom[208] = 32'sd2055013722; sine_rom[209] = 32'sd2058800035; sine_rom[210] = 32'sd2062508835; sine_rom[211] = 32'sd2066139982;
    sine_rom[212] = 32'sd2069693341; sine_rom[213] = 32'sd2073168776; sine_rom[214] = 32'sd2076566159; sine_rom[215] = 32'sd2079885359;
    sine_rom[216] = 32'sd2083126253; sine_rom[217] = 32'sd2086288719; sine_rom[218] = 32'sd2089372637; sine_rom[219] = 32'sd2092377891;
    sine_rom[220] = 32'sd2095304369; sine_rom[221] = 32'sd2098151959; sine_rom[222] = 32'sd2100920555; sine_rom[223] = 32'sd2103610053;
    sine_rom[224] = 32'sd2106220351; sine_rom[225] = 32'sd2108751351; sine_rom[226] = 32'sd2111202958; sine_rom[227] = 32'sd2113575079;
    sine_rom[228] = 32'sd2115867625; sine_rom[229] = 32'sd2118080510; sine_rom[230] = 32'sd2120213650; sine_rom[231] = 32'sd2122266966;
    sine_rom[232] = 32'sd2124240379; sine_rom[233] = 32'sd2126133816; sine_rom[234] = 32'sd2127947205; sine_rom[235] = 32'sd2129680479;
    sine_rom[236] = 32'sd2131333571; sine_rom[237] = 32'sd2132906419; sine_rom[238] = 32'sd2134398965; sine_rom[239] = 32'sd2135811152;
    sine_rom[240] = 32'sd2137142926; sine_rom[241] = 32'sd2138394239; sine_rom[242] = 32'sd2139565042; sine_rom[243] = 32'sd2140655292;
    sine_rom[244] = 32'sd2141664947; sine_rom[245] = 32'sd2142593970; sine_rom[246] = 32'sd2143442325; sine_rom[247] = 32'sd2144209981;
    sine_rom[248] = 32'sd2144896909; sine_rom[249] = 32'sd2145503082; sine_rom[250] = 32'sd2146028479; sine_rom[251] = 32'sd2146473079;
    sine_rom[252] = 32'sd2146836865; sine_rom[253] = 32'sd2147119824; sine_rom[254] = 32'sd2147321945; sine_rom[255] = 32'sd2147443221;
  end

  always_ff @(posedge clk_in) begin
    quarter_amp <= sine_rom[quarter_phase];
  end

  assign amp_out = (quadrant[1]) ? -quarter_amp : quarter_amp;

endmodule
