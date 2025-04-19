"""
llm_client.py: Communicate with OpenAI/OpenRouter to generate MIDI responses.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

llm = OpenAI(api_key=api_key)


system_prompt = """
    You are a creative musician. Given a melody as a list of MIDI note events, respond with a new
    melody as a compact CSV list of note events.
    Each event is a line: notes,velocity,start_time,duration.
    notes can be a single MIDI note (0-127) or multiple notes separated by '|' for chords
    (e.g., 60|64|67).
    velocity (0-127), start_time (seconds), duration (seconds).
    Only output the CSV, no extra text.
    Example (C major chord, then E):\n60|64|67,100,0.0,0.5\n64,90,0.5,0.5

    <style>mellow</style>
    <activity>Call and response between two musicians</activity>
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


def get_llm_midi_response(midi_input, model="gpt-4.1"):
    """
    Send MIDI input to the LLM and return a generated MIDI response as a list
    of note events (supporting chords).
    Args:
        midi_input (list): List of input MIDI note events (dicts).
        model (str): OpenAI model name.
    Returns:
        list: List of output MIDI note events (dicts).
    """
    print(f"[llm_client] Called get_llm_midi_response with midi_input: "
          f"{midi_input}")
    user_message = (
        "Input melody (as CSV):\n" + midi_events_to_csv(midi_input)
    )
    print(f"[llm_client] Sending to LLM, model={model}")

    llm_params = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }

    response = llm.chat.completions.create(
        **llm_params
    )
    # Extract the CSV from the response
    content = response.choices[0].message.content
    preview = content[:200] + ('...' if len(content) > 200 else '')
    print(f"[llm_client] LLM response content: {preview}")
    try:
        midi_events = csv_to_midi_events(content)
    except Exception as e:
        print(f"[llm_client] Error parsing LLM response: {e}")
        raise ValueError("Could not parse LLM MIDI response: " + content)
    print(f"[llm_client] Parsed midi_events: {midi_events}")
    return midi_events
