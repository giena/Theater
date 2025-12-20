import sys
import re
import os
import json
import asyncio
import edge_tts
import pygame

# Fichier de configuration par défaut
CASTING_FILE = "casting.json"

# Configuration par défaut si le fichier est absent
DEFAULT_CONFIG = {
    "default_voice": "fr-FR-DeniseNeural",
    "voices": {},
    "roles": {}
}

def load_casting(filepath):
    """Charge la configuration du casting depuis un fichier JSON."""
    if not os.path.exists(filepath):
        print(f"Attention : Fichier de casting '{filepath}' non trouvé. Utilisation de la configuration par défaut.")
        return DEFAULT_CONFIG
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture de {filepath} : {e}")
        return DEFAULT_CONFIG

def get_voice_for_speaker(speaker_name, config):
    """Retourne la voix associée au personnage en fonction de la config."""
    name_upper = speaker_name.upper().strip()
    
    role_key = None
    if name_upper in config.get("roles", {}):
        role_key = config["roles"][name_upper]
    else:
        for key in config.get("roles", {}):
            if key in name_upper:
                role_key = config["roles"][key]
                break
    
    voice_name = config.get("default_voice", "fr-FR-DeniseNeural")
    if role_key:
        if role_key in config.get("voices", {}):
            voice_name = config["voices"][role_key]
        else:
            voice_name = role_key
    if voice_name in config.get("voices", {}):
        voice_name = config["voices"][voice_name]
    return voice_name

def parse_txt_scene(filepath):
    """Analyse un fichier texte classique (Legacy)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    dialogue = []
    current_speaker = None
    current_text = []
    speaker_pattern = re.compile(r'^([A-ZÀ-ÖØ-Þ\-\s\'’]+(?:\([^\)]+\))?)\.\s*(.*)')

    for line in lines:
        line = line.strip()
        if not line: continue
        match = speaker_pattern.match(line)
        if match:
            if current_speaker:
                dialogue.append({'speaker': current_speaker, 'text': " ".join(current_text)})
            raw_speaker = match.group(1)
            clean_name = re.sub(r'\s*\(.*\)', '', raw_speaker).strip()
            current_speaker = clean_name
            current_text = [match.group(2)]
        else:
            if current_speaker:
                current_text.append(line)
    if current_speaker:
        dialogue.append({'speaker': current_speaker, 'text': " ".join(current_text)})
    return dialogue

def load_scene(filepath):
    """Charge une scène depuis un fichier JSON (recommandé) ou TXT."""
    if filepath.endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validation basique : on attend une liste d'objets avec 'speaker' et 'text'
                if isinstance(data, list):
                    return data
                else:
                    print("Erreur : Le fichier JSON doit contenir une liste de répliques.")
                    return []
        except Exception as e:
            print(f"Erreur de lecture JSON : {e}")
            return []
    else:
        return parse_txt_scene(filepath)

async def speak_edge(text, voice):
    """Génère l'audio avec Edge TTS et le joue avec Pygame."""
    # Nettoyage supplémentaire au cas où (même si le JSON est censé être propre)
    text_clean = re.sub(r'\([^\)]+\)', '', text)
    if not text_clean.strip():
        return

    output_file = "temp_speech.mp3"
    
    try:
        communicate = edge_tts.Communicate(text_clean, voice)
        await communicate.save(output_file)

        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()
        
    except Exception as e:
        print(f"(Erreur audio : {e})")

async def rehearse_async(filepath, my_role):
    if not os.path.exists(filepath):
        print(f"Erreur : Le fichier {filepath} n'existe pas.")
        return

    config = load_casting(CASTING_FILE)
    pygame.mixer.init()

    print(f"--- Répétition pour le rôle de : {my_role} ---")
    print(f"--- Scène : {filepath} ---")
    
    dialogue = load_scene(filepath)
    my_role = my_role.upper()

    for line in dialogue:
        speaker = line.get('speaker', 'INCONNU')
        text = line.get('text', '')
        
        # On ignore les lignes sans texte (didascalies pures en JSON)
        if not text.strip():
            continue

        if speaker.upper() == my_role:
            print(f"\n[{speaker}] (C'est à vous !)")
            input("Appuyez sur Entrée après avoir dit votre texte...")
            print(f"   -> Vous deviez dire : \"{text}\"")
        else:
            voice = get_voice_for_speaker(speaker, config)
            print(f"\n[{speaker}] ({voice}) : {text}")
            await speak_edge(text, voice)

    if os.path.exists("temp_speech.mp3"):
        try: os.remove("temp_speech.mp3")
        except: pass

def rehearse(filepath, my_role):
    asyncio.run(rehearse_async(filepath, my_role))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python repetition.py <fichier_scene.json|txt> <nom_du_personnage>")
    else:
        rehearse(sys.argv[1], sys.argv[2])
