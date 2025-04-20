"""
audio_input.py: Capture audio from the default output device.
"""

import sounddevice as sd
import numpy as np


def capture_audio(duration=2.0, samplerate=16000):
    """
    Capture audio from the default output device.
    Args:
        duration (float): Duration to record in seconds.
        samplerate (int): Sample rate in Hz (default 16000).
    Returns:
        np.ndarray: Recorded audio data (mono, float32).
    """
    print(
        f"Recording {duration}s of audio at {samplerate}Hz..."
    )
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    return audio.flatten()


def capture_on_sound_then_until_silence(
    samplerate=16000,
    threshold=0.01,
    silence_duration=1.0,
    blocksize=1024,
    max_record=30.0
):
    """
    Wait for audio above a threshold, start recording, and stop after
    'silence_duration' seconds of continuous silence.
    Args:
        samplerate (int): Audio sample rate (default 16000).
        threshold (float): RMS threshold to detect sound start.
        silence_duration (float): Seconds of silence to stop recording.
        blocksize (int): Block size for monitoring.
        max_record (float): Max seconds to record (safety).
    Returns:
        np.ndarray: Recorded audio data (mono, float32).
    """
    print("Waiting for sound to start...")
    recorded = []
    recording = False
    silence_blocks = 0
    silence_blocks_needed = int(silence_duration * samplerate / blocksize)
    max_blocks = int(max_record * samplerate / blocksize)
    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        blocksize=blocksize,
        dtype='float32'
    ) as stream:
        for block_idx in range(max_blocks):
            block, _ = stream.read(blocksize)
            rms = np.sqrt(np.mean(block**2))
            if not recording:
                if rms > threshold:
                    print("Sound detected, recording...")
                    recording = True
                    recorded.append(block)
                    silence_blocks = 0
            else:
                recorded.append(block)
                if rms < threshold:
                    silence_blocks += 1
                    if silence_blocks >= silence_blocks_needed:
                        print(
                            f"Detected {silence_duration}s of silence, "
                            f"stopping."
                        )
                        break
                else:
                    silence_blocks = 0
    if not recorded:
        print("No sound detected.")
        return np.array([], dtype='float32')
    return np.concatenate(recorded).flatten()


def capture_audio_blocks_on_sound_then_until_silence(
    samplerate=16000,
    threshold=0.01,
    silence_duration=0.5,
    blocksize=1024,
    max_record=30.0
):
    """
    Generator version: Wait for audio above a threshold, then yield each audio block
    as it is recorded, until 'silence_duration' seconds of continuous silence.
    Args:
        samplerate (int): Audio sample rate (default 16000).
        threshold (float): RMS threshold to detect sound start.
        silence_duration (float): Seconds of silence to stop recording.
        blocksize (int): Block size for monitoring.
        max_record (float): Max seconds to record (safety).
    Yields:
        np.ndarray: Audio block (mono, float32) as soon as it is recorded.
    """
    print("Waiting for sound to start...")
    recording = False
    silence_blocks = 0
    silence_blocks_needed = int(silence_duration * samplerate / blocksize)
    max_blocks = int(max_record * samplerate / blocksize)
    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        blocksize=blocksize,
        dtype='float32'
    ) as stream:
        for block_idx in range(max_blocks):
            block, _ = stream.read(blocksize)
            rms = np.sqrt(np.mean(block**2))
            if not recording:
                if rms > threshold:
                    print("Sound detected, recording...")
                    recording = True
                    silence_blocks = 0
                    yield block.flatten()
            else:
                yield block.flatten()
                if rms < threshold:
                    silence_blocks += 1
                    if silence_blocks >= silence_blocks_needed:
                        print(
                            f"Detected {silence_duration}s of silence, "
                            f"stopping."
                        )
                        break
                else:
                    silence_blocks = 0
