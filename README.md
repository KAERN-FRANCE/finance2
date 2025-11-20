# Meeting Assistant MVP

Assistant IA pour réunions de direction avec analyse en temps réel et génération de rapports complets.

## Vue d'ensemble

Meeting Assistant est une application web qui utilise l'IA pour :
- **Phase Pré-Réunion** : Indexer et analyser les documents de l'entreprise
- **Phase Temps Réel** : Transcrire et analyser les réunions en direct avec alertes
- **Phase Post-Réunion** : Générer des rapports complets avec fact-checking et analyse des angles morts

## Architecture

```
finance2/
├── backend/           # API FastAPI Python
│   ├── api/          # Routes et endpoints
│   ├── services/     # Logique métier
│   ├── models/       # Modèles de données
│   └── utils/        # Utilitaires
├── frontend/         # Interface React TypeScript
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── types/
├── data/             # Données locales
│   ├── uploads/      # Documents uploadés
│   ├── vector_db/    # Base vectorielle ChromaDB
│   └── reports/      # Rapports générés
└── logs/             # Logs applicatifs
```

## Prérequis

- **Python 3.10+**
- **Node.js 18+** et npm
- **Clés API** :
  - OpenAI API Key (pour Whisper)
  - Anthropic API Key (pour Claude 4.5)

## Installation

### 1. Cloner le projet

```bash
cd finance2
```

### 2. Configuration Backend

```bash
# Créer un environnement virtuel Python
python -m venv venv

# Activer l'environnement
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
cd backend
pip install -r requirements.txt
```

### 3. Configuration Frontend

```bash
cd frontend
npm install
```

### 4. Variables d'environnement

Créer un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditer `.env` et ajouter vos clés API :

```env
# API Keys (OBLIGATOIRE)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Chemins
VECTOR_DB_PATH=./data/vector_db
UPLOAD_DIR=./data/uploads
REPORTS_DIR=./reports
DATABASE_URL=sqlite:///./data/meetings.db

# Serveur
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Limites
MAX_UPLOAD_SIZE_MB=100
MAX_DOCUMENTS=1000
MAX_MEETING_DURATION_HOURS=4

# Audio
AUDIO_CHUNK_DURATION_SECONDS=30
WHISPER_MODEL=whisper-1

# Claude
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Langues
SUPPORTED_LANGUAGES=fr,en
DEFAULT_LANGUAGE=fr
```

## Lancement de l'application

### Option 1 : Développement (2 terminaux)

**Terminal 1 - Backend :**
```bash
cd backend
source ../venv/bin/activate  # ou venv\Scripts\activate sur Windows
python main.py
```

Le backend sera accessible sur `http://localhost:8000`

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
```

Le frontend sera accessible sur `http://localhost:3000`

### Option 2 : Script de lancement (recommandé)

Créer un fichier `start.sh` (Linux/Mac) :

```bash
#!/bin/bash
# Démarrer le backend
cd backend
source ../venv/bin/activate
python main.py &
BACKEND_PID=$!

# Démarrer le frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Attendre Ctrl+C et arrêter proprement
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

Rendre exécutable et lancer :
```bash
chmod +x start.sh
./start.sh
```

## Utilisation

### 1. Phase Pré-Réunion : Gestion des Documents

1. Accédez à `http://localhost:3000/documents`
2. Uploadez vos documents d'entreprise (PDF, DOCX, CSV, XLSX)
3. L'application va :
   - Extraire le texte et les métadonnées
   - Analyser le contenu avec Claude
   - Catégoriser automatiquement
   - Créer des embeddings et indexer dans ChromaDB

**Conseil** : Uploadez vos documents de :
- Finance (bilans, budgets, KPIs)
- Stratégie (plans, projets)
- RH (effectifs, org charts)
- Opérations (processus, SLAs)

### 2. Phase Réunion : Enregistrement et Analyse Temps Réel

1. Créer une nouvelle réunion :
   - Cliquez sur "Nouvelle Réunion"
   - Remplissez le titre, participants, agenda
   - Choisissez la langue (FR/EN)

2. Démarrer l'enregistrement :
   - Cliquez sur "Démarrer l'enregistrement"
   - Autorisez l'accès au microphone
   - La transcription apparaît en temps réel

3. Alertes automatiques :
   - Des alertes s'affichent si des incohérences sont détectées
   - Les affirmations problématiques sont signalées
   - Sources de contradiction indiquées

4. Arrêter la réunion :
   - Cliquez sur "Arrêter"
   - La réunion passe en statut "Complétée"

### 3. Phase Post-Réunion : Génération de Rapport

1. Après avoir arrêté la réunion, cliquez sur "Générer le rapport"
2. L'analyse complète prend quelques minutes :
   - Résumé exécutif
   - Fact-checking de toutes les affirmations
   - Analyse des angles morts (risques, opportunités, contraintes)
   - Recommandations actionnables
3. Le rapport s'affiche avec navigation par sections
4. Exportez en Markdown via le bouton "Télécharger"

## Structure du Rapport

Le rapport généré contient :

### 1. Résumé Exécutif
- Contexte et objectif de la réunion
- Points clés discutés
- Décisions prises
- Actions à suivre
- Conclusion

### 2. Vérification des Faits
- Statistiques d'exactitude
- Liste des affirmations vérifiées
- Contradictions détectées avec sources
- Score de confiance pour chaque fait

### 3. Analyse des Angles Morts

**Risques Non Mentionnés**
- Type (financier, opérationnel, légal, etc.)
- Probabilité et impact
- Description détaillée

**Opportunités Manquées**
- Synergies possibles
- Optimisations
- Innovations
- Valeur potentielle

**Solutions Alternatives**
- Approches non évoquées
- Avantages/inconvénients
- Faisabilité

**Contraintes Oubliées**
- Légales/réglementaires
- Techniques
- Budgétaires
- Temporelles
- Ressources humaines
- Infrastructure

**Stakeholders Non Considérés**
- Parties prenantes impactées mais non mentionnées

**Points d'Amélioration**
- Comment améliorer les propositions faites

### 4. Recommandations
Classées par priorité (Haute/Moyenne/Basse) :
- Description de la recommandation
- Justification
- Impact attendu
- Catégorie (stratégie, opérations, risques, etc.)

### 5. Transcription Complète
- Avec timestamps
- Segmentée par intervenant (si détecté)

## API Endpoints

### Documents
```
POST   /api/documents/upload     - Upload un document
GET    /api/documents            - Liste tous les documents
GET    /api/documents/stats      - Statistiques
GET    /api/documents/{id}       - Détails d'un document
DELETE /api/documents/{id}       - Supprimer un document
```

### Meetings
```
POST   /api/meetings                    - Créer une réunion
GET    /api/meetings                    - Liste des réunions
GET    /api/meetings/{id}               - Détails d'une réunion
PUT    /api/meetings/{id}               - Mettre à jour
DELETE /api/meetings/{id}               - Supprimer
POST   /api/meetings/{id}/start         - Démarrer l'enregistrement
POST   /api/meetings/{id}/stop          - Arrêter
POST   /api/meetings/{id}/audio         - Upload chunk audio
GET    /api/meetings/{id}/transcription - Récupérer transcription
GET    /api/meetings/{id}/alerts        - Récupérer alertes
POST   /api/meetings/{id}/generate-report - Générer rapport
```

### Reports
```
GET /api/reports/{id}              - Récupérer un rapport
GET /api/reports/{id}/markdown     - Export markdown
GET /api/reports/meeting/{id}      - Rapports d'une réunion
```

### WebSocket
```
WS /ws/meeting/{id}  - Connexion temps réel pour transcription et alertes
```

### Health & Config
```
GET /api/health  - Health check
GET /api/config  - Configuration exposée au frontend
```

## Dépannage

### Erreur "Module not found"
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Erreur "Port already in use"
Modifiez le port dans `.env` (backend) ou `vite.config.ts` (frontend)

### Erreur "API Key invalid"
Vérifiez que vos clés API sont correctement configurées dans `.env`

### ChromaDB errors
Supprimez et recréez la base vectorielle :
```bash
rm -rf data/vector_db/*
# Puis réuploadez vos documents
```

### Microphone non détecté
- Vérifiez les permissions du navigateur
- Utilisez HTTPS ou localhost (requis pour WebRTC)
- Testez avec un autre navigateur (Chrome recommandé)

## Limitations du MVP

- **Scalabilité** : Optimisé pour moyenne entreprise (quelques Go de documents)
- **Diarisation** : Identification des intervenants basique
- **Langues** : Français et anglais principalement
- **Sécurité** : Authentification simple, à renforcer pour production
- **Déploiement** : Configuration pour environnement local/dev

## Améliorations Futures

1. **Authentification robuste** (OAuth, SSO)
2. **Support multilingue étendu**
3. **Diarisation avancée** (reconnaissance vocale des participants)
4. **Intégrations** (Slack, Teams, Calendar)
5. **Dashboard analytics** (tendances, métriques agrégées)
6. **Exports enrichis** (PDF formaté, PowerPoint)
7. **Migration vers OpenAI Assistants API** (agents IA)
8. **Déploiement cloud** (Docker, Kubernetes)

## Support

Pour toute question ou problème :
1. Vérifiez les logs : `logs/app.log`
2. Consultez la documentation API : `http://localhost:8000/docs`
3. Vérifiez l'état de santé : `http://localhost:8000/api/health`

## Technologies Utilisées

**Backend:**
- FastAPI (API REST)
- SQLAlchemy (ORM)
- ChromaDB (Vector Store)
- Anthropic Claude 4.5 (LLM)
- OpenAI Whisper (Transcription)
- Sentence Transformers (Embeddings)

**Frontend:**
- React 18 + TypeScript
- TailwindCSS
- React Query
- Zustand
- Socket.io
- React Router

**Processing:**
- PyPDF2 / pdfplumber (PDF)
- python-docx (DOCX)
- pandas (CSV/XLSX)
- WebRTC (Audio)

## Licence

Propriétaire - Usage interne uniquement
