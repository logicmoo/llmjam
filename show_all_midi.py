import rtmidi
import time
import threading

# Print MIDI message details
def print_message(midi, port_name):
    if midi.isNoteOn():
        print(f"[{port_name}] ON:  {midi.getMidiNoteName(midi.getNoteNumber())} Vel={midi.getVelocity()}")
    elif midi.isNoteOff():
        print(f"[{port_name}] OFF: {midi.getMidiNoteName(midi.getNoteNumber())}")
    elif midi.isController():
        print(f"[{port_name}] CONTROLLER: {midi.getControllerNumber()} -> {midi.getControllerValue()}")
    else:
        print(f"[{port_name}] OTHER: {midi}")

# Monitor a single port in its own thread
def monitor_port(index, port_name):
    midiin = rtmidi.MidiIn()
    try:
        midiin.open_port(index)
        print(f"Listening on port {index}: {port_name}")
        while True:
            try:
                msg = midiin.get_message()  # 10ms timeout
                if msg:
                    print_message(msg, port_name)
            except rtmidi.Error as e:
                print(f"RTMidi error on port {index}: {e}")
                break
            time.sleep(0.01)  # Avoid busy waiting
    except Exception as e:
        print(f"Error monitoring port {index}: {e}")
        return


# Main setup
midiin_probe = rtmidi.MidiIn()
port_count = midiin_probe.get_port_count()

if port_count == 0:
    print("NO MIDI INPUT PORTS!")
else:
    print(f"Found {port_count} MIDI input ports:")
    for i in range(port_count):
        name = midiin_probe.get_port_name(i)
        print(f"  [{i}] {name}")

    # Start threads to listen to all ports
    for i in range(port_count):
        name = midiin_probe.get_port_name(i)
        thread = threading.Thread(target=monitor_port, args=(i, name), daemon=True)
        thread.start()

    print("\nPress Ctrl+C to stop monitoring.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
