# 🚨 Risk Monitor

## Présentation du projet

Ce projet contient ma proposition de solution dans le temps imparti au problème d'analyse de données des abonnés à risques pour l'équipe support et opérations.

Risk Monitor est une application web interne qui centralise l'analyse des abonnés à risque, permettant d'identifier, scorer et traiter les cas suspects de manière semi-automatique. L'objectif est de détecter les utilisateurs ayant plus de 40% d'échecs sur leurs 3 derniers paiements et d'autres patterns de risque.

## 🎯 Fonctionnalités

### ✅ Phase 1 - MVP (Implémentée)
- **Modèles de données** : User, Subscription, Paiement 
- **Calcul de risque** : Algorithme pondéré détectant les patterns à risque
- **API REST** : Endpoints pour lister, analyser et alerter
- **Dashboard Streamlit** : Interface web avec filtres et visualisations
- **Auto-initialisation** : Population automatique de la base de données

### 🔄 Patterns de risque détectés
- **Pattern classique** : "Paient une fois, puis déclinent les paiements suivants"
- **Échecs récents** : Plus de 40% d'échecs sur les 3 derniers paiements
- **Downgrade** : Passage vers un abonnement moins cher (signal de départ)
- **Abonnements bas coût** : Montants faibles = risque de churn élevé

## 🚀 Installation et démarrage

### Prérequis
- Python 3.8+
- PostgreSQL (via Docker recommandé)
- Git

### 1. Installation de l'environnement Python

```bash
# Cloner le projet
git clone <url-du-repo>
cd "Risk Monitor"

# Créer l'environnement virtuel (IMPORTANT: laisser 'env')
python -m venv env

# Activer l'environnement virtuel
# Sur Windows :
.\env\Scripts\activate
# Sur Linux/Mac :
source env/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration de la base de données PostgreSQL

#### Option A : Avec Docker (Recommandé)
```bash
# Démarrer PostgreSQL via Docker
.\start_postgres.bat

# Ou manuellement :
docker run --name risk-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=risk_monitor -p 5432:5432 -d postgres:15
```

#### Option B : Installation locale
1. Installer PostgreSQL localement
2. Créer une base de données `risk_monitor`
3. Adapter l'URL dans `config.env` si nécessaire

### 3. Configuration des variables d'environnement

Le fichier `config.env` est déjà configuré pour un usage local :
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/risk_monitor
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
HIGH_RISK_THRESHOLD=0.4
CRITICAL_RISK_THRESHOLD=0.7
```

### 4. Démarrage de l'application(Rassurez vous d'avoir lancé la base de données postgres avant)

#### Démarrage automatique (Recommandé)
```bash
# Démarre l'API et le dashboard automatiquement
.\start_all.bat
```

#### Démarrage manuel 
```bash
# Terminal 1 : API Backend
cd backend
python populate_db.py # Générer des données de test
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Dashboard Frontend
streamlit run frontend/app.py --server.port 8501
```

### 5. Accès aux services

- **API FastAPI** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Dashboard Streamlit** : http://localhost:8501

## 📊 Utilisation

### Dashboard principal
1. **Vue d'ensemble** : Statistiques globales et distribution des risques
2. **Liste des utilisateurs à risque** : Tableau filtrable avec scores et possibiliter de rechercher un nom ou email
3. **Analyse détaillée** : Historique des abonnements et paiements
4. **Actions** : Envoi d'alertes pour les cas critiques

### API Endpoints
- `GET /` : Health check
- `GET /api/risky-users` : Liste des utilisateurs à risque
- `GET /api/user/{user_id}/risk-analysis` : Analyse détaillée d'un utilisateur
- `GET /api/stats` : Statistiques globales du système
- `POST /api/alert/{user_id}` : Envoyer une alerte

## 🏗️ Architecture technique

### Backend (FastAPI)
```
backend/
├── main.py              # Point d'entrée API
├── risk_calculator.py   # Logic métier de calcul de risque
├── database/
│   ├── database.py      # Configuration SQLAlchemy
│   ├── models.py        # Modèles de données
│   └── schemas.py       # Schémas Pydantic
├── populate_db.py       # Génération de données de test
└── test/               # Scripts de test
```

### Frontend (Streamlit)
```
frontend/
└── app.py              # Dashboard principal
```

### Base de données
- **PostgreSQL** avec SQLAlchemy ORM
- **3 tables principales** : users, user_subscriptions, subscription_payments
- **Support temporal** : évolution des abonnements dans le temps

## 🧪 Tests et développement

### Scripts de test disponibles

```bash
# Reset necessaire de la db avant les tests
python backend/reset_db.py

# Test du calculateur de risque
python backend/test/test_risk_calculator.py

# Test de connectivité DB
python backend/test/test_db.py

# Test des endpoints API
python backend/test/test_api.py

# Génération de données volumineuses
python backend/test/generate_test_data.py
```

### Reset de la base de données
```bash
# En cas de changement de schéma
python backend/reset_db.py
```

### Population manuelle de données
```bash
# Données persistantes pour l'API
python backend/populate_db.py
```

## 📱 Interface responsive

L'interface s'adapte automatiquement aux différentes tailles d'écran :
- **Desktop** : Vue complète avec tableaux
- **Mobile/Tablet** : Vue compacte avec format de liste
- **Option de basculement** : Vue compacte/tableau selon les préférences

## ⚙️ Configuration avancée

### Seuils de risque
Modifiables dans `config.env` et `risk_calculator.py` :
- `HIGH_RISK_THRESHOLD=0.4` (40%)
- `CRITICAL_RISK_THRESHOLD=0.7` (70%)

### Algorithme de calcul de risque
Poids des facteurs dans `risk_calculator.py` :
- **Échecs récents(sur les 3 derniers paiements)** : 50% (critère principal)
- **Montant/Downgrade** : 20% (indicateur de churn)
- **Taux global d'échec** : 15%
- **Pattern spécifique** : 10% ("pay once then decline")
- **Âge du compte** : 5%

## 🔮 Fonctionnalités futures (Roadmap)

### Phase 2 - Améliorations
- [ ] Intégration Slack pour alertes automatiques
- [ ] Filtres avancés (par email, score, type d'abonnement)
- [ ] Déploiement automatique en ligne via Render, Railway
- [ ] Rapports automatiques journaliers
- [ ] Meilleure interface graphique pour faciliter le travail de l'équipe support
- [ ] Automatisation et Exports vers des outils BI plus poussés(AirTable, Google Sheets, Tableau, ...)
- [ ] Bouton "sanctionner" → API Sharesub ou Notion pour créer une tâche modération

### Phase 3 - Intelligence
- [ ] Machine Learning pour prédiction de churn
- [ ] Scoring avancé avec ML
- [ ] Détection d'anomalies automatique
- [ ] Recommandations d'actions personnalisées

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework API moderne et rapide
- **SQLAlchemy** : ORM pour PostgreSQL
- **Pydantic** : Validation et sérialisation des données
- **PostgreSQL** : Base de données relationnelle

### Frontend
- **Streamlit** : Framework de dashboard Python
- **Plotly** : Visualisations interactives
- **Pandas** : Manipulation de données

### DevOps
- **Docker** : Containerisation PostgreSQL
- **python-dotenv** : Gestion des variables d'environnement
- **Uvicorn** : Serveur ASGI pour FastAPI

## 📈 Métriques et KPIs

L'application track automatiquement :
- **Nombre total d'utilisateurs**
- **Pourcentage d'utilisateurs à haut risque**
- **Taux d'échec global des paiements**
- **Distribution des scores de risque**
- **Évolution temporelle des patterns**

## 🔧 Troubleshooting

### Problèmes courants

**1. Erreur de connexion PostgreSQL**
```bash
# Vérifier que PostgreSQL est démarré
docker ps | grep postgres

# Redémarrer si nécessaire
docker restart risk-postgres
```

**2. ModuleNotFoundError**
```bash
# Vérifier l'activation de l'environnement virtuel
.\env\Scripts\activate
pip install -r requirements.txt
```

**3. Port déjà utilisé**
```bash
# Changer les ports dans config.env ou start_all.bat
API_PORT=8001
```

**4. Base de données vide**
```bash
# L'application se peuple automatiquement au premier démarrage
# Ou manuellement :
python backend/populate_db.py
```

## 📝 Logs et débogage

### Activation du mode debug
Dans `config.env` :
```env
DEBUG=True
```

### Logs de l'API
L'API FastAPI affiche les logs en temps réel lors du démarrage avec `--reload`.

### Logs Streamlit
Streamlit affiche les erreurs dans la console et l'interface web.

## 🤝 Contribution

### Structure de développement
1. **Backend** : Logic métier dans `risk_calculator.py`
2. **Modèles** : Extensions dans `database/models.py`
3. **API** : Nouveaux endpoints dans `main.py`
4. **Frontend** : Améliorations UI dans `frontend/app.py`

### Bonnes pratiques
- Tests unitaires pour chaque nouvelle fonctionnalité
- Documentation des endpoints API
- Validation Pydantic pour tous les inputs
- Gestion d'erreurs explicite

### Utilisation de l’IA
Pour optimiser le temps de développement et garantir la qualité du code,
j’ai utilisé l’assistance d’une intelligence artificielle pour :
• Générer des données factices pour la base de données
• Tester les différentes fonctionnalités au fur et a mesure du developpement
• Rédiger la documentation technique (README.md)
• Fluidifier et accélérer le développement des interfaces avec Streamlit

Toutes les décisions techniques du projet ont été choisies, validées et adaptées par mes soins.
 
**Date** : Août 2025  
**Version** : 1.0.0 (MVP)