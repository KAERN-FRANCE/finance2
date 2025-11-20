#!/bin/bash

# Meeting Assistant - Script de démarrage
echo "🚀 Démarrage de Meeting Assistant..."

# Vérifier que l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Exécutez d'abord:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   cd backend && pip install -r requirements.txt"
    exit 1
fi

# Vérifier que .env existe
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env non trouvé. Copiez .env.example vers .env et configurez vos clés API."
    exit 1
fi

# Démarrer le backend
echo "📡 Démarrage du backend..."
cd backend
source ../venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
sleep 3

# Démarrer le frontend
echo "🎨 Démarrage du frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application démarrée !"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"

# Attendre Ctrl+C et arrêter proprement
trap "echo '🛑 Arrêt de l\'application...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM

wait
