"""
pitch_to_midi.py: Convert audio to MIDI notes using pitch detection (crepe).
"""

import crepe
import numpy as np
import tensorflow as tf

print(tf.config.list_physical_devices('GPU'))


def audio_to_midi(audio_data, samplerate=44100, threshold=0.3, min_note_len=0.1):
    """
    Convert raw audio data to a list of MIDI note events using crepe pitch
    detection.
    Args:
        audio_data (np.ndarray): Mono audio data.
        samplerate (int): Audio sample rate (16000 or 44100 Hz).
        threshold (float): Confidence threshold for note detection.
        min_note_len (float): Minimum note duration in seconds.
    Returns:
        List[dict]: List of MIDI note events with 'note', 'start_time',
        'duration'.
    """
    print(f"[pitch_to_midi] Called audio_to_midi with audio_data.shape="
          f"{audio_data.shape}, samplerate={samplerate}")
    # crepe expects float32, 16kHz or 44.1kHz mono
    if samplerate not in (16000, 44100):
        print(f"[pitch_to_midi] Unsupported samplerate: {samplerate}")
        raise ValueError(
            "audio_to_midi only supports 16000 Hz or 44100 Hz audio"
        )
    # crepe expects shape (n,)
    audio_data = np.ascontiguousarray(audio_data, dtype=np.float32)
    print(f"[pitch_to_midi] Converted audio_data to float32, "
          f"shape={audio_data.shape}")
    # Predict pitches and confidence
    time_arr, freq_arr, conf_arr, _ = crepe.predict(
        audio_data, samplerate, viterbi=True, step_size=30
    )
    print(f"[pitch_to_midi] crepe.predict returned {len(time_arr)} frames")
    # Convert to MIDI notes
    midi_arr = 69 + 12 * np.log2(freq_arr / 440.0)
    # Detect note onsets and durations
    notes = []
    current_note = None
    current_onset = None
    for i, (midi, conf, t) in enumerate(zip(midi_arr, conf_arr, time_arr)):
        if conf >= threshold and 0 <= midi <= 127:
            if current_note is None:
                current_note = midi
                current_onset = t
            elif abs(midi - current_note) > 0.5:
                # New note
                duration = t - current_onset
                if duration >= min_note_len:
                    notes.append({
                        'note': int(round(current_note)),
                        'start_time': float(current_onset),
                        'duration': float(duration)
                    })
                current_note = midi
                current_onset = t
        else:
            if current_note is not None:
                duration = t - current_onset
                if duration >= min_note_len:
                    notes.append({
                        'note': int(round(current_note)),
                        'start_time': float(current_onset),
                        'duration': float(duration)
                    })
                current_note = None
                current_onset = None
    # Add last note if still active
    if current_note is not None and current_onset is not None:
        duration = time_arr[-1] - current_onset
        if duration >= min_note_len:
            notes.append({
                'note': int(round(current_note)),
                'start_time': float(current_onset),
                'duration': float(duration)
            })
    print(f"[pitch_to_midi] Returning {len(notes)} MIDI notes: {notes}")
    return notes
