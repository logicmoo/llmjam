# Monitors all MIDI input ports and handles system errors gracefully
import rtmidi
import time
import threading

def print_message(midi, port_name):
    if midi.isNoteOn():
        print(f"[{port_name}] ON:  {midi.getMidiNoteName(midi.getNoteNumber())} Vel={midi.getVelocity()}")
    elif midi.isNoteOff():
        print(f"[{port_name}] OFF: {midi.getMidiNoteName(midi.getNoteNumber())}")
    elif midi.isController():
        print(f"[{port_name}] CONTROLLER: {midi.getControllerNumber()} -> {midi.getControllerValue()}")
    else:
        print(f"[{port_name}] OTHER: {midi}")

def monitor_port(index, port_name):
    try:
        print(f"rtmidi.MidiIn: ATTEMPT OPEN PORT {index}: {port_name}")
        midiin = rtmidi.RtMidiIn()
        midiin.openPort(index)
        print(f"SUCCESS OPENING PORT {index}: {port_name}")
    except rtmidi.Error as e:
        print(f"FAILED TO OPEN PORT {index}: {port_name} — {e}")
        return

    print(f"Listening on port {index}: {port_name}")
    while True:
        msg = midiin.getMessage(10)
        if msg:
            print_message(msg, port_name)

def main():
    probe = rtmidi.RtMidiIn()
    port_count = probe.getPortCount()

    if port_count == 0:
        print("❌ NO MIDI INPUT PORTS FOUND.")
        return

    print(f"✅ Found {port_count} MIDI input ports:\n")
    port_names = []
    for i in range(port_count):
        name = probe.getPortName(i)
        port_names.append(name)
        print(f"  [{i}] {name}")

    print("\n🚀 Starting MIDI listeners...\n")
    opened_names = set()
    for i in range(port_count):
        name = port_names[i]
        if name in opened_names:
            print(f"⚠️  SKIPPING DUPLICATE PORT NAME: {name}")
            continue
        opened_names.add(name)
        thread = threading.Thread(target=monitor_port, args=(i, name), daemon=True)
        thread.start()

    print("\n🟢 Monitoring started. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")

if __name__ == "__main__":
    main()
