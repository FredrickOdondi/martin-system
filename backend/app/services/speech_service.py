import os
from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
from app.core.config import settings
from loguru import logger
import asyncio

class SpeechService:
    def __init__(self):
        self.project_id = settings.GOOGLE_PROJECT_ID if hasattr(settings, 'GOOGLE_PROJECT_ID') else "favorable-valor-457510-a6"
        self.location = "global"
        self.client = speech_v2.SpeechAsyncClient()
        self.recognizer_name = f"projects/{self.project_id}/locations/{self.location}/recognizers/_"
        
        logger.info(f"Initialized Google Speech Service for project {self.project_id}")

    async def stream_audio(self, audio_generator):
        """
        Streams audio to Google Cloud STT and yields back transcripts.
        """
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="chirp",  # Or 'long' / 'short' depending on use case. Chirp is newer.
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                diarization_config=cloud_speech.SpeakerDiarizationConfig(
                    min_speaker_count=1,
                    max_speaker_count=5
                )
            ),
        )

        streaming_config = cloud_speech.StreamingRecognitionConfig(
            config=config,
            streaming_features=cloud_speech.StreamingRecognitionFeatures(enable_voice_activity_events=True)
        )

        # Generator to yield request chunks
        async def request_generator():
             # First yield the config
            yield cloud_speech.StreamingRecognizeRequest(
                recognizer=self.recognizer_name,
                streaming_config=streaming_config
            )
            
            # Then yield audio chunks
            async for chunk in audio_generator:
                print(f"Sending audio chunk size: {len(chunk)}")
                yield cloud_speech.StreamingRecognizeRequest(audio=chunk)

        try:
            logger.info("Starting bidi stream to Google STT...")
            responses = await self.client.streaming_recognize(requests=request_generator())
            
            async for response in responses:
                if not response.results:
                    continue
                
                for result in response.results:
                     # Calculate stability or is_final if needed.
                     # V2 API structure is slightly different.
                     alternatives = result.alternatives
                     if alternatives:
                         transcript = alternatives[0].transcript
                         is_final = result.is_final
                         
                         yield {
                             "transcript": transcript,
                             "is_final": is_final,
                             "confidence": alternatives[0].confidence
                         }
                         
        except Exception as e:
            logger.error(f"Error in speech stream: {e}")
            import traceback
            traceback.print_exc()
            raise e

# Singleton
speech_service = SpeechService()
