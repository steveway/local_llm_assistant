import os
import subprocess
import wave
from openai import OpenAI
import pyaudio
import webrtcvad
import openwakeword
import whisper


# import piper # Use piper on Raspberry Pi

class VoiceAssistant:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.client = OpenAI(
            base_url="http://127.0.0.1:8080/v1",
            api_key="sk-no-key-required"
        )

    def record_wav(self):
        form_1 = pyaudio.paInt16
        chans = 1
        samp_rate = 16000
        frame_duration = 30
        chunk = int(samp_rate * (frame_duration / 1000.0))
        dev_index = 1
        wav_output_filename = 'input.wav'

        audio = pyaudio.PyAudio()

        # Create pyaudio stream.
        stream = audio.open(format=form_1, rate=samp_rate, channels=chans,
                            input_device_index=dev_index, input=True,
                            frames_per_buffer=chunk)
        print("Listening...")

        vad = webrtcvad.Vad()
        vad.set_mode(1)  # Aggressive mode

        frames = []

        # Loop through stream and append audio chunks to frame array.
        while True:
            data = stream.read(chunk)
            is_speech = vad.is_speech(data, samp_rate)
            if is_speech:
                frames.append(data)
            else:
                if len(frames) > 0:
                    break

        print("Recording...")
        frames.extend(stream.read(chunk) for _ in range(0, int(samp_rate / chunk) * 3))

        print("Finished recording")

        # Stop the stream, close it, and terminate the PyAudio instantiation.
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the audio frames as a .wav file.
        with wave.open(wav_output_filename, 'wb') as wavefile:
            wavefile.setnchannels(chans)
            wavefile.setsampwidth(audio.get_sample_size(form_1))
            wavefile.setframerate(samp_rate)
            wavefile.writeframes(b''.join(frames))

        return wav_output_filename

    def transcribe_audio(self, audio_file):
        print(audio_file)
        print(os.path.exists(audio_file))
        result = self.model.transcribe(audio_file)
        return result["text"]

    def query_llm(self, request):
        completion = self.client.chat.completions.create(
            model="LLaMA_CPP",
            messages=[
                {"role": "system",
                 "content": "You are an AI assistant. Your priority is helping users with their requests."},
                {"role": "user", "content": request}
            ]
        )
        return completion.choices[0].message.content

    def speak_result(self, message):
        # audio_array = bark.generate_audio(message)
        # Use pyaudio to play the audio array
        # p = pyaudio.PyAudio()
        # stream = p.open(format=pyaudio.paFloat32,
        #                 channels=1,
        #                 rate=16000,
        #                 output=True)
        # stream.write(audio_array)
        # stream.stop_stream()
        # stream.close()
        # p.terminate()
        espeak_path = r'C:/Program Files/eSpeak NG/espeak-ng.exe'
        if os.path.exists(espeak_path):
            subprocess.Popen(espeak_path + ' "{0}"'.format(message))
            # os.system(espeak_path + ' "{0}"'.format(message))


def main():
    assistant = VoiceAssistant()

    print("Ready...")

    while True:
        try:
            audio_file = assistant.record_wav()
            request = assistant.transcribe_audio(audio_file)
            if request:
                if len(request) > 15:
                    print("Transcription: {0}".format(request))
                    response = assistant.query_llm(request)
                    print("LLM result: {0}".format(response))
                    assistant.speak_result(response)
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            break


if __name__ == "__main__":
    main()
