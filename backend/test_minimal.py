#!/usr/bin/env python3
"""
Script de test minimal pour vérifier que le backend fonctionne
sans toutes les dépendances IA.
"""
import sys

def test_imports():
    """Test des imports minimaux."""
    print("🔍 Test des imports...")

    try:
        import fastapi
        print("  ✅ FastAPI")
    except ImportError:
        print("  ❌ FastAPI - pip install fastapi")
        return False

    try:
        import sqlalchemy
        print("  ✅ SQLAlchemy")
    except ImportError:
        print("  ❌ SQLAlchemy - pip install sqlalchemy")
        return False

    try:
        import pydantic
        print("  ✅ Pydantic")
    except ImportError:
        print("  ❌ Pydantic - pip install pydantic")
        return False

    # Optional AI modules
    ai_modules_ok = True
    try:
        import anthropic
        print("  ✅ Anthropic")
    except ImportError:
        print("  ⚠️  Anthropic (optionnel) - mode simple activé")
        ai_modules_ok = False

    try:
        import chromadb
        print("  ✅ ChromaDB")
    except ImportError:
        print("  ⚠️  ChromaDB (optionnel) - mode simple activé")
        ai_modules_ok = False

    if ai_modules_ok:
        print("\n💡 Mode COMPLET disponible (avec IA)")
    else:
        print("\n💡 Mode SIMPLE disponible (sans IA)")
        print("   Pour le mode complet: pip install -r requirements.txt")

    return True

def test_database():
    """Test de la base de données."""
    print("\n🗄️  Test de la base de données...")

    try:
        from backend.models.database import init_db, SessionLocal, DocumentModel

        # Initialize DB
        init_db()
        print("  ✅ Tables créées")

        # Test connection
        db = SessionLocal()
        count = db.query(DocumentModel).count()
        db.close()
        print(f"  ✅ Connection OK ({count} documents)")

        return True
    except Exception as e:
        print(f"  ❌ Erreur BDD: {e}")
        return False

def test_config():
    """Test de la configuration."""
    print("\n⚙️  Test de la configuration...")

    try:
        from backend.config import settings

        print(f"  ℹ️  Upload dir: {settings.upload_dir}")
        print(f"  ℹ️  Vector DB: {settings.vector_db_path}")
        print(f"  ℹ️  Database: {settings.database_url}")

        # Check API keys
        if settings.openai_api_key and "your-key" not in settings.openai_api_key:
            print("  ✅ OpenAI API key configurée")
        else:
            print("  ⚠️  OpenAI API key non configurée")

        if settings.anthropic_api_key and "your-key" not in settings.anthropic_api_key:
            print("  ✅ Anthropic API key configurée")
        else:
            print("  ⚠️  Anthropic API key non configurée")

        return True
    except Exception as e:
        print(f"  ❌ Erreur config: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Test Minimal du Backend Meeting Assistant")
    print("=" * 60)

    all_ok = True

    if not test_imports():
        all_ok = False

    if not test_config():
        all_ok = False

    if not test_database():
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ TOUS LES TESTS PASSÉS")
        print("\n💡 Vous pouvez démarrer le backend:")
        print("   python main.py")
        print("\n   Puis testez: http://localhost:8000/api/health")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("\n📋 Vérifiez:")
        print("   1. Les dépendances: pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv loguru")
        print("   2. Le fichier .env avec vos clés API")
        print("   3. Les permissions sur le répertoire data/")
        return 1

if __name__ == "__main__":
    sys.exit(main())
