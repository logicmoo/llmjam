# llmjam

A real-time AI-powered musical jam session tool. Capture your melody via microphone, convert it to MIDI, send it to a Large Language Model (LLM) for creative response, and play back the AI's musical reply through a virtual MIDI device.

## Features
- **Audio-to-MIDI**: Converts your live audio input into MIDI notes using pitch detection (CREPE).
- **LLM Musician**: Sends your melody to a Large Language Model (LLM) (e.g., OpenAI GPT-4 or any model via OpenRouter) which responds with a new, creative MIDI sequence.
- **Virtual MIDI Output**: Plays the AI's response through a virtual MIDI port, usable with any DAW or synth.
- **Call-and-response**: Designed for interactive, improvisational music sessions.

## Installation

### Requirements
- Python 3.11
- macOS (tested; may work on Linux/Windows with adjustments)
- [PortAudio](http://www.portaudio.com/) (for `sounddevice`)
- [RtMidi](https://www.music.mcgill.ca/~gary/rtmidi/) (for `python-rtmidi`)
- [TensorFlow-macos](https://developer.apple.com/metal/tensorflow-plugin/) and [TensorFlow-metal](https://developer.apple.com/metal/tensorflow-plugin/) (for fast pitch detection)

### Python Dependencies
All dependencies are listed in `pyproject.toml`:
- sounddevice
- crepe
- openai
- requests
- python-rtmidi
- python-dotenv
- tensorflow-macos
- tensorflow-metal

Install with:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or use a tool like uv or pip-tools
```

## Setup
1. **API Keys**: Create a `.env` file in the project root with your API key. You can use either OpenAI or OpenRouter:
   ```
   # For OpenAI (default)
   OPENAI_API_KEY=sk-...
   # Or for OpenRouter (uses https://openrouter.ai, supports many models)
   OPENROUTER_API_KEY=...  # If set, OpenRouter will be used instead of OpenAI
   ```
   If both are set, OpenRouter will be used.
2. **Audio/MIDI Devices**: Ensure your system has a working microphone and a DAW or synth that can receive MIDI from a virtual port.

## Usage
Run the main app:
```bash
python llmjam.py
```

- Press Enter to start jamming.
- Play or sing a melody. Recording starts on sound and stops after 1s of silence.
- The melody is converted to MIDI, sent to the LLM, and the AI's response is played back as MIDI.
- To stop, press `Ctrl+C` or `Cmd+C`.

## How it Works
1. **Audio Capture**: Listens for sound, records until silence.
2. **Pitch Detection**: Uses CREPE (TensorFlow) to convert audio to MIDI notes.
3. **LLM Response**: Sends MIDI to an LLM (e.g., GPT-4 or any OpenRouter-supported model) with a musician prompt; receives a new melody as CSV.
4. **MIDI Playback**: Plays the AI's response through a virtual MIDI port.

## Troubleshooting
- **No sound detected**: Check your microphone and input device settings.
- **No MIDI output**: Ensure your DAW/synth is listening to the "llmjam MIDI Out" port.
- **API errors**: Check your `.env` file and API key validity.
- **TensorFlow/CREPE errors**: Ensure you have the correct versions for your platform (see TensorFlow-macos/metal docs).

## License
MIT

## Credits
- [CREPE](https://github.com/marl/crepe) for pitch detection
- [OpenAI](https://openai.com/) for LLM API
- [OpenRouter](https://openrouter.ai/) for multi-provider LLM API
- [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi) for MIDI output
