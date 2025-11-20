# Corrections et Améliorations

## Problèmes corrigés

### 1. Base de données locale ✅
- Ajout du champ `problematiques` au modèle Document
- Configuration SQLite pour base de données locale
- Script d'initialisation de la BDD créé

### 2. Problématiques sur les documents ✅
- Ajout d'un modal d'upload avec saisie des problématiques
- Possibilité d'ajouter plusieurs problématiques par document
- Affichage des problématiques dans la liste des documents
- Les problématiques sont stockées en base et indexées

## Installation et Démarrage

### 1. Installer les dépendances

**Backend:**
```bash
# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
cd backend
pip install -r requirements.txt
cd ..
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 2. Configurer les clés API

Éditez le fichier `.env` à la racine et ajoutez vos clés :
```env
OPENAI_API_KEY=sk-votre-clé-openai
ANTHROPIC_API_KEY=sk-ant-votre-clé-anthropic
```

### 3. Initialiser la base de données

```bash
cd backend
source ../venv/bin/activate  # Windows: ..\venv\Scripts\activate
python init_db.py
```

Vous devriez voir :
```
Creating database tables...
Database tables created successfully!
Tables: documents, meetings, transcriptions, alerts, reports
```

### 4. Lancer l'application

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

Accédez à http://localhost:3000

## Nouvelles Fonctionnalités

### Upload de documents avec problématiques

1. Cliquez sur la zone d'upload dans la page Documents
2. Sélectionnez un fichier
3. Une modale s'ouvre avec :
   - Le nom du fichier sélectionné
   - Un champ pour ajouter des problématiques
   - Bouton "Ajouter une problématique" pour en ajouter plusieurs
4. Exemple de problématiques :
   - "Quelle est notre marge opérationnelle Q1 2024?"
   - "Quels sont les principaux risques financiers?"
   - "Avons-nous respecté notre budget marketing?"
5. Cliquez sur "Uploader"

Les problématiques seront :
- Stockées en base de données
- Affichées dans la liste des documents
- Utilisables pour contextualiser les analyses en réunion

### Affichage des problématiques

Dans la liste des documents, sous chaque document, vous verrez :
```
Problématiques :
• Quelle est notre marge opérationnelle Q1 2024?
• Quels sont les principaux risques financiers?
```

## Vérification

### Vérifier la base de données

```bash
sqlite3 data/meetings.db

# Dans sqlite3:
.schema documents
# Vous devriez voir le champ 'problematiques'

.exit
```

### Vérifier les logs

```bash
tail -f logs/app.log
```

### Tester l'upload

1. Créez un fichier test.txt avec du contenu
2. Uploadez-le via l'interface
3. Vérifiez les logs backend
4. Vérifiez que le document apparaît avec status "processing" puis "indexed"

## Résolution de problèmes

### Erreur "Module not found"
```bash
# Réactiver l'environnement et réinstaller
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Erreur "Table doesn't exist"
```bash
# Recréer la base de données
cd backend
python init_db.py --reset
```

### Erreur lors de l'upload
1. Vérifiez les logs : `tail -f logs/app.log`
2. Vérifiez que les répertoires existent : `ls -la data/`
3. Vérifiez les permissions : `chmod -R 755 data/`
4. Vérifiez que vos clés API sont configurées

### Frontend ne connecte pas au backend
1. Vérifiez que le backend tourne : http://localhost:8000/api/health
2. Vérifiez la config CORS dans `.env`
3. Vérifiez le proxy dans `frontend/vite.config.ts`

## Tests rapides

### Test 1: Health Check
```bash
curl http://localhost:8000/api/health
```

Devrait retourner du JSON avec status "healthy"

### Test 2: Upload API
```bash
# Créer un fichier de test
echo "Test document" > test.txt

# Uploader via API
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.txt" \
  -F "problematiques=[\"Problème 1\", \"Problème 2\"]"
```

### Test 3: Liste des documents
```bash
curl http://localhost:8000/api/documents
```

Devrait retourner un tableau JSON des documents avec leurs problématiques.

## Notes importantes

1. **Première utilisation :** Assurez-vous d'avoir vos clés API configurées
2. **Base de données :** SQLite locale dans `data/meetings.db`
3. **Documents :** Stockés dans `data/uploads/`
4. **Embeddings :** Stockés dans `data/vector_db/`
5. **Rapports :** Générés dans `reports/`

## Prochaines étapes

Pour tester le système complet :
1. Uploadez quelques documents avec des problématiques pertinentes
2. Créez une réunion
3. Lancez l'enregistrement (testez avec des phrases simples)
4. Arrêtez et générez le rapport
5. Vérifiez que les problématiques sont prises en compte dans l'analyse
