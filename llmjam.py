"""
llmjam: Main entry point for the LLM jam session app.
"""

from pitch_to_midi import StreamingPitchToMidi
from audio_input import capture_audio_blocks_on_sound_then_until_silence
import llm_client
import midi_output
import time
import threading
import sys
import termios
import tty

stop_flag = False
playing_style = "mellow"


def listen_for_s_and_phrase():
    global playing_style
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        while True:
            tty.setcbreak(fd)
            ch = sys.stdin.read(1)
            if ch == 's':
                print("\n's' pressed. Enter a short phrase for playing style:")
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                phrase = input("Describe your playing style: ")
                playing_style = phrase
                print(f"Playing style set to: {playing_style}")
                # No need to re-enable cbreak here; the loop will do it
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main():
    global playing_style

    """Main event loop for llmjam."""
    print("Welcome to llmjam!")
    user_in = input("\nPress Enter to start jamming, or 'q' to quit: ")
    if user_in.strip().lower() == 'q':
        print("Goodbye!")
        exit()

    print("To stop jamming, press Cmd+C/Ctrl+c")

    # Start background thread to listen for 's' and get playing style
    listener_thread = threading.Thread(
        target=listen_for_s_and_phrase, daemon=True
    )
    listener_thread.start()

    block_samplerate = 44100
    blocksize = 4096  # 2048 samples is ~46ms at 44100Hz, adjust as needed
    block_duration = blocksize / block_samplerate

    while True:
        if stop_flag:
            print("Exiting jam session.")
            break

        # 1. Capture audio
        print(
            "Waiting for sound to start, then recording until 1s of silence..."
        )
        streaming_midi = StreamingPitchToMidi(samplerate=block_samplerate)
        block_start_time = 0.0

        for block in capture_audio_blocks_on_sound_then_until_silence(
            samplerate=block_samplerate,
            blocksize=blocksize
        ):
            # Process to MIDI while capturing
            streaming_midi.process_block(block, block_start_time)
            block_start_time += block_duration

        midi_input = streaming_midi.get_midi_events()
        print(f"Detected MIDI notes: {midi_input}")
        if not midi_input:
            print("No notes detected. Try again.")
            continue

        # 3. Send MIDI to LLM and get response
        print("Sending to LLM for response (streaming)...")
        midi_event_stream = llm_client.stream_llm_midi_response(
            midi_input,
            playing_style
        )
        print("Playing LLM response as it streams...")
        midi_output.play_midi_events_streaming(midi_event_stream)
        # Wait a bit before next round
        time.sleep(0.5)


if __name__ == "__main__":
    main()
