import googlemaps
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

def afficher_progression(actuel, total):
    """Affiche une barre de progression"""
    pourcentage = int((actuel / total) * 100)
    barre = '█' * (pourcentage // 2) + '░' * (50 - pourcentage // 2)
    print(f'\r[{barre}] {pourcentage}% ({actuel}/{total})', end='', flush=True)

def obtenir_mode_transport(mode):
    """Convertit le mode de transport en format Google Maps"""
    modes = {
        'VOITURE': 'driving',
        'TRANSPORTS': 'transit',
        'VELO': 'bicycling',
        'MARCHE': 'walking'
    }
    return modes.get(mode.upper(), 'driving')

def calculer_temps_trajet(gmaps, origine, destination, mode, heure_depart):
    """Calcule le temps de trajet pour un itinéraire"""
    try:
        # Préparer les paramètres
        params = {
            'origins': origine,
            'destinations': destination,
            'mode': mode,
            'language': 'fr'
        }
        
        # Ajouter l'heure de départ si spécifiée
        if heure_depart and str(heure_depart).strip():
            today = datetime.now()
            heures, minutes = str(heure_depart).split(':')
            departure_time = today.replace(hour=int(heures), minute=int(minutes), second=0)
            params['departure_time'] = departure_time
            
            # Options spécifiques selon le mode
            if mode == 'driving':
                params['traffic_model'] = 'best_guess'
        
        # Appel à l'API
        result = gmaps.distance_matrix(**params)
        
        if result['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                temps = element['duration']['text']
                distance = element['distance']['text']
                return temps, distance, 'OK'
            else:
                return 'Erreur', '-', f"Trajet introuvable: {element['status']}"
        else:
            return 'Erreur', '-', f"Erreur API: {result['status']}"
            
    except Exception as e:
        return 'Erreur', '-', str(e)

def main():
    print("=" * 70)
    print("🗺️  CALCULATEUR DE TEMPS DE TRAJET GOOGLE MAPS")
    print("=" * 70)
    print()
    
    # 1. Demander la clé API
    cle_api = input("📝 Entrez votre clé API Google Maps: ").strip()
    
    if not cle_api:
        print("❌ Clé API requise !")
        return
    
    # 2. Demander le fichier CSV
    fichier_csv = input("📁 Entrez le nom du fichier CSV (ex: Estimation trajet - Feuille 1.csv): ").strip()
    
    try:
        # Lire le CSV
        print(f"\n📂 Lecture du fichier '{fichier_csv}'...")
        df = pd.read_csv(fichier_csv)
        
        # Vérifier les colonnes
        colonnes_requises = ['Origine', 'Destination', 'Mode de transport']
        for col in colonnes_requises:
            if col not in df.columns:
                print(f"❌ Colonne manquante: '{col}'")
                return
        
        print(f"✅ {len(df)} trajets trouvés")
        
    except FileNotFoundError:
        print(f"❌ Fichier '{fichier_csv}' introuvable !")
        return
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # 3. Initialiser Google Maps
    print("\n🔌 Connexion à l'API Google Maps...")
    try:
        gmaps = googlemaps.Client(key=cle_api)
        print("✅ Connexion réussie !")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 4. Calculer les trajets
    print(f"\n🚀 Calcul des temps de trajet en cours...\n")
    
    resultats = []
    
    for idx, row in df.iterrows():
        # Afficher la progression
        afficher_progression(idx, len(df))
        
        # Récupérer les données
        origine = row['Origine']
        destination = row['Destination']
        mode = obtenir_mode_transport(row['Mode de transport'])
        heure = row.get('Heure de départ', row.get('Heure de dÃ©part', ''))
        
        # Calculer le trajet
        temps, distance, statut = calculer_temps_trajet(gmaps, origine, destination, mode, heure)
        
        # Stocker les résultats
        resultats.append({
            'Origine': origine,
            'Destination': destination,
            'Mode de transport': row['Mode de transport'],
            'Heure de départ': heure,
            'Temps de trajet': temps,
            'Distance': distance,
            'Statut': statut
        })
        
        # Pause pour éviter de surcharger l'API
        time.sleep(0.2)
    
    # Terminer la barre de progression
    afficher_progression(len(df), len(df))
    print("\n")
    
    # 5. Créer le DataFrame de résultats
    df_resultats = pd.DataFrame(resultats)
    
    # 6. Sauvegarder les résultats
    nom_sortie = f"resultats_trajets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_resultats.to_csv(nom_sortie, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Calcul terminé !")
    print(f"📊 Résultats sauvegardés dans: {nom_sortie}")
    
    # 7. Afficher un résumé
    print("\n" + "=" * 70)
    print("📈 RÉSUMÉ")
    print("=" * 70)
    
    succes = len(df_resultats[df_resultats['Statut'] == 'OK'])
    erreurs = len(df_resultats[df_resultats['Statut'] != 'OK'])
    
    print(f"✅ Trajets réussis: {succes}/{len(df)}")
    print(f"❌ Trajets en erreur: {erreurs}/{len(df)}")
    
    if erreurs > 0:
        print("\n⚠️  Trajets en erreur:")
        for idx, row in df_resultats[df_resultats['Statut'] != 'OK'].iterrows():
            print(f"  - Ligne {idx+1}: {row['Origine']} → {row['Destination']}")
            print(f"    Raison: {row['Statut']}")
    
    print("\n" + "=" * 70)
    print("🎉 Terminé ! Vous pouvez ouvrir le fichier CSV avec Excel.")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération annulée par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")