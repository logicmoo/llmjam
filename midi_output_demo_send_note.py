# Demonstrates sending MIDI output (note on/off)
import rtmidi
import time

midiout = rtmidi.RtMidiOut()
available_ports = midiout.getPortCount()

# Open the first available output port
if available_ports:
    midiout.openPort(0)
else:
    midiout.openVirtualPort("My Output")

# Send a middle C note on (channel 1)
note_on = [0x90, 60, 112]  # 0x90 = note_on on channel 1, 60 = middle C, 112 = velocity
note_off = [0x80, 60, 0]   # 0x80 = note_off

midiout.sendMessage(note_on)
time.sleep(0.5)
midiout.sendMessage(note_off)
