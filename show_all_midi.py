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
    midiin = rtmidi.RtMidiIn()
    midiin.openPort(index)
    print(f"Listening on port {index}: {port_name}")
    while True:
        msg = midiin.getMessage(10)  # 10ms timeout
        if msg:
            print_message(msg, port_name)

# Main setup
midiin_probe = rtmidi.RtMidiIn()
port_count = midiin_probe.getPortCount()

if port_count == 0:
    print("NO MIDI INPUT PORTS!")
else:
    print(f"Found {port_count} MIDI input ports:")
    for i in range(port_count):
        name = midiin_probe.getPortName(i)
        print(f"  [{i}] {name}")

    # Start threads to listen to all ports
    for i in range(port_count):
        name = midiin_probe.getPortName(i)
        thread = threading.Thread(target=monitor_port, args=(i, name), daemon=True)
        thread.start()

    print("\nPress Ctrl+C to stop monitoring.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
