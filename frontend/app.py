"""
Risk Monitor - Streamlit Dashboard
Interface utilisateur pour visualiser les utilisateurs à risque
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configuration de la page
st.set_page_config(
    page_title="Risk Monitor",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration API
API_BASE = "http://localhost:8000"

# CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ff4b4b;
    }
    .high-risk { border-left-color: #ff4b4b; }
    .medium-risk { border-left-color: #ffa500; }
    .low-risk { border-left-color: #00cc00; }
    
    .stDataFrame {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)  # Cache pendant 1 minute
def fetch_risky_users(min_risk_score=0.4, limit=100):
    """Récupérer les utilisateurs à risque depuis l'API"""
    try:
        response = requests.get(f"{API_BASE}/api/risky-users", 
                              params={"min_risk_score": min_risk_score, "limit": limit})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("🚫 Impossible de se connecter à l'API. Assurez-vous qu'elle est démarrée.")
        return []
    except Exception as e:
        st.error(f"Erreur: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_user_analysis(user_id):
    """Récupérer l'analyse détaillée d'un utilisateur"""
    try:
        response = requests.get(f"{API_BASE}/api/user/{user_id}/risk-analysis")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Erreur lors de l'analyse: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_stats():
    """Récupérer les statistiques globales"""
    try:
        response = requests.get(f"{API_BASE}/api/stats")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Erreur statistiques: {e}")
        return None

def send_alert(user_id):
    """Envoyer une alerte pour un utilisateur"""
    try:
        response = requests.post(f"{API_BASE}/api/alert/{user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Erreur envoi alerte: {e}")
        return None

def main():
    # Header
    st.title("🚨 Risk Monitor Dashboard")
    st.markdown("**Surveillance des abonnés à risque - Plateforme de partage**")
    
    # Sidebar pour les filtres
    st.sidebar.header("🔍 Filtres")
    
    # Seuil de risque
    risk_threshold = st.sidebar.slider(
        "Seuil de risque minimum (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        help="Afficher les utilisateurs avec un score de risque supérieur à ce seuil"
    )
    
    # Nombre max d'utilisateurs
    max_users = st.sidebar.selectbox(
        "Nombre maximum d'utilisateurs",
        [10, 25, 50, 100, 200],
        index=2
    )
    
    # Bouton de rafraîchissement
    if st.sidebar.button("🔄 Actualiser", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Récupération des données
    with st.spinner("📡 Chargement des données..."):
        risky_users = fetch_risky_users(risk_threshold/100, max_users)
        stats = fetch_stats()
    
    if not risky_users:
        st.warning("Aucun utilisateur à risque trouvé ou problème de connexion API.")
        return
    
    # Métriques principales
    st.header("📊 Vue d'ensemble")
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="👥 Utilisateurs totaux",
                value=stats["total_users"]
            )
        
        with col2:
            st.metric(
                label="🚨 Utilisateurs à risque",
                value=stats["high_risk_users"],
                delta=f"{stats['high_risk_users']/stats['total_users']*100:.1f}%" if stats['total_users'] > 0 else "0%"
            )
        
        with col3:
            st.metric(
                label="💳 Taux d'échec global",
                value=f"{stats['overall_failure_rate']*100:.1f}%",
                delta=f"Objectif: <40%",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                label="🎯 Score de risque moyen",
                value=f"{stats['avg_risk_score']*100:.1f}%"
            )
    
    # Graphiques
    if len(risky_users) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Distribution des scores de risque")
            
            # Graphique en barres des scores de risque
            df_risk = pd.DataFrame(risky_users)
            fig_risk = px.histogram(
                df_risk, 
                x='risk_score',
                nbins=20,
                title="Répartition des scores de risque",
                labels={'risk_score': 'Score de risque', 'count': 'Nombre d\'utilisateurs'},
                color_discrete_sequence=['#ff4b4b']
            )
            fig_risk.update_layout(height=400)
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Répartition par type d'abonnement")
            
            # Graphique camembert par type de subscription
            subscription_counts = df_risk['subscription_type'].value_counts()
            fig_pie = px.pie(
                values=subscription_counts.values,
                names=subscription_counts.index,
                title="Types d'abonnements à risque",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Liste des utilisateurs à risque
    st.header("👥 Utilisateurs à risque")
    
    # Création du DataFrame pour l'affichage
    if risky_users:
        df_users = pd.DataFrame(risky_users)
        
        # Formatage des colonnes
        df_display = df_users.copy()
        df_display['risk_score'] = df_display['risk_score'].apply(lambda x: f"{x*100:.1f}%")
        df_display['failure_rate'] = df_display['failure_rate'].apply(lambda x: f"{x*100:.1f}%")
        df_display['monthly_amount'] = df_display['monthly_amount'].apply(lambda x: f"{x:.2f}€")
        df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%Y-%m-%d')
        
        # Renommage des colonnes pour l'affichage
        df_display = df_display.rename(columns={
            'name': 'Nom',
            'email': 'Email',
            'risk_score': 'Score de risque',
            'failure_rate': 'Taux d\'échec',
            'subscription_type': 'Type d\'abonnement',
            'monthly_amount': 'Montant mensuel',
            'total_payments': 'Total paiements',
            'failed_payments': 'Échecs',
            'created_at': 'Créé le'
        })
        
        # Affichage du tableau
        st.dataframe(
            df_display[['Nom', 'Email', 'Score de risque', 'Taux d\'échec', 'Type d\'abonnement', 'Montant mensuel', 'Échecs']],
            use_container_width=True,
            hide_index=True
        )
        
        # Sélection utilisateur avec selectbox
        user_options = [f"{user['name']} ({user['email']})" for user in risky_users]
        selected_user_idx = st.selectbox(
            "🔍 Sélectionner un utilisateur pour analyse détaillée:",
            range(len(user_options)),
            format_func=lambda x: user_options[x],
            index=0 if user_options else None
        )
        
        # Analyse détaillée si un utilisateur est sélectionné
        if selected_user_idx is not None:
            selected_user = risky_users[selected_user_idx]
            
            st.header(f"🔍 Analyse détaillée - {selected_user['name']}")
            
            with st.spinner("Chargement de l'analyse..."):
                analysis = fetch_user_analysis(selected_user['id'])
            
            if analysis:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("⚠️ Facteurs de risque")
                    for factor in analysis['risk_factors']:
                        st.write(f"• {factor}")
                    
                    st.subheader("💡 Recommandations")
                    for rec in analysis['recommendations']:
                        st.write(f"• {rec}")
                
                with col2:
                    # Métriques de l'utilisateur
                    st.metric("🎯 Score de risque", f"{analysis['risk_score']*100:.1f}%")
                    st.metric("🚨 Niveau de risque", analysis['risk_level'].upper())
                    st.metric("💳 Paiements échoués", f"{analysis['failed_payments']}/{analysis['total_payments']}")
                    
                    # Bouton d'alerte
                    if st.button("🚨 Envoyer une alerte", type="primary"):
                        alert_result = send_alert(selected_user['id'])
                        if alert_result:
                            st.success("✅ Alerte envoyée avec succès!")
                        else:
                            st.error("❌ Erreur lors de l'envoi de l'alerte")
                    
                    # Informations sur l'abonnement
                    st.subheader("📋 Informations abonnement")
                    sub_info = analysis['subscription_info']
                    for key, value in sub_info.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                # Historique des paiements
                if analysis['payment_history']:
                    st.subheader("💳 Historique des paiements")
                    
                    payments_df = pd.DataFrame(analysis['payment_history'])
                    payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'])
                    payments_df = payments_df.sort_values('payment_date', ascending=False)
                    
                    # Graphique timeline des paiements
                    fig_timeline = px.scatter(
                        payments_df,
                        x='payment_date',
                        y='amount',
                        color='status',
                        title="Timeline des paiements",
                        labels={'payment_date': 'Date', 'amount': 'Montant (€)', 'status': 'Statut'},
                        color_discrete_map={'success': 'green', 'failed': 'red', 'declined': 'orange'}
                    )
                    fig_timeline.update_layout(height=300)
                    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Fonctionnalités d'export
    st.sidebar.header("📥 Export")
    
    if risky_users:
        # Export CSV
        csv_data = pd.DataFrame(risky_users).to_csv(index=False)
        st.sidebar.download_button(
            label="📊 Télécharger CSV",
            data=csv_data,
            file_name=f"risky_users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Export JSON
        json_data = json.dumps(risky_users, indent=2, default=str)
        st.sidebar.download_button(
            label="📄 Télécharger JSON",
            data=json_data,
            file_name=f"risky_users_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("**Risk Monitor** - Surveillance des abonnements à risque | Données mises à jour en temps réel")

if __name__ == "__main__":
    main()