"""
llm_client.py: Communicate with OpenAI/OpenRouter to generate MIDI responses.
"""

import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

llm = OpenAI(api_key=api_key)


def get_llm_midi_response(midi_input, model="gpt-4.1-nano"):
    """
    Send MIDI input to the LLM and return a generated MIDI response as a list
    of note events.
    Args:
        midi_input (list): List of input MIDI note events (dicts).
        model (str): OpenAI model name.
    Returns:
        list: List of output MIDI note events (dicts).
    """
    print(f"[llm_client] Called get_llm_midi_response with midi_input: "
          f"{midi_input}")
    system_prompt = (
        "You are a creative AI musician. "
        "Given a melody as a list of MIDI note events, respond with a new "
        "melody as a JSON list of note events. Each event should be a JSON "
        "object with keys: note (0-127), velocity (0-127), start_time "
        "(seconds), and duration (seconds). Only output the JSON list."
    )
    user_message = (
        "Input melody (as JSON):\n" + json.dumps(midi_input)
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
    # Extract the JSON from the response
    content = response.choices[0].message.content
    print(f"[llm_client] LLM response content: "
          f"{content}")
    try:
        midi_events = json.loads(content)
    except Exception as e:
        print(f"[llm_client] Error parsing LLM response: {e}")
        # Try to extract JSON substring if LLM output extra text
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            midi_events = json.loads(match.group(0))
        else:
            raise ValueError("Could not parse LLM MIDI response: " + content)
    print(f"[llm_client] Parsed midi_events: {midi_events}")
    return midi_events
