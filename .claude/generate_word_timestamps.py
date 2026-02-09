#!/usr/bin/env python3
"""
Generate word-level timestamps for all testimony audio files using OpenAI Whisper API.
Outputs a JavaScript file with word-level transcript data.

Usage:
    pip3 install openai
    export OPENAI_API_KEY="your-api-key"
    python3 generate_word_timestamps.py
"""

import os
import json
import re
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed.")
    print("Please run: pip3 install openai")
    sys.exit(1)

# Configuration - use absolute path
AUDIO_DIR = Path("/Users/sarahmuller/Desktop/THESIS/Stories/testimonies/testimonies")
OUTPUT_FILE = AUDIO_DIR / "word-transcripts.js"

def extract_speaker_key(filename):
    """Extract speaker key from filename, handling duplicates."""
    match = re.match(r'^([A-Z]+)', filename)
    if not match:
        return None

    speaker = match.group(1)

    # Handle speakers with multiple testimonies
    if speaker == "DOM":
        if "Ice Cream" in filename:
            return "DOM_ICECREAM"
        else:
            return "DOM_GIRAFFE"
    elif speaker == "RILEY":
        if "Ironic" in filename:
            return "RILEY_IRONIC"
        else:
            return "RILEY_BOAT"

    return speaker

def transcribe_audio(client, audio_path):
    """Transcribe audio file and get word-level timestamps."""
    print(f"    Opening file: {audio_path.name}")
    with open(audio_path, "rb") as audio_file:
        print(f"    Calling Whisper API...")
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        print(f"    API response received")
    return response

def process_all_files():
    """Process all MP3 files and generate word-level transcripts."""
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please run: export OPENAI_API_KEY=\"your-api-key\"")
        sys.exit(1)

    print(f"API key found: {api_key[:8]}...{api_key[-4:]}")

    client = OpenAI()

    transcripts = {}
    mp3_files = sorted(AUDIO_DIR.glob("*.mp3"))

    print(f"\nFound {len(mp3_files)} audio files to process")
    print(f"Output will be written to: {OUTPUT_FILE}")
    print("-" * 50)

    if len(mp3_files) == 0:
        print("ERROR: No MP3 files found!")
        print(f"Looking in: {AUDIO_DIR}")
        sys.exit(1)

    for i, audio_path in enumerate(mp3_files, 1):
        key = extract_speaker_key(audio_path.name)
        if not key:
            print(f"  Skipping {audio_path.name} - could not extract speaker name")
            continue

        print(f"\n[{i}/{len(mp3_files)}] Processing {audio_path.name}...")
        print(f"    Speaker key: {key}")

        try:
            response = transcribe_audio(client, audio_path)

            # Extract words with timestamps
            words = []
            if hasattr(response, 'words') and response.words:
                for word_data in response.words:
                    words.append({
                        "w": word_data.word,
                        "s": round(word_data.start, 2),
                        "e": round(word_data.end, 2)
                    })
                print(f"    SUCCESS: {len(words)} words extracted")
            else:
                print(f"    WARNING: No words in response")
                print(f"    Response type: {type(response)}")
                if hasattr(response, 'text'):
                    print(f"    Has text: {response.text[:100]}...")

            transcripts[key] = words

        except Exception as e:
            print(f"    ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Write output as JavaScript
    print("\n" + "-" * 50)
    print(f"Writing output to {OUTPUT_FILE}")

    js_content = f"const wordTranscripts = {json.dumps(transcripts, indent=2)};\n"

    with open(OUTPUT_FILE, "w") as f:
        f.write(js_content)

    print(f"Done! Processed {len(transcripts)} speakers")

    # Summary
    total_words = sum(len(words) for words in transcripts.values())
    print(f"Total words extracted: {total_words}")

    return transcripts

if __name__ == "__main__":
    print("Starting word timestamp generation...")
    process_all_files()
    print("\nScript complete!")
