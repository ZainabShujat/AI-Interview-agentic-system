import os
import httpx
from typing import Dict, Any, List, Optional

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def transcribe_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Transcribes audio using Deepgram.
    Returns a dictionary matching the required future-ready schema:
    {
      "transcript": "...",
      "confidence": 0.92,
      "duration": 32.4,
      "words": [...]
    }
    """
    if not DEEPGRAM_API_KEY:
        # Default V1 mock fallback
        return {
            "transcript": "I design distributed systems by isolating stateful database connections and utilizing caching policies.",
            "confidence": 0.96,
            "duration": 12.5,
            "words": [
                {"word": "I", "start": 0.1, "end": 0.3, "confidence": 0.99},
                {"word": "design", "start": 0.3, "end": 0.7, "confidence": 0.98},
                {"word": "distributed", "start": 0.7, "end": 1.2, "confidence": 0.95},
                {"word": "systems", "start": 1.2, "end": 1.6, "confidence": 0.97}
            ]
        }
        
    url = "https://api.deepgram.com/v1/listen?smart_format=true&model=nova-2"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, content=audio_bytes, headers=headers, timeout=30.0)
        
    if response.status_code != 200:
        raise Exception(f"Deepgram transcription failed: {response.text}")
        
    data = response.json()
    channels = data.get("results", {}).get("channels", [])
    if not channels:
        raise Exception("No transcription channel results found.")
        
    alternatives = channels[0].get("alternatives", [])
    if not alternatives:
        raise Exception("No transcript alternatives found.")
        
    best_alt = alternatives[0]
    
    return {
        "transcript": best_alt.get("transcript", ""),
        "confidence": best_alt.get("confidence", 0.0),
        "duration": data.get("metadata", {}).get("duration", 0.0),
        "words": best_alt.get("words", [])
    }

def analyze_voice_features(audio_bytes: bytes) -> Dict[str, float]:
    """
    Analyzes acoustic features using OpenSMILE.
    Returns:
    {
      "speakingRate": float,  # Syllables per second
      "energy": float,        # RMS energy
      "intensity": float,     # Decibels (dB)
      "pitchVariance": float, # Hz standard deviation
      "jitter": float,        # Frequency perturbation
      "shimmer": float        # Amplitude perturbation
    }
    """
    # Future OpenSMILE library invocation placeholder:
    # import opensmile
    # smile = opensmile.Smile(
    #     feature_set=opensmile.FeatureSet.GeMAPSv01b,
    #     feature_level=opensmile.FeatureLevel.Functionals,
    # )
    # features = smile.process_signal(signal, sampling_rate)
    
    # Standard V1 mock fallback for MVP metrics collection:
    return {
        "speakingRate": 3.4,
        "energy": 0.052,
        "intensity": 71.3,
        "pitchVariance": 28.1,
        "jitter": 0.015,
        "shimmer": 0.042
    }
