# 🚀 Démarrage Rapide - Fix Upload Infini

## Problème Rencontré

L'upload de documents reste bloqué sur "Upload en cours..." indéfiniment.

## ✅ Solution : Mode Simple (Sans IA)

Le système peut maintenant fonctionner en **mode simplifié** sans avoir besoin d'installer toutes les dépendances IA !

### Étape 1 : Installer les Dépendances Minimales (2 min)

```bash
cd /home/user/finance2

# Installer UNIQUEMENT les modules essentiels
pip install fastapi==0.109.0 uvicorn==0.27.0 sqlalchemy==2.0.25 \
  pydantic==2.6.0 pydantic-settings==2.1.0 python-dotenv==1.0.0 \
  python-multipart==0.0.6 loguru==0.7.2 aiofiles==23.2.1
```

### Étape 2 : Initialiser la Base de Données

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

### Étape 3 : Tester l'Installation

```bash
python test_minimal.py
```

Vous devriez voir :
```
✅ TOUS LES TESTS PASSÉS

Mode SIMPLE disponible (sans IA)
```

### Étape 4 : Démarrer le Backend

```bash
# Toujours depuis /home/user/finance2/backend
python main.py
```

Vous devriez voir :
```
Using SIMPLE processor (no AI dependencies required)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Étape 5 : Tester l'API

Dans un autre terminal :

```bash
# Health check
curl http://localhost:8000/api/health

# Liste des documents
curl http://localhost:8000/api/documents
```

### Étape 6 : Tester l'Upload via le Frontend

1. Dans un autre terminal, lancez le frontend :
   ```bash
   cd /home/user/finance2/frontend
   npm run dev
   ```

2. Ouvrez http://localhost:3000/documents

3. Uploadez un fichier de test

4. **Cette fois, l'upload devrait se terminer en quelques secondes !**

## 🎯 Différences Mode Simple vs Mode Complet

### Mode Simple (Activé par Défaut)
✅ Upload et stockage des documents
✅ Affichage des problématiques
✅ Catégorisation basique par nom de fichier
✅ Liste et statistiques
❌ Pas d'analyse IA du contenu
❌ Pas d'embeddings / recherche sémantique
❌ Pas de transcription audio

**Avantages :**
- Installation rapide (2 min)
- Fonctionne sans clés API
- Parfait pour tester l'interface

### Mode Complet (Optionnel)
✅ Toutes les fonctionnalités du mode simple
✅ Analyse IA du contenu avec Claude
✅ Embeddings et recherche sémantique
✅ Transcription audio avec Whisper
✅ Fact-checking et analyse des angles morts

**Installation :**
```bash
pip install -r requirements.txt
```
(Prend 10-15 minutes)

## 🔍 Vérifications

### Le backend est-il démarré ?

```bash
curl http://localhost:8000/api/health
```

Devrait retourner :
```json
{
  "status": "healthy" ou "degraded",
  "services": {
    "database": "ok",
    "vector_store": "not configured" (normal en mode simple),
    "openai_api": "not configured" (normal en mode simple),
    "anthropic_api": "not configured" (normal en mode simple)
  }
}
```

### Les documents s'uploadent-ils ?

1. Créez un fichier de test :
   ```bash
   echo "Test document" > test.txt
   ```

2. Uploadez via API :
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload \
     -F "file=@test.txt" \
     -F "problematiques=[\"Test problématique\"]"
   ```

3. Vérifiez :
   ```bash
   curl http://localhost:8000/api/documents
   ```

Vous devriez voir votre document avec `"status": "indexed"`

### Voir les Logs

```bash
tail -f /home/user/finance2/logs/app.log
```

Lors de l'upload, vous devriez voir :
```
Using SIMPLE processor for test.txt
Document processed (simple mode): test.txt - Category: other
```

## 🆙 Passer au Mode Complet (Plus Tard)

Quand vous serez prêt pour les fonctionnalités IA complètes :

```bash
cd /home/user/finance2

# 1. Installer toutes les dépendances
pip install -r backend/requirements.txt

# 2. Configurer les clés API dans .env
nano .env
# Ajouter vos vraies clés:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# 3. Redémarrer le backend
cd backend
python main.py
```

Le système détectera automatiquement les modules IA et passera en mode complet :
```
Full AI processor available
Using FULL processor for ...
```

## 📝 Notes

- **Mode Simple :** Parfait pour développer l'interface et tester le workflow
- **Mode Complet :** Nécessaire pour la production avec toutes les analyses IA
- **Transition :** Aucun changement de code nécessaire, juste installer les dépendances

## ❓ Problèmes Fréquents

### "Module not found: fastapi"
```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv
```

### "Table documents doesn't exist"
```bash
cd backend
python init_db.py
```

### Upload toujours bloqué
1. Vérifiez que le backend tourne : `curl http://localhost:8000/api/health`
2. Vérifiez les logs : `tail -f logs/app.log`
3. Redémarrez le backend : Ctrl+C puis `python main.py`
4. Vérifiez les permissions : `chmod -R 755 data/`

### "Cannot connect to backend"
1. Le backend est sur http://localhost:8000
2. Le frontend est sur http://localhost:3000
3. Vérifiez qu'ils tournent tous les deux
4. Vérifiez le proxy dans `frontend/vite.config.ts`

## 🎉 Succès !

Si vous voyez ça, c'est bon :
- ✅ Documents uploadés avec status "indexed"
- ✅ Problématiques stockées et affichées
- ✅ Liste et stats fonctionnelles
- ✅ Pas de blocage à l'upload

Vous pouvez maintenant développer et tester l'interface tranquillement !
