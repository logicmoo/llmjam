
from pitch_to_midi import StreamingPitchToMidi
from audio_input import capture_audio_blocks_on_sound_then_until_silence
import llm_client
import midi_output
import time
import threading
import sys
import argparse
import platform

if platform.system() != "Windows":
    import termios
    import tty

stop_flag = False
playing_style = "mellow"


def listen_for_s_and_phrase():
    global playing_style
    if platform.system() == "Windows":
        import msvcrt
        print("Press 's' to change playing style (Windows)")
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode("utf-8").lower()
                if ch == "s":
                    phrase = input("Describe your playing style: ")
                    playing_style = phrase
                    print(f"Playing style set to: {playing_style}")
    else:
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
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

args = None

def main():
    global playing_style
    parser = argparse.ArgumentParser(description="llmjam: A musical jam session with an LLM.")
    parser.add_argument("--create", action="store_true", help="Create virtual MIDI ports instead of selecting existing ones.")
    parser.add_argument("--bpm", type=float, default=95.0, help="Set the beats per minute (BPM) for the jam session.")
    global args
    args = parser.parse_args()

    print("Welcome to llmjam!")
    print(f"Jamming at {args.bpm} BPM. To change playing style, press 's'.")

    midi_output.setup_output_midi(create=args.create)
    midi_output.update_bpm(args.bpm)

    user_in = input("\nPress Enter to start jamming, or 'q' to quit: ")
    if user_in.strip().lower() == 'q':
        print("Goodbye!")
        exit()

    midi_output.start_jam()
    print("To stop jamming, press Cmd+C/Ctrl+C")

    listener_thread = threading.Thread(target=listen_for_s_and_phrase, daemon=True)
    listener_thread.start()

    block_samplerate = 44100
    blocksize = 4096
    block_duration = blocksize / block_samplerate

    while True:
        if stop_flag:
            print("Exiting jam session.")
            break

        print("Waiting for sound to start, then recording until 1s of silence...")
        streaming_midi = StreamingPitchToMidi(samplerate=block_samplerate)
        block_start_time = 0.0

        for block in capture_audio_blocks_on_sound_then_until_silence(
            samplerate=block_samplerate,
            blocksize=blocksize
        ):
            streaming_midi.process_block(block, block_start_time)
            block_start_time += block_duration

        midi_input = streaming_midi.get_midi_events()
        print(f"Detected MIDI notes: {midi_input}")
        if not midi_input:
            print("No notes detected. Try again.")
            continue

        print("Sending to LLM for response (streaming)...")
        midi_event_stream = llm_client.stream_llm_midi_response(
            midi_input,
            playing_style,
            args.bpm
        )
        print("Playing LLM response as it streams...")
        midi_output.play_midi_events_streaming(midi_event_stream)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
