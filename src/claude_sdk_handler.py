#!/usr/bin/env python3
"""
Claude SDK handler for agent requests
Uses Anthropic Python SDK for reliable streaming
"""
import sys
import json
import os
from anthropic import Anthropic

def stream_claude_response(system_prompt: str, user_message: str):
    """
    Stream a response from Claude using the Anthropic SDK

    Args:
        system_prompt: System prompt with UFC context
        user_message: User's message
    """
    # Initialize Anthropic client
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print(json.dumps({
            'type': 'error',
            'error': 'ANTHROPIC_API_KEY not set'
        }), flush=True)
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    try:
        # Stream the response
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=8096,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_message
            }]
        ) as stream:
            for text in stream.text_stream:
                # Output each text chunk as JSON
                print(json.dumps({
                    'type': 'text',
                    'text': text
                }), flush=True)

        # Send completion signal
        print(json.dumps({
            'type': 'complete'
        }), flush=True)

    except Exception as e:
        print(json.dumps({
            'type': 'error',
            'error': str(e)
        }), flush=True)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(json.dumps({
            'type': 'error',
            'error': 'Usage: claude_sdk_handler.py <system_prompt> <user_message>'
        }), flush=True)
        sys.exit(1)

    system_prompt = sys.argv[1]
    user_message = sys.argv[2]

    stream_claude_response(system_prompt, user_message)
