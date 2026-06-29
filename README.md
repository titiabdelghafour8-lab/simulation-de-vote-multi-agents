# 🗳️ Simulation de Vote Multi-Agents (Méthode Delphi)

Ce projet est une plateforme de simulation et de modélisation de délibérations collectives. Il simule des agents électeurs (personas) qui débattent et réévaluent leurs intentions de vote au fil de plusieurs tours de scrutin (Méthode Delphi) sous l'influence des résumés de débats générés par l'IA.

---

## 🛠️ Pile Technique

* **Langage** : Python 3
* **Orchestration LLM & Prompts** : LangChain
* **Modèle d'IA & Inférence** : Llama-3.1 (via l'API Groq et ses processeurs LPU ultra-rapides)
* **Structure & Validation** : Pydantic
* **Stockage & Persistance** : SQLite
* **Visualisation & Dashboard** : Streamlit & Altair

---

## 📁 Structure du Projet

```
PFA PROJECT/
├── .streamlit/
│   └── config.toml           # Style et thèmes Streamlit
├── config.json               # Manifestes des candidats et profils des personas
├── dashboard.py              # Application principale (Dashboard de visualisation)
├── database.py               # Gestion de la base de données SQLite
├── simulation.py             # Moteur de simulation Delphi
├── requirements.txt          # Dépendances du projet
├── .env.example              # Modèle de configuration pour la clé API
├── .gitignore                # Fichiers à exclure pour Git
└── README.md                 # Ce guide de documentation
```

---

## 🚀 Installation et Configuration

### 1. Cloner le Projet
```bash
git clone <url_de_votre_depot>
cd "PFA PROJECT"
```

### 2. Configurer les variables d'environnement
Copiez le fichier exemple `.env.example` pour créer votre fichier `.env` :
```bash
cp .env.example .env
```
Ouvrez le fichier `.env` et ajoutez votre clé API Groq :
```env
GROQ_API_KEY=gsk_votre_cle_api_ici
```

### 3. Installer les dépendances
Nous vous recommandons de créer un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Utilisation

### Lancer l'interface de visualisation (Dashboard)
Pour démarrer le dashboard interactif Streamlit :
```bash
streamlit run dashboard.py
```
L'interface s'ouvrira automatiquement dans votre navigateur. Vous pourrez :
* Lancer une nouvelle simulation de vote en direct.
* Parcourir l'historique de chaque simulation round par round.
* Analyser le raisonnement de chaque agent et tracer l'évolution de ses choix.
* Exporter les données au format CSV.

### Lancer la simulation manuellement
Si vous souhaitez exécuter la simulation directement en ligne de commande :
```bash
python3 simulation.py
```
Les résultats seront automatiquement ajoutés à la base de données SQLite locale `election.db`.
