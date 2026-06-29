
## Installation et Configuration

### 1. Configurer les variables d'environnement
Copiez le fichier exemple `.env.example` pour créer votre fichier `.env` :
```bash
cp .env.example .env
```
Ouvrez le fichier `.env` et ajoutez votre clé API Groq :
```env
GROQ_API_KEY=gsk_votre_cle_api_ici
```

### 2. Lancer l'installation automatique
Le projet utilise un `Makefile` et un script de construction automatique. Lancez simplement la commande suivante :
```bash
make build
```
Cette commande crée automatiquement l'environnement virtuel (`linux_venv`) et y installe toutes les dépendances.

---

## Utilisation

### Lancer l'interface de visualisation (Dashboard)
Pour démarrer le dashboard interactif Streamlit :
```bash
make dashboard
```

### Lancer la simulation manuellement en ligne de commande
Si vous souhaitez exécuter la simulation directement en tâche de fond :
```bash
make simulate
```
Les résultats seront automatiquement enregistrés dans la base de données SQLite locale `election.db`.
