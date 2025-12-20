import os
import re
import json
import asyncio
import edge_tts
import shutil

# --- CONFIGURATION ---
SCENE_FILE = "scenes/mariage.txt"
CASTING_FILE = "casting.json"
EXPORT_DIR = "export"
AUDIO_DIR = "audio"

# --- FONCTIONS UTILITAIRES ---

def load_casting(filepath):
    if not os.path.exists(filepath):
        return {"default_voice": "fr-FR-DeniseNeural", "voices": {}, "roles": {}}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_voice_for_speaker(speaker_name, config):
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

def parse_scene(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    dialogue = []
    current_speaker = None
    current_text = []
    speaker_pattern = re.compile(r'^([A-ZÀ-ÖØ-Þ\-\s]+(?:\([^\)]+\))?)\.\s*(.*)')

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

# --- GÉNÉRATION ---

async def generate_export():
    print(f"--- Démarrage de l'export HTML ---")
    
    full_export_path = os.path.join(os.getcwd(), EXPORT_DIR)
    full_audio_path = os.path.join(full_export_path, AUDIO_DIR)
    
    if os.path.exists(full_export_path):
        shutil.rmtree(full_export_path)
    os.makedirs(full_audio_path)
    
    print(f"Dossier créé : {full_export_path}")

    config = load_casting(CASTING_FILE)
    dialogue = parse_scene(SCENE_FILE)
    all_speakers = sorted(list(set(d['speaker'] for d in dialogue)))
    
    js_data = []
    
    print(f"Génération des fichiers audio ({len(dialogue)} répliques)...")
    
    for index, line in enumerate(dialogue):
        speaker = line['speaker']
        text = line['text']
        voice = get_voice_for_speaker(speaker, config)
        
        filename = f"line_{index:03d}.mp3"
        filepath = os.path.join(full_audio_path, filename)
        
        text_clean = re.sub(r'\([^\)]+\)', '', text)
        
        if text_clean.strip():
            communicate = edge_tts.Communicate(text_clean, voice)
            await communicate.save(filepath)
        
        js_data.append({
            "id": index,
            "speaker": speaker,
            "text": text,
            "audio": f"{AUDIO_DIR}/{filename}" if text_clean.strip() else None
        })
        
        if index % 10 == 0:
            print(f"  -> {index}/{len(dialogue)}...")

    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Répétition : {os.path.basename(SCENE_FILE)}</title>
    <style>
        body {{ font-family: sans-serif; background: #1a1a1a; color: #eee; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }}
        #setup {{ text-align: center; margin-top: 50px; }}
        select {{ padding: 10px; font-size: 1.2em; margin: 10px; }}
        button {{ padding: 10px 20px; font-size: 1.2em; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 5px; }}
        
        #stage {{ display: none; flex: 1; flex-direction: column; overflow: hidden; }}
        #dialogue-container {{ flex: 1; overflow-y: auto; padding: 20px; border: 1px solid #333; border-radius: 8px; background: #252525; margin-bottom: 20px; }}
        
        .line {{ padding: 15px; margin-bottom: 10px; border-radius: 5px; opacity: 0.5; transition: all 0.3s; }}
        .line.active {{ opacity: 1; background: #333; border-left: 5px solid #4CAF50; transform: scale(1.02); }}
        .line.user-turn {{ border-left-color: #FF9800; background: #3e2723; }}
        
        .speaker {{ font-weight: bold; font-size: 0.9em; color: #aaa; margin-bottom: 5px; }}
        .text {{ font-size: 1.2em; line-height: 1.4; transition: all 0.3s; }}
        
        .hidden-text {{
            color: transparent;
            text-shadow: 0 0 15px rgba(255,255,255,0.5);
            user-select: none;
        }}
        
        #controls {{ height: 80px; display: flex; justify-content: center; align-items: center; }}
        #action-btn {{ width: 100%; height: 100%; font-size: 1.5em; background: #2196F3; }}
        #status {{ text-align: center; color: #888; margin-bottom: 10px; }}
        #error-msg {{ color: red; text-align: center; display: none; }}
    </style>
</head>
<body>

    <div id="setup">
        <h1>Configuration de la répétition</h1>
        <p>Quel rôle voulez-vous jouer ?</p>
        <select id="role-select">
            {''.join([f'<option value="{s}">{s}</option>' for s in all_speakers])}
        </select>
        <br><br>
        <button onclick="startRehearsal()">Commencer</button>
        <p style="font-size:0.8em; color:#888;">Note : Cliquez pour activer l'audio.</p>
    </div>

    <div id="stage">
        <div id="status">En attente...</div>
        <div id="error-msg"></div>
        <div id="dialogue-container"></div>
        <div id="controls">
            <button id="action-btn" onclick="handleUserAction()">Démarrer</button>
        </div>
    </div>

    <script>
        const scriptData = {json.dumps(js_data, ensure_ascii=False)};
        let currentLineIndex = 0;
        let userRole = "";
        let isUserTurn = false;
        let userStep = "verify"; 
        let audioPlayer = new Audio();

        audioPlayer.onerror = function() {{
            const err = "Erreur de lecture audio : " + (audioPlayer.error ? audioPlayer.error.message : "Inconnue");
            console.error(err);
            document.getElementById('error-msg').innerText = err + " (Vérifiez que les fichiers sont bien dans le dossier audio/)";
            document.getElementById('error-msg').style.display = 'block';
            setTimeout(() => playLine(currentLineIndex + 1), 2000);
        }};

        function startRehearsal() {{
            userRole = document.getElementById('role-select').value;
            document.getElementById('setup').style.display = 'none';
            document.getElementById('stage').style.display = 'flex';
            
            audioPlayer.play().catch(() => {{}});
            
            renderScript();
            playLine(0);
        }}

        function renderScript() {{
            const container = document.getElementById('dialogue-container');
            container.innerHTML = scriptData.map((line, index) => {{
                // On cache le texte si c'est le rôle de l'utilisateur
                const isUser = line.speaker === userRole;
                const hiddenClass = isUser ? 'hidden-text' : '';
                
                return `
                <div class="line" id="line-${{index}}">
                    <div class="speaker">${{line.speaker}}</div>
                    <div class="text ${{hiddenClass}}">${{line.text}}</div>
                </div>
                `;
            }}).join('');
        }}

        function scrollToLine(index) {{
            const el = document.getElementById(`line-${{index}}`);
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                document.querySelectorAll('.line').forEach(l => l.classList.remove('active', 'user-turn'));
                el.classList.add('active');
                if (scriptData[index].speaker === userRole) {{
                    el.classList.add('user-turn');
                }}
            }}
        }}

        function playLine(index) {{
            if (index >= scriptData.length) {{
                document.getElementById('status').innerText = "Fin de la scène.";
                return;
            }}

            currentLineIndex = index;
            scrollToLine(index);
            const line = scriptData[index];
            const btn = document.getElementById('action-btn');
            const status = document.getElementById('status');
            document.getElementById('error-msg').style.display = 'none';

            if (line.speaker === userRole) {{
                isUserTurn = true;
                userStep = "verify";
                
                // Le texte est déjà caché par renderScript, pas besoin de le refaire ici
                
                status.innerText = "C'est à vous !";
                btn.innerText = "Vérifier";
                btn.style.background = "#FF9800";
                btn.disabled = false;
            }} else {{
                isUserTurn = false;
                status.innerText = line.speaker + " parle...";
                btn.innerText = "Écoute...";
                btn.style.background = "#555";
                btn.disabled = true;

                if (line.audio) {{
                    console.log("Lecture : " + line.audio);
                    audioPlayer.src = line.audio;
                    
                    const playPromise = audioPlayer.play();
                    
                    if (playPromise !== undefined) {{
                        playPromise.then(_ => {{}})
                        .catch(error => {{
                            console.warn("Autoplay bloqué ou erreur : " + error);
                            btn.innerText = "Lecture bloquée (Cliquez ici)";
                            btn.style.background = "red";
                            btn.disabled = false;
                            btn.onclick = function() {{
                                audioPlayer.play();
                                btn.onclick = handleUserAction;
                                btn.disabled = true;
                                btn.style.background = "#555";
                            }};
                        }});
                    }}
                    
                    audioPlayer.onended = () => {{
                        playLine(index + 1);
                    }};
                }} else {{
                    setTimeout(() => playLine(index + 1), 1000);
                }}
            }}
        }}

        function handleUserAction() {{
            if (!isUserTurn) return;

            if (userStep === "verify") {{
                // Étape 1 : Révéler le texte
                const textEl = document.querySelector(`#line-${{currentLineIndex}} .text`);
                textEl.classList.remove('hidden-text');
                
                const btn = document.getElementById('action-btn');
                btn.innerText = "Continuer";
                btn.style.background = "#4CAF50";
                userStep = "next";
            }} else {{
                // Étape 2 : Passer à la suite
                playLine(currentLineIndex + 1);
            }}
        }}
    </script>
</body>
</html>
    """
    
    with open(os.path.join(full_export_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"--- Export terminé avec succès ! ---")
    print(f"Ouvrez ce fichier dans votre navigateur : {os.path.join(full_export_path, 'index.html')}")

if __name__ == "__main__":
    asyncio.run(generate_export())
