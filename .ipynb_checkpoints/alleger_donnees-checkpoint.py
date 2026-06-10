"""
alleger_donnees.py
But : créer des versions LÉGÈRES des CSV pour les héberger sur GitHub.
On ne garde que les colonnes et lignes réellement utilisées par le site.

À lancer UNE FOIS depuis le dossier "capstone web" :
    python alleger_donnees.py

Résultat : un dossier  data_light/  contenant les CSV allégés.
Ensuite, on renommera data_light en data pour la mise en ligne (voir étapes).
"""
from pathlib import Path
import pandas as pd

SRC = Path("data")            # tes CSV actuels
OUT = Path("data_light")      # sortie allégée
OUT.mkdir(exist_ok=True)

def lire(nom):
    return pd.read_csv(SRC / nom, sep=";", encoding="utf-8-sig", low_memory=False)

def ecrire(df, nom):
    df.to_csv(OUT / nom, sep=";", encoding="utf-8-sig", index=False)
    mo = (OUT / nom).stat().st_size / 1e6
    print(f"  ✓ {nom:48s} {mo:6.2f} Mo  ({len(df):,} lignes)".replace(",", " "))

print("== ATLAS ==")
import glob
atlas_file = glob.glob(str(SRC / "fr-esr-atlas*.csv"))[0]
atlas = pd.read_csv(atlas_file, sep=";", encoding="utf-8-sig", low_memory=False)
# Colonnes utilisées par le site
cols_atlas = [
    "Année universitaire",
    "Niveau géographique",
    "Unité géographique",
    "Regroupements de formations ou d’établissements",
    "Secteur de l’établissement d’inscription",
    "Nombre total d’étudiants inscrits",
    "Nombre d’étudiants inscrits en STS et assimilés sous statut d’apprenti",
]
cols_atlas = [c for c in cols_atlas if c in atlas.columns]
# Lignes utilisées : uniquement niveaux Pays et Région
atlas_l = atlas[atlas["Niveau géographique"].isin(["Pays", "Région"])][cols_atlas].copy()
ecrire(atlas_l, Path(atlas_file).name)

print("\n== APPRENTISSAGE ==")
appr = lire("fr-esr-parcoursup-apprentissage.csv")
cols_appr = [
    "Session",
    "Statut de l’établissement de la filière de formation",
    "Région de l’établissement",
    "Filière de formation très agrégée",
    "Effectif total des candidats pour la formation",
    "Nombre de de vœux placés en « Recherche de contrat » par la formation",
]
cols_appr = [c for c in cols_appr if c in appr.columns]
appr_l = appr[appr["Session"] == 2025][cols_appr].copy()
ecrire(appr_l, "fr-esr-parcoursup-apprentissage.csv")

print("\n== PARCOURSUP 2025 (seul millésime utilisé par le site) ==")
# Le site n'utilise que l'année 2025 (annees["2025"])
pc = lire("fr-esr-parcoursup_2025.csv")
STAT = [c for c in pc.columns if "tatut" in c][0]
cols_pc = [
    STAT,
    "Filière de formation très agrégée",
    "Filière de formation détaillée bis",
    "Capacité de l’établissement par formation",
    "Effectif total des candidats ayant accepté la proposition de l’établissement (admis)",
    "Effectif des admis néo bacheliers",
    "Dont effectif des admis boursiers néo bacheliers",
    "Dont effectif des admis néo bacheliers avec mention Très Bien au bac",
    "Dont effectif des admis néo bacheliers avec mention Très Bien avec félicitations au bac",
    "Dont effectif des admis néo bacheliers sans mention au bac",
]
cols_pc = [c for c in cols_pc if c in pc.columns]
pc_l = pc[cols_pc].copy()
ecrire(pc_l, "fr-esr-parcoursup_2025.csv")

print("\nTerminé. Dossier 'data_light' prêt.")
print("Poids total :",
      round(sum(f.stat().st_size for f in OUT.glob('*.csv')) / 1e6, 1), "Mo")
