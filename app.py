import streamlit as st
import googlemaps
import pandas as pd
from datetime import datetime, timedelta
import time
import io

# Configuration de la page
st.set_page_config(
    page_title="Calculateur de Temps de Trajet",
    page_icon="🗺️",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Titre
st.title("🗺️ Calculateur de Temps de Trajet Google Maps")
st.markdown("---")

# Fonction pour convertir le mode de transport
def obtenir_mode_transport(mode):
    modes = {
        'VOITURE': 'driving',
        'TRANSPORTS': 'transit',
        'VELO': 'bicycling',
        'MARCHE': 'walking'
    }
    return modes.get(mode.upper(), 'driving')

# Fonction pour calculer un trajet
def calculer_temps_trajet(gmaps, origine, destination, mode, heure_depart, jour_semaine=None):
    try:
        params = {
            'origins': origine,
            'destinations': destination,
            'mode': mode,
            'language': 'fr'
        }
        
        if heure_depart and str(heure_depart).strip():
            # Mapping des jours de la semaine en français
            jours = {
                'lundi': 0, 'monday': 0,
                'mardi': 1, 'tuesday': 1,
                'mercredi': 2, 'wednesday': 2,
                'jeudi': 3, 'thursday': 3,
                'vendredi': 4, 'friday': 4,
                'samedi': 5, 'saturday': 5,
                'dimanche': 6, 'sunday': 6
            }
            
            # Déterminer la date du prochain jour spécifié
            today = datetime.now()
            
            if jour_semaine and str(jour_semaine).strip():
                # Trouver le jour demandé
                jour_demande = None
                for key, value in jours.items():
                    if key.lower() == str(jour_semaine).strip().lower():
                        jour_demande = value
                        break
                
                if jour_demande is not None:
                    # Calculer le nombre de jours jusqu'au prochain jour demandé
                    jours_jusque = (jour_demande - today.weekday()) % 7
                    if jours_jusque == 0:
                        jours_jusque = 7  # Prendre la semaine prochaine si c'est aujourd'hui
                    target_date = today + timedelta(days=jours_jusque)
                else:
                    target_date = today
            else:
                target_date = today
            
            # Définir l'heure
            heures, minutes = str(heure_depart).split(':')
            departure_time = target_date.replace(hour=int(heures), minute=int(minutes), second=0, microsecond=0)
            params['departure_time'] = departure_time
            
            if mode == 'driving':
                params['traffic_model'] = 'best_guess'
        
        result = gmaps.distance_matrix(**params)
        
        if result['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                temps = element['duration']['text']
                distance = element['distance']['text']
                
                # Vérifier s'il y a des infos de trafic
                if 'duration_in_traffic' in element:
                    temps_trafic = element['duration_in_traffic']['text']
                    return temps_trafic, distance, '✅ OK (avec trafic)'
                
                return temps, distance, '✅ OK'
            else:
                return 'Erreur', '-', f"❌ {element['status']}"
        else:
            return 'Erreur', '-', f"❌ {result['status']}"
            
    except Exception as e:
        return 'Erreur', '-', f"❌ {str(e)}"

# Sidebar pour la configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.info("📌 **Prérequis**\n\nActivez ces APIs dans Google Cloud Console:\n- Maps JavaScript API\n- Distance Matrix API")
    
    api_key = st.text_input(
        "🔑 Clé API Google Maps",
        type="password",
        help="Obtenez votre clé sur console.cloud.google.com"
    )
    
    st.markdown("---")
    
    st.markdown("### 📊 Format CSV attendu")
    st.code("""Origine,Destination,Mode de transport,Heure de départ,Jour
Adresse 1,Adresse 2,VOITURE,08:00,Lundi
Adresse 3,Adresse 4,TRANSPORTS,09:30,Mercredi""")
    
    st.markdown("**Modes acceptés:**")
    st.markdown("- VOITURE\n- TRANSPORTS\n- VELO\n- MARCHE")
    
    st.markdown("**Jours acceptés:**")
    st.markdown("- Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche")
    st.caption("(Facultatif - sinon calcul pour aujourd'hui)")

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📁 Importer votre fichier CSV")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CSV",
        type=['csv'],
        help="Le fichier doit contenir les colonnes: Origine, Destination, Mode de transport, Heure de départ"
    )

with col2:
    st.header("ℹ️ Informations")
    if uploaded_file:
        st.success(f"✅ Fichier chargé: {uploaded_file.name}")
    else:
        st.warning("⏳ En attente d'un fichier...")

# Si un fichier est uploadé
if uploaded_file is not None:
    try:
        # Lire le CSV
        df = pd.read_csv(uploaded_file)
        
        # Vérifier les colonnes
        colonnes_requises = ['Origine', 'Destination', 'Mode de transport']
        colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
        
        if colonnes_manquantes:
            st.error(f"❌ Colonnes manquantes: {', '.join(colonnes_manquantes)}")
        else:
            st.success(f"✅ {len(df)} trajets détectés")
            
            # Aperçu des données
            with st.expander("👀 Aperçu des données", expanded=True):
                st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            
            # Bouton de calcul
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                bouton_calcul = st.button(
                    "🚀 Calculer les temps de trajet",
                    type="primary",
                    use_container_width=True,
                    disabled=not api_key
                )
            
            if not api_key:
                st.warning("⚠️ Veuillez entrer votre clé API dans la barre latérale")
            
            # Si le bouton est cliqué
            if bouton_calcul:
                if not api_key:
                    st.error("❌ Clé API manquante !")
                else:
                    try:
                        # Initialiser Google Maps
                        gmaps = googlemaps.Client(key=api_key)
                        
                        # Barre de progression
                        st.markdown("### 📊 Progression")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Conteneur pour les résultats en temps réel
                        results_placeholder = st.empty()
                        
                        resultats = []
                        
                        # Calculer chaque trajet
                        for idx, row in df.iterrows():
                            # Mise à jour de la progression
                            progress = (idx + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"⏳ Traitement: {idx + 1}/{len(df)} trajets")
                            
                            # Récupérer les données
                            origine = row['Origine']
                            destination = row['Destination']
                            mode = obtenir_mode_transport(row['Mode de transport'])
                            heure = row.get('Heure de départ', row.get('Heure de dÃ©part', ''))
                            jour = row.get('Jour', '')
                            
                            # Calculer le trajet
                            try:
                                temps, distance, statut = calculer_temps_trajet(
                                    gmaps, origine, destination, mode, heure, jour
                                )
                            except Exception as e:
                                temps, distance, statut = 'Erreur', '-', f'❌ {str(e)}'
                            
                            # Stocker les résultats
                            resultats.append({
                                '#': idx + 1,
                                'Origine': origine[:50] + '...' if len(origine) > 50 else origine,
                                'Destination': destination[:50] + '...' if len(destination) > 50 else destination,
                                'Mode': row['Mode de transport'],
                                'Jour': jour if jour else 'Aujourd\'hui',
                                'Heure': heure,
                                'Temps de trajet': temps,
                                'Distance': distance,
                                'Statut': statut
                            })
                            
                            # Afficher les résultats en temps réel
                            if len(resultats) > 0:
                                df_temp = pd.DataFrame(resultats)
                                results_placeholder.dataframe(df_temp, use_container_width=True, height=400)
                            
                            # Pause pour éviter de surcharger l'API
                            time.sleep(0.5)
                        
                        # Compléter la progression
                        progress_bar.progress(1.0)
                        status_text.text(f"✅ Calcul terminé ! {len(df)}/{len(df)} trajets")
                        
                        # Créer le DataFrame de résultats complet
                        df_resultats = pd.DataFrame(resultats)
                        
                        # Préparer le DataFrame pour le téléchargement (avec toutes les colonnes originales)
                        df_download = pd.DataFrame([{
                            'Origine': df.iloc[i]['Origine'],
                            'Destination': df.iloc[i]['Destination'],
                            'Mode de transport': df.iloc[i]['Mode de transport'],
                            'Heure de départ': df.iloc[i].get('Heure de départ', df.iloc[i].get('Heure de dÃ©part', '')),
                            'Jour': df.iloc[i].get('Jour', ''),
                            'Temps de trajet': resultats[i]['Temps de trajet'],
                            'Distance': resultats[i]['Distance'],
                            'Statut': resultats[i]['Statut']
                        } for i in range(len(df))])
                        
                        # Afficher les résultats
                        st.markdown("---")
                        st.markdown("### 📊 Résultats")
                        
                        # Statistiques
                        col1, col2, col3 = st.columns(3)
                        succes = len(df_resultats[df_resultats['Statut'].str.contains('OK', na=False)])
                        erreurs = len(df_resultats) - succes
                        
                        with col1:
                            st.metric("Total trajets", len(df_resultats))
                        with col2:
                            st.metric("✅ Succès", succes)
                        with col3:
                            st.metric("❌ Erreurs", erreurs)
                        
                        # Bouton de téléchargement
                        csv = df_download.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ Télécharger les résultats (CSV)",
                            data=csv,
                            file_name=f"resultats_trajets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )
                        
                        # Afficher les erreurs si présentes
                        if erreurs > 0:
                            with st.expander("⚠️ Détails des erreurs", expanded=False):
                                df_erreurs = df_resultats[~df_resultats['Statut'].str.contains('OK', na=False)]
                                st.dataframe(df_erreurs, use_container_width=True)
                        
                        st.success("🎉 Traitement terminé avec succès !")
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors du traitement: {str(e)}")
                        st.info("💡 Vérifiez que votre clé API est correcte et que les APIs nécessaires sont activées.")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
        st.info("💡 Assurez-vous que votre fichier CSV est bien formaté.")
else:
    # Instructions si aucun fichier
    st.info("👆 Commencez par uploader votre fichier CSV")
    
    st.markdown("### 🎯 Comment utiliser cette application ?")
    st.markdown("""
    1. **Obtenez une clé API** sur [Google Cloud Console](https://console.cloud.google.com/)
    2. **Activez les APIs** nécessaires (Maps JavaScript API et Distance Matrix API)
    3. **Entrez votre clé API** dans la barre latérale
    4. **Uploadez votre fichier CSV** avec vos trajets
    5. **Cliquez sur "Calculer"** et attendez les résultats
    6. **Téléchargez** le fichier CSV avec les temps de trajet calculés
    """)
    
    st.markdown("### 💰 Tarification Google Maps")
    st.info("""
    - 💵 **200$ de crédit gratuit par mois** (~40 000 requêtes)
    - 📊 Distance Matrix API: ~0.005$ par requête
    - 💳 Carte bancaire requise (même pour la version gratuite)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>🗺️ Calculateur de Temps de Trajet - Propulsé par Google Maps API</div>",
    unsafe_allow_html=True
)
