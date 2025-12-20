# Outil de Répétition de Théâtre

Ce petit outil permet de répéter un rôle en donnant la réplique. Il lit le texte des autres personnages avec une voix naturelle (Google TTS) et attend votre intervention.

## Prérequis

- Python 3 installé
- Une connexion internet (pour la génération de voix)

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

Pour lancer une répétition, utilisez la commande suivante :

```bash
python repetition.py <chemin_du_fichier_scene> <NOM_DU_PERSONNAGE>
```

### Exemple

Pour répéter le rôle de **Christian** dans la scène `mariage.txt` :

```bash
python repetition.py scenes/mariage.txt CHRISTIAN
```

## Fonctionnement

- Le script lit le fichier texte ligne par ligne.
- Il détecte les personnages (format `NOM. Texte...`).
- Il prononce à voix haute les répliques des autres personnages.
- Quand c'est à votre tour, il s'arrête et affiche `(C'est à vous !)`.
- Dites votre texte, puis appuyez sur **Entrée** pour vérifier et continuer.
