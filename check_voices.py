import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print(f"Found {len(voices)} voices:")
for i, voice in enumerate(voices):
    print(f"{i}: ID='{voice.id}' NAME='{voice.name}'")
