import os
import random
import time


class AIBridgeService:
    """
    Central AI Service Layer

    This class acts as a bridge between Django
    and external AI providers.

    Currently it simulates APIs.

    Later we can replace these methods
    with OpenAI, ElevenLabs,
    Google STT, Azure, Twilio, etc.
    """

    def __init__(self):

        self.api_key = os.getenv("AI_API_KEY")

    # -------------------------------
    # Generate Interview Question
    # -------------------------------

    def generate_question(self, job_title):

        print(f"Generating AI question for {job_title}")

        return {
            "success": True,
            "question": f"What interests you about the {job_title} role?",
        }

    # -------------------------------
    # Speech → Text
    # -------------------------------

    def speech_to_text(self, audio_file):

        print("Converting speech to text...")

        return {"success": True, "transcript": "This is a simulated transcript."}

    # -------------------------------
    # Text → Speech
    # -------------------------------

    def text_to_speech(self, text, voice="Female"):

        print(f"Generating speech using {voice} voice...")

        return {"success": True, "audio_url": "/fake/audio/output.mp3"}

    # -------------------------------
    # Trigger Voice Call
    # -------------------------------

    def trigger_call(self, phone_number, language="English", voice="Female"):

        print("=" * 50)
        print("Starting AI Voice Call")
        print("Phone:", phone_number)
        print("Language:", language)
        print("Voice:", voice)
        print("=" * 50)

        time.sleep(2)

        return {"success": True, "call_id": random.randint(10000, 99999)}
        # -------------------------------

    # Start AI Interview
    # -------------------------------

    def start_interview(self, interview):

        print("=" * 50)
        print("Starting AI Interview")
        print("Interview ID:", interview.id)

        candidate = interview.application.candidate

        phone_number = getattr(candidate, "phone_number", None)

        if not phone_number:
            phone_number = "+910000000000"

        call = self.trigger_call(
            phone_number=phone_number,
            language="English",
            voice="Female",
        )

        if call["success"]:

            print("Call Started")
            print("Call ID:", call["call_id"])

            return True

        return False
