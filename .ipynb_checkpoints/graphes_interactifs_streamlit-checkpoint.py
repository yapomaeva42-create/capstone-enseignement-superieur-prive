import streamlit as st
import pandas as pd
from pathlib import Path

from graphes_interactifs_streamlit import construire_toutes_les_figures


st.set_page_config(
    page_title="Capstone — Enseignement supérieur privé",
    layout="wide"
)

DATA_DIR = Path("data")


@st.cache_data
def charger_csv(path, sep=";", encoding="utf-8-sig"):
    return pd.read_csv(
        path,
        sep=sep,
        encoding=encoding,
        low_memory=False
    )


@st.cache_data
def charger_toutes_les_donnees():
    # 1. ATLAS / SIES
    atlas_files = list(DATA_DIR.glob("fr-esr-atlas*.csv"))

    if not atlas_files:
        raise FileNotFoundError("Aucun fichier ATLAS trouvé dans le dossier data.")

    atlas = charger_csv(atlas_files[0])

    # 2. Parcoursup 2018-2025
    fichiers_parcoursup = {
        "2018": DATA_DIR / "fr-esr-parcoursup-2018.csv",
        "2019": DATA_DIR / "fr-esr-parcoursup-2019.csv",
        "2020": DATA_DIR / "fr-esr-parcoursup_2020.csv",
        "2021": DATA_DIR / "fr-esr-parcoursup_2021.csv",
        "2022": DATA_DIR / "fr-esr-parcoursup_2022.csv",
        "2023": DATA_DIR / "fr-esr-parcoursup_2023.csv",
        "2024": DATA_DIR / "fr-esr-parcoursup_2024.csv",
        "2025": DATA_DIR / "fr-esr-parcoursup_2025.csv",
    }

    annees = {}

    for annee, fichier in fichiers_parcoursup.items():
        if fichier.exists():
            annees[annee] = charger_csv(fichier)
        else:
            st.warning(f"Fichier Parcoursup manquant pour {annee} : {fichier}")

    # 3. Parcoursup apprentissage
    fichier_apprentissage = DATA_DIR / "fr-esr-parcoursup-apprentissage.csv"

    if not fichier_apprentissage.exists():
        raise FileNotFoundError(
            "Le fichier fr-esr-parcoursup-apprentissage.csv est introuvable."
        )

    appr = charger_csv(fichier_apprentissage)

    # 4. Fichiers préparés, si tu veux encore les utiliser
    fichiers_prepares = {}

    for nom in [
        "evolution_inscrits.csv",
        "croissance_regions.csv",
        "prive_vs_public.csv"
    ]:
        chemin = DATA_DIR / nom
        if chemin.exists():
            fichiers_prepares[nom] = charger_csv(chemin)

    return atlas, annees, appr, fichiers_prepares


atlas, annees, appr, fichiers_prepares = charger_toutes_les_donnees()


figs = construire_toutes_les_figures(
    atlas=atlas,
    appr=appr,
    annees=annees
)