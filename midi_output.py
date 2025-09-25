
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
    SND_BASS_DRUM = pygame.mixer.Sound("sounds/kick.wav")
    SND_SNARE_DRUM = pygame.mixer.Sound("sounds/snare.wav")
    SND_CLOSED_HI_HAT = pygame.mixer.Sound("sounds/hi-hat.wav")
except pygame.error as e:
    print(f"Error loading sound files: {e}")
    print("Please ensure you have 'kick.wav', 'snare.wav', and 'hi-hat.wav' in a 'sounds' directory.")
    exit()

# --- Global state ---
jam_running = threading.Event()
jam_start_time = 0.0
midiout = None

def setup_output_midi(create=False):
    """Initialize MIDI output port. If create=True, use virtual port."""
    global midiout
    midiout = rtmidi.MidiOut()
    if create:
        port_name = "llmjam MIDI Out"
        try:
            midiout.open_virtual_port(port_name)
            print(f"Opened virtual MIDI port: {port_name}")
        except rtmidi.RtMidiError as e:
            print(f"Error opening virtual MIDI port: {e}")
            print("? No MIDI output ports available.")
            select_existing_ports()
    else:
        select_existing_ports()

def select_existing_ports():
    global midiout
    ports = midiout.get_ports()
    if not ports:
        print("❌ No MIDI output ports available.")
        exit()
    print("\nAvailable MIDI Output Ports:")
    for i, name in enumerate(ports):
        print(f"  [{i}] {name}")
    try:
        selection = int(input("Enter the number of the port to use: "))
        midiout.open_port(selection)
        print(f"Opened MIDI output port: {ports[selection]}")
    except (ValueError, IndexError):
        print("Invalid selection.")
        exit()

def drum_beat_loop():
    """The main loop for the drum machine, runs in a separate thread."""
    eighth_note_count = 0
    while jam_running.is_set():
        next_event_time = jam_start_time + (eighth_note_count * EIGHTH_NOTE_DURATION)
        now = time.time()
        sleep_time = next_event_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)
        SND_CLOSED_HI_HAT.play()
        if eighth_note_count % 2 == 0:
            beat_in_bar = (eighth_note_count // 2) % BEATS_PER_BAR
            if beat_in_bar == 0:
                SND_BASS_DRUM.play()
            elif beat_in_bar == 1:
                SND_SNARE_DRUM.play()
            elif beat_in_bar == 2:
                SND_BASS_DRUM.play()
            elif beat_in_bar == 3:
                SND_SNARE_DRUM.play()
        eighth_note_count += 1

def start_jam():
    global jam_start_time
    if not jam_running.is_set():
        jam_start_time = time.time()
        jam_running.set()
        drum_thread = threading.Thread(target=drum_beat_loop)
        drum_thread.daemon = True
        drum_thread.start()
        print("Drum machine started.")

def stop_jam():
    jam_running.clear()
    pygame.mixer.quit()
    print("Drum machine stopped.")

def send_midi_sequence(midi_events, channel=0):
    if not jam_running.is_set():
        print("Jam not started. Call start_jam() first.")
        _play_unsynced(midi_events, channel)
        return
    print("[midi_output] Called send_midi_sequence")
    time_since_start = time.time() - jam_start_time
    current_bar = int(time_since_start / BAR_DURATION)
    next_bar_time = jam_start_time + (current_bar + 1) * BAR_DURATION
    play_time = next_bar_time + (2 * BAR_DURATION)
    wait_for = play_time - time.time()
    print(f"Waiting {wait_for:.2f} seconds to sync to next phrase...")
    if wait_for > 0:
        time.sleep(wait_for)
    events = sorted(midi_events, key=lambda e: e['start_time'])
    if events:
        base_time = events[0]['start_time']
        for event in events:
            event['start_time'] -= base_time
    sequence_start_time = time.time()
    for event in events:
        now = time.time()
        wait_time = event['start_time'] - (now - sequence_start_time)
        if wait_time > 0:
            time.sleep(wait_time)
        notes = event['note']
        if not isinstance(notes, list):
            notes = [notes]
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        for note in notes:
            midiout.send_message([0x90 | channel, note, velocity])
        time.sleep(duration)
        for note in notes:
            midiout.send_message([0x80 | channel, note, 0])

def _play_unsynced(midi_events, channel=0):
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
        if not isinstance(notes, list):
            notes = [notes]
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        for note in notes:
            midiout.send_message([0x90 | channel, note, velocity])
        time.sleep(duration)
        for note in notes:
            midiout.send_message([0x80 | channel, note, 0])

def play_midi_events_streaming(event_iter, channel=0):
    print("[midi_output] Streaming MIDI playback started.")
    zero_time = None
    first_event_processed = False
    for event in event_iter:
        if not first_event_processed:
            if jam_running.is_set():
                time_since_start = time.time() - jam_start_time
                current_bar = int(time_since_start / BAR_DURATION)
                play_time = jam_start_time + (current_bar + 1) * BAR_DURATION
                wait_for = play_time - time.time()
                if wait_for > 0:
                    time.sleep(wait_for)
            zero_time = time.time() - event.get('start_time', 0)
            first_event_processed = True
        now = time.time()
        event_time = zero_time + event.get('start_time', 0)
        wait_time = event_time - now
        if wait_time > 0:
            time.sleep(wait_time)
        notes = event['note']
        if not isinstance(notes, list):
            notes = [notes]
        velocity = event.get('velocity', 100)
        duration = event.get('duration', 0.5)
        for note in notes:
            midiout.send_message([0x90 | channel, note, velocity])
        time.sleep(duration)
        for note in notes:
            midiout.send_message([0x80 | channel, note, 0])
    print("[midi_output] Streaming MIDI playback finished.")

def update_bpm(new_bpm):
    global BPM, BEAT_DURATION, EIGHTH_NOTE_DURATION, BAR_DURATION
    BPM = float(new_bpm)
    BEAT_DURATION = 60.0 / BPM
    EIGHTH_NOTE_DURATION = BEAT_DURATION / 2
    BAR_DURATION = BEAT_DURATION * BEATS_PER_BAR
    print(f"BPM updated to: {BPM}")
