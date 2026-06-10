# streamlit.py
# Application Streamlit complète : chargement des CSV + construction de tous les graphes Plotly interactifs.
# À placer à la racine de ton dossier "capstone web", au même niveau que le dossier data/.
#
# Lancement :
#   streamlit run streamlit.py

from pathlib import Path
import json
from urllib.request import urlopen

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# CONFIGURATION GÉNÉRALE
# ============================================================

st.set_page_config(
    page_title="Capstone — Enseignement supérieur privé",
    layout="wide"
)

DATA_DIR = Path("data")

COLOR_PRIVATE = "#534AB7"
COLOR_PUBLIC = "#888780"
COLOR_TOTAL = "#D85A30"
COLOR_GREEN = "#1D9E75"
COLOR_ORANGE = "#D85A30"
COLOR_PINK = "#D4537E"
COLOR_BLUE = "#378ADD"


# ============================================================
# PETITES FONCTIONS UTILES
# ============================================================

def _num(s):
    """Convertit une série en numérique en remplaçant les valeurs manquantes par 0."""
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _fmt_int_fr(x):
    """Format français pour les entiers : 1 234 567."""
    try:
        return f"{int(round(float(x))):,}".replace(",", " ")
    except Exception:
        return ""


def _fmt_pct_fr(x, ndigits=1):
    """Format français pour les pourcentages : 12,3 %."""
    try:
        return f"{float(x):.{ndigits}f}".replace(".", ",") + " %"
    except Exception:
        return ""


def _find_col(df, candidates, required=True):
    """Trouve une colonne parmi plusieurs noms possibles."""
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(
            "Aucune des colonnes attendues n'a été trouvée : "
            + " | ".join(candidates)
        )
    return None


def _clean_region_name(s):
    """Nettoie certains noms de régions pour faciliter les jointures cartographiques."""
    if pd.isna(s):
        return s
    s = str(s).strip()
    replacements = {
        "Provence-Alpes-Côte d’Azur": "Provence-Alpes-Côte d'Azur",
        "Provence-Alpes-Côte d'Azur": "Provence-Alpes-Côte d'Azur",
        "Auvergne Rhône Alpes": "Auvergne-Rhône-Alpes",
        "Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes",
        "Bourgogne Franche Comté": "Bourgogne-Franche-Comté",
        "Bourgogne-Franche-Comté": "Bourgogne-Franche-Comté",
        "Centre Val de Loire": "Centre-Val de Loire",
        "Centre-Val de Loire": "Centre-Val de Loire",
        "Grand-Est": "Grand Est",
    }
    return replacements.get(s, s)


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

@st.cache_data(show_spinner="Chargement des CSV...")
def charger_csv(path, sep=";", encoding="utf-8-sig"):
    return pd.read_csv(
        path,
        sep=sep,
        encoding=encoding,
        low_memory=False
    )


@st.cache_data(show_spinner="Chargement de toutes les données...")
def charger_toutes_les_donnees():
    # 1. ATLAS / SIES
    atlas_files = list(DATA_DIR.glob("fr-esr-atlas*.csv"))

    if not atlas_files:
        raise FileNotFoundError(
            "Aucun fichier ATLAS trouvé dans le dossier data. "
            "Le fichier doit commencer par : fr-esr-atlas"
        )

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
            # On ne bloque pas tout le site si un fichier manque.
            pass

    if "2025" not in annees:
        raise FileNotFoundError(
            "Le fichier Parcoursup 2025 est nécessaire pour plusieurs graphiques : "
            "data/fr-esr-parcoursup_2025.csv"
        )

    # 3. Parcoursup apprentissage
    fichier_apprentissage = DATA_DIR / "fr-esr-parcoursup-apprentissage.csv"

    if not fichier_apprentissage.exists():
        raise FileNotFoundError(
            "Le fichier fr-esr-parcoursup-apprentissage.csv est introuvable dans data."
        )

    appr = charger_csv(fichier_apprentissage)

    # 4. Fichiers préparés optionnels
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


# ============================================================
# FIGURES INTERACTIVES PLOTLY
# ============================================================

def fig_evolution_total_inscrits(atlas):
    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["Regroupements de formations ou d’établissements", "regroupement"])
    C_EFF = "Nombre total d’étudiants inscrits"

    d = atlas[
        (atlas["Niveau géographique"] == "Pays")
        & (atlas[C_REG] == "Total des formations d'enseignement supérieur")
    ].copy()

    d[C_EFF] = _num(d[C_EFF])
    serie = d.groupby(C_AN, as_index=False)[C_EFF].sum().sort_values(C_AN)
    serie["effectif_fmt"] = serie[C_EFF].map(lambda x: _fmt_int_fr(x) + " étudiants")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=serie[C_AN],
            y=serie[C_EFF],
            mode="lines+markers",
            line=dict(width=3, color=COLOR_PRIVATE),
            marker=dict(size=7),
            fill="tozeroy",
            fillcolor="rgba(83,74,183,0.10)",
            customdata=np.stack([serie["effectif_fmt"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>Effectif total : %{customdata[0]}<extra></extra>",
            name="Total",
        )
    )
    fig.update_layout(
        title="Évolution du nombre d’étudiants inscrits dans le supérieur (2001-2025)",
        xaxis_title="Année universitaire",
        yaxis_title="Étudiants inscrits",
        hovermode="x unified",
        template="plotly_white",
    )
    fig.update_yaxes(tickformat=",.0f")
    return fig


def fig_donuts_etablissements(atlas):
    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["regroupement", "Regroupements de formations ou d’établissements"])
    C_SEC = "Secteur de l’établissement d’inscription"
    C_EFF = "Nombre total d’étudiants inscrits"

    etabs = ["UNIV", "EC_COM", "EC_PARAM", "EC_ART", "EC_JUR", "EC_autres", "EPEU", "GE", "ENS", "INP", "UT"]
    mapping = {
        "EC_COM": "Écoles de commerce",
        "EC_ART": "Écoles d’art & culture",
        "EC_PARAM": "Paramédical & social",
        "EC_autres": "Autres écoles spécialisées",
        "EPEU": "Universités privées",
    }
    ordre = [
        "Écoles de commerce",
        "Écoles d’art & culture",
        "Paramédical & social",
        "Autres écoles spécialisées",
        "Universités privées",
        "Autres",
    ]

    def repartition(an):
        d = atlas[
            (atlas["Niveau géographique"] == "Pays")
            & (atlas[C_SEC] == "Établissements privés")
            & (atlas[C_REG].isin(etabs))
            & (atlas[C_AN] == an)
        ].copy()
        d[C_EFF] = _num(d[C_EFF])
        d["catégorie"] = d[C_REG].map(mapping).fillna("Autres")
        s = d.groupby("catégorie")[C_EFF].sum().reindex(ordre).fillna(0)
        return s

    s2001 = repartition("2001-02")
    s2024 = repartition("2024-25")

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=["2001", "2024"]
    )

    for col, s, label in [(1, s2001, "2001"), (2, s2024, "2024")]:
        total = s.sum()
        custom = np.stack([
            s.index,
            s.values,
            [v / total * 100 if total else 0 for v in s.values],
            [_fmt_int_fr(v) for v in s.values],
            [_fmt_int_fr(total) for _ in s.values],
        ], axis=-1)

        fig.add_trace(
            go.Pie(
                labels=s.index,
                values=s.values,
                hole=0.55,
                name=label,
                customdata=custom,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Effectif : %{customdata[3]} étudiants<br>"
                    "Part : %{customdata[2]:.1f} %<br>"
                    "Total privé : %{customdata[4]} étudiants"
                    "<extra></extra>"
                ),
            ),
            row=1, col=col
        )

        fig.add_annotation(
            text=f"{_fmt_int_fr(total)}<br>étudiants",
            x=0.18 if col == 1 else 0.82,
            y=0.5,
            showarrow=False,
            font=dict(size=14)
        )

    fig.update_layout(
        title="Répartition des étudiants privés par type d’établissement : 2001 vs 2024",
        template="plotly_white",
        legend_title_text="Type d’établissement",
    )
    return fig


def fig_croissance_par_type(atlas):
    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["regroupement", "Regroupements de formations ou d’établissements"])
    C_SEC = "Secteur de l’établissement d’inscription"
    C_EFF = "Nombre total d’étudiants inscrits"

    etabs = ["UNIV", "EC_COM", "EC_PARAM", "EC_ART", "EC_JUR", "EC_autres", "EPEU", "GE", "ENS", "INP", "UT"]
    mapping = {
        "EC_COM": "Écoles de commerce",
        "EC_ART": "Écoles d’art & culture",
        "EC_PARAM": "Paramédical & social",
        "EC_autres": "Autres écoles spécialisées",
        "EPEU": "Universités privées",
    }

    def eff(an):
        d = atlas[
            (atlas["Niveau géographique"] == "Pays")
            & (atlas[C_SEC] == "Établissements privés")
            & (atlas[C_REG].isin(etabs))
            & (atlas[C_AN] == an)
        ].copy()
        d[C_EFF] = _num(d[C_EFF])
        d["type"] = d[C_REG].map(mapping).fillna("Autres")
        return d.groupby("type")[C_EFF].sum()

    e2001 = eff("2001-02")
    e2024 = eff("2024-25")
    g = pd.concat([e2001.rename("2001"), e2024.rename("2024")], axis=1).fillna(0)
    g["gain"] = g["2024"] - g["2001"]
    total_gain = g["gain"].sum()
    g["contribution"] = g["gain"] / total_gain * 100
    g["croissance"] = np.where(g["2001"] > 0, (g["2024"] / g["2001"] - 1) * 100, np.nan)
    g = g.sort_values("gain", ascending=True).reset_index()
    g["gain_fmt"] = g["gain"].map(_fmt_int_fr)
    g["contribution_fmt"] = g["contribution"].map(lambda x: _fmt_pct_fr(x, 1))
    g["croissance_fmt"] = g["croissance"].map(lambda x: _fmt_pct_fr(x, 0))

    fig = px.bar(
        g,
        x="gain",
        y="type",
        orientation="h",
        custom_data=["gain_fmt", "contribution_fmt", "croissance_fmt"],
        title="Quel type d’établissement a porté la croissance du privé ? 2001-2024",
    )
    fig.update_traces(
        marker_color=COLOR_PRIVATE,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Gain : %{customdata[0]} étudiants<br>"
            "Contribution : %{customdata[1]}<br>"
            "Croissance : %{customdata[2]}<extra></extra>"
        ),
    )
    fig.update_layout(
        xaxis_title="Gain d’effectifs privés",
        yaxis_title="",
        template="plotly_white",
    )
    fig.update_xaxes(tickformat=",.0f")
    return fig


def fig_croissance_prive_vs_public(atlas):
    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["Regroupements de formations ou d’établissements", "regroupement"])
    C_SEC = "Secteur de l’établissement d’inscription"
    C_EFF = "Nombre total d’étudiants inscrits"

    d = atlas[
        (atlas["Niveau géographique"] == "Pays")
        & (atlas[C_REG] == "Total des formations d'enseignement supérieur")
    ].copy()
    d[C_EFF] = _num(d[C_EFF])
    d["secteur"] = d[C_SEC].map({
        "Établissements privés": "Privé",
        "Établissements publics": "Public"
    })

    piv = d.pivot_table(index=C_AN, columns="secteur", values=C_EFF, aggfunc="sum", fill_value=0).sort_index()
    piv["Total"] = piv["Privé"] + piv["Public"]
    piv["Part du privé"] = piv["Privé"] / piv["Total"] * 100
    data = piv.reset_index()

    fig = go.Figure()
    for secteur, color in [("Public", COLOR_PUBLIC), ("Privé", COLOR_PRIVATE)]:
        fig.add_trace(
            go.Scatter(
                x=data[C_AN],
                y=data[secteur],
                mode="lines+markers",
                line=dict(width=3, color=color),
                marker=dict(size=7),
                name=secteur,
                customdata=np.stack([
                    [_fmt_int_fr(v) + " étudiants" for v in data[secteur]],
                    data["Part du privé"].map(lambda x: _fmt_pct_fr(x, 1)),
                ], axis=-1),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"Secteur : {secteur}<br>"
                    "Effectif : %{customdata[0]}<br>"
                    "Part du privé cette année-là : %{customdata[1]}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Qui porte la croissance du supérieur ? Privé vs public (2001-2025)",
        xaxis_title="Année universitaire",
        yaxis_title="Étudiants inscrits",
        hovermode="x unified",
        template="plotly_white",
    )
    fig.update_yaxes(tickformat=",.0f")
    return fig


def fig_part_prive_regions(atlas):
    """
    Carte interactive avec slider temporel.
    Nécessite Internet pour charger le GeoJSON depuis GitHub.
    Si la carte ne charge pas, utilise le tableau df_croissance_region ou une image statique.
    """
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"

    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["Regroupements de formations ou d’établissements", "regroupement"])
    C_SEC = "Secteur de l’établissement d’inscription"
    C_EFF = "Nombre total d’étudiants inscrits"
    C_GEO = "Unité géographique"

    dates = ["2001-02", "2013-14", "2018-19", "2024-25"]

    reg = atlas[
        (atlas["Niveau géographique"] == "Région")
        & (atlas[C_REG] == "Total des formations d'enseignement supérieur")
        & (atlas[C_AN].isin(dates))
    ].copy()

    reg[C_GEO] = reg[C_GEO].map(_clean_region_name)
    reg[C_EFF] = _num(reg[C_EFF])
    reg["secteur"] = reg[C_SEC].map({
        "Établissements privés": "Privé",
        "Établissements publics": "Public"
    })

    piv = reg.pivot_table(index=[C_AN, C_GEO], columns="secteur", values=C_EFF, aggfunc="sum", fill_value=0).reset_index()
    piv["Total"] = piv["Privé"] + piv["Public"]
    piv["part_prive"] = piv["Privé"] / piv["Total"] * 100
    piv["annee"] = piv[C_AN].str[:4]
    piv["privé_fmt"] = piv["Privé"].map(_fmt_int_fr)
    piv["public_fmt"] = piv["Public"].map(_fmt_int_fr)
    piv["part_fmt"] = piv["part_prive"].map(lambda x: _fmt_pct_fr(x, 1))

    with urlopen(geojson_url) as response:
        geojson = json.load(response)

    fig = px.choropleth(
        piv,
        geojson=geojson,
        locations=C_GEO,
        featureidkey="properties.nom",
        color="part_prive",
        animation_frame="annee",
        color_continuous_scale="Blues",
        range_color=(0, max(30, piv["part_prive"].max())),
        custom_data=["privé_fmt", "public_fmt", "part_fmt"],
        title="Part du privé par région : 2001 → 2013 → 2018 → 2024",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{location}</b><br>"
            "Part du privé : %{customdata[2]}<br>"
            "Étudiants privés : %{customdata[0]}<br>"
            "Étudiants publics : %{customdata[1]}"
            "<extra></extra>"
        )
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=60, b=0))
    return fig


def df_croissance_region(atlas):
    C_AN = "Année universitaire"
    C_REG = _find_col(atlas, ["Regroupements de formations ou d’établissements", "regroupement"])
    C_SEC = "Secteur de l’établissement d’inscription"
    C_EFF = "Nombre total d’étudiants inscrits"
    C_GEO = "Unité géographique"

    reg = atlas[
        (atlas["Niveau géographique"] == "Région")
        & (atlas[C_REG] == "Total des formations d'enseignement supérieur")
        & (atlas[C_SEC] == "Établissements privés")
        & (atlas[C_AN].isin(["2001-02", "2024-25"]))
    ].copy()
    reg[C_GEO] = reg[C_GEO].map(_clean_region_name)
    reg[C_EFF] = _num(reg[C_EFF])

    piv = reg.pivot_table(index=C_GEO, columns=C_AN, values=C_EFF, aggfunc="sum", fill_value=0)
    piv = piv.rename(columns={"2001-02": "Privé 2001", "2024-25": "Privé 2024"})
    piv["Croissance %"] = np.where(piv["Privé 2001"] > 0, (piv["Privé 2024"] / piv["Privé 2001"] - 1) * 100, np.nan)

    out = piv.reset_index().rename(columns={C_GEO: "Région"}).sort_values("Croissance %", ascending=False)
    out["Privé 2001"] = out["Privé 2001"].astype(int)
    out["Privé 2024"] = out["Privé 2024"].astype(int)
    return out


def fig_croissance_regions_bar(atlas):
    d = df_croissance_region(atlas).copy()
    d = d[~d["Région"].isin(["Corse", "Mayotte", "Guyane", "Guadeloupe", "Martinique", "La Réunion"])].copy()
    d = d.sort_values("Croissance %", ascending=True)
    d["croissance_fmt"] = d["Croissance %"].map(lambda x: _fmt_pct_fr(x, 1))
    d["p2001_fmt"] = d["Privé 2001"].map(_fmt_int_fr)
    d["p2024_fmt"] = d["Privé 2024"].map(_fmt_int_fr)

    fig = px.bar(
        d,
        x="Croissance %",
        y="Région",
        orientation="h",
        custom_data=["croissance_fmt", "p2001_fmt", "p2024_fmt"],
        title="Croissance des effectifs privés par région (2001-2024)"
    )
    fig.update_traces(
        marker_color=COLOR_BLUE,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Croissance : %{customdata[0]}<br>"
            "Privé 2001 : %{customdata[1]} étudiants<br>"
            "Privé 2024 : %{customdata[2]} étudiants<extra></extra>"
        )
    )
    fig.update_layout(template="plotly_white", xaxis_title="Croissance des effectifs privés (%)", yaxis_title="")
    return fig


def fig_apprentis_bts(atlas):
    C_AN = "Année universitaire"
    C_REG = "Regroupements de formations ou d’établissements"
    C_SEC = "Secteur de l’établissement d’inscription"
    C_APP = "Nombre d’étudiants inscrits en STS et assimilés sous statut d’apprenti"

    d = atlas[
        (atlas[C_REG] == "Sections de techniciens supérieurs (STS) et assimilés")
        & (atlas["Niveau géographique"] == "Pays")
    ].copy()

    d[C_APP] = _num(d[C_APP])
    d["secteur"] = d[C_SEC].map({"Établissements privés": "Privé", "Établissements publics": "Public"})

    piv = d.groupby([C_AN, "secteur"])[C_APP].sum().unstack(fill_value=0).sort_index()
    piv["Total"] = piv.get("Privé", 0) + piv.get("Public", 0)
    piv = piv[piv["Total"] > 0].reset_index()

    fig = go.Figure()
    for col, color, dash in [("Total", COLOR_TOTAL, None), ("Privé", COLOR_PRIVATE, None), ("Public", COLOR_PUBLIC, "dash")]:
        fig.add_trace(
            go.Scatter(
                x=piv[C_AN],
                y=piv[col],
                mode="lines+markers",
                name=col,
                line=dict(width=3, color=color, dash=dash),
                marker=dict(size=7),
                customdata=np.stack([piv[col].map(lambda x: _fmt_int_fr(x) + " apprentis")], axis=-1),
                hovertemplate="<b>%{x}</b><br>" + col + " : %{customdata[0]}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Apprentis en BTS : total, privé et public (2015-2025)",
        xaxis_title="Année universitaire",
        yaxis_title="Apprentis en BTS",
        hovermode="x unified",
        template="plotly_white",
    )
    fig.update_yaxes(tickformat=",.0f")
    return fig


def fig_part_apprentissage_bts_secteur(atlas):
    C_AN = "Année universitaire"
    C_REG = "Regroupements de formations ou d’établissements"
    C_SEC = "Secteur de l’établissement d’inscription"
    C_APP = "Nombre d’étudiants inscrits en STS et assimilés sous statut d’apprenti"
    C_EFF = "Nombre total d’étudiants inscrits"

    d = atlas[
        (atlas[C_REG] == "Sections de techniciens supérieurs (STS) et assimilés")
        & (atlas["Niveau géographique"] == "Pays")
    ].copy()

    d[C_APP] = _num(d[C_APP])
    d[C_EFF] = _num(d[C_EFF])
    d["secteur"] = d[C_SEC].map({"Établissements privés": "Privé", "Établissements publics": "Public"})

    g = d.groupby([C_AN, "secteur"]).agg(apprentis=(C_APP, "sum"), total=(C_EFF, "sum")).reset_index()
    g["part"] = g["apprentis"] / g["total"] * 100
    g["part_fmt"] = g["part"].map(lambda x: _fmt_pct_fr(x, 1))
    g["app_fmt"] = g["apprentis"].map(_fmt_int_fr)
    g["total_fmt"] = g["total"].map(_fmt_int_fr)

    fig = px.line(
        g,
        x=C_AN,
        y="part",
        color="secteur",
        markers=True,
        color_discrete_map={"Privé": COLOR_PRIVATE, "Public": COLOR_PUBLIC},
        custom_data=["part_fmt", "app_fmt", "total_fmt"],
        title="Part de l’apprentissage dans le BTS, par secteur (2015-2025)",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Part apprentis : %{customdata[0]}<br>"
            "Apprentis : %{customdata[1]}<br>"
            "Total BTS : %{customdata[2]}<extra></extra>"
        )
    )
    fig.update_layout(
        xaxis_title="Année universitaire",
        yaxis_title="Part de l’apprentissage (%)",
        template="plotly_white"
    )
    return fig


def fig_treemap_filiere_apprentissage(appr):
    C_STAT = "Statut de l’établissement de la filière de formation"
    C_FIL = "Filière de formation très agrégée"

    d = appr[appr["Session"] == 2025].copy()
    d["secteur"] = d[C_STAT].apply(lambda s: "Public" if s == "Public" else "Privé")

    vol = (
        d[d["secteur"] == "Privé"]
        .groupby(C_FIL)
        .size()
        .reset_index(name="formations")
        .sort_values("formations", ascending=False)
    )

    total = vol["formations"].sum()
    vol["part"] = vol["formations"] / total * 100
    vol["nom"] = vol[C_FIL].astype(str).str.replace(r"^\d+_", "", regex=True)
    vol["formations_fmt"] = vol["formations"].map(_fmt_int_fr)
    vol["part_fmt"] = vol["part"].map(lambda x: _fmt_pct_fr(x, 1))

    fig = px.treemap(
        vol,
        path=["nom"],
        values="formations",
        custom_data=["formations_fmt", "part_fmt"],
        title=f"Volume du privé par filière en apprentissage (2025) — total : {_fmt_int_fr(total)} formations",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Formations privées : %{customdata[0]}<br>"
            "Part : %{customdata[1]}<extra></extra>"
        )
    )
    fig.update_layout(template="plotly_white")
    return fig


def fig_recherche_contrat(appr):
    C_STAT = "Statut de l’établissement de la filière de formation"
    CAND = "Effectif total des candidats pour la formation"
    RECH = "Nombre de de vœux placés en « Recherche de contrat » par la formation"

    d = appr[appr["Session"] == 2025].copy()
    d[CAND] = _num(d[CAND])
    d[RECH] = _num(d[RECH])

    g = d.groupby(C_STAT).agg(
        candidats=(CAND, "sum"),
        recherche=(RECH, "sum"),
        formations=(C_STAT, "size")
    ).reset_index()

    g["sécurisés"] = g["candidats"] - g["recherche"]
    g["part_recherche"] = g["recherche"] / g["candidats"] * 100

    ordre = ["Privé hors contrat", "Privé sous contrat d'association", "Privé enseignement supérieur", "Public"]
    g[C_STAT] = pd.Categorical(g[C_STAT], categories=ordre, ordered=True)
    g = g.sort_values(C_STAT)
    g["statut_label"] = g[C_STAT].astype(str) + "<br>(" + g["formations"].astype(int).astype(str) + " formations)"

    long = g.melt(
        id_vars=[C_STAT, "statut_label", "candidats", "formations", "part_recherche"],
        value_vars=["sécurisés", "recherche"],
        var_name="situation",
        value_name="effectif",
    )
    long["situation"] = long["situation"].replace({
        "sécurisés": "Avec débouché",
        "recherche": "En recherche de contrat"
    })
    long["effectif_fmt"] = long["effectif"].map(_fmt_int_fr)
    long["part_recherche_fmt"] = long["part_recherche"].map(lambda x: _fmt_pct_fr(x, 1))

    fig = px.bar(
        long,
        x="statut_label",
        y="effectif",
        color="situation",
        color_discrete_map={"Avec débouché": COLOR_PUBLIC, "En recherche de contrat": COLOR_PRIVATE},
        custom_data=["effectif_fmt", "part_recherche_fmt"],
        title="Apprentissage 2025 : candidats sans employeur par statut",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "%{fullData.name} : %{customdata[0]} candidats<br>"
            "Part sans employeur : %{customdata[1]}<extra></extra>"
        )
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title="",
        yaxis_title="Nombre de candidats",
        template="plotly_white"
    )
    fig.update_yaxes(tickformat=",.0f")
    return fig


def fig_composition_statut_region(appr):
    C_STAT = "Statut de l’établissement de la filière de formation"
    C_REG = "Région de l’établissement"

    d = appr[appr["Session"] == 2025].copy()
    rep = pd.crosstab(d[C_REG], d[C_STAT], normalize="index") * 100

    drom = ["Mayotte", "Guyane", "Guadeloupe", "Martinique", "La Réunion", "Corse"]
    rep = rep[~rep.index.isin(drom)].reset_index()

    long = rep.melt(id_vars=C_REG, var_name="statut", value_name="part")
    long["part_fmt"] = long["part"].map(lambda x: _fmt_pct_fr(x, 1))

    if "Privé hors contrat" in long["statut"].unique():
        ordre = (
            long[long["statut"] == "Privé hors contrat"]
            .sort_values("part")[C_REG]
            .tolist()
        )
        long[C_REG] = pd.Categorical(long[C_REG], categories=ordre, ordered=True)

    fig = px.bar(
        long,
        x="part",
        y=C_REG,
        color="statut",
        orientation="h",
        custom_data=["part_fmt"],
        title="Composition par statut de l’offre d’apprentissage par région (2025)",
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{fullData.name} : %{customdata[0]}<extra></extra>"
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title="Part de l’offre d’apprentissage (%)",
        yaxis_title="",
        template="plotly_white"
    )
    return fig


def fig_remplissage_prive_public(annees):
    d = annees["2025"].copy()

    STAT = [c for c in d.columns if "tatut" in c][0]
    FIL = "Filière de formation détaillée bis"
    CAPA = "Capacité de l’établissement par formation"
    ADM = "Effectif total des candidats ayant accepté la proposition de l’établissement (admis)"

    d[CAPA] = _num(d[CAPA])
    d[ADM] = _num(d[ADM])
    d["secteur"] = d[STAT].apply(lambda s: "Public" if s == "Public" else "Privé")

    g = d.groupby([FIL, "secteur"]).agg(capa=(CAPA, "sum"), adm=(ADM, "sum")).reset_index()
    g["remplissage"] = g["adm"] / g["capa"] * 100
    g = g.replace([np.inf, -np.inf], np.nan).dropna(subset=["remplissage"])

    top = g[g["secteur"] == "Privé"].set_index(FIL)["capa"].sort_values(ascending=False).head(14).index
    g = g[g[FIL].isin(top)].copy()
    g[FIL] = pd.Categorical(g[FIL], categories=list(top)[::-1], ordered=True)

    g["remplissage_fmt"] = g["remplissage"].map(lambda x: _fmt_pct_fr(x, 1))
    g["capa_fmt"] = g["capa"].map(_fmt_int_fr)
    g["adm_fmt"] = g["adm"].map(_fmt_int_fr)

    fig = px.bar(
        g,
        x="remplissage",
        y=FIL,
        color="secteur",
        orientation="h",
        barmode="group",
        color_discrete_map={"Privé": COLOR_PRIVATE, "Public": COLOR_PUBLIC},
        custom_data=["remplissage_fmt", "capa_fmt", "adm_fmt"],
        title="Remplissage privé vs public par filière (2025)",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Secteur : %{fullData.name}<br>"
            "Taux de remplissage : %{customdata[0]}<br>"
            "Capacité : %{customdata[1]} places<br>"
            "Admis : %{customdata[2]}<extra></extra>"
        )
    )
    fig.update_layout(
        xaxis_title="Taux de remplissage (%)",
        yaxis_title="",
        template="plotly_white"
    )
    return fig


def fig_profil_social_academique(annees):
    d = annees["2025"].copy()

    STAT = [c for c in d.columns if "tatut" in c][0]
    cols = {
        "neobac": "Effectif des admis néo bacheliers",
        "boursiers": "Dont effectif des admis boursiers néo bacheliers",
        "TB": "Dont effectif des admis néo bacheliers avec mention Très Bien au bac",
        "TBF": "Dont effectif des admis néo bacheliers avec mention Très Bien avec félicitations au bac",
        "sansmention": "Dont effectif des admis néo bacheliers sans mention au bac",
    }

    for c in cols.values():
        d[c] = _num(d[c])

    g = d.groupby(STAT).agg(**{k: (c, "sum") for k, c in cols.items()}).reset_index()
    g["% boursiers"] = g["boursiers"] / g["neobac"] * 100
    g["% TB+"] = (g["TB"] + g["TBF"]) / g["neobac"] * 100
    g["% sans mention"] = g["sansmention"] / g["neobac"] * 100

    ordre = ["Public", "Privé sous contrat d'association", "Privé enseignement supérieur", "Privé hors contrat"]
    g[STAT] = pd.Categorical(g[STAT], categories=ordre, ordered=True)
    g = g.sort_values(STAT)

    long = g.melt(
        id_vars=[STAT, "neobac"],
        value_vars=["% boursiers", "% TB+", "% sans mention"],
        var_name="indicateur",
        value_name="part",
    )

    long["part_fmt"] = long["part"].map(lambda x: _fmt_pct_fr(x, 1))
    long["neobac_fmt"] = long["neobac"].map(_fmt_int_fr)

    fig = px.bar(
        long,
        x="indicateur",
        y="part",
        color=STAT,
        barmode="group",
        custom_data=["part_fmt", "neobac_fmt"],
        title="Profil social et académique des admis par sous-statut (2025)",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "%{x} : %{customdata[0]}<br>"
            "Admis néo-bacheliers : %{customdata[1]}<extra></extra>"
        )
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Part (%)",
        template="plotly_white"
    )
    return fig


def fig_boursiers_filiere(annees):
    d = annees["2025"].copy()

    STAT = [c for c in d.columns if "tatut" in c][0]
    FILA = "Filière de formation très agrégée"
    NEO = "Effectif des admis néo bacheliers"
    BRS = "Dont effectif des admis boursiers néo bacheliers"

    d[NEO] = _num(d[NEO])
    d[BRS] = _num(d[BRS])
    d["secteur"] = d[STAT].apply(lambda s: "Public" if s == "Public" else "Privé")

    g = d.groupby([FILA, "secteur"]).agg(neobac=(NEO, "sum"), boursiers=(BRS, "sum")).reset_index()
    g = g[g["neobac"] >= 200].copy()
    g["part"] = g["boursiers"] / g["neobac"] * 100

    top = g.groupby(FILA)["boursiers"].sum().sort_values(ascending=False).head(14).index
    g = g[g[FILA].isin(top)].copy()

    order = g.groupby(FILA)["boursiers"].sum().sort_values(ascending=True).index
    g[FILA] = pd.Categorical(g[FILA], categories=order, ordered=True)

    g["boursiers_fmt"] = g["boursiers"].map(_fmt_int_fr)
    g["part_fmt"] = g["part"].map(lambda x: _fmt_pct_fr(x, 1))
    g["neobac_fmt"] = g["neobac"].map(_fmt_int_fr)

    fig = px.bar(
        g,
        x="boursiers",
        y=FILA,
        color="secteur",
        orientation="h",
        barmode="group",
        color_discrete_map={"Privé": COLOR_PRIVATE, "Public": COLOR_PUBLIC},
        custom_data=["boursiers_fmt", "part_fmt", "neobac_fmt"],
        title="Privé/Public : boursiers par filière (2025)",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Secteur : %{fullData.name}<br>"
            "Boursiers : %{customdata[0]}<br>"
            "Part de boursiers : %{customdata[1]}<br>"
            "Admis néo-bacheliers : %{customdata[2]}<extra></extra>"
        )
    )
    fig.update_layout(
        xaxis_title="Nombre de boursiers admis",
        yaxis_title="",
        template="plotly_white"
    )
    fig.update_xaxes(tickformat=",.0f")
    return fig


@st.cache_resource(show_spinner="Construction des graphiques interactifs...")
def construire_toutes_les_figures(atlas, appr, annees):
    figs = {
        "fig_evolution_total_inscrits": fig_evolution_total_inscrits(atlas),
        "fig_donuts_etablissements": fig_donuts_etablissements(atlas),
        "fig_croissance_par_type": fig_croissance_par_type(atlas),
        "fig_croissance_prive_vs_public": fig_croissance_prive_vs_public(atlas),
        "df_croissance_region": df_croissance_region(atlas),
        "fig_croissance_regions_bar": fig_croissance_regions_bar(atlas),
        "fig_apprentis_bts": fig_apprentis_bts(atlas),
        "fig_part_apprentissage_bts_secteur": fig_part_apprentissage_bts_secteur(atlas),
        "fig_treemap_filiere_apprentissage": fig_treemap_filiere_apprentissage(appr),
        "fig_recherche_contrat": fig_recherche_contrat(appr),
        "fig_composition_statut_region": fig_composition_statut_region(appr),
        "fig_remplissage_prive_public": fig_remplissage_prive_public(annees),
        "fig_profil_social_academique": fig_profil_social_academique(annees),
        "fig_boursiers_filiere": fig_boursiers_filiere(annees),
    }

    # La carte interactive peut échouer si Internet est coupé.
    try:
        figs["fig_part_prive_regions"] = fig_part_prive_regions(atlas)
    except Exception as e:
        figs["fig_part_prive_regions"] = None
        figs["erreur_carte_regions"] = str(e)

    return figs


# ============================================================
# CHARGEMENT + CONSTRUCTION DES FIGURES
# ============================================================

try:
    atlas, annees, appr, fichiers_prepares = charger_toutes_les_donnees()
    figs = construire_toutes_les_figures(atlas, appr, annees)
except Exception as e:
    st.error("Erreur pendant le chargement des données ou la construction des graphiques.")
    st.exception(e)
    st.stop()


# ============================================================
# INTERFACE DU SITE
# ============================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "1 — L’essor du privé",
        "2 — Le piège du mot privé",
        "3 — Le privé, un archipel",
        "4 — Le for-profit",
        "5 — Croissance public / privé",
        "6 — Géographie du privé",
        "7 — Alternance",
        "8 — Filières et attractivité",
        "9 — Profils étudiants",
        "10 — Vérification des données",
    ]
)


if page == "1 — L’essor du privé":
    st.title("L’essor de l’enseignement supérieur privé en France")

    st.markdown("""
    En vingt ans, l’enseignement supérieur français a changé d’échelle.
    Mais cette massification ne raconte pas seulement une hausse générale :
    elle révèle aussi une recomposition du système, dans laquelle le privé
    occupe une place de plus en plus visible.

    Avant de regarder qui compose le privé, il faut mesurer l’ampleur du mouvement.
    La première série temporelle donne le point de départ.
    """)

    st.plotly_chart(figs["fig_evolution_total_inscrits"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, données 2001-2025, calculs de l’autrice.")

    st.markdown("""
    Le survol de la courbe permet de lire directement les effectifs année par année.
    Le graphique n’est donc plus seulement une image : il devient un outil de lecture.
    """)


elif page == "2 — Le piège du mot privé":
    st.header("Le piège du mot privé")

    st.markdown("""
    Le premier piège est là : le privé ne désigne pas une seule réalité.
    Dans les données, il peut renvoyer à des établissements sous contrat,
    à des établissements privés d’enseignement supérieur, à des écoles hors contrat,
    ou à une catégorie agrégée opposée au public.

    La question n’est donc pas seulement de savoir si une école est privée,
    mais de savoir ce qu’elle garantit : diplôme visé, grade, titre RNCP
    ou diplôme d’établissement.
    """)

    df_reconnaissance = pd.DataFrame({
        "Reconnaissance": [
            "Diplôme visé par l’État",
            "Grade licence/master",
            "Titre RNCP",
            "Diplôme d’établissement"
        ],
        "Signification": [
            "Reconnaissance académique par le ministère",
            "Alignement avec le système universitaire LMD",
            "Certification professionnelle via France Compétences",
            "Reconnaissance propre à l’école"
        ],
        "Enjeu pour l’étudiant": [
            "Plus forte crédibilité",
            "Meilleure lisibilité nationale et internationale",
            "Reconnaissance professionnelle, mais pas équivalente à un diplôme universitaire",
            "Plus risqué : dépend de la réputation de l’école"
        ]
    })

    st.dataframe(df_reconnaissance, use_container_width=True, hide_index=True)


elif page == "3 — Le privé, un archipel":
    st.header("Le privé n’est pas une famille, c’est un archipel")

    st.markdown("""
    Parler du privé au singulier conduit immédiatement à une erreur :
    un institut catholique, une école de commerce reconnue, une école de santé
    conventionnée et une école détenue par un groupe financier ne relèvent pas
    du même monde.

    Pour saisir ce qu’est devenu cet archipel, il faut regarder non pas seulement
    son volume, mais sa composition.
    """)

    st.plotly_chart(figs["fig_donuts_etablissements"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, comparaison 2001 vs 2024, calculs de l’autrice.")


elif page == "4 — Le for-profit":
    st.header("Quand l’école devient un marché : le for-profit")

    st.markdown("""
    Une partie du privé fonctionne désormais comme un secteur économique à part entière.
    Des groupes rachètent des écoles, les regroupent sous une marque commune,
    ouvrent des campus dans plusieurs villes et raisonnent en portefeuille de formations.

    Reste à savoir si cette logique commerciale se lit dans les chiffres de croissance.
    Elle s’y lit nettement.
    """)

    df_groupes = pd.DataFrame({
        "Groupe": [
            "Galileo", "Eduservices", "Omnes", "IONIS",
            "AD Education", "Compétences & Développement", "Ynov"
        ],
        "Nombre d’écoles": [61, 24, 15, 29, 19, 14, 1],
        "Étudiants en France": [85000, 44000, 32000, 29000, 11500, 16000, 11000],
        "Étudiants total": [210000, 44000, 40000, 35000, 36000, 16000, 11000],
        "Positionnement": [
            "commerce, arts, design, digital, management",
            "BTS, commerce, management, alternance",
            "commerce, management, ingénierie, international",
            "informatique, ingénierie, business, tech",
            "art, design, communication, luxe",
            "management, commerce, RH, ingénierie",
            "digital, informatique, création numérique"
        ]
    })

    st.dataframe(df_groupes, use_container_width=True, hide_index=True)

    st.plotly_chart(figs["fig_croissance_par_type"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, croissance 2001-2024, calculs de l’autrice.")


elif page == "5 — Croissance public / privé":
    st.header("Croissance : public et privé ne suivent pas la même trajectoire")

    st.markdown("""
    La croissance globale du supérieur cache une privatisation.
    Pour la mesurer, il faut séparer les deux trajectoires et les poser
    l’une à côté de l’autre.
    """)

    st.plotly_chart(figs["fig_croissance_prive_vs_public"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, données 2001-2025, calculs de l’autrice.")


elif page == "6 — Géographie du privé":
    st.header("Une géographie qui ne se résume pas à Paris")

    st.markdown("""
    La géographie du privé combine deux logiques : des régions historiquement privées,
    et des régions de croissance récente. La carte interactive permet d’observer
    l’évolution de la part du privé dans le temps.
    """)

    if figs.get("fig_part_prive_regions") is not None:
        st.plotly_chart(figs["fig_part_prive_regions"], use_container_width=True)
        st.caption("Source : SIES/ATLAS, part du privé par région, 2001 à 2024.")
    else:
        st.warning("La carte interactive n’a pas pu être construite, probablement faute d’accès Internet au GeoJSON.")
        st.write(figs.get("erreur_carte_regions", ""))

    st.markdown("""
    Une carte de niveau ne suffit pas. Une région peut être très privée sans avoir
    beaucoup changé, ou au contraire connaître une expansion spectaculaire en partant de bas.
    """)

    st.plotly_chart(figs["fig_croissance_regions_bar"], use_container_width=True)
    st.dataframe(figs["df_croissance_region"], use_container_width=True, hide_index=True)


elif page == "7 — Alternance":
    st.header("L’alternance : solution financière ou nouveau filtre ?")

    st.markdown("""
    L’alternance est l’un des moteurs les plus puissants de l’expansion privée.
    Elle réduit le coût apparent pour l’étudiant, mais elle introduit une autre
    condition d’accès : trouver un employeur.
    """)

    st.plotly_chart(figs["fig_apprentis_bts"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, apprentis en BTS, 2015-2025.")

    st.plotly_chart(figs["fig_part_apprentissage_bts_secteur"], use_container_width=True)
    st.caption("Source : SIES/ATLAS, part de l’apprentissage dans le BTS par secteur, 2015-2025.")

    st.plotly_chart(figs["fig_treemap_filiere_apprentissage"], use_container_width=True)
    st.caption("Source : Parcoursup, offre d’apprentissage 2025, calculs de l’autrice.")

    st.plotly_chart(figs["fig_recherche_contrat"], use_container_width=True)
    st.caption("Source : Parcoursup, apprentissage 2025.")

    st.plotly_chart(figs["fig_composition_statut_region"], use_container_width=True)
    st.caption("Source : Parcoursup, apprentissage 2025.")


elif page == "8 — Filières et attractivité":
    st.header("Là où le privé s’installe : filières, diplômes et attractivité")

    st.markdown("""
    Le privé ne se développe pas de manière neutre. Il se concentre dans les formations
    professionnalisantes, là où la promesse d’emploi est immédiatement lisible.
    Le taux de remplissage permet d’observer si cette offre rencontre réellement
    une demande.
    """)

    st.plotly_chart(figs["fig_remplissage_prive_public"], use_container_width=True)
    st.caption("Source : Parcoursup, données 2025, calculs de l’autrice.")

    df_frais = pd.DataFrame({
        "Type d’acteur": [
            "Grande école de commerce",
            "Groupe for-profit",
            "CFA privé",
            "Institut catholique",
            "École santé/sociale privée"
        ],
        "Formations": [
            "PGE, Bachelor, MSc",
            "Bachelor, mastère, RNCP",
            "BTS, bachelor, mastère",
            "Licence, master, écoles",
            "IFSI, EFTS"
        ],
        "Coût pour l’étudiant": [
            "Élevé",
            "Variable à élevé",
            "Souvent pris en charge",
            "Modéré à élevé",
            "Variable"
        ],
        "Financement dominant": [
            "Famille, prêt, alternance partielle",
            "Alternance, famille, prêt",
            "Entreprise / OPCO",
            "Famille, bourses, aides",
            "Aides régionales, famille"
        ],
        "Point de vigilance": [
            "Retour sur investissement",
            "Reconnaissance du diplôme",
            "Nécessité d’un contrat",
            "Statut variable",
            "Forte hétérogénéité"
        ]
    })

    st.dataframe(df_frais, use_container_width=True, hide_index=True)


elif page == "9 — Profils étudiants":
    st.header("Qui entre dans le privé ?")

    st.markdown("""
    Répondre « le privé » au singulier serait une faute, car les trois sous-statuts
    n’accueillent pas les mêmes étudiants. En croisant origine sociale et niveau scolaire,
    les écarts apparaissent plus clairement.
    """)

    st.plotly_chart(figs["fig_profil_social_academique"], use_container_width=True)
    st.caption("Source : Parcoursup, admis néo-bacheliers 2025, calculs de l’autrice.")

    st.plotly_chart(figs["fig_boursiers_filiere"], use_container_width=True)
    st.caption("Source : Parcoursup, données 2025, calculs de l’autrice.")


elif page == "10 — Vérification des données":
    st.header("Vérification du chargement des données")

    st.markdown("""
    Cette page sert seulement à vérifier que tous les fichiers CSV sont bien chargés.
    Tu peux la supprimer quand ton site est finalisé.
    """)

    st.write("ATLAS :", atlas.shape)
    st.write("Apprentissage :", appr.shape)

    st.subheader("Fichiers Parcoursup chargés")
    for annee, df in annees.items():
        st.write(f"Parcoursup {annee} :", df.shape)

    st.subheader("Fichiers préparés détectés")
    if fichiers_prepares:
        for nom, df in fichiers_prepares.items():
            st.write(nom, ":", df.shape)
    else:
        st.write("Aucun fichier préparé détecté.")
