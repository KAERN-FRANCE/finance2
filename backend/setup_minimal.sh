#!/bin/bash

# Script d'installation rapide des dépendances essentielles

echo "🔧 Installation des dépendances essentielles du backend..."

# Dépendances minimales pour faire tourner le backend
pip install --no-cache-dir \
  fastapi==0.109.0 \
  uvicorn==0.27.0 \
  sqlalchemy==2.0.25 \
  pydantic==2.6.0 \
  pydantic-settings==2.1.0 \
  python-dotenv==1.0.0 \
  python-multipart==0.0.6 \
  loguru==0.7.2

echo ""
echo "✅ Dépendances de base installées"
echo ""
echo "Pour installer les dépendances complètes (IA, embeddings, etc.):"
echo "pip install -r requirements.txt"
echo ""
echo "Initialisation de la base de données..."
python init_db.py

echo ""
echo "✅ Setup terminé !"
echo ""
echo "Pour démarrer le backend:"
echo "python main.py"
