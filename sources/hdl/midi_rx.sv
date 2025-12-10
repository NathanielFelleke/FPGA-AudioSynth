// Simplified MIDI RX based on reference implementation
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

   localparam BAUD_BIT_PERIOD = INPUT_CLOCK_FREQ/BAUD_RATE; // 3200 for 100MHz

   // UART State Machine
   logic        uart_state;  // 0=IDLE, 1=READ
   logic [3:0]  bit_count;
   logic [15:0] cycle_count;
   logic [7:0]  rx_data;
   logic        rx_done;

   // MIDI Parsing State Variables
   logic [7:0]  last_status;
   logic [7:0]  stored_note;
   logic        expecting_vel;

   // Free channel finder
   logic [3:0] free_channel;
   assign free_channel =
       (~on_out[0])? 4'd0 : (~on_out[1])? 4'd1 : (~on_out[2])? 4'd2 :
       (~on_out[3])? 4'd3 : (~on_out[4])? 4'd4 : (~on_out[5])? 4'd5 :
       (~on_out[6])? 4'd6 : (~on_out[7])? 4'd7 : 4'd8;

   // UART State Machine (matches reference from jzkmath)
   always_ff @(posedge clk) begin
      if(rst) begin
         uart_state <= 0;
         bit_count <= 0;
         cycle_count <= 0;
         rx_data <= 0;
         rx_done <= 0;

         on_out <= 0;
         velocity_out <= 0;
         note_out <= 0;
         last_status <= 0;
         stored_note <= 0;
         expecting_vel <= 0;
      end
      else begin
         // State Machine
         case(uart_state)
            1'b0: begin // IDLE
               rx_done <= 0;
               if(data_in == 0) begin // Start bit detected
                  uart_state <= 1;
                  bit_count <= 0;
                  cycle_count <= 0;
               end
            end

            1'b1: begin // READ
               cycle_count <= cycle_count + 1;

               // Skip start bit (wait BAUD_BIT_PERIOD/2)
               if(cycle_count == BAUD_BIT_PERIOD/2 && bit_count == 0) begin
                  cycle_count <= 0;
                  bit_count <= 1; // Mark that we've skipped start bit
               end

               // Sample data bits (8 bits total)
               else if(cycle_count == BAUD_BIT_PERIOD && bit_count >= 1 && bit_count <= 8) begin
                  // LSB first: shift right, new bit enters at MSB
                  rx_data <= {data_in, rx_data[7:1]};
                  bit_count <= bit_count + 1;
                  cycle_count <= 0;
               end

               // Check stop bit
               else if(cycle_count == BAUD_BIT_PERIOD && bit_count == 9 && data_in == 1) begin
                  rx_done <= 1;
                  uart_state <= 0; // Back to IDLE
                  bit_count <= 0;
                  cycle_count <= 0;
               end

               // Framing error - no valid stop bit
               else if(cycle_count == BAUD_BIT_PERIOD && bit_count == 9 && data_in == 0) begin
                  uart_state <= 0; // Abort, back to IDLE
                  bit_count <= 0;
                  cycle_count <= 0;
               end
            end
         endcase

         // MIDI Processing (on rx_done pulse)
         if(rx_done) begin
            // Status byte (bit 7 = 1)
            if(rx_data[7] == 1) begin
               if(rx_data < 8'hF0) begin
                  last_status <= rx_data;
                  expecting_vel <= 0;
               end
            end
            // Data byte (bit 7 = 0)
            else begin
               if(expecting_vel == 0) begin
                  // This is the note number
                  stored_note <= rx_data;
                  expecting_vel <= 1;
               end
               else begin
                  // This is the velocity - trigger action
                  expecting_vel <= 0;

                  // Note ON (0x90)
                  if(last_status[7:4] == 4'h9 && rx_data > 0) begin
                     if(free_channel != 8) begin
                        on_out[free_channel] <= 1;
                        note_out[free_channel] <= stored_note[6:0];
                        velocity_out[free_channel] <= rx_data[7:5];
                     end
                  end

                  // Note OFF (0x80 or 0x90 with vel=0)
                  else if(last_status[7:4] == 4'h8 || (last_status[7:4] == 4'h9 && rx_data == 0)) begin
                     for(int i=0; i<8; i=i+1) begin
                        if(on_out[i] && note_out[i] == stored_note[6:0]) begin
                           on_out[i] <= 0;
                        end
                     end
                  end
               end
            end
         end
      end
   end

endmodule
