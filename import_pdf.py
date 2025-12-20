import sys
import os
import re
from pypdf import PdfReader

RAW_DIR = "raw_extracts"

def clean_text(text):
    # Suppression des numéros de page isolés
    lines = text.split('\n')
    lines = [l for l in lines if not l.strip().isdigit()]
    
    # Fusion des lignes pour gérer les coupures arbitraires
    full_text = " ".join([l.strip() for l in lines])
    full_text = re.sub(r'\s+', ' ', full_text)

    # Insertion de sauts de ligne avant les Personnages (heuristique)
    # Pattern : Majuscules (min 2 lettres) + optionnel parenthèses + point
    speaker_pattern = r'([A-ZÀ-ÖØ-Þ\-\s\'’]{2,}(?:\s*\(.*?\))?)\.'
    
    def replace_speaker(match):
        return "\n\n" + match.group(1) + "."

    formatted_text = re.sub(speaker_pattern, replace_speaker, full_text)
    return formatted_text

def extract_pdf_text(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Erreur : Fichier {pdf_path} introuvable.")
        return

    print(f"Lecture du PDF : {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"Erreur PDF : {e}")
        return

    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    print("Nettoyage du texte...")
    final_text = clean_text(full_text)

    # Création du dossier de sortie
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(RAW_DIR, f"{base_name}.txt")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
        
    print(f"Succès ! Texte complet extrait vers : {output_path}")
    print("Vous pouvez maintenant copier-coller les scènes qui vous intéressent pour les convertir en JSON.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python import_pdf.py <fichier.pdf>")
    else:
        extract_pdf_text(sys.argv[1])
