from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
from app.core.config import settings
import asyncio
import os

async def test_api_access():
    project_id = settings.GOOGLE_PROJECT_ID if hasattr(settings, 'GOOGLE_PROJECT_ID') else "favorable-valor-457510-a6"
    location = "global"
    
    print(f"Testing access for Project: {project_id}")
    
    client = speech_v2.SpeechAsyncClient()
    recognizer_name = f"projects/{project_id}/locations/{location}/recognizers/_"
    
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="date", # Small model for quick test
    )
    
    print("Initiating simple recognition request (mock audio)...")
    
    # We just want to check auth/enabling, so we send an empty request or minimal config
    # Actually, let's try to list recognizers or something simple, 
    # OR just initialize a stream.
    
    try:
        # Just listing recognizers is a good test of API enabled status
        parent = f"projects/{project_id}/locations/{location}"
        # We need a synchronous client for simple list if we don't want to setup full async loop just for that,
        # but we have async client.
        
        request = cloud_speech.ListRecognizersRequest(parent=parent)
        print("Sending ListRecognizersRequest...")
        response = await client.list_recognizers(request=request)
        print("✅ API is ENABLED and accessible.")
        async for recognizer in response:
            print(f"Found recognizer: {recognizer.name}")
            break
            
    except Exception as e:
        print("\n❌ API Test Failed!")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_access())
