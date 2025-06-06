"""
midi_output.py: Send MIDI to a virtual MIDI device.
"""

import rtmidi
import time
import threading
import pygame


# --- Metronome and Clock ---
BPM = 95.0
BEATS_PER_BAR = 4
BEAT_DURATION = 60.0 / BPM
EIGHTH_NOTE_DURATION = BEAT_DURATION / 2
BAR_DURATION = BEAT_DURATION * BEATS_PER_BAR

# --- Audio setup for drums ---
pygame.mixer.init()
try:
    # NOTE: You need to provide these audio files.
    # Replace with the actual paths to your drum samples.
    SND_BASS_DRUM = pygame.mixer.Sound("sounds/kick.wav")
    SND_SNARE_DRUM = pygame.mixer.Sound("sounds/snare.wav")
    SND_CLOSED_HI_HAT = pygame.mixer.Sound("sounds/hi-hat.wav")
except pygame.error as e:
    print(f"Error loading sound files: {e}")
    print("Please ensure you have 'kick.wav', 'snare.wav', and 'hi-hat.wav' "
          "in a 'sounds' directory.")
    exit()

# --- Global state ---
jam_running = threading.Event()
jam_start_time = 0.0


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


def drum_beat_loop():
    """The main loop for the drum machine, runs in a separate thread."""
    eighth_note_count = 0
    while jam_running.is_set():
        # Calculate the precise time of the next eighth note
        next_event_time = jam_start_time + \
            (eighth_note_count * EIGHTH_NOTE_DURATION)
        now = time.time()
        sleep_time = next_event_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Play hi-hat on every 8th note
        SND_CLOSED_HI_HAT.play()

        # Play kick and snare on the downbeats (quarter notes)
        if eighth_note_count % 2 == 0:
            beat_in_bar = (eighth_note_count // 2) % BEATS_PER_BAR
            if beat_in_bar == 0:  # Beat 1: Bass drum
                SND_BASS_DRUM.play()
            elif beat_in_bar == 1:  # Beat 2: Snare
                SND_SNARE_DRUM.play()
            elif beat_in_bar == 2:  # Beat 3: Bass drum
                SND_BASS_DRUM.play()
            elif beat_in_bar == 3:  # Beat 4: Snare
                SND_SNARE_DRUM.play()

        eighth_note_count += 1


def start_jam():
    """Starts the drum machine in a background thread."""
    global jam_start_time
    if not jam_running.is_set():
        jam_start_time = time.time()
        jam_running.set()
        drum_thread = threading.Thread(target=drum_beat_loop)
        drum_thread.daemon = True
        drum_thread.start()
        print("Drum machine started.")


def stop_jam():
    """Stops the drum machine."""
    jam_running.clear()
    pygame.mixer.quit()
    print("Drum machine stopped.")


def send_midi_sequence(midi_events, channel=0):
    """
    Send a sequence of MIDI events to the virtual MIDI device, synced to the
    beat.
    The sequence is scheduled to start after a 2-bar wait.
    Args:
        midi_events (list): List of dicts with 'note', 'velocity',
        'start_time', 'duration'.
        channel (int): MIDI channel (default 0).
    """
    if not jam_running.is_set():
        print("Jam not started. Call start_jam() first.")
        # For standalone testing, we can play without syncing
        # Let's keep original behaviour if jam is not running
        _play_unsynced(midi_events, channel)
        return

    print("[midi_output] Called send_midi_sequence with ")
    print(len(midi_events))
    print("events,")
    print(f"channel={channel}")

    # --- Syncing logic ---
    time_since_start = time.time() - jam_start_time
    current_bar = int(time_since_start / BAR_DURATION)
    # Wait for the next bar to start, then wait 2 more bars
    next_bar_time = jam_start_time + (current_bar + 1) * BAR_DURATION
    play_time = next_bar_time + (2 * BAR_DURATION)

    wait_for = play_time - time.time()
    print(f"Waiting for {wait_for:.2f} seconds to sync with the beat "
          f"(2 bars).")
    if wait_for > 0:
        time.sleep(wait_for)

    # Sort events by start_time
    events = sorted(midi_events, key=lambda e: e['start_time'])
    # Normalize start times so the first event starts at 0
    if events:
        base_time = events[0]['start_time']
        for event in events:
            event['start_time'] -= base_time

    sequence_start_time = time.time()
    for event in events:
        now = time.time()
        wait_time = event['start_time'] - (now - sequence_start_time)
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


def _play_unsynced(midi_events, channel=0):
    """Original playback logic for when jam is not running."""
    # This is basically the old send_midi_sequence
    print("[midi_output] Playing unsynced sequence.")
    start_time = time.time()
    events = sorted(midi_events, key=lambda e: e['start_time'])
    if events:
        base_time = events[0]['start_time']
        for event in events:
            event['start_time'] -= base_time

    for event in events:
        now = time.time()
        wait_time = event['start_time'] - (now - start_time)
        if wait_time > 0:
            time.sleep(wait_time)
        notes = event['note']
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        if not isinstance(notes, list):
            notes = [notes]
        status_on = 0x90 | channel
        for note in notes:
            midiout.send_message([status_on, note, velocity])
        time.sleep(duration)
        status_off = 0x80 | channel
        for note in notes:
            midiout.send_message([status_off, note, 0])


def play_midi_events_streaming(event_iter, channel=0):
    """
    Play MIDI events from a stream, synced to the beat.
    The LLM call is made immediately, and this function syncs the
    start of the playback to the beginning of the next musical bar.
    Args:
        event_iter: Iterator/generator yielding MIDI event dicts.
        channel (int): MIDI channel (default 0).
    """
    print("[midi_output] Streaming MIDI playback started.")
    zero_time = None
    first_event_processed = False

    for event in event_iter:
        if not first_event_processed:
            if jam_running.is_set():
                # Sync to the start of the next bar
                time_since_start = time.time() - jam_start_time
                current_bar = int(time_since_start / BAR_DURATION)
                play_time = jam_start_time + (current_bar + 1) * BAR_DURATION
                wait_for = play_time - time.time()
                if wait_for > 0:
                    print(
                        f"Waiting for {wait_for:.2f}s to sync with the "
                        "start of the next bar."
                    )
                    time.sleep(wait_for)

            # Set the clock for the rest of the streaming events
            zero_time = time.time() - event.get('start_time', 0)
            first_event_processed = True

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


def update_bpm(new_bpm):
    """Updates the global BPM and recalculates timing variables."""
    global BPM, BEAT_DURATION, EIGHTH_NOTE_DURATION, BAR_DURATION
    BPM = float(new_bpm)
    BEAT_DURATION = 60.0 / BPM
    EIGHTH_NOTE_DURATION = BEAT_DURATION / 2
    BAR_DURATION = BEAT_DURATION * BEATS_PER_BAR
    print(f"BPM updated to: {BPM}")
