# Installation Rapide - Meeting Assistant

## Problème Rencontré

Erreur 500 lors de l'accès à `/api/documents` → Les dépendances Python ne sont pas installées.

## Solution en 3 Étapes

### Étape 1 : Installer les dépendances Python

Ouvrez un terminal et exécutez :

```bash
cd /home/user/finance2

# Option A : Installation complète (recommandé mais plus long - 5-10 min)
pip install -r backend/requirements.txt

# Option B : Installation minimale pour tester (rapide - 1 min)
pip install fastapi==0.109.0 uvicorn==0.27.0 sqlalchemy==2.0.25 \
  pydantic==2.6.0 pydantic-settings==2.1.0 python-dotenv==1.0.0 \
  python-multipart==0.0.6 loguru==0.7.2 aiofiles==23.2.1

# Pour IA/Embeddings (optionnel, à installer plus tard) :
# pip install anthropic==0.18.1 openai==1.12.0 chromadb==0.4.22 \
#   sentence-transformers==2.3.1 PyPDF2==3.0.1 pdfplumber==0.10.3 \
#   python-docx==1.1.0 pandas==2.2.0 openpyxl==3.1.2 langdetect==1.0.9
```

### Étape 2 : Initialiser la base de données

```bash
cd backend
python init_db.py
```

Vous devriez voir :
```
Creating database tables...
Database tables created successfully!
Tables: documents, meetings, transcriptions, alerts, reports
```

### Étape 3 : Configurer les clés API

Éditez le fichier `.env` à la racine :

```bash
nano ../.env  # ou vi, code, etc.
```

Remplacez par vos vraies clés :
```env
OPENAI_API_KEY=sk-votre-vraie-clé-openai
ANTHROPIC_API_KEY=sk-ant-votre-vraie-clé-anthropic
```

### Étape 4 : Démarrer le backend

```bash
# Depuis /home/user/finance2/backend
python main.py
```

Vous devriez voir :
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Étape 5 : Démarrer le frontend (dans un autre terminal)

```bash
cd /home/user/finance2/frontend
npm install  # Si pas déjà fait
npm run dev
```

### Vérification

1. **Backend Health Check :**
   ```bash
   curl http://localhost:8000/api/health
   ```
   Devrait retourner du JSON avec `"status": "healthy"` ou `"degraded"`

2. **Liste des documents :**
   ```bash
   curl http://localhost:8000/api/documents
   ```
   Devrait retourner `[]` (liste vide) si OK

3. **Frontend :**
   Ouvrez http://localhost:3000/documents dans votre navigateur

## Commandes Utiles

### Vérifier l'installation des modules

```bash
python -c "import fastapi, sqlalchemy; print('✓ Modules de base OK')"
```

### Voir les logs en temps réel

```bash
tail -f /home/user/finance2/logs/app.log
```

### Reset de la base de données

```bash
cd /home/user/finance2/backend
python init_db.py --reset
# Tapez 'yes' pour confirmer
```

### Vérifier la base de données

```bash
sqlite3 /home/user/finance2/data/meetings.db

# Dans sqlite3:
.tables                    # Voir les tables
.schema documents          # Voir la structure de la table documents
SELECT * FROM documents;   # Voir les documents
.exit
```

## Résolution de Problèmes

### Erreur "Module not found"

```bash
# Réinstaller les dépendances
pip install -r backend/requirements.txt
```

### Erreur "Port already in use"

```bash
# Trouver et tuer le processus sur le port 8000
lsof -ti:8000 | xargs kill -9

# Ou changer le port dans .env:
PORT=8001
```

### Erreur "Permission denied" pour la BDD

```bash
chmod -R 755 /home/user/finance2/data
```

### L'upload de documents ne fonctionne toujours pas

1. Vérifiez que les modules IA sont installés :
   ```bash
   python -c "import anthropic, openai; print('IA modules OK')"
   ```

2. Si non, installez-les :
   ```bash
   pip install anthropic openai chromadb sentence-transformers \
     PyPDF2 pdfplumber python-docx pandas openpyxl langdetect
   ```

3. Redémarrez le backend

## Installation Complète Recommandée

Pour une installation complète avec toutes les fonctionnalités :

```bash
cd /home/user/finance2

# 1. Backend
pip install -r backend/requirements.txt
cd backend
python init_db.py
cd ..

# 2. Frontend
cd frontend
npm install
cd ..

# 3. Configuration
# Éditer .env avec vos clés API

# 4. Lancer (2 terminaux)
# Terminal 1:
cd backend && python main.py

# Terminal 2:
cd frontend && npm run dev
```

## Notes

- **Sans clés API :** Le système fonctionnera mais sans transcription ni analyse IA
- **Installation minimale :** Permet de tester l'interface et la BDD sans IA
- **Installation complète :** Nécessaire pour toutes les fonctionnalités (transcription, analyse, rapports)

## Support

Si vous rencontrez d'autres erreurs, vérifiez :
1. Les logs : `tail -f logs/app.log`
2. L'API Docs : http://localhost:8000/docs
3. Le health check : http://localhost:8000/api/health
