# Guide de Démarrage Rapide - Meeting Assistant

## Installation en 5 minutes

### 1. Prérequis
- Python 3.10+
- Node.js 18+
- Clés API OpenAI et Anthropic

### 2. Installation des dépendances

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 3. Configuration

Créer `.env` à la racine :
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Lancement

**Terminal 1 - Backend:**
```bash
cd backend
source ../venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Accès

Ouvrir http://localhost:3000

## Workflow Typique

1. **Uploader des documents** (page Documents)
   - PDFs, DOCX, CSV, XLSX
   - Attendre indexation complète

2. **Créer une réunion** (Nouvelle Réunion)
   - Titre + Participants + Agenda
   - Choisir langue (FR/EN)

3. **Enregistrer la réunion**
   - Démarrer enregistrement
   - Voir transcription temps réel
   - Observer alertes automatiques
   - Arrêter l'enregistrement

4. **Générer le rapport**
   - Cliquer "Générer le rapport"
   - Attendre analyse (2-5 min)
   - Consulter résultats
   - Exporter en Markdown

## Résolution Rapide

**Backend ne démarre pas :**
- Vérifier que le port 8000 est libre
- Vérifier les clés API dans `.env`
- Vérifier que l'environnement virtuel est activé

**Frontend ne démarre pas :**
- `npm install` dans frontend/
- Vérifier que le port 3000 est libre

**Microphone ne fonctionne pas :**
- Utiliser Chrome (recommandé)
- Autoriser l'accès microphone
- Utiliser HTTPS ou localhost

**Documents ne s'indexent pas :**
- Vérifier les logs : `logs/app.log`
- Vérifier format de fichier supporté
- Vérifier taille < 100MB

## Exemple de Test

1. Upload un document PDF (ex: rapport financier)
2. Créer une réunion "Test Q1"
3. Dire quelques phrases avec des chiffres
4. Arrêter et générer le rapport
5. Vérifier le fact-checking et les recommandations

## Liens Utiles

- Documentation API: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
- Frontend: http://localhost:3000
