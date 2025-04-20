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
    # Normalize start times so the first event starts at 0
    if events:
        base_time = events[0]['start_time']
        for event in events:
            event['start_time'] -= base_time
    start_time = time.time()
    for event in events:
        now = time.time()
        wait_time = event['start_time'] - (now - start_time)
        if wait_time > 0:
            print(
                f"[midi_output] Waiting {wait_time:.3f}s before next note..."
            )
            time.sleep(wait_time)
        notes = event['note']
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        # Support both single note and list of notes (for chords)
        if not isinstance(notes, list):
            notes = [notes]
        print(
            f"[midi_output] Note ON: notes={notes}, velocity={velocity},"
        )
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


def play_midi_events_streaming(event_iter, channel=0):
    """
    Play MIDI events as they are yielded from an iterator/generator, in real-time.
    The first event sets time zero; all subsequent events are scheduled relative to it.
    Args:
        event_iter: Iterator/generator yielding MIDI event dicts.
        channel (int): MIDI channel (default 0).
    """
    print("[midi_output] Streaming MIDI playback started.")
    zero_time = None
    for event in event_iter:
        if zero_time is None:
            zero_time = time.time() - event.get('start_time', 0)
        now = time.time()
        event_time = zero_time + event.get('start_time', 0)
        wait_time = event_time - now
        if wait_time > 0:
            print(
                f"[midi_output] Waiting {wait_time:.3f}s before next note..."
            )
            time.sleep(wait_time)
        notes = event['note']
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        if not isinstance(notes, list):
            notes = [notes]
        print(
            f"[midi_output] Note ON: notes={notes}, velocity={velocity}, "
            f"duration={duration}"
        )
        status_on = 0x90 | channel
        for note in notes:
            midiout.send_message([status_on, note, velocity])
        time.sleep(duration)
        status_off = 0x80 | channel
        print(
            f"[midi_output] Note OFF: notes={notes}"
        )
        for note in notes:
            midiout.send_message([status_off, note, 0])
    print("[midi_output] Streaming MIDI playback finished.")
