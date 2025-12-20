# Outil de Répétition de Théâtre

Ce projet fournit des outils pour aider les comédiens à apprendre leur texte. Il permet de répéter une scène en donnant la réplique, soit via un script Python interactif, soit via une page web autonome générée.

## Prérequis

- Python 3 installé
- Une connexion internet (pour la génération des voix via Microsoft Edge TTS)

## Installation

1. **Créer un environnement virtuel** (recommandé) :
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   # venv\Scripts\activate  # Sur Windows
   ```

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### 1. Répétition interactive (Terminal)

Pour lancer une répétition directement dans votre terminal :

```bash
python repetition.py <chemin_du_fichier_scene> <NOM_DU_PERSONNAGE>
```

**Exemple :**
Pour répéter le rôle de **Christian** dans la scène `mariage.txt` :
```bash
python repetition.py scenes/mariage.txt CHRISTIAN
```

Le script lira les répliques des autres personnages et s'arrêtera quand c'est à vous de parler. Appuyez sur **Entrée** une fois votre texte dit pour continuer.

### 2. Exportation Web (HTML/Audio)

Vous pouvez générer une version autonome de la scène (page HTML + fichiers MP3) pour répéter sur n'importe quel appareil (smartphone, tablette) sans avoir besoin de Python.

Lancez la commande :
```bash
python export_html.py
```

Cela va créer un dossier `export/` contenant :
- `index.html` : L'interface de répétition.
- `audio/` : Tous les fichiers sons générés.

Il vous suffit de copier ce dossier `export` où vous voulez et d'ouvrir `index.html` dans un navigateur.

## Configuration (Casting)

Vous pouvez configurer les voix (Homme/Femme) associées à chaque personnage en modifiant le fichier `casting.json`.

Exemple :
```json
{
  "roles": {
    "CHRISTIAN": "homme",
    "CAROLINE": "femme"
  }
}
```
