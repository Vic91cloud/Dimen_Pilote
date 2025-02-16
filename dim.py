import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
import matplotlib.dates as mdates

# Charger les données Excel
file_path = r"C:\Dimensionnement\dimensionnement_pilotes.xlsx"
xls = pd.ExcelFile(file_path)

df_vols = pd.read_excel(xls, "Programme_vols")
df_parametres = pd.read_excel(xls, "Parametres")

st.title("Simulation du Dimensionnement des Pilotes")

# Vérification des données
st.subheader("Aperçu des données")
st.write("Programme des vols", df_vols.head())
st.write("Paramètres", df_parametres.head())

# Calcul du nombre total d'heures nécessaires
heures_totales = df_vols["Heures_rotation"].sum()

# Correction de la récupération des jours travaillés
jours_travail_ivoirien = df_parametres.loc[df_parametres["Type_contrat"] == "Ivoirien", "jours_travailles_par_mois"].values[0]
jours_travail_location = df_parametres.loc[df_parametres["Type_contrat"] == "Location", "jours_travailles_par_mois"].values[0]

# Calcul du besoin en pilotes
pilotes_necessaires = df_vols["Jours_engagement"].sum() / jours_travail_ivoirien
pilotes_necessaires = -(-pilotes_necessaires // 1)  # Arrondi au supérieur

# Vérification de la disponibilité des pilotes ivoiriens
pilotes_ivoiriens_existants = df_parametres.loc[df_parametres["Type_contrat"] == "Ivoirien", "Nombre_pilotes_existants"].values[0]

if pilotes_ivoiriens_existants >= pilotes_necessaires:
    pilotes_ivoiriens_utilises = pilotes_necessaires
    pilotes_location_utilises = 0
else:
    pilotes_ivoiriens_utilises = pilotes_ivoiriens_existants
    pilotes_restant_a_couvrir = pilotes_necessaires - pilotes_ivoiriens_existants
    pilotes_location_utilises = pilotes_restant_a_couvrir * jours_travail_ivoirien / jours_travail_location

# Calcul de la productivité
productivite = heures_totales / pilotes_necessaires

# Affichage des résultats
st.subheader("Résultats du dimensionnement")
st.write(f"Nombre de pilotes nécessaires: {pilotes_necessaires}")
st.write(f"Pilotes Ivoiriens utilisés: {pilotes_ivoiriens_utilises}")
st.write(f"Pilotes de Location utilisés: {pilotes_location_utilises}")
st.write(f"Productivité (heures par pilote): {productivite:.2f}")

# Visualisation des résultats
st.subheader("Répartition des pilotes")
labels = ["Ivoiriens", "Location"]
values = [pilotes_ivoiriens_utilises, pilotes_location_utilises]
fig, ax = plt.subplots()
ax.pie(values, labels=labels, autopct='%1.1f%%', colors=["blue", "orange"])
ax.set_title("Répartition des pilotes")
st.pyplot(fig)

# Simulation des plannings
st.subheader("Simulation des plannings des pilotes")
plannings = {"Ivoirien": {}, "Location": {}}
rotations_disponibles = df_vols.to_dict('records')
random.shuffle(rotations_disponibles)

dates_periode = pd.date_range(df_vols["Date_début"].min(), df_vols["Date_fin"].max())

for contrat, nb_pilotes in zip(["Ivoirien", "Location"], [pilotes_ivoiriens_utilises, pilotes_location_utilises]):
    pilotes = [f"Pilote_{contrat}_{i+1}" for i in range(int(nb_pilotes))]
    planning_pilotes = {pilote: [] for pilote in pilotes}
    jours_sans_rotation = {pilote: set(dates_periode) for pilote in pilotes}
    
    for rotation in list(rotations_disponibles):  # Copie de la liste pour éviter les modifications en cours d'itération
        for pilote in pilotes:
            if not any(r["Date_début"] == rotation["Date_début"] for r in planning_pilotes[pilote]):
                planning_pilotes[pilote].append(rotation)
                jours_sans_rotation[pilote].difference_update(pd.date_range(rotation["Date_début"], rotation["Date_fin"]))
                rotations_disponibles.remove(rotation)
                break
    
    plannings[contrat] = planning_pilotes
    
# Création du graphique de planning
fig, ax = plt.subplots(figsize=(12, 6))
colors = {"Rotation": "blue"}
y_offset = 0

for contrat, planning in plannings.items():
    for pilote, rotations in planning.items():
        for r in rotations:
            debut = pd.to_datetime(r["Date_début"])
            fin = pd.to_datetime(r["Date_fin"])
            ax.barh(pilote, fin - debut, left=debut, color=colors["Rotation"])
    y_offset += 1

ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.xticks(rotation=45)
plt.xlabel("Dates")
plt.ylabel("Pilotes")
plt.title("Simulation de planning des pilotes")
st.pyplot(fig)

# Affichage du nombre de jours sans rotation
st.subheader("Jours sans rotation par pilote")
jours_sans_rotation_counts = {pilote: len(jours) for pilote, jours in jours_sans_rotation.items()}
st.write(pd.DataFrame.from_dict(jours_sans_rotation_counts, orient='index', columns=["Jours sans rotation"]))
