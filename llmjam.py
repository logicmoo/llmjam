"""
llmjam: Main entry point for the LLM jam session app.
"""

import audio_input
import pitch_to_midi
import llm_client
import midi_output
import time


def main():
    """Main event loop for llmjam."""
    print("Welcome to llmjam!")
    user_in = input("\nPress Enter to start jamming, or 'q' to quit: ")
    if user_in.strip().lower() == 'q':
        print("Goodbye!")
        exit()

    print("To stop jamming, press Ctrl+C/Cmd+C")

    while True:
        # 1. Capture audio
        print(
            "Waiting for sound to start, then recording until 1s of silence..."
        )
        audio = audio_input.capture_on_sound_then_until_silence(
            samplerate=44100
        )

        # 2. Convert audio to MIDI
        midi_input = pitch_to_midi.audio_to_midi(
            audio,
            samplerate=44100
        )
        print(f"Detected MIDI notes: {midi_input}")
        if not midi_input:
            print("No notes detected. Try again.")
            continue

        # 3. Send MIDI to LLM and get response
        print("Sending to LLM for response...")
        midi_response = llm_client.get_llm_midi_response(midi_input)
        print(f"LLM MIDI response: {midi_response}")
        if not midi_response:
            print("LLM did not return any notes. Try again.")
            continue

        # 4. Play LLM MIDI response (ignore audio input during playback)
        print("Playing LLM response...")
        # Start playback
        midi_output.send_midi_sequence(midi_response)
        # Wait a bit before next round
        time.sleep(0.5)


if __name__ == "__main__":
    main()
