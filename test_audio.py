import pyttsx3

print("--- DIAGNOSTIC AUDIO ---")
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print(f"{len(voices)} voix trouvées.")
    
    for index, voice in enumerate(voices):
        print(f"\nTest de la voix {index}:")
        print(f" - ID: {voice.id}")
        print(f" - Nom: {voice.name}")
        print(f" - Langues: {voice.languages}")
        
        try:
            engine.setProperty('voice', voice.id)
            engine.say(f"Ceci est la voix numéro {index}")
            engine.runAndWait()
            print("   -> Test OK (avez-vous entendu ?)")
        except Exception as e:
            print(f"   -> Erreur lors du test : {e}")

except Exception as e:
    print(f"Erreur critique d'initialisation : {e}")
