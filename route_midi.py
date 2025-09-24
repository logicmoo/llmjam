# route_midi.py
# Utility to route MIDI input to output ports.
# If no arguments are provided, it lists ports and asks the user to pick which input to route to which output.

import rtmidi
import sys

def list_ports():
    midi_in = rtmidi.RtMidiIn()
    midi_out = rtmidi.RtMidiOut()

    print("🎹 Available MIDI Input Ports:")
    for i in range(midi_in.getPortCount()):
        print(f"  [{i}] {midi_in.getPortName(i)}")

    print("\n🎧 Available MIDI Output Ports:")
    for i in range(midi_out.getPortCount()):
        print(f"  [{i}] {midi_out.getPortName(i)}")

    return midi_in.getPortCount(), midi_out.getPortCount()

def main():
    if len(sys.argv) < 3:
        print("Usage: python route_midi.py [input_port_num] [output_port_num]")
        print("No ports specified. Listing ports:")
        in_count, out_count = list_ports()
        if in_count == 0 or out_count == 0:
            print("\n❌ No available MIDI input or output ports.")
            return
        try:
            input_index = int(input("\nEnter input port number to route from: "))
            output_index = int(input("Enter output port number to route to: "))
        except ValueError:
            print("Invalid input. Exiting.")
            return
    else:
        input_index = int(sys.argv[1])
        output_index = int(sys.argv[2])

    midi_in = rtmidi.RtMidiIn()
    midi_out = rtmidi.RtMidiOut()

    try:
        midi_in.openPort(input_index)
        midi_out.openPort(output_index)
    except rtmidi.Error as e:
        print(f"Error opening ports: {e}")
        return

    print(f"🔁 Routing input port '{midi_in.getPortName(input_index)}' to output port '{midi_out.getPortName(output_index)}'")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            msg = midi_in.getMessage(10)
            if msg:
                midi_out.sendMessage(msg)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
