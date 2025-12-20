import os
import re
import json
import asyncio
import edge_tts
import shutil

# --- CONFIGURATION ---
SCENES_DIR = "scenes"
CASTING_FILE = "casting.json"
EXPORT_DIR = "docs"  # Changement ici : 'export' -> 'docs' pour GitHub Pages
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

def load_scene(filepath):
    if filepath.endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# --- GÉNÉRATION ---

async def generate_export():
    print(f"--- Démarrage de l'export HTML pour GitHub Pages (dossier docs/) ---")
    
    full_export_path = os.path.join(os.getcwd(), EXPORT_DIR)
    full_audio_path = os.path.join(full_export_path, AUDIO_DIR)
    
    if os.path.exists(full_export_path):
        shutil.rmtree(full_export_path)
    os.makedirs(full_audio_path)
    
    # Création d'un fichier .nojekyll pour dire à GitHub de ne pas traiter ce dossier
    # (utile si on a des dossiers commençant par _ comme _audio, mais ici audio est ok)
    with open(os.path.join(full_export_path, ".nojekyll"), "w") as f:
        f.write("")
    
    config = load_casting(CASTING_FILE)
    scenes_data = {}
    
    all_files = os.listdir(SCENES_DIR)
    scene_files = [f for f in all_files if f.endswith(".json")]
    scene_files.sort()
    
    if not scene_files:
        print(f"Erreur : Aucun fichier .json trouvé dans '{SCENES_DIR}'")
        return

    print(f"Scènes trouvées : {len(scene_files)}")

    for scene_file in scene_files:
        scene_name = os.path.splitext(scene_file)[0]
        print(f"\nTraitement de la scène : {scene_name}")
        
        dialogue = load_scene(os.path.join(SCENES_DIR, scene_file))
        if not dialogue: continue

        roles = sorted(list(set(d.get('speaker', 'UNKNOWN') for d in dialogue)))
        processed_dialogue = []
        
        for index, line in enumerate(dialogue):
            speaker = line.get('speaker', 'UNKNOWN')
            text = line.get('text', '')
            action = line.get('action', '')
            voice = get_voice_for_speaker(speaker, config)
            
            safe_scene_name = re.sub(r'[^a-zA-Z0-9]', '_', scene_name)
            filename = f"{safe_scene_name}_{index:03d}.mp3"
            filepath = os.path.join(full_audio_path, filename)
            
            text_clean = re.sub(r'\([^\)]+\)', '', text)
            
            has_audio = False
            if text_clean.strip():
                try:
                    communicate = edge_tts.Communicate(text_clean, voice)
                    await communicate.save(filepath)
                    has_audio = True
                except Exception as e:
                    print(f"  Erreur audio ({speaker}): {e}")
            
            processed_dialogue.append({
                "id": index,
                "speaker": speaker,
                "text": text,
                "action": action,
                "audio": f"{AUDIO_DIR}/{filename}" if has_audio else None
            })
            
            if index % 10 == 0:
                print(f"  -> {index}/{len(dialogue)}...")
        
        scenes_data[scene_name] = {
            "roles": roles,
            "dialogue": processed_dialogue
        }

    # --- GÉNÉRATION HTML ---
    
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Théâtre Studio</title>
    <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --paper-color: #1e1e1e;
            --accent-color: #d4af37; /* Or */
            --highlight-color: #2c2c2c;
            --user-highlight: #3e2723;
            --font-script: 'Courier Prime', monospace;
            --font-title: 'Playfair Display', serif;
        }}

        body {{
            font-family: var(--font-script);
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        /* --- SETUP SCREEN --- */
        #setup {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at center, #2a2a2a 0%, #000000 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 100;
        }}

        h1 {{
            font-family: var(--font-title);
            font-size: 3em;
            color: var(--accent-color);
            margin-bottom: 40px;
            text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
            letter-spacing: 2px;
        }}

        .setup-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 40px;
            border-radius: 8px;
            border: 1px solid #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }}

        select {{
            width: 100%;
            padding: 12px;
            margin: 15px 0;
            background: #333;
            color: white;
            border: 1px solid #555;
            border-radius: 4px;
            font-family: var(--font-script);
            font-size: 1.1em;
        }}

        button.start-btn {{
            background: var(--accent-color);
            color: #000;
            font-family: var(--font-title);
            font-weight: bold;
            font-size: 1.2em;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            margin-top: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        button.start-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(212, 175, 55, 0.5);
        }}

        /* --- STAGE --- */
        #stage {{
            display: none;
            flex: 1;
            flex-direction: column;
            height: 100%;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
            background: var(--paper-color);
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
            position: relative;
        }}

        #header-bar {{
            padding: 15px 20px;
            border-bottom: 2px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #181818;
        }}

        #scene-title {{
            font-family: var(--font-title);
            color: var(--accent-color);
            font-size: 1.2em;
        }}

        #back-btn {{
            background: transparent;
            border: 1px solid #555;
            color: #888;
            padding: 5px 15px;
            cursor: pointer;
            font-family: var(--font-script);
            font-size: 0.8em;
        }}

        #dialogue-container {{
            flex: 1;
            overflow-y: auto;
            padding: 40px 20px;
            scroll-behavior: smooth;
        }}

        /* --- SCRIPT FORMATTING --- */
        .line {{
            margin-bottom: 25px;
            opacity: 0.4;
            transition: opacity 0.5s, transform 0.5s;
            padding: 10px;
            border-left: 3px solid transparent;
        }}

        .line.active {{
            opacity: 1;
            background: rgba(255, 255, 255, 0.03);
            border-left-color: var(--accent-color);
            transform: scale(1.02);
        }}

        .line.user-turn {{
            border-left-color: #ff5722; /* Orange pour l'utilisateur */
        }}

        .speaker {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #bbb;
        }}

        .action {{
            font-style: italic;
            color: #888;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}

        .text {{
            font-size: 1.1em;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
        }}

        .hidden-text {{
            color: transparent;
            text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
            user-select: none;
        }}

        /* --- CONTROLS --- */
        #controls {{
            padding: 20px;
            background: #181818;
            border-top: 1px solid #333;
            text-align: center;
        }}

        #status {{
            margin-bottom: 10px;
            color: #666;
            font-size: 0.9em;
            font-style: italic;
        }}

        #action-btn {{
            width: 100%;
            max-width: 400px;
            padding: 15px;
            font-family: var(--font-title);
            font-size: 1.2em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background: #333;
            color: #aaa;
            transition: all 0.3s;
        }}

        #action-btn:not(:disabled) {{
            background: var(--accent-color);
            color: #000;
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
        }}

        #action-btn.verify-mode {{
            background: #ff5722; /* Orange */
            color: white;
        }}
        
        #action-btn.continue-mode {{
            background: #4caf50; /* Vert */
            color: white;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #121212; }}
        ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #555; }}

    </style>
</head>
<body>

    <div id="setup">
        <h1>THÉÂTRE STUDIO</h1>
        <div class="setup-card">
            <div class="form-group">
                <label>SCÈNE</label>
                <select id="scene-select" onchange="updateRoles()">
                    <option value="">-- Choisir une scène --</option>
                </select>
            </div>

            <div class="form-group" id="role-group" style="display:none;">
                <label>RÔLE</label>
                <select id="role-select">
                    <!-- Rempli par JS -->
                </select>
            </div>

            <button class="start-btn" id="start-btn" onclick="startRehearsal()" style="display:none;">ENTRER EN SCÈNE</button>
        </div>
    </div>

    <div id="stage">
        <div id="header-bar">
            <span id="scene-title">TITRE</span>
            <button id="back-btn" onclick="location.reload()">QUITTER</button>
        </div>
        
        <div id="dialogue-container"></div>
        
        <div id="controls">
            <div id="status">En attente...</div>
            <div id="error-msg" style="color:red; display:none; margin-bottom:5px;"></div>
            <button id="action-btn" onclick="handleUserAction()" disabled>Démarrer</button>
        </div>
    </div>

    <script>
        const allScenesData = {json.dumps(scenes_data, ensure_ascii=False)};
        
        let currentSceneData = null;
        let currentLineIndex = 0;
        let userRole = "";
        let isUserTurn = false;
        let userStep = "verify"; 
        let audioPlayer = new Audio();

        const sceneSelect = document.getElementById('scene-select');
        const roleSelect = document.getElementById('role-select');
        const roleGroup = document.getElementById('role-group');
        const startBtn = document.getElementById('start-btn');

        Object.keys(allScenesData).forEach(sceneName => {{
            const option = document.createElement('option');
            option.value = sceneName;
            option.textContent = sceneName.toUpperCase();
            sceneSelect.appendChild(option);
        }});

        function updateRoles() {{
            const sceneName = sceneSelect.value;
            roleSelect.innerHTML = "";
            
            if (sceneName && allScenesData[sceneName]) {{
                const roles = allScenesData[sceneName].roles;
                roles.forEach(role => {{
                    const option = document.createElement('option');
                    option.value = role;
                    option.textContent = role;
                    roleSelect.appendChild(option);
                }});
                roleGroup.style.display = 'block';
                startBtn.style.display = 'inline-block';
            }} else {{
                roleGroup.style.display = 'none';
                startBtn.style.display = 'none';
            }}
        }}

        audioPlayer.onerror = function() {{
            const err = "Erreur audio";
            console.error(err);
            document.getElementById('error-msg').innerText = err;
            document.getElementById('error-msg').style.display = 'block';
            setTimeout(() => playLine(currentLineIndex + 1), 2000);
        }};

        function startRehearsal() {{
            const sceneName = sceneSelect.value;
            userRole = roleSelect.value;
            
            if (!sceneName || !userRole) return;
            
            currentSceneData = allScenesData[sceneName].dialogue;
            
            document.getElementById('scene-title').innerText = sceneName.toUpperCase() + " // " + userRole;
            document.getElementById('setup').style.opacity = '0';
            setTimeout(() => {{
                document.getElementById('setup').style.display = 'none';
                document.getElementById('stage').style.display = 'flex';
            }}, 500);
            
            audioPlayer.play().catch(() => {{}});
            
            renderScript();
            
            setTimeout(() => playLine(0), 500);
        }}

        function renderScript() {{
            const container = document.getElementById('dialogue-container');
            container.innerHTML = currentSceneData.map((line, index) => {{
                const isUser = line.speaker === userRole;
                const hiddenClass = isUser ? 'hidden-text' : '';
                
                let actionHtml = '';
                if (line.action) {{
                    actionHtml = `<div class="action">${{line.action}}</div>`;
                }}

                return `
                <div class="line" id="line-${{index}}">
                    <div class="speaker">${{line.speaker}}</div>
                    ${{actionHtml}}
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
                if (currentSceneData[index].speaker === userRole) {{
                    el.classList.add('user-turn');
                }}
            }}
        }}

        function playLine(index) {{
            if (index >= currentSceneData.length) {{
                document.getElementById('status').innerText = "FIN DE LA SCÈNE";
                document.getElementById('action-btn').innerText = "Recommencer";
                document.getElementById('action-btn').onclick = () => location.reload();
                document.getElementById('action-btn').disabled = false;
                document.getElementById('action-btn').className = "";
                return;
            }}

            currentLineIndex = index;
            scrollToLine(index);
            const line = currentSceneData[index];
            const btn = document.getElementById('action-btn');
            const status = document.getElementById('status');
            document.getElementById('error-msg').style.display = 'none';

            if (line.speaker === userRole) {{
                isUserTurn = true;
                userStep = "verify";
                status.innerText = "C'EST À VOUS";
                btn.innerText = "VÉRIFIER";
                btn.className = "verify-mode";
                btn.disabled = false;
            }} else {{
                isUserTurn = false;
                status.innerText = line.speaker + " PARLE...";
                btn.innerText = "ÉCOUTE...";
                btn.className = "";
                btn.disabled = true;

                if (line.audio) {{
                    audioPlayer.src = line.audio;
                    const playPromise = audioPlayer.play();
                    if (playPromise !== undefined) {{
                        playPromise.then(_ => {{}}).catch(error => {{
                            console.warn("Autoplay bloqué");
                            btn.innerText = "LECTURE BLOQUÉE (CLIQUEZ)";
                            btn.style.background = "red";
                            btn.disabled = false;
                            btn.onclick = function() {{
                                audioPlayer.play();
                                btn.onclick = handleUserAction;
                                btn.disabled = true;
                                btn.style.background = "#333";
                            }};
                        }});
                    }}
                    audioPlayer.onended = () => {{ playLine(index + 1); }};
                }} else {{
                    setTimeout(() => playLine(index + 1), 1500);
                }}
            }}
        }}

        function handleUserAction() {{
            if (!isUserTurn) return;
            if (userStep === "verify") {{
                const textEl = document.querySelector(`#line-${{currentLineIndex}} .text`);
                textEl.classList.remove('hidden-text');
                const btn = document.getElementById('action-btn');
                btn.innerText = "CONTINUER";
                btn.className = "continue-mode";
                userStep = "next";
            }} else {{
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
    print(f"Ouvrez ce fichier : {os.path.join(full_export_path, 'index.html')}")

if __name__ == "__main__":
    asyncio.run(generate_export())
