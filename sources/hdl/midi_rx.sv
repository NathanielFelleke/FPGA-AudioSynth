My apologies. I see exactly what you mean now. You want the **exact** structure of your reference UART code (using `if/else if`, specific states 0-4, and the `BAUD_BIT_PERIOD` logic), but modified to handle **MSB-first** data collection and integrated with the MIDI processing logic you need.

Here is the `midi_rx` module rebuilt from scratch using your specific template and timing logic.

### Key Changes to Match Your Request:

1.  **Structure:** Copied your `uart_receive` state machine structure exactly (States 0-4, `BAUD_BIT_PERIOD` calculations).
2.  **MSB Logic:** In `state == 2` (Data), I changed the bit assignment to `temp_data[7 - data_counter] <= data_in`. This ensures the first bit received goes to the MSB (Bit 7).
3.  **Integration:** The MIDI parsing logic happens in **State 4** (where your reference code asserts `new_data_out`).

<!-- end list -->

```systemverilog
module midi_rx 
  #(
    parameter INPUT_CLOCK_FREQ = 100_000_000,
    parameter BAUD_RATE = 31_250 // MIDI Standard
   )
   (
    input wire         clk,
    input wire         rst,
    input wire         data_in,
    
    // 8 Voices
    output logic [7:0]       on_out,       // 1 = Note is Active
    output logic [7:0][2:0]  velocity_out, // 3-bit Velocity per voice
    output logic [7:0][6:0]  note_out      // Note Number per voice
   );
   
   localparam BAUD_BIT_PERIOD = INPUT_CLOCK_FREQ/BAUD_RATE;

   logic [3:0]  data_counter = 0;
   logic [15:0] clk_counter  = 0;
   logic [3:0]  state        = 0; 
   logic [7:0]  temp_data    = 0;
   
   // MIDI Parsing State Variables
   logic [7:0]  last_status;      // Holds the running status (e.g., 0x90)
   logic [7:0]  stored_note;      // Holds the first data byte (Note Number)
   logic        expecting_vel;    // Toggle to track if we are waiting for Note or Velocity
   
   // Free channel finder (Combinational)
   logic [3:0] free_channel;
   assign free_channel = 
       (~on_out[0])? 4'd0 : (~on_out[1])? 4'd1 : (~on_out[2])? 4'd2 : 
       (~on_out[3])? 4'd3 : (~on_out[4])? 4'd4 : (~on_out[5])? 4'd5 : 
       (~on_out[6])? 4'd6 : (~on_out[7])? 4'd7 : 4'd8; 

   always_ff @(posedge clk) begin
    if(rst == 1) begin
      state         <= 4'd0;
      data_counter  <= 0;
      clk_counter   <= 0;
      temp_data     <= 0;
      
      // Reset Outputs
      on_out        <= 0;
      velocity_out  <= 0;
      note_out      <= 0;
      
      // Reset MIDI Parser
      last_status   <= 0;
      stored_note   <= 0;
      expecting_vel <= 0;
    end
    
    // --------------------------------------------------------
    // STATE 0: IDLE
    // --------------------------------------------------------
    else if(state == 4'd0) begin
      if(data_in == 0) begin
        state       <= 4'd1;
        clk_counter <= 0;
      end
    end
    
    // --------------------------------------------------------
    // STATE 1: START BIT CHECK
    // --------------------------------------------------------
    else if(state == 4'd1) begin
      if(clk_counter == BAUD_BIT_PERIOD/2) begin
        if(data_in == 0) begin
          state <= 4'd2; // Valid start bit, go to data
        end
        else begin
          state <= 4'd0; // False start, go back to idle
        end
        clk_counter <= 0;
      end
      else begin
        clk_counter <= clk_counter + 1;
      end
    end
    
    // --------------------------------------------------------
    // STATE 2: DATA BITS (MSB FIRST MODIFICATION)
    // --------------------------------------------------------
    else if(state == 4'd2) begin
      if(clk_counter == BAUD_BIT_PERIOD - 1) begin
        // *** MSB FIRST LOGIC ***
        // Bit 0 received -> Index 7. Bit 7 received -> Index 0.
        temp_data[3'd7 - data_counter[2:0]] <= data_in;
        
        data_counter <= data_counter + 1;
        if(data_counter == 4'd7) begin
          state        <= 4'd3;
          data_counter <= 0;
        end
        clk_counter <= 0;
      end
      else begin
        clk_counter <= clk_counter + 1;
      end
    end
    
    // --------------------------------------------------------
    // STATE 3: STOP BIT CHECK
    // --------------------------------------------------------
    else if(state == 4'd3) begin
      if(clk_counter == BAUD_BIT_PERIOD - 1) begin
        // Check for Stop Bit (Should be 1)
        if(data_in == 0) begin
           state <= 4'd0; // Framing Error
        end 
        else begin
           state <= 4'd4; // Success
        end
        clk_counter <= 0;
      end
      else begin
        clk_counter <= clk_counter + 1;
      end
    end
    
    // --------------------------------------------------------
    // STATE 4: PROCESS BYTE (MIDI LOGIC)
    // --------------------------------------------------------
    else if(state == 4'd4) begin
      
      // 1. HANDLE STATUS BYTE (Bit 7 is High)
      if (temp_data[7] == 1) begin
          if (temp_data < 8'hF0) begin // Ignore Realtime/SysEx for simplicity
              last_status   <= temp_data;
              expecting_vel <= 0; // Reset to expect Note next
          end
      end
      
      // 2. HANDLE DATA BYTE (Bit 7 is Low)
      else begin
          // If we are not expecting velocity, this must be the NOTE number
          if (expecting_vel == 0) begin
              stored_note   <= temp_data;
              expecting_vel <= 1; // Next byte should be velocity
          end
          
          // If we ARE expecting velocity, this is the VELOCITY (Trigger Action)
          else begin
              expecting_vel <= 0; // Reset for next note (Running Status)
              
              // --- NOTE ON (0x90) ---
              if (last_status[7:4] == 4'h9 && temp_data > 0) begin
                  if (free_channel != 8) begin
                      on_out[free_channel]       <= 1;
                      note_out[free_channel]     <= stored_note[6:0];
                      velocity_out[free_channel] <= temp_data[7:5]; // Top 3 bits
                  end
              end
              
              // --- NOTE OFF (0x80 OR 0x90 with Vel=0) ---
              else if (last_status[7:4] == 4'h8 || (last_status[7:4] == 4'h9 && temp_data == 0)) begin
                  for (int i=0; i<8; i=i+1) begin
                      // If channel is on AND note matches, turn it off
                      if (on_out[i] && note_out[i] == stored_note[6:0]) begin
                          on_out[i] <= 0;
                      end
                  end
              end
          end
      end

      state <= 4'd0; // Return to IDLE
    end
   end

endmodule
```