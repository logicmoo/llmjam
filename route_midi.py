# route_midi.py
# Utility to route MIDI input to output ports.
# If no arguments are provided, it lists ports and asks the user to pick which input to route to which output.

import sys
import time

try:
    import rtmidi  # Provided by the 'python-rtmidi' package
except Exception as e:
    print("❌ Failed to import 'rtmidi'. This script requires the 'python-rtmidi' package.")
    print(f"   Reason: {type(e).__name__}: {e}")
    print("   How to install: pip install python-rtmidi")
    sys.exit(1)


def list_ports():
    """
    Print available MIDI input/output ports and return their counts.
    Exits with an explicit message if the MIDI backend cannot be initialized.
    """
    try:
        midi_in = rtmidi.MidiIn()
        midi_out = rtmidi.MidiOut()
    except Exception as e:
        print(f"❌ Failed to initialize the MIDI system: {type(e).__name__}: {e}")
        print("   This can happen if your OS MIDI subsystem is unavailable or misconfigured.")
        sys.exit(1)

    in_count = midi_in.get_port_count()
    out_count = midi_out.get_port_count()

    print("🎹 Available MIDI Input Ports:")
    for i in range(in_count):
        try:
            print(f"  [{i}] {midi_in.get_port_name(i)}")
        except Exception as e:
            print(f"  [{i}] <error reading name: {type(e).__name__}: {e}>")

    print("\n🎧 Available MIDI Output Ports:")
    for i in range(out_count):
        try:
            print(f"  [{i}] {midi_out.get_port_name(i)}")
        except Exception as e:
            print(f"  [{i}] <error reading name: {type(e).__name__}: {e}>")

    return in_count, out_count


def main():
    if len(sys.argv) < 3:
        print("Usage: python route_midi.py [input_port_num] [output_port_num]")
        print("No ports specified. Listing ports:")
        in_count, out_count = list_ports()
        if in_count == 0 or out_count == 0:
            print(f"\n❌ No available MIDI ports. Inputs: {in_count}, Outputs: {out_count}.")
            return
        try:
            input_index = int(input("\nEnter input port number to route from: "))
            output_index = int(input("Enter output port number to route to: "))
        except ValueError:
            print("❌ Invalid input: please enter integers for port numbers. Exiting.")
            return
    else:
        try:
            input_index = int(sys.argv[1])
            output_index = int(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid command-line arguments: {sys.argv[1:]}. Port numbers must be integers.")
            return

    # Initialize MIDI interfaces
    try:
        midi_in = rtmidi.MidiIn()
        midi_out = rtmidi.MidiOut()
    except Exception as e:
        print(f"❌ Failed to initialize MIDI interfaces: {type(e).__name__}: {e}")
        return

    in_count = midi_in.get_port_count()
    out_count = midi_out.get_port_count()

    if in_count == 0 or out_count == 0:
        print(f"❌ No available MIDI ports to open. Inputs: {in_count}, Outputs: {out_count}.")
        return

    # Validate indices explicitly
    if input_index < 0 or input_index >= in_count:
        print(f"❌ Input port index {input_index} is out of range (valid: 0..{in_count-1}).")
        print("   Available ports:")
        list_ports()
        return
    if output_index < 0 or output_index >= out_count:
        print(f"❌ Output port index {output_index} is out of range (valid: 0..{out_count-1}).")
        print("   Available ports:")
        list_ports()
        return

    # Try opening the selected ports (using correct python-rtmidi API)
    try:
        midi_in.open_port(input_index)
    except Exception as e:
        try:
            in_name = midi_in.get_port_name(input_index)
        except Exception:
            in_name = f"index {input_index}"
        print(f"❌ Failed to open MIDI input port {input_index} ('{in_name}'): {type(e).__name__}: {e}")
        print("   This can happen if the device was disconnected, busy, or access is denied.")
        return

    try:
        midi_out.open_port(output_index)
    except Exception as e:
        try:
            out_name = midi_out.get_port_name(output_index)
        except Exception:
            out_name = f"index {output_index}"
        print(f"❌ Failed to open MIDI output port {output_index} ('{out_name}'): {type(e).__name__}: {e}")
        print("   This can happen if the device was disconnected, busy, or access is denied.")
        try:
            midi_in.close_port()
        except Exception:
            pass
        return

    # Do not ignore any message types so routing is complete
    try:
        midi_in.ignore_types(sysex=False, timing=False, sensing=False)
    except Exception:
        # Not critical; continue even if backend doesn't support this call
        pass

    print(f"🔁 Routing input port '{midi_in.get_port_name(input_index)}' to output port '{midi_out.get_port_name(output_index)}'")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            msg = midi_in.get_message()
            if msg:
                message, delta_time = msg  # message is a list[ints], delta_time is float
                try:
                    midi_out.send_message(message)
                except Exception as e:
                    print(f"\n❌ Send error while routing: {type(e).__name__}: {e}")
                    break
            else:
                # No message available right now; avoid busy-waiting
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\n❌ Unexpected error while routing: {type(e).__name__}: {e}")
    finally:
        try:
            midi_in.close_port()
        except Exception:
            pass
        try:
            midi_out.close_port()
        except Exception:
            pass


if __name__ == "__main__":
    main()
