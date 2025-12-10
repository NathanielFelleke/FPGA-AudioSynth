module midi_rx
  #( 
    parameter INPUT_CLOCK_FREQ = 100_000_000, 
    parameter BAUD_RATE = 31_250 // Unused, kept for compatibility
   ) 
   ( 
    input wire          clk, 
    input wire          rst, 
    input wire          data_in, 
 
    // 8 Voices 
    output logic [7:0]       on_out,       
    output logic [7:0][2:0]  velocity_out, 
    output logic [7:0][6:0]  note_out      
   ); 
 
   // ==========================================================================
   // TIMING CONFIGURATION
   // ==========================================================================
   // 120 BPM = 0.5s per beat. 
   localparam BEAT_TICKS = INPUT_CLOCK_FREQ / 2; 
 
   // ==========================================================================
   // SONG ROM (Twinkle Twinkle)
   // ==========================================================================
   // We store: {Note Number (7 bits), Duration in Beats (2 bits), Velocity (3 bits)}
   // Total width = 12 bits
   logic [11:0] song_rom [0:13];
   
   initial begin
      // Format: { NOTE, DURATION, VELOCITY }
      
      // Phrase 1: "Twin-kle Twin-kle Lit-tle Star..."
      song_rom[0]  = {7'd60, 2'd1, 3'd7}; // C4, 1 beat,  Loud (Downbeat)
      song_rom[1]  = {7'd60, 2'd1, 3'd5}; // C4, 1 beat,  Soft
      song_rom[2]  = {7'd67, 2'd1, 3'd6}; // G4, 1 beat,  Medium
      song_rom[3]  = {7'd67, 2'd1, 3'd5}; // G4, 1 beat,  Soft
      song_rom[4]  = {7'd69, 2'd1, 3'd6}; // A4, 1 beat,  Medium
      song_rom[5]  = {7'd69, 2'd1, 3'd5}; // A4, 1 beat,  Soft
      song_rom[6]  = {7'd67, 2'd2, 3'd7}; // G4, 2 BEATS, Loud (End of phrase)
      
      // Phrase 2: "How I won-der what you are..."
      song_rom[7]  = {7'd65, 2'd1, 3'd6}; // F4, 1 beat,  Medium
      song_rom[8]  = {7'd65, 2'd1, 3'd5}; // F4, 1 beat,  Soft
      song_rom[9]  = {7'd64, 2'd1, 3'd6}; // E4, 1 beat,  Medium
      song_rom[10] = {7'd64, 2'd1, 3'd5}; // E4, 1 beat,  Soft
      song_rom[11] = {7'd62, 2'd1, 3'd6}; // D4, 1 beat,  Medium
      song_rom[12] = {7'd62, 2'd1, 3'd5}; // D4, 1 beat,  Soft
      song_rom[13] = {7'd60, 2'd2, 3'd7}; // C4, 2 BEATS, Loud (End)
   end
 
   // ==========================================================================
   // SEQUENCER LOGIC
   // ==========================================================================
   typedef enum {START, NOTE_ON, SUSTAIN, NOTE_OFF, GAP} state_t;
   state_t state;
   
   logic [31:0] timer;
   logic [3:0]  note_index;
   logic [31:0] current_note_duration; // Calculated based on ROM
 
   always_ff @(posedge clk) begin
      if (rst) begin
         on_out       <= 8'b0;
         velocity_out <= '0;
         note_out     <= '0;
         state        <= START;
         timer        <= 0;
         note_index   <= 0;
      end else begin
         case (state)
            START: begin
               // Small delay at startup
               if (timer > INPUT_CLOCK_FREQ/4) begin
                  timer <= 0;
                  state <= NOTE_ON;
               end else timer <= timer + 1;
            end
 
            NOTE_ON: begin
               // 1. Read from ROM
               logic [6:0] note_val;
               logic [1:0] dur_beats;
               logic [2:0] vel_val;
               
               {note_val, dur_beats, vel_val} = song_rom[note_index];
 
               // 2. Apply to Channel 0 (Simulating single finger playing)
               on_out[0]       <= 1'b1;
               note_out[0]     <= note_val;
               velocity_out[0] <= vel_val;
               
               // 3. Calculate hold time (90% of total duration for "Human" feel)
               // If duration is 1 beat, hold for 0.9 beats. 
               // If duration is 2 beats, hold for 1.9 beats.
               current_note_duration <= (BEAT_TICKS * dur_beats * 9) / 10;
               
               timer <= 0;
               state <= SUSTAIN;
            end
 
            SUSTAIN: begin
               if (timer >= current_note_duration) begin
                  state <= NOTE_OFF;
                  timer <= 0;
               end else timer <= timer + 1;
            end
 
            NOTE_OFF: begin
               on_out[0] <= 1'b0; // Lift finger
               state     <= GAP;
               timer     <= 0;
            end
 
            GAP: begin
               // The "Gap" fills the remaining 10% of the beat time
               // We approximate this by waiting a fixed small amount 
               // to ensure the Note Off is registered by your synth.
               if (timer >= (BEAT_TICKS / 10)) begin
                  timer <= 0;
                  if (note_index == 13) note_index <= 0;
                  else note_index <= note_index + 1;
                  
                  state <= NOTE_ON;
               end else timer <= timer + 1;
            end
         endcase
      end
   end
endmodule