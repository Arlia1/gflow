#!/usr/bin/env python3
"""
Voiceover Synthesis for Argentine Spanish
Uses Edge-TTS or ElevenLabs to generate realistic narration for Todo Frenos.
"""

import os
import asyncio

async def generate_voiceover_edge(text, output_path="output/audio/voiceover.mp3", voice="es-AR-TomasNeural"):
    """Generates audio using edge-tts (free, neural Argentine voice)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print(f"Voiceover saved to {output_path}")
        return output_path
    except ImportError:
        print("edge-tts not installed. Run: pip install edge-tts")
        return None

if __name__ == "__main__":
    import sys
    sample_text = (
        "Si pisás el pedal de freno y parece que estás pisando una baldosa, no sigas manejando. "
        "Se te pinchó el diafragma del servofreno. En Todo Frenos hace 35 años que cuidamos a los conductores de Gerli. "
        "Mandanos un mensaje directo y coordinamos tu revisión sin cargo."
    )
    text = sys.argv[1] if len(sys.argv) > 1 else sample_text
    asyncio.run(generate_voiceover_edge(text))
