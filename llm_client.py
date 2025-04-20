"""
llm_client.py: Communicate with OpenAI/OpenRouter to generate MIDI responses.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Support both OpenAI and OpenRouter (OpenAI-compatible) endpoints
openai_api_key = os.getenv("OPENAI_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if openrouter_api_key:
    # Use OpenRouter endpoint if key is present
    llm = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    model = "anthropic/claude-3.7-sonnet:thinking"
    print("[llm_client] Using OpenRouter API")
else:
    llm = OpenAI(api_key=openai_api_key)
    model = "gpt-4.1"
    print("[llm_client] Using OpenAI API")


system_prompt = """
    <playing_style_or_character>{playing_style}</playing_style_or_character>
    <activity>Call and response between two musicians</activity>
    <velocity>humanize</velocity>

    <answer_format>
    A compact CSV list of note events.
    Each event is a line: notes,velocity,start_time,duration.
    notes can be a single MIDI note (0-127) or multiple notes separated by '|' for chords
    (e.g., 60|64|67).
    velocity (0-127), start_time (seconds), duration (seconds).
    Only output the CSV, no extra text.
    Example (C major chord, then E):\n60|64|67,100,0.0,0.5\n64,90,0.5,0.5
    </answer_format>

    Given a melody as a list of MIDI note events, respond with a new melody.
    MOST IMPORTANT THING: Follow the given playing style/character.
"""


def midi_events_to_csv(midi_events):
    """
    Convert a list of MIDI events (dicts) to a compact CSV-like string.
    Each event: notes,velocity,start_time,duration
    notes: single note or pipe-separated notes for chords (e.g., 60|64|67)
    """
    lines = []
    for event in midi_events:
        notes = event['note']
        if isinstance(notes, list):
            notes_str = '|'.join(str(n) for n in notes)
        else:
            notes_str = str(notes)
        velocity = event.get('velocity', 100)
        start_time = event.get('start_time', 0)
        duration = event.get('duration', 0.5)
        lines.append(f"{notes_str},{velocity},{start_time},{duration}")
    return '\n'.join(lines)


def csv_to_midi_events(csv_str):
    """
    Parse a CSV-like string of MIDI events into a list of dicts.
    Each line: notes,velocity,start_time,duration
    notes: single note or pipe-separated notes for chords
    """
    events = []
    for line in csv_str.strip().splitlines():
        parts = line.strip().split(',')
        if len(parts) != 4:
            continue
        notes_part, velocity, start_time, duration = parts
        if '|' in notes_part:
            notes = [int(n) for n in notes_part.split('|')]
        else:
            notes = int(notes_part)
        events.append({
            'note': notes,
            'velocity': int(velocity),
            'start_time': float(start_time),
            'duration': float(duration)
        })
    return events


def stream_llm_midi_response(midi_input, playing_style="mellow"):
    """
    Stream LLM response and yield MIDI events as soon as each line is complete.
    Args:
        midi_input (list): List of input MIDI note events (dicts).
        playing_style (str, optional): User-provided playing style phrase.
    Yields:
        dict: Parsed MIDI event dicts as soon as each line is available.
    """
    print(
        f"[llm_client] Called stream_llm_midi_response with midi_input: {midi_input}"
    )
    user_message = (
        "Input melody (as CSV):\n" + midi_events_to_csv(midi_input)
    )
    print(
        f"[llm_client] Streaming to LLM, model={model}"
    )

    sys_prompt = system_prompt.format(playing_style=playing_style)

    print(sys_prompt)

    llm_params = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 512,
        "temperature": 0.75,
        "stream": True
    }

    buffer = ""
    # OpenAI Python SDK v1 streaming
    response = llm.chat.completions.create(**llm_params)
    for chunk in response:
        delta = chunk.choices[0].delta.content \
            if hasattr(chunk.choices[0].delta, 'content') else None
        if not delta:
            continue
        buffer += delta
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            line = line.strip()
            if not line:
                continue
            try:
                # Try to parse the line as a MIDI event
                events = csv_to_midi_events(line)
                if events:
                    yield events[0]  # Only one event per line
            except Exception as e:
                print(
                    f"[llm_client] Error parsing streamed MIDI event: {e}, "
                    f"line: {line}"
                )
                continue
