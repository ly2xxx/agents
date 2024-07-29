# Real-Time Audio Recording and Transcription in Python on Windows

Recording system audio and converting it to text in real-time using Python is a powerful capability that can be achieved using various libraries and APIs. This article provides a comprehensive guide on how to accomplish this on Windows, utilizing libraries like **PyAudio**, **Vosk**, and **AssemblyAI**.

## Overview of Required Libraries

1. **PyAudio**: A set of Python bindings for PortAudio, allowing you to record and play audio using Python. It's particularly useful for capturing audio input from a microphone or system sound.

2. **Vosk**: An offline speech recognition toolkit that allows for real-time transcription. It is efficient and supports multiple languages.

3. **AssemblyAI**: A cloud-based speech recognition service that provides real-time transcription capabilities via WebSocket connections.

4. **SoundDevice**: A Python module that provides bindings for the PortAudio library, enabling audio recording from various input devices.

## Step 1: Setting Up Your Environment

Before you start coding, ensure that you have Python installed on your Windows machine. You will also need to install the necessary libraries. Open your command prompt and run:

```bash
pip install pyaudio vosk assemblyai sounddevice
```

For **PyAudio**, if you encounter issues, you may need to install it using a `.whl` file from [PyAudio's unofficial binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

## Step 2: Recording System Audio

### Using PyAudio to Record System Audio

You can record audio from your system's speakers using the **WASAPI** loopback feature. Here’s how to do it:

1. **Enable Stereo Mix**: First, ensure that "Stereo Mix" is enabled in your Windows sound settings. Go to Control Panel > Sound > Recording, right-click on "Stereo Mix," and enable it.

2. **Record Audio**: Use the following code snippet to record audio:

```python
import pyaudio
import wave

# Setup parameters
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"

# Initialize PyAudio
p = pyaudio.PyAudio()

# Start recording
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
print("* recording")

frames = []

for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")

# Stop and close the stream
stream.stop_stream()
stream.close()
p.terminate()

# Save the recorded data as a WAV file
with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
```

## Step 3: Transcribing Audio in Real-Time

### Using Vosk for Real-Time Transcription

To transcribe audio captured from your microphone or speakers in real-time using Vosk:

1. Download a Vosk model from [Vosk Models](https://alphacephei.com/vosk/models).

2. Use the following code to perform real-time transcription:

```python
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

model = Model("path_to_vosk_model")
recognizer = KaldiRecognizer(model, 44100)

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

with sd.RawInputStream(samplerate=44100, channels=1, callback=callback):
    print("Recording... Press Ctrl+C to stop.")
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            print(json.loads(result)["text"])
```

### Using AssemblyAI for Real-Time Transcription

For those who prefer a cloud-based solution, AssemblyAI offers a robust API for real-time transcription.

1. Get your API key from [AssemblyAI](https://www.assemblyai.com).

2. Use the following code to set up real-time transcription:

```python
import assemblyai
import sounddevice as sd

api_key = "your_api_key"
client = assemblyai.Client(api_key)

def transcribe_audio():
    audio_stream = assemblyai.MicrophoneStream()
    transcriber = client.transcriber()

    print("Starting transcription...")
    for transcript in transcriber.transcribe(audio_stream):
        print(transcript['text'])

transcribe_audio()
```

## Conclusion

By following these steps, you can successfully record system audio on Windows and convert it to text in real-time using Python. Whether you choose to use Vosk for offline processing or AssemblyAI for cloud-based transcription, both methods provide effective solutions for real-time audio transcription. 

Feel free to explore and modify the code snippets provided to fit your specific needs and applications. Happy coding!


URL: https://stackoverflow.com/questions/57268372/how-to-convert-live-real-time-audio-from-mic-to-text - fetched successfully.
URL: https://shankhanilborthakur.medium.com/recording-system-audio-in-windows-10-using-pyaudio-1559f3e1b64f - fetched successfully.
URL: https://www.assemblyai.com/blog/real-time-transcription-in-python/ - fetched successfully.
URL: https://www.delftstack.com/howto/python/real-time-audio-processing-python/ - fetched successfully.
URL: https://singerlinks.com/2022/03/how-to-convert-microphone-speech-to-text-using-python-and-vosk/ - fetched successfully.
URL: https://picovoice.ai/blog/real-time-transcription-in-python/ - fetched successfully.