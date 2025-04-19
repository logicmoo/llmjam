"""
midi_output.py: Send MIDI to a virtual MIDI device.
"""

import rtmidi
import time


# Create a virtual MIDI port (singleton)
midiout = rtmidi.MidiOut()

# Create a virtual MIDI port
port_name = "llmjam MIDI Out"
try:
    midiout.open_virtual_port(port_name)
    print(f"Opened virtual MIDI port: {port_name}")
except rtmidi.RtMidiError as e:
    print(f"Error opening virtual MIDI port: {e}")
    # Handle error appropriately, maybe exit or fallback
    exit()


def send_midi_sequence(midi_events, channel=0):
    """
    Send a sequence of MIDI events to the virtual MIDI device.
    Args:
        midi_events (list): List of dicts with 'note', 'velocity', 'start_time',
        'duration'.
        channel (int): MIDI channel (default 0).
    """
    print("[midi_output] Called send_midi_sequence with ")
    print(len(midi_events))
    print("events,")
    print(f"channel={channel}")
    # Sort events by start_time
    events = sorted(midi_events, key=lambda e: e['start_time'])
    start_time = time.time()
    first = True
    for event in events:
        now = time.time()
        wait_time = event['start_time'] - (now - start_time)
        if wait_time > 0 and not first:
            print(f"[midi_output] Waiting {wait_time:.3f}s before next note...")
            time.sleep(wait_time)
        else:
            first = False
        notes = event['note']
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        # Support both single note and list of notes (for chords)
        if not isinstance(notes, list):
            notes = [notes]
        print(f"[midi_output] Note ON: notes={notes}, velocity={velocity},")
        print(f"duration={duration}")
        # Send Note On for all notes in the chord
        status_on = 0x90 | channel
        for note in notes:
            midiout.send_message([status_on, note, velocity])
        # Schedule Note Off for all notes
        time.sleep(duration)
        status_off = 0x80 | channel
        print("[midi_output] Note OFF: notes=")
        for n in notes:
            print(n)
        for note in notes:
            midiout.send_message([status_off, note, 0])
