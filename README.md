# Application Web Simple

Une application web simple utilisant Flask et Gunicorn.

## Installation

1. Créer un environnement virtuel :
```bash
python -m venv venv
```

2. Activer l'environnement virtuel :
- Windows :
```bash
.\venv\Scripts\activate
```
- Linux/Mac :
```bash
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

Pour lancer l'application avec Gunicorn :
```bash
gunicorn app:app
```

L'application sera accessible à l'adresse : http://localhost:8000 