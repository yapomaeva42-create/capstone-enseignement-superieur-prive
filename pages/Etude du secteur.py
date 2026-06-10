# article.py
# Capstone — L'essor de l'enseignement supérieur privé en France
# Format : article web unique, sommaire latéral cliquable, graphes Plotly interactifs.
# À placer à la racine de "capstone web", au même niveau que le dossier data/.
# Lancement :  streamlit run article.py

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
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="L'enseignement supérieur privé en France",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")

COLOR_PRIVATE = "#534AB7"
COLOR_PUBLIC = "#888780"
COLOR_TOTAL = "#D85A30"
COLOR_GREEN = "#1D9E75"
COLOR_BLUE = "#378ADD"

# Style : largeur de lecture confortable + sommaire soigné
st.markdown("""
<style>
.block-container {max-width: 860px; padding-top: 2rem;}
h2 {margin-top: 2.5rem; padding-top: 0.5rem; border-top: 1px solid #eee;}
.toc a {text-decoration: none; color: #444; display: block; padding: 2px 0; font-size: 0.9rem;}
.toc a:hover {color: #534AB7;}
.intro-lead {font-size: 1.15rem; line-height: 1.7; color: #333;}
blockquote {border-left: 4px solid #534AB7; padding-left: 1rem; color: #555; font-style: italic;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PETITES FONCTIONS UTILES
# ============================================================
def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

def _fmt_int_fr(x):
    try:
        return f"{int(round(float(x))):,}".replace(",", " ")
    except Exception:
        return ""

def _fmt_pct_fr(x, ndigits=1):
    try:
        return f"{float(x):.{ndigits}f}".replace(".", ",") + " %"
    except Exception:
        return ""

def _find_col(df, candidates, required=True):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError("Colonnes introuvables : " + " | ".join(candidates))
    return None

def _clean_region_name(s):
    if pd.isna(s):
        return s
    s = str(s).strip()
    replacements = {
        "Provence-Alpes-Côte d’Azur": "Provence-Alpes-Côte d'Azur",
        "Auvergne Rhône Alpes": "Auvergne-Rhône-Alpes",
        "Bourgogne Franche Comté": "Bourgogne-Franche-Comté",
        "Centre Val de Loire": "Centre-Val de Loire",
        "Grand-Est": "Grand Est",
    }
    return replacements.get(s, s)

def anchor(name):
    """Crée une ancre HTML invisible pour la navigation du sommaire."""
    st.markdown(f"<div id='{name}'></div>", unsafe_allow_html=True)

# ============================================================
# ============================================================
# CHARGEMENT DES DONNÉES WEB ALLÉGÉES
# ============================================================
# Cette version est prévue pour Streamlit Cloud : elle ne lit plus les bases brutes.
# Les CSV de data_web/ sont créés en local avec prepare_data_web.py.
DATA_WEB_DIR = Path("data_web")

@st.cache_data(show_spinner="Chargement des données préparées…")
def charger_web_csv(nom):
    path = DATA_WEB_DIR / nom
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier manquant : {path}. Lance d'abord python prepare_data_web.py en local, "
            "puis ajoute le dossier data_web sur GitHub."
        )
    return pd.read_csv(path, encoding="utf-8-sig")

def _verifier_data_web():
    requis = [
        "evolution_inscrits.csv", "prive_vs_public.csv", "croissance_regions.csv",
        "repartition_prive_type.csv", "contribution_croissance_type.csv", "part_prive_regions.csv",
        "apprentis_bts.csv", "part_apprentissage_bts.csv", "apprentissage_region_statut.csv",
        "apprentissage_filiere_prive.csv", "recherche_contrat_statut.csv", "remplissage_filiere.csv",
        "profil_social_academique.csv", "boursiers_filiere.csv",
    ]
    manquants = [f for f in requis if not (DATA_WEB_DIR / f).exists()]
    if manquants:
        raise FileNotFoundError("Fichiers data_web manquants : " + ", ".join(manquants))

# ============================================================
# FIGURES PLOTLY — VERSION CLOUD À PARTIR DE data_web/
# ============================================================
def fig_evolution_total_inscrits(_atlas=None):
    s = charger_web_csv("evolution_inscrits.csv").sort_values("annee")
    s["fmt"] = s["inscrits"].map(lambda x: _fmt_int_fr(x) + " étudiants")
    fig = go.Figure(go.Scatter(
        x=s["annee"], y=s["inscrits"], mode="lines+markers",
        line=dict(width=3, color=COLOR_PRIVATE), marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(83,74,183,0.10)",
        customdata=np.stack([s["fmt"]], axis=-1),
        hovertemplate="<b>%{x}</b><br>Effectif total : %{customdata[0]}<extra></extra>"))
    fig.update_layout(title="Évolution du nombre d'étudiants inscrits dans le supérieur (2001-2025)",
                      xaxis_title="Année universitaire", yaxis_title="Étudiants inscrits",
                      hovermode="x unified", template="plotly_white", height=460)
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(tickformat=",.0f", rangemode="tozero")
    return fig

def fig_donuts_etablissements(_atlas=None):
    d = charger_web_csv("repartition_prive_type.csv")
    ordre = ["Écoles de commerce", "Écoles d'art & culture", "Paramédical & social",
             "Autres écoles spécialisées", "Universités privées", "Autres"]
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]],
                        subplot_titles=["2001", "2024"])
    for col, an in [(1, "2001"), (2, "2024")]:
        s = d[d["annee"].astype(str) == an].set_index("type")["effectif"].reindex(ordre).fillna(0)
        total = s.sum()
        custom = np.stack([s.index, s.values,
                           [v/total*100 if total else 0 for v in s.values],
                           [_fmt_int_fr(v) for v in s.values],
                           [_fmt_int_fr(total) for _ in s.values]], axis=-1)
        fig.add_trace(go.Pie(labels=s.index, values=s.values, hole=0.55,
                             customdata=custom,
                             hovertemplate=("<b>%{customdata[0]}</b><br>Effectif : %{customdata[3]} étud.<br>"
                                            "Part : %{customdata[2]:.1f} %<br>Total privé : %{customdata[4]}<extra></extra>")),
                      row=1, col=col)
        fig.add_annotation(text=f"{_fmt_int_fr(total)}<br>étudiants",
                           x=0.18 if col == 1 else 0.82, y=0.5, showarrow=False, font=dict(size=13))
    fig.update_layout(title="Répartition des étudiants privés par type d'établissement : 2001 vs 2024",
                      template="plotly_white", legend_title_text="Type d'établissement")
    return fig

def fig_croissance_par_type(_atlas=None):
    g = charger_web_csv("contribution_croissance_type.csv").sort_values("gain")
    g["gain_fmt"] = g["gain"].map(_fmt_int_fr)
    g["contribution_fmt"] = g["contribution"].map(lambda x: _fmt_pct_fr(x, 1))
    g["croissance_fmt"] = g["croissance"].map(lambda x: _fmt_pct_fr(x, 0))
    fig = px.bar(g, x="gain", y="type", orientation="h",
                 custom_data=["gain_fmt", "contribution_fmt", "croissance_fmt"],
                 title="Quel type d'établissement a porté la croissance du privé ? (2001-2024)")
    fig.update_traces(marker_color=COLOR_PRIVATE,
                      hovertemplate=("<b>%{y}</b><br>Gain : %{customdata[0]} étud.<br>"
                                     "Contribution : %{customdata[1]}<br>Croissance : %{customdata[2]}<extra></extra>"))
    fig.update_layout(xaxis_title="Gain d'effectifs privés", yaxis_title="", template="plotly_white")
    fig.update_xaxes(tickformat=",.0f")
    return fig

def fig_croissance_prive_vs_public(_atlas=None):
    data = charger_web_csv("prive_vs_public.csv").sort_values("annee")
    data["Total"] = data["prive"] + data["public"]
    data["Part"] = data["prive"] / data["Total"] * 100
    fig = go.Figure()
    for col, label, color in [("public", "Public", COLOR_PUBLIC), ("prive", "Privé", COLOR_PRIVATE)]:
        fig.add_trace(go.Scatter(x=data["annee"], y=data[col], mode="lines+markers",
                                 line=dict(width=3, color=color), marker=dict(size=7), name=label,
                                 customdata=np.stack([data[col].map(lambda x: _fmt_int_fr(x)+" étud."),
                                                      data["Part"].map(lambda x: _fmt_pct_fr(x,1))], axis=-1),
                                 hovertemplate=("<b>%{x}</b><br>Secteur : "+label+"<br>Effectif : %{customdata[0]}<br>"
                                                "Part du privé : %{customdata[1]}<extra></extra>")))
    fig.update_layout(title="Qui porte la croissance du supérieur ? Privé vs public (2001-2025)",
                      xaxis_title="Année universitaire", yaxis_title="Étudiants inscrits",
                      hovermode="x unified", template="plotly_white", height=460)
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(tickformat=",.0f", rangemode="tozero")
    return fig

def df_croissance_region(_atlas=None):
    d = charger_web_csv("croissance_regions.csv").copy()
    d = d.rename(columns={"region": "Région", "prive_2001": "Privé 2001", "prive_2024": "Privé 2024", "croissance": "Croissance %"})
    d["Privé 2001"] = d["Privé 2001"].round(0).astype(int)
    d["Privé 2024"] = d["Privé 2024"].round(0).astype(int)
    d["Croissance %"] = d["Croissance %"].round(0)
    return d.sort_values("Croissance %", ascending=False)

def fig_croissance_regions_bar(_atlas=None):
    d = df_croissance_region().copy()
    hors = ["Corse", "Mayotte", "Guyane", "Guadeloupe", "Martinique", "La Réunion",
            "Collectivités d'outre-mer", "Collectivités d’outre-mer", "Étranger",
            "Collectivités d'Outre-Mer", "France métropolitaine + DROM"]
    d = d[~d["Région"].isin(hors)].copy().sort_values("Croissance %", ascending=True)
    d["c_fmt"] = d["Croissance %"].map(lambda x: _fmt_pct_fr(x, 0))
    d["p1"] = d["Privé 2001"].map(_fmt_int_fr)
    d["p2"] = d["Privé 2024"].map(_fmt_int_fr)
    fig = px.bar(d, x="Croissance %", y="Région", orientation="h",
                 custom_data=["c_fmt", "p1", "p2"],
                 title="Croissance des effectifs privés par région (2001-2024, France métropolitaine hors Corse)")
    fig.update_traces(marker_color=COLOR_PRIVATE,
                      hovertemplate=("<b>%{y}</b><br>Croissance : %{customdata[0]}<br>"
                                     "Privé 2001 : %{customdata[1]} étud.<br>Privé 2024 : %{customdata[2]} étud.<extra></extra>"))
    fig.update_layout(template="plotly_white", xaxis_title="Croissance des effectifs privés (%)",
                      yaxis_title="", height=520)
    return fig

def fig_part_prive_regions(_atlas=None):
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"
    piv = charger_web_csv("part_prive_regions.csv").copy()
    piv["pf"] = piv["part"].map(lambda x: _fmt_pct_fr(x, 1))
    with urlopen(url) as r:
        gj = json.load(r)
    vmax = float(np.ceil(piv["part"].max() / 5) * 5)
    fig = px.choropleth(piv, geojson=gj, locations="region", featureidkey="properties.nom",
                        color="part", animation_frame="annee", color_continuous_scale="YlOrRd",
                        range_color=(0, vmax), custom_data=["pf"],
                        title="Part du privé par région : 2001 → 2013 → 2018 → 2024")
    fig.update_traces(hovertemplate="<b>%{location}</b><br>Part du privé : %{customdata[0]}<extra></extra>")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=60, b=0), height=560,
                      coloraxis_colorbar=dict(title="Part du privé (%)", ticksuffix=" %"))
    return fig

def fig_apprentis_bts(_atlas=None):
    piv = charger_web_csv("apprentis_bts.csv").sort_values("annee")
    fig = go.Figure()
    for col, label, color, dash in [("total", "Total", COLOR_TOTAL, None), ("prive", "Privé", COLOR_PRIVATE, None), ("public", "Public", COLOR_PUBLIC, "dash")]:
        fig.add_trace(go.Scatter(x=piv["annee"], y=piv[col], mode="lines+markers", name=label,
                                 line=dict(width=3, color=color, dash=dash), marker=dict(size=7),
                                 customdata=np.stack([piv[col].map(lambda x: _fmt_int_fr(x)+" apprentis")], axis=-1),
                                 hovertemplate="<b>%{x}</b><br>"+label+" : %{customdata[0]}<extra></extra>"))
    fig.update_layout(title="Apprentis en BTS : total, privé et public (2015-2025)",
                      xaxis_title="Année universitaire", yaxis_title="Apprentis en BTS",
                      hovermode="x unified", template="plotly_white", height=460)
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(tickformat=",.0f")
    return fig

def fig_part_apprentissage_bts_secteur(_atlas=None):
    g = charger_web_csv("part_apprentissage_bts.csv").sort_values("annee")
    g["pf"] = g["part"].map(lambda x: _fmt_pct_fr(x, 1))
    g["af"] = g["apprentis"].map(_fmt_int_fr)
    g["tf"] = g["total"].map(_fmt_int_fr)
    fig = px.line(g, x="annee", y="part", color="secteur", markers=True,
                  color_discrete_map={"Privé": COLOR_PRIVATE, "Public": COLOR_PUBLIC},
                  custom_data=["pf", "af", "tf"],
                  title="Part de l'apprentissage dans le BTS, par secteur (2015-2025)")
    fig.update_traces(line=dict(width=3), marker=dict(size=8),
                      hovertemplate=("<b>%{x}</b><br>Part apprentis : %{customdata[0]}<br>"
                                     "Apprentis : %{customdata[1]}<br>Total BTS : %{customdata[2]}<extra></extra>"))
    fig.update_layout(xaxis_title="Année universitaire", yaxis_title="Part de l'apprentissage (%)",
                      template="plotly_white", height=460)
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(range=[0, 80], ticksuffix=" %")
    return fig

def fig_treemap_filiere_apprentissage(_appr=None):
    vol = charger_web_csv("apprentissage_filiere_prive.csv")
    total = vol["formations"].sum()
    vol["ff"] = vol["formations"].map(_fmt_int_fr)
    vol["pf"] = vol["part"].map(lambda x: _fmt_pct_fr(x, 1))
    fig = px.treemap(vol, path=["nom"], values="formations", custom_data=["ff", "pf"],
                     title=f"Volume du privé par filière en apprentissage (2025) — {_fmt_int_fr(total)} formations")
    fig.update_traces(hovertemplate=("<b>%{label}</b><br>Formations privées : %{customdata[0]}<br>"
                                     "Part : %{customdata[1]}<extra></extra>"))
    fig.update_layout(template="plotly_white")
    return fig

def fig_recherche_contrat(_appr=None):
    g = charger_web_csv("recherche_contrat_statut.csv")
    ordre = ["Privé hors contrat", "Privé sous contrat d'association", "Privé enseignement supérieur", "Public"]
    g["statut"] = pd.Categorical(g["statut"], categories=ordre, ordered=True)
    g = g.sort_values("statut")
    g["lbl"] = g["statut"].astype(str) + "<br>(" + g["formations"].astype(int).astype(str) + " formations)"
    long = g.melt(id_vars=["statut", "lbl", "candidats", "formations", "part_recherche"],
                  value_vars=["securises", "recherche"], var_name="situation", value_name="effectif")
    long["situation"] = long["situation"].replace({"securises": "Avec débouché", "recherche": "En recherche de contrat"})
    long["ef"] = long["effectif"].map(_fmt_int_fr)
    long["prf"] = long["part_recherche"].map(lambda x: _fmt_pct_fr(x, 1))
    fig = px.bar(long, x="lbl", y="effectif", color="situation",
                 color_discrete_map={"Avec débouché": COLOR_PUBLIC, "En recherche de contrat": COLOR_PRIVATE},
                 custom_data=["ef", "prf"], title="Apprentissage 2025 : candidats sans employeur par statut")
    fig.update_traces(hovertemplate=("<b>%{x}</b><br>%{fullData.name} : %{customdata[0]} cand.<br>"
                                     "Part sans employeur : %{customdata[1]}<extra></extra>"))
    fig.update_layout(barmode="stack", xaxis_title="", yaxis_title="Candidats", template="plotly_white")
    fig.update_yaxes(tickformat=",.0f")
    return fig

def fig_composition_statut_region(_appr=None):
    long = charger_web_csv("apprentissage_region_statut.csv")
    long["part_fmt"] = long["part"].map(lambda x: _fmt_pct_fr(x, 1))
    if "Privé hors contrat" in long["statut"].unique():
        ordre = long[long["statut"] == "Privé hors contrat"].sort_values("part")["region"].tolist()
        long["region"] = pd.Categorical(long["region"], categories=ordre, ordered=True)
    fig = px.bar(long, x="part", y="region", color="statut", orientation="h",
                 custom_data=["part_fmt"],
                 title="Composition par statut de l'offre d'apprentissage par région (2025)")
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name} : %{customdata[0]}<extra></extra>")
    fig.update_layout(barmode="stack", xaxis_title="Part de l'offre d'apprentissage (%)",
                      yaxis_title="", template="plotly_white", legend_title_text="Statut")
    return fig

def fig_remplissage_prive_public(_annees=None):
    g = charger_web_csv("remplissage_filiere.csv")
    top = g[g["secteur"] == "Privé"].set_index("filiere")["capa"].sort_values(ascending=False).head(14).index
    g = g[g["filiere"].isin(top)].copy()
    g["filiere"] = pd.Categorical(g["filiere"], categories=list(top)[::-1], ordered=True)
    g["rf"] = g["remplissage"].map(lambda x: _fmt_pct_fr(x, 1))
    g["cf"] = g["capa"].map(_fmt_int_fr)
    g["af"] = g["adm"].map(_fmt_int_fr)
    fig = px.bar(g, x="remplissage", y="filiere", color="secteur", orientation="h", barmode="group",
                 color_discrete_map={"Privé": COLOR_PRIVATE, "Public": COLOR_PUBLIC},
                 custom_data=["rf", "cf", "af"], title="Remplissage privé vs public par filière (2025)")
    fig.update_traces(hovertemplate=("<b>%{y}</b><br>Secteur : %{fullData.name}<br>"
                                     "Remplissage : %{customdata[0]}<br>Capacité : %{customdata[1]} places<br>"
                                     "Admis : %{customdata[2]}<extra></extra>"))
    fig.update_layout(xaxis_title="Taux de remplissage (%)", yaxis_title="", template="plotly_white")
    return fig

def fig_profil_social_academique(_annees=None):
    g = charger_web_csv("profil_social_academique.csv")
    ordre = ["Public", "Privé sous contrat d'association", "Privé enseignement supérieur", "Privé hors contrat"]
    g["statut"] = pd.Categorical(g["statut"], categories=ordre, ordered=True)
    g = g.sort_values("statut")
    long = g.melt(id_vars=["statut", "neobac"], value_vars=["% boursiers", "% TB+", "% sans mention"],
                  var_name="indicateur", value_name="part")
    long["pf"] = long["part"].map(lambda x: _fmt_pct_fr(x, 1))
    long["nf"] = long["neobac"].map(_fmt_int_fr)
    fig = px.bar(long, x="indicateur", y="part", color="statut", barmode="group",
                 custom_data=["pf", "nf"], title="Profil social et académique des admis par sous-statut (2025)")
    fig.update_traces(hovertemplate=("<b>%{fullData.name}</b><br>%{x} : %{customdata[0]}<br>"
                                     "Admis néo-bacheliers : %{customdata[1]}<extra></extra>"))
    fig.update_layout(xaxis_title="", yaxis_title="Part (%)", template="plotly_white")
    return fig

def fig_boursiers_filiere(_annees=None):
    g = charger_web_csv("boursiers_filiere.csv")
    communes = set(g[g["secteur"] == "Privé"]["nom"]) & set(g[g["secteur"] == "Public"]["nom"])
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Privé", "Public"],
                        specs=[[{"secondary_y": True}, {"secondary_y": True}]],
                        horizontal_spacing=0.13)
    for col, sec in [(1, "Privé"), (2, "Public")]:
        sub = g[g["secteur"] == sec].sort_values("boursiers", ascending=False).head(10).copy()
        sub["bf"] = sub["boursiers"].map(_fmt_int_fr)
        sub["pf"] = sub["part"].map(lambda x: _fmt_pct_fr(x, 1))
        fig.add_trace(go.Bar(x=sub["nom"], y=sub["boursiers"],
                             marker_color=(COLOR_PRIVATE if sec == "Privé" else COLOR_PUBLIC),
                             name="Nombre de boursiers", showlegend=(col == 1),
                             customdata=sub["bf"],
                             hovertemplate="<b>%{x}</b><br>Boursiers : %{customdata}<extra></extra>"),
                      row=1, col=col, secondary_y=False)
        fig.add_trace(go.Scatter(x=sub["nom"], y=sub["part"], mode="markers",
                                 marker=dict(symbol="square", size=11, color="#D4537E"),
                                 name="Part de boursiers (%)", showlegend=(col == 1),
                                 customdata=sub["pf"],
                                 hovertemplate="<b>%{x}</b><br>Part : %{customdata}<extra></extra>"),
                      row=1, col=col, secondary_y=True)
        comm = sub[sub["nom"].isin(communes)]
        if not comm.empty:
            fig.add_trace(go.Scatter(x=comm["nom"], y=comm["part"], mode="markers",
                                     marker=dict(symbol="circle-open", size=22,
                                                 line=dict(width=2, color="#D4537E")),
                                     name="Filière commune (comparable)", showlegend=(col == 1),
                                     hoverinfo="skip"),
                          row=1, col=col, secondary_y=True)
        fig.update_yaxes(title_text="Boursiers", row=1, col=col, secondary_y=False, tickformat=",.0f")
        fig.update_yaxes(title_text="Part (%)", row=1, col=col, secondary_y=True,
                         range=[0, 40], ticksuffix=" %", showgrid=False)
        fig.update_xaxes(tickangle=-40, row=1, col=col)
    fig.update_layout(title="Boursiers par filière : comparaison public / privé (2025)",
                      template="plotly_white", height=580,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5))
    return fig

# ============================================================
# CHARGEMENT
# ============================================================
try:
    _verifier_data_web()
    # Variables conservées pour ne pas modifier les appels existants plus bas.
    atlas, annees, appr = None, {"2025": None}, None
except Exception as e:
    st.error("Erreur de chargement des données allégées.")
    st.exception(e)
    st.stop()


# ============================================================
# SOMMAIRE LATÉRAL (sans bibliographie — voir page Bibliographie)
# ============================================================
st.sidebar.title("Sommaire")
st.sidebar.markdown("""
<style>.toc a{text-decoration:none;color:#444;display:block;padding:1px 0;font-size:0.88rem;}
.toc a:hover{color:#534AB7;} .toc .part{font-weight:700;color:#534AB7;margin-top:8px;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;}</style>
<div class="toc">
<a href="#intro"><b>Introduction</b></a>
<div class="part">Partie I · Définir et objectiver</div>
<a href="#c1">1 · Le piège du mot privé</a>
<a href="#c2">2 · Un même mot pour plusieurs mondes</a>
<a href="#c3">3 · Le for-profit</a>
<div class="part">Partie II · Une croissance inégale</div>
<a href="#c4">4 · Public vs privé</a>
<a href="#c5">5 · Géographie</a>
<a href="#c6">6 · L'alternance</a>
<div class="part">Partie III · Ce que le privé propose</div>
<a href="#c7">7 · Filières et attractivité</a>
<div class="part">Partie IV · Publics et résultats</div>
<a href="#c8">8 · Qui entre dans le privé ?</a>
<a href="#c9">9 · Les zones d'ombre</a>
<div class="part">Pour finir</div>
<a href="#ccl">Conclusion</a>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption("Cliquez pour aller à une section. La bibliographie est sur la page « Bibliographie » (menu en haut).")

# ============================================================
# EN-TÊTE
# ============================================================
anchor("intro")
st.markdown("<p style='color:#D4A017;text-transform:uppercase;letter-spacing:3px;font-size:0.8rem;'>"
            "Projet Capstone · Master 1 Économie, Data & Transition</p>", unsafe_allow_html=True)
st.title("L'essor de l'enseignement supérieur privé en France")
st.markdown("*Acteurs, filières, alternance et nouvelles lignes de régulation*")
st.markdown("<p class='intro-lead'>Que recouvre réellement la croissance de l'enseignement supérieur "
            "privé en France : quels acteurs la portent, quelles formations se développent, quels publics "
            "y accèdent, et comment l'alternance, le for-profit et les régimes de reconnaissance "
            "transforment-ils ce secteur ?</p>", unsafe_allow_html=True)

# ============================================================
# INTRODUCTION
# ============================================================
st.header("Introduction")
st.markdown("""
En vingt ans, l'enseignement supérieur français est passé de 2,17 à 3,09 millions d'étudiants inscrits. La hausse est de 42 %, elle paraît raconter une histoire simple : on étudie plus, et plus
longtemps. C'est exact, mais c'est aussi la partie la moins intéressante de l'histoire. On se demande alors
ce que cache cette évolution.

Cette croissance n'a pas profité de la même manière à tous les acteurs. Derrière l'augmentation des effectifs
d'étudiants inscrits se joue une recomposition plus discrète, et plus politique : le secteur privé, longtemps
en retrait, est devenu l'un des moteurs principaux de cette expansion. Aujourd'hui, plus d'un quart des
étudiants relèvent du privé, et parmi eux, près de la moitié d'un établissement à but lucratif, soit environ
un étudiant sur dix.

Ce travail enquête sur cette transformation à partir des données publiques : les effectifs régionalisés du
SIES, à travers la base ATLAS, et les données d'admission de Parcoursup. Il défend une idée simple et
exigeante à la fois : le mot « privé » ne désigne pas une seule réalité. Il faut le décomposer pour le
comprendre. Plus ce secteur prend de l'ampleur, plus il devient indispensable d'en distinguer les composantes, non par souci de classification, mais parce que comprendre clairement l'offre privée est désormais une
question d'intérêt public. Avant de regarder qui compose le privé, il faut mesurer l'ampleur du mouvement
global.
""")
st.plotly_chart(fig_evolution_total_inscrits(atlas), use_container_width=True)
st.caption("Figure 1 — Évolution du nombre d'étudiants inscrits dans le supérieur (2001-2025). "
           "Source : SIES, base ATLAS (effectifs d'étudiants inscrits), niveau national, 2001-2025 ; calculs de l'autrice.")
st.markdown("""
Le privé n'est plus un secteur que l'on mentionne en marge du public ; il devient l'espace où se concentrent
plusieurs transformations à la fois : professionnalisation, apprentissage, écoles nouvelles, logiques de
groupe, titres RNCP, promesse d'insertion rapide. Derrière cette hausse des effectifs dans le supérieur, on
observe un déplacement progressif vers le privé. Mais ce privé est hétérogène, et derrière cette hétérogénéité
se cachent des modèles économiques opposés ; et derrière eux se trouve un moteur récent, l'alternance. Mais
avant de suivre cette croissance, une difficulté doit être levée : le mot que nous employons sans cesse
« privé » est précisément celui qui résiste le plus à la mesure.
""")

# ============================================================
# PARTIE I
# ============================================================
st.markdown("## Partie I - Définir et objectiver l'enseignement supérieur privé")

# ---- Chapitre 1 ----
anchor("c1")
st.header("1 · Le piège du mot privé")
st.markdown("""
Le premier piège est là : le privé ne désigne pas une seule réalité. C'est une catégorie pratique, mais
difficile à encadrer ou à classifier. Selon la source utilisée pour l'analyse, elle ne recouvre pas exactement
les mêmes établissements, ni les mêmes formations, ni les mêmes publics. C'est embêtant, n'est-ce pas ? Car
cette difficulté n'est pas un simple détail de méthode : elle conditionne tout ce que l'on peut dire ensuite
sur la croissance du secteur.

Dans les données de Parcoursup, le privé se scinde en plusieurs statuts : le privé sous contrat d'association
avec l'État, souvent confessionnel ou associatif ; le privé d'enseignement supérieur, qui rassemble notamment
des grandes écoles et une partie des groupes privés ; et le privé hors contrat. En théorie, on pourrait aussi
distinguer le privé lucratif et le privé non lucratif, car ces deux modèles ne reposent pas sur les mêmes
logiques économiques. Mais cette distinction, pourtant essentielle, n'apparaît pas clairement dans ces bases.
Dans la base ATLAS du SIES, la lecture est encore plus agrégée : les établissements sont distingués entre
public et privé, sans toujours permettre de retrouver la finesse juridique des acteurs ni leur finalité
lucrative ou non lucrative. Deux bases peuvent donc parler du « privé » sans parler exactement du même objet.

Cette précaution est essentielle. Un chiffre sur le privé n'a de sens que si l'on sait ce qu'il mesure : des
inscrits, des admis, des formations, des apprentis, des établissements, ou des diplômes. Le privé n'est pas
un bloc face au public ; c'est un ensemble d'acteurs aux statuts, aux finalités et aux garanties très
différents.

La difficulté devient plus forte encore lorsqu'on regarde ce que l'étudiant croit réellement acheter. Une
école privée peut délivrer un diplôme visé par l'État, conférer un grade de licence ou de master, préparer un
titre inscrit au RNCP, ou proposer seulement un diplôme d'établissement. Ces régimes de reconnaissance ne sont
pas équivalents : ils n'ouvrent pas les mêmes droits, ne garantissent pas la même valeur et ne donnent pas les
mêmes garanties pour la suite du parcours. Le risque n'est pas seulement de payer cher : il est aussi de sortir
avec un diplôme dont la valeur réelle est bien plus faible que celle annoncée. Quand on pense que ce choix engage souvent plusieurs années d'études, un budget familial important et parfois un prêt étudiant.
""")
df_reco = pd.DataFrame({
    "Reconnaissance": ["Diplôme visé par l'État", "Grade licence/master", "Titre RNCP", "Diplôme d'établissement"],
    "Signification": ["Reconnaissance académique accordée par le ministère après évaluation",
                      "Alignement avec le système universitaire LMD, lisibilité nationale et internationale",
                      "Certification professionnelle inscrite au répertoire de France Compétences",
                      "Diplôme propre à l'école, sans reconnaissance académique automatique"],
    "Enjeu pour l'étudiant": ["Plus forte crédibilité académique et institutionnelle",
                              "Meilleure lisibilité pour la poursuite d'études et la mobilité",
                              "Reconnaissance professionnelle utile, mais différente d'un diplôme universitaire",
                              "Valeur plus incertaine, dépendante de la réputation de l'établissement"],
})
st.dataframe(df_reco, use_container_width=True, hide_index=True)
st.caption("Tableau 1 — Les régimes de reconnaissance des diplômes. "
           "Source : France Compétences (RNCP) ; MESR ; Assemblée nationale, rapport n°2458, 2024 ; synthèse de l'autrice.")
st.markdown("""
La question n'est donc pas seulement : combien coûte l'école ? Elle est aussi : que croit-on acheter ? Un
même intitulé — « bachelor », « mastère », « formation certifiante » peut renvoyer à des réalités très
différentes selon le niveau de reconnaissance obtenu. Pour une famille, comme pour un étudiant pourtant
informé, la différence entre un grade, un titre RNCP et un diplôme d'établissement peut rester floue, car ces
catégories appartiennent à un langage administratif rarement maîtrisé au moment de choisir une formation.
C'est ici que la croissance du privé devient un enjeu public : plus le secteur se développe, plus l'information
doit être claire. Une fois ce vocabulaire stabilisé, une question demeure : qui sont, concrètement, les
établissements qui peuplent ce privé ?
""")

# ---- Chapitre 2 ----
anchor("c2")
st.header("2 · Le privé : un même mot pour plusieurs mondes")
st.markdown("""
C'est ici que l'analyse doit ralentir. Parler du privé au singulier conduit immédiatement à une erreur, car
un institut catholique fondé au XIXᵉ siècle, une école de commerce reconnue, une école de santé conventionnée
et une école détenue par un groupe financier ne relèvent pas du même monde.

Le privé ne remplace pas ses anciens visages ; il en ajoute de nouveaux. La première couche est historique :
instituts catholiques, établissements confessionnels, écoles consulaires ou associatives, souvent anciennes,
parfois reconnues par l'État, généralement éloignées d'une logique strictement lucrative. La deuxième est
professionnalisante : écoles spécialisées en santé, social, numérique, design, communication, management ou
ingénierie, répondant à une demande plus directement reliée à l'emploi. La troisième, plus récente et plus
discutée, est celle des groupes privés à but lucratif, qui raisonnent en marques, campus, rachats et
portefeuilles de formations.

Pour comprendre ce qu'est devenu cet archipel, il faut regarder non seulement combien le privé a grandi, mais
comment sa composition interne s'est déplacée.
""")
st.plotly_chart(fig_donuts_etablissements(atlas), use_container_width=True)
st.caption("Figure 2 — Répartition des étudiants privés par type d'établissement : 2001 vs 2024. "
           "Source : SIES, base ATLAS (secteur privé, niveau national), regroupements par type d'établissement ; calculs de l'autrice.")
st.markdown("""
Le graphique ne raconte pas seulement une hausse ; il révèle un déplacement du centre de gravité. En 2001, les
étudiants du privé se répartissaient de façon relativement équilibrée : les écoles de commerce occupaient déjà
une place importante (38 %), mais le paramédical et social (23 %), les établissements spécialisés et les
universités privées formaient un ensemble dispersé. En 2024-2025, les écoles de commerce concentrent près de
la moitié des effectifs, tandis que le paramédical retombe à 12 %.

Ce recul mérite une lecture attentive, car il est trompeur en apparence : le paramédical n'a pas diminué, il
est plutôt passé d'environ 43 000 à 65 000 étudiants. Mais il a crû bien plus lentement que le commerce, si
bien que sa part dans l'ensemble a fondu de moitié. C'est toute la différence entre une baisse en part et une
baisse en volume. Le privé ne s'est donc pas seulement agrandi ; il s'est recomposé autour de formations plus
professionnalisantes, plus directement associées à l'emploi. Cette bascule prépare la question suivante :
quels acteurs portent cette dynamique ?
""")

# ---- Chapitre 3 ----
anchor("c3")
st.header("3 · Quand l'école devient un marché : le for-profit")
st.markdown("""
Une partie du privé fonctionne désormais comme un secteur économique à part entière. Des groupes rachètent des
écoles, les regroupent sous une marque commune, ouvrent des campus dans plusieurs villes et raisonnent en
portefeuille de formations. L'école n'est plus seulement un lieu de transmission du savoir : elle devient aussi
un actif, avec une logique de croissance, de rentabilité et d'image.

Cette évolution ne signifie pas que tout le privé serait lucratif, ce serait une erreur de le penser. Un
établissement associatif, un EESPIG, une école consulaire, un institut catholique et un groupe détenu par des
investisseurs ne relèvent pas du même modèle. Mais dans les données publiques, ces différences restent
difficiles à identifier directement. Le rapport de l'Assemblée nationale sur l'enseignement supérieur privé à
but lucratif (n°2458, 2024) a précisément cherché à documenter ces acteurs.
""")
st.subheader("Les principaux groupes privés à but lucratif")
df_grp = pd.DataFrame({
    "Groupe": ["Galileo", "Eduservices", "Omnes", "IONIS", "AD Education", "Compétences & Développement", "Ynov"],
    "Écoles": [61, 24, 15, 29, 19, 14, 1],
    "Étudiants France": ["85 000", "44 000", "32 000", "29 000", "11 500", "16 000", "11 000"],
    "Étudiants total": ["210 000", "44 000", "40 000", "35 000", "36 000", "16 000", "11 000"],
    "Positionnement": ["commerce, arts, design, digital, management", "BTS, commerce, management, alternance",
                       "commerce, management, ingénierie, international", "informatique, ingénierie, business, tech",
                       "art, design, communication, luxe, création", "management, commerce, RH, ingénierie",
                       "digital, informatique, création numérique"],
})
st.dataframe(df_grp, use_container_width=True, hide_index=True)
st.caption("Tableau 2 — Principaux groupes privés à but lucratif. "
           "Source : Assemblée nationale, rapport d'information n°2458, 10 avril 2024 (annexe). Effectifs déclarés par les groupes.")
st.markdown("""
Ces chiffres changent la perception du secteur. Un seul groupe, Galileo, revendique plus de 200 000 étudiants
dans le monde — davantage que la plupart des universités françaises prises individuellement. La logique n'est
plus celle d'un établissement isolé, mais d'une marque qui décline ses écoles sur plusieurs campus, plusieurs
filières et plusieurs pays, en s'appuyant largement sur l'alternance pour réduire le coût direct supporté par
les familles. Cette promesse peut répondre à de vraies attentes ; elle ouvre aussi une zone de risque lorsque
la valeur du diplôme, les frais réels ou la qualité pédagogique ne sont pas transparents.

Reste à savoir si cette logique se lit dans les chiffres de croissance. Le graphique ci-dessous mesure, pour
chaque type d'établissement, le gain d'effectifs entre 2001 et 2024 et la part qu'il représente dans la
croissance totale du privé (gain du type ÷ gain total du privé).
""")
st.plotly_chart(fig_croissance_par_type(atlas), use_container_width=True)
st.caption("Figure 3 — Contribution des types d'établissement à la croissance du privé (2001-2024). "
           "Source : SIES, base ATLAS (secteur privé, niveau national) ; gain d'effectifs par type entre 2001-02 et 2024-25 ; calculs de l'autrice.")
st.markdown("""
Sur les 342 000 étudiants gagnés par les établissements privés entre 2001 et 2024 (SIES/ATLAS), les seules
écoles de commerce, gestion et comptabilité en expliquent 55 %. Le paramédical et social, pilier historique,
ne pèse que 6,5 % de cette croissance, avec la plus faible progression de toutes. Le privé ne s'est donc pas
renforcé en consolidant ses segments confessionnels ou sociaux : il s'est renforcé autour de formations
compatibles avec une logique de marché.

Une précision essentielle s'impose ici. Ce graphique mesure des *types d'établissement* : écoles de commerce,
d'art, paramédical; et non leur caractère lucratif. Les écoles de commerce, qui dominent la croissance du
privé, correspondent en partie au for-profit, mais les deux catégories ne se confondent pas : une école de
commerce peut être associative et non lucrative. Le statut juridique visible dans les bases ne dit pas qui
possède l'école ni selon quelle finalité elle fonctionne. Les données publiques ne permettent donc pas
d'isoler le lucratif ; seuls les rapports parlementaires le documentent. Cette frontière entre ce que l'on
mesure et ce que l'on doit aller chercher ailleurs est l'un des fils de l'enquête.
""")

# ============================================================
# PARTIE II
# ============================================================
st.markdown("## Partie II - Une croissance rapide mais territorialement inégale")

# ---- Chapitre 4 ----
anchor("c4")
st.header("4 · Croissance : public et privé ne suivent pas la même trajectoire")
st.markdown("""
La croissance globale du supérieur, on l'a vu, cache une privatisation. Pour la mesurer, il faut séparer les
deux trajectoires et les poser l'une à côté de l'autre. C'est là que l'écart, jusqu'ici noyé dans le total,
devient visible. L'enseignement supérieur public reste majoritaire et structure encore l'essentiel du système.
Mais la question n'est pas seulement celle du poids actuel : elle est celle de la dynamique. Qui absorbe la
nouvelle demande ?
""")
st.plotly_chart(fig_croissance_prive_vs_public(atlas), use_container_width=True)
st.caption("Figure 4 — Croissance comparée du public et du privé (2001-2025). "
           "Source : SIES, base ATLAS (effectifs d'étudiants inscrits, niveau national, par secteur) ; calculs de l'autrice.")
st.markdown("""
Les deux courbes ne disent pas la même chose. Le public a progressé de 22 % en vingt-quatre ans, et sa courbe
s'aplatit nettement à partir de 2010. Le privé, lui, a crû de 175 % : il a presque triplé, passant d'environ
292 000 à 802 000 étudiants. Le chiffre décisif est le suivant : le privé, qui ne pesait que 13,5 % des
effectifs en 2001, a porté à lui seul 55 % de la croissance totale du supérieur sur la période, et sa part a
doublé pour atteindre 26 % en 2024.

Ce que la première courbe d'évolution de l'enseignement supérieur présentait comme une simple massification se révèle donc, pour une large
part, une privatisation. Cette lecture ne signifie pas que les étudiants auraient quitté le public pour le
privé : elle dit que lorsque le système s'est élargi, le privé a davantage profité de l'élargissement. La
nuance évite deux erreurs opposées : exagérer le recul du public, ou minimiser la montée du privé. Reste à
savoir où cette privatisation se produit, car elle n'a pas la même intensité partout.
""")

# ---- Chapitre 5 ----
anchor("c5")
st.header("5 · Une géographie qui ne se résume pas à Paris")
st.markdown("""
La progression du privé ne se voit pas seulement dans les chiffres nationaux ; elle prend aussi forme dans les
territoires. Certaines régions étaient déjà fortement marquées par sa présence au début des années 2000,
tandis que d'autres ont connu une accélération plus récente. Regarder les territoires permet de dépasser
l'idée d'une simple hausse générale. La carte suit la part du privé dans les effectifs régionaux à quatre
moments : 2001, 2013, 2018 et 2024.
""")
try:
    st.plotly_chart(fig_part_prive_regions(atlas), use_container_width=True)
    st.caption("Figure 5 — Part du privé par région : 2001, 2013, 2018 et 2024. "
               "Source : SIES, base ATLAS (niveau régional, par secteur) ; calculs de l'autrice. (Carte interactive : nécessite Internet.)")
except Exception:
    st.warning("La carte interactive n'a pas pu se charger (accès Internet au fond de carte requis). "
               "Le graphique de croissance et le tableau ci-dessous restent disponibles.")
    st.caption("Figure 5 — Part du privé par région. Source : SIES, base ATLAS (niveau régional, par secteur) ; calculs de l'autrice.")
st.markdown("""
À première vue, on pourrait croire que la progression du privé est surtout une affaire parisienne.
L'Île-de-France concentre les grandes écoles, les groupes privés et une forte densité étudiante. Pourtant, les
cartes racontent une histoire plus nuancée : la montée du privé ne se limite pas à la région parisienne, elle
gagne progressivement plusieurs territoires.

En 2001, les Pays de la Loire se distinguent déjà avec une part du privé élevée, autour de 25 %. Cette avance
traduit un ancrage ancien, probablement lié à des établissements confessionnels, associatifs ou spécialisés.
En 2013 puis en 2018, la carte se fonce progressivement : les Hauts-de-France, le Centre-Val de Loire, mais
aussi certaines régions de l'Ouest et du Sud deviennent plus visibles. En 2024, les Pays de la Loire restent
en tête, autour de 36 %, mais le Centre-Val de Loire atteint environ 32 %, les Hauts-de-France près de 28 % et
Provence-Alpes-Côte d'Azur environ 27 %.

Ces cartes corrigent donc une idée trop simple : l'essor du privé n'est pas uniquement porté par Paris. Il est
national, mais inégal. Certaines régions disposent d'un socle ancien, tandis que d'autres connaissent une
montée plus récente. Le privé s'étend, mais il ne s'homogénéise pas. Il faut toutefois distinguer la part et
la croissance : une région très privée en 2024 n'est pas forcément celle où le privé a le plus progressé
depuis 2001.
""")
st.plotly_chart(fig_croissance_regions_bar(atlas), use_container_width=True)
st.caption("Figure 6 — Croissance des effectifs privés par région (2001-2024, hors Corse). "
           "Source : SIES, base ATLAS (secteur privé, niveau régional) ; calculs de l'autrice.")
st.markdown("""
Le graphique de croissance complète la lecture des cartes. Il ne montre plus seulement les régions où le privé
pèse le plus, mais celles où il a le plus progressé depuis 2001. Certaines hausses peuvent traduire un effet
de rattrapage, notamment lorsque le privé partait d'un niveau faible au début de la période. D'autres peuvent
être liées à l'ouverture de campus, au développement de formations professionnalisantes ou à la montée de
l'alternance. Mais les données disponibles indiquent surtout *où* le privé a grandi ; elles ne permettent pas
toujours d'en identifier précisément les causes.

La Corse a été écartée du classement, car son taux de croissance dépasse 360 % mais repose sur de très faibles
effectifs, passés d'environ 106 à 490 étudiants privés. L'inclure aurait donné une impression trompeuse et
faussé la comparaison entre régions. Le tableau ci-dessous permet de lire les volumes derrière les
pourcentages : pour comprendre la transformation, il faut croiser trois éléments: le niveau de départ, le
niveau d'arrivée et le taux de croissance. Pris séparément, aucun ne suffit.
""")
_dfreg = df_croissance_region(atlas)
_hors = ["Corse", "Mayotte", "Guyane", "Guadeloupe", "Martinique", "La Réunion",
         "Collectivités d'outre-mer", "Collectivités d’outre-mer", "Étranger"]
_dfreg = _dfreg[~_dfreg["Région"].isin(_hors)]
st.dataframe(_dfreg, use_container_width=True, hide_index=True)
st.caption("Tableau — Effectifs privés par région en 2001 et 2024 et taux de croissance. Source : SIES, base ATLAS ; calculs de l'autrice.")

# ---- Chapitre 6 ----
anchor("c6")
st.header("6 · L'alternance : solution financière ou nouveau filtre ?")
st.markdown("""
À première vue, l'alternance semble apporter une réponse presque idéale à l'un des principaux reproches faits
au privé : son coût. Là où une formation privée classique peut représenter plusieurs milliers d'euros par an,
l'apprentissage promet autre chose : une formation financée, une expérience professionnelle, un salaire, et
une entrée plus directe dans l'emploi. Pour beaucoup de familles, la différence est décisive. Le privé ne
paraît plus seulement payant ; il peut devenir accessible, à condition d'obtenir un contrat.

Mais c'est précisément à cette condition que se joue le caractère à double tranchant du modèle. L'alternance
ne supprime pas la sélection : elle la déplace. L'étudiant ne doit plus seulement choisir une école, être
admis, ou trouver les moyens de payer. Il doit aussi convaincre une entreprise. Autrement dit, l'alternance
transforme une partie du coût financier en épreuve d'accès au marché du travail. Avant même de regarder les
filières, il faut donc observer où cette offre d'apprentissage se déploie et qui la porte.
""")
st.plotly_chart(fig_composition_statut_region(appr), use_container_width=True)
st.caption("Figure 7 — Composition par statut de l'offre d'apprentissage par région (2025). "
           "Source : Parcoursup, base apprentissage (session 2025) ; statut de l'établissement de la filière ; calculs de l'autrice.")
st.markdown("""
Le graphique confirme que l'apprentissage n'est pas porté de la même manière selon les régions. Au niveau
national, l'offre d'apprentissage visible sur Parcoursup est très majoritairement privée : le public ne
représente qu'environ 17 % des capacités, contre près de 83 % pour l'ensemble du privé. On aurait pu penser
que l'apprentissage restait d'abord un outil public de formation professionnelle ; les données montrent au
contraire qu'il est devenu un espace très investi par les acteurs privés.

Cette présence privée est particulièrement forte en Île-de-France, où elle atteint environ 92 % des capacités,
en Bretagne autour de 91 %, et dans les Pays de la Loire autour de 89 %. Mais le privé n'a pas partout le même
visage. En Bretagne, par exemple, la forte présence du privé hors contrat peut s'expliquer par le développement
d'écoles spécialisées et de formations professionnalisantes plus souples, souvent tournées vers le commerce, le
numérique ou les services, secteurs compatibles avec l'alternance.

Les données SIES/ATLAS permettent de suivre l'évolution des apprentis en BTS dans le temps, en distinguant
public et privé. Les données Parcoursup complètent cette lecture pour 2025, mais uniquement pour les formations
présentes sur la plateforme. L'analyse porte donc sur une partie visible du privé : certains bachelors,
mastères ou écoles recrutant hors Parcoursup échappent à l'observation.
""")
st.plotly_chart(fig_treemap_filiere_apprentissage(appr), use_container_width=True)
st.caption("Figure 8 — Volume du privé par filière en apprentissage (2025). "
           "Source : Parcoursup, base apprentissage (session 2025), formations du privé ; calculs de l'autrice.")
st.markdown("""
Le premier élément frappant est la place du BTS. Dans l'offre privée en apprentissage visible sur Parcoursup,
il domine très largement les autres filières. Ce n'est pas un hasard : le BTS est court, professionnalisant,
bien identifié par les employeurs, et compatible avec une organisation en entreprise. Il constitue donc un
terrain idéal pour le développement de l'alternance privée. Il concentre une promesse simple et puissante : se
former à un métier, financer ses études et entrer plus rapidement dans l'emploi.
""")
st.plotly_chart(fig_apprentis_bts(atlas), use_container_width=True)
st.caption("Figure 9 — Apprentis en BTS : total, privé et public (2015-2025). "
           "Source : SIES, base ATLAS, colonne « inscrits en STS sous statut d'apprenti », niveau national ; calculs de l'autrice.")
st.markdown("""
Le basculement est net : en moins de dix ans, les apprentis en BTS passent d'environ 60 000 à 187 000. Mais le
plus important n'est pas seulement le niveau atteint : c'est la manière dont cette croissance se répartit. La
courbe du privé suit presque la courbe totale, ce qui signifie que l'augmentation du nombre d'apprentis en BTS
est très largement portée par le secteur privé. L'accélération devient particulièrement visible à partir de
2020. Elle intervient après la réforme de l'apprentissage de 2018 et dans le contexte des aides exceptionnelles
à l'embauche d'apprentis mises en place lors de la crise sanitaire. Il serait imprudent d'attribuer
mécaniquement la hausse à une seule cause, mais le résultat est clair : l'apprentissage devient à ce moment-là
un levier central de développement pour le BTS privé. L'étudiant est attiré par la possibilité de ne pas payer
directement ; l'établissement sécurise une partie de ses ressources ; l'entreprise devient un acteur de la
formation.
""")
st.plotly_chart(fig_part_apprentissage_bts_secteur(atlas), use_container_width=True)
st.caption("Figure 10 — Part de l'apprentissage dans le BTS par secteur (2015-2025). "
           "Source : SIES, base ATLAS ; apprentis en STS rapportés au total des inscrits en STS, pour chaque secteur ; calculs de l'autrice.")
st.markdown("""
Pour comprendre si cette hausse change réellement la nature du BTS, il faut passer des volumes aux proportions.
Le calcul est simple : pour chaque secteur, on rapporte le nombre d'étudiants de BTS sous statut d'apprenti au
nombre total d'étudiants inscrits en BTS dans ce même secteur. La formule est donc : part de l'apprentissage
dans le BTS privé = (nombre d'apprentis en BTS privé ÷ nombre total d'étudiants en BTS privé) × 100. Le même
calcul est fait pour le public. Ces pourcentages ne s'additionnent donc pas : ils ne disent pas quelle part des
apprentis va dans le privé ou le public, mais quelle place l'apprentissage occupe à l'intérieur de chaque
secteur.

C'est dans le BTS privé que la transformation apparaît le plus clairement : la part de l'apprentissage passe
d'environ 33 % à 71 %. Cela signifie qu'en 2024, près de trois étudiants de BTS privé sur quatre sont apprentis.
Dans le public, la progression existe, mais elle reste beaucoup plus limitée : la part passe d'environ 10 % à
20 %. Derrière un même diplôme, deux modèles se distinguent désormais : le BTS public reste encore
majoritairement scolaire, tandis que le BTS privé s'organise de plus en plus autour de l'entreprise, du contrat
et du financement par l'apprentissage.
""")
st.plotly_chart(fig_recherche_contrat(appr), use_container_width=True)
st.caption("Figure 11 — Apprentissage 2025 : candidats sans employeur par statut. "
           "Source : Parcoursup, base apprentissage (session 2025) ; vœux en « recherche de contrat » rapportés au total des candidats ; calculs de l'autrice.")
st.markdown("""
Mais cette promesse repose sur une condition moins visible : l'existence d'un contrat. Après une acceptation
provisoire par l'établissement, on pourrait croire que le plus difficile est fait. Or, l'entrée en formation
reste suspendue à une seconde validation : celle de l'entreprise. Tous les candidats ne disposent pas des mêmes
ressources pour trouver un employeur : certains maîtrisent déjà les codes du recrutement, sont accompagnés ou
disposent d'un réseau ; d'autres doivent chercher seuls.

C'est dans le privé hors contrat que la fragilité du modèle apparaît le plus fortement. En 2025, près de
441 600 candidats y sont encore en recherche de contrat, soit 88,8 % des candidats, la proportion la plus
élevée de tous les statuts. Elle reste élevée dans le privé sous contrat d'association (76,5 %) et dans le privé
d'enseignement supérieur (72,5 %). Le public est aussi concerné, mais dans une moindre mesure : 62,3 % des
candidats y sont en recherche d'employeur. Ce taux mesure toutefois les vœux en recherche de contrat à un
instant donné, et non un échec définitif : une partie de ces candidats trouvera un employeur, et signera donc
un contrat, plus tard dans la campagne.
L'alternance a bien permis au privé de croître rapidement, surtout dans les BTS, en rendant certaines
formations plus attractives et parfois plus accessibles financièrement. Mais elle ne fait pas disparaître la
barrière d'entrée : elle la déplace. Le coût peut être allégé, mais une autre condition apparaît, celle du
contrat. Or cette condition ne dépend pas seulement de l'étudiant ; elle dépend aussi du regard des
entreprises, parfois prudentes face à des établissements moins connus ou dont la reconnaissance reste
difficile à identifier. L'alternance devient donc à la fois un modèle de croissance pour le privé et un
filtre d'accès plus discret, mais bien réel.
""")

# ============================================================
# PARTIE III
# ============================================================
st.markdown("## Partie III - Ce que le privé propose")

# ---- Chapitre 7 ----
anchor("c7")
st.header("7 · Là où le privé s'installe : filières, diplômes et attractivité")
st.markdown("""
Le privé ne se développe pas au hasard. Sa croissance se concentre dans des filières où la promesse
professionnelle est immédiatement lisible : commerce, gestion, santé, social, numérique, design, communication
ou management. À l'inverse, les disciplines plus fondamentales : lettres, sciences générales, sciences humaines; restent davantage associées au public. Pour comprendre cette logique, le taux de remplissage est un
indicateur utile : il mesure la part des places ouvertes qui sont effectivement occupées.

Le taux de remplissage est calculé en rapportant le nombre d'admis à la capacité d'accueil déclarée pour chaque
formation. Dans ce graphique, les filières retenues sont les quatorze filières où le privé ouvre le plus de
places sur Parcoursup 2025. Le but n'est donc pas de représenter toutes les formations, mais d'observer les
espaces où le privé est fortement présent, puis de comparer son remplissage à celui du public.
""")
st.plotly_chart(fig_remplissage_prive_public(annees), use_container_width=True)
st.caption("Figure 12 — Remplissage privé vs public par filière (2025). "
           "Source : Parcoursup (session 2025) ; admis rapportés à la capacité déclarée, par filière et secteur ; calculs de l'autrice.")
st.markdown("""
La comparaison révèle une réalité plus nuancée qu'une simple opposition entre public et privé. Dans certaines
filières longues et fortement reconnues, le public conserve un net avantage. C'est le cas des formations
d'ingénieur Bac +5, où le public atteint près de 98 % de remplissage, contre environ 72 % dans le privé. Le
même écart apparaît dans les écoles de commerce et de management Bac +5 : le public remplit presque toutes ses
places, tandis que le privé reste autour de 69 %. Lorsque les deux secteurs se retrouvent sur des formations
prestigieuses et bien identifiées, le public garde une forte capacité d'attraction.

Mais l'image n'est pas uniforme. Le privé se remplit très bien dans certaines filières où sa présence est
installée ou la promesse professionnelle claire : le D.E Infirmier atteint près de 98 % de remplissage dans le
privé, presque autant que le public ; le D.E Éducateur spécialisé atteint aussi environ 98 %, contre 78 % dans
le public ; et le Commerce international est davantage rempli dans le privé, autour de 88 %, contre 62 % dans
le public.

Le graphique montre donc que l'attractivité du privé varie fortement selon les filières. Là où le public offre
une alternative reconnue et moins coûteuse, le privé peut laisser davantage de places vacantes. À l'inverse,
lorsqu'il est bien installé ou directement associé à l'emploi, il résiste mieux. Cette lecture appelle une
précaution : Parcoursup ne couvre pas tout le privé; Certains bachelors, mastères ou écoles recrutant hors
plateforme y échappent. Le graphique donne donc une fenêtre utile, mais partielle, sur les choix d'orientation
après le baccalauréat.
""")
st.subheader("Frais, financement et points de vigilance")
df_frais = pd.DataFrame({
    "Type d'acteur": ["Grande école de commerce", "Groupe for-profit", "CFA privé", "Institut catholique", "École santé/sociale privée"],
    "Exemple en France": ["HEC Paris", "EPITECH (IONIS)", "Skill & You", "Institut catholique de Paris", "IFSI Paris"],
    "Formations fréquentes": ["PGE, bachelor, MSc", "Bachelor, mastère, titre RNCP", "BTS, bachelor, mastère en alternance",
                              "Licence, master, écoles internes", "Formations sociales ou paramédicales"],
    "Coût affiché": ["≈ 28 850 €/an (MiM)", "≈ 9 960 € (initial)", "Souvent pris en charge si contrat",
                     "≈ 7 780 €/an", "≈ 6 507 €/an"],
    "Financement dominant": ["Famille, prêt, alternance", "Alternance, famille, prêt", "Entreprise / OPCO",
                             "Famille, bourses, aides", "Aides régionales, famille"],
    "Point de vigilance": ["Retour sur investissement", "Reconnaissance du diplôme", "Nécessité d'un contrat",
                           "Statut de l'établissement", "Forte hétérogénéité"],
})
st.dataframe(df_frais, use_container_width=True, hide_index=True)
st.caption("Tableau 3 — Frais, financement et points de vigilance par type d'acteur. "
           "Source : sites institutionnels des établissements cités (frais affichés) ; synthèse de l'autrice.")
st.markdown("""
Ce tableau rend visible ce que les bases statistiques capturent mal : le privé ne renvoie pas à un seul niveau
de coût. Selon les segments, le prix peut aller de quelques milliers d'euros à près de 30 000 € par an. Il peut
être payé directement par la famille, financé par un prêt, modulé selon les revenus, ou pris en charge par
l'entreprise dans le cadre de l'alternance. L'enjeu n'est donc pas seulement le montant affiché, mais le reste
à charge réel pour l'étudiant et les conditions qui permettent de le réduire.

Mais une question demeure, plus brutale : que se passe-t-il si le jeu n'en vaut pas la chandelle ? Si une
famille engage plusieurs dizaines de milliers d'euros dans une formation, parfois jusqu'à 60 000 € sur
l'ensemble d'un parcours, elle ne paie pas seulement des cours. Elle paie une promesse : celle d'un diplôme
reconnu, d'un emploi qualifié, d'un salaire à la hauteur de l'investissement. Or, si cette promesse se
transforme en emploi précaire, sous-qualifié ou sans rapport avec la formation suivie, le coût ne se mesure
plus seulement en euros : il devient aussi une dette, une désillusion.
""")

# ============================================================
# PARTIE IV
# ============================================================
st.markdown("## Partie IV - Qui va dans le privé, et que sait-on des résultats ?")

# ---- Chapitre 8 ----
anchor("c8")
st.header("8 · Qui entre dans le privé ?")
st.markdown("""
Voici la question la plus sociale de toutes : qui franchit la porte du privé ? Là encore, parler du « privé »
au singulier serait trop simple, car les sous-statuts n'accueillent pas les mêmes étudiants. Les données
Parcoursup permettent de croiser deux dimensions : l'origine sociale, approchée par la part d'admis boursiers,
et le niveau scolaire, approché par les mentions au baccalauréat.
""")
st.plotly_chart(fig_profil_social_academique(annees), use_container_width=True)
st.caption("Figure 13 — Profil social et académique des admis par sous-statut (2025). "
           "Source : Parcoursup (session 2025), admis néo-bacheliers ; part de boursiers et de mentions au bac, par statut ; calculs de l'autrice.")
st.markdown("""
Le résultat dément l'image d'un privé uniformément élitaire. En 2025, le privé sous contrat d'association reste
relativement proche du public : 16,3 % de ses admis néo-bacheliers sont boursiers, contre 22,0 % dans le public.
L'écart existe, mais il n'a rien de comparable avec celui du privé d'enseignement supérieur, où les boursiers
ne représentent que 6,5 % des admis. C'est là que la sélection sociale apparaît le plus nettement. Le privé
d'enseignement supérieur accueille un public beaucoup plus favorisé, mais pas nécessairement plus brillant
scolairement : la part des mentions Très Bien et Très Bien avec félicitations y atteint 8,4 %, contre 12,8 %
dans le public. Autrement dit, ce segment recrute plus aisé, sans recruter plus excellent.

Il faut donc distinguer deux formes de sélection : la sélection académique, fondée sur les résultats scolaires,
et la sélection sociale, liée aux ressources économiques, familiales et informationnelles. Dans le privé
d'enseignement supérieur, c'est surtout cette seconde sélection qui semble dominer.
""")
st.plotly_chart(fig_boursiers_filiere(annees), use_container_width=True)
st.caption("Figure 14 - Boursiers par filière : comparaison public/privé (2025). "
           "Source : Parcoursup (session 2025) ; nombre et part d'admis boursiers néo-bacheliers, par filière et secteur ; calculs de l'autrice.")
st.markdown("""
Ce graphique compare la présence des boursiers selon les filières, dans le privé et dans le public. Les barres
bleues indiquent le nombre de boursiers admis ; les carrés rouges indiquent leur part parmi les admis
néo-bacheliers. Cette distinction est importante : une filière peut compter beaucoup de boursiers simplement
parce qu'elle accueille beaucoup d'étudiants, sans qu'ils y représentent une grande part des admis. La part de
boursiers est donc calculée ainsi : (nombre d'admis boursiers néo-bacheliers ÷ nombre total d'admis
néo-bacheliers) × 100. Les filières entourées en rouge sont présentes dans les deux secteurs, ce qui permet une
comparaison directe.

La lecture principale est nette : à filière comparable, le public accueille souvent une part de boursiers plus
élevée. Dans les écoles d'ingénieurs, les boursiers représentent environ 4 % des admis dans le privé, contre
9 % dans le public. Dans les écoles de commerce, l'écart est similaire : 4 % dans le privé contre 9 % dans le
public. Les IFSI font exception, avec une part proche dans les deux secteurs : environ 22 % dans le privé
contre 20 % dans le public. Le privé n'a donc pas un seul visage social : le BTS y accueille beaucoup de
boursiers, mais sur une même filière reconnue, le public en accueille souvent davantage.
""")

# ---- Chapitre 9 ----
anchor("c9")
st.header("9 · Ce que les données laissent dans l'ombre")
st.markdown("""
Les données éclairent une partie du phénomène, mais leurs angles morts sont tout aussi révélateurs. De nombreux
aspects du privé échappent encore aux bases publiques. Ce n'est pas seulement un angle mort statistique : c'est
un enjeu de transparence, de régulation et de protection des étudiants.

Le premier angle mort concerne les enseignants. Les bases ouvertes renseignent mal, pour le privé, la part
d'enseignants permanents, leur qualification ou la place de la recherche. Or ces éléments sont essentiels pour
juger de la qualité pédagogique : une école peut mettre en avant un suivi personnalisé, mais sans données
comparables, cette promesse reste invérifiable. Le deuxième angle mort est l'insertion professionnelle,
pourtant l'argument le plus mobilisé par les écoles : les taux publiés ne suivent pas toujours une méthode
homogène, les non-réponses peuvent être importantes, et les résultats sont rarement vérifiés par une source
indépendante. Le troisième est financier : ni les frais réels, ni les restes à charge, ni les taux d'abandon
ne figurent dans une base consolidée. S'y ajoute la difficulté, déjà rencontrée, d'identifier le lucratif car
le statut juridique ne dit pas qui possède une école.

Ces lacunes expliquent pourquoi la régulation du privé est devenue un sujet public. Il ne s'agit pas d'encadrer
une croissance quantitative, mais de la rendre lisible.
""")
st.subheader("Le cadre de régulation en construction")
st.markdown("""
Plusieurs travaux institutionnels récents convergent : la croissance du privé exige une information plus claire
et un contrôle renforcé. Les principales pistes portent sur l'évaluation pédagogique des formations, la
lisibilité des diplômes, des grades, des titres RNCP et des diplômes d'établissement, l'encadrement des
pratiques commerciales, la protection des étudiants en cas de frais élevés ou de rupture de parcours, le
contrôle des formations présentes sur Parcoursup, et le conditionnement de certaines aides publiques,
notamment dans l'apprentissage, à des exigences de qualité. Le rapport de l'Assemblée nationale (n°2458, 2024)
formulait vingt-deux recommandations ; le Sénat a poursuivi ce travail (2025) ; un projet de loi du MESR vise
désormais à garantir la qualité des formations. Le problème n'est pas seulement la croissance du privé, mais la
qualité de l'information disponible sur cette croissance. On ne régule bien que ce que l'on mesure.
""")

# ============================================================
# CONCLUSION
# ============================================================
anchor("ccl")
st.markdown("## Conclusion ")
st.markdown("""
Au départ, nous avions un tableau rassurant : l'enseignement supérieur a gagné près d'un million d'étudiants en
vingt ans. À l'arrivée, un constat plus inquiet : l'essentiel de cette croissance a été absorbé par un privé
que l'on connaît mal et que l'on nomme mal.

Cinq résultats se tiennent. Le privé est devenu central sans devenir homogène : sous ce mot cohabitent
instituts catholiques, écoles conventionnées de santé et groupes commerciaux qui n'ont en commun que
l'étiquette. Sa croissance n'a pas été uniforme : elle s'est concentrée dans les filières professionnalisantes,
le commerce en tête, qui explique à lui seul plus de la moitié de l'expansion des établissements privés. Le
for-profit a transformé la logique du secteur, en y important une logique de marque et de rentabilité que les
données publiques peinent même à délimiter. L'alternance a été un moteur puissant, elle a converti le BTS
privé jusqu'à 71 %, mais aussi un filtre, car elle reporte sur l'étudiant la charge de trouver un employeur,
parfois bien trop tôt. Enfin, les profils étudiants restent différenciés : à filière comparable, le privé
accueille moins de boursiers que le public, et son segment le plus marchand recrute aisé sans recruter brillant.

Ces résultats conduisent à un point central : l'enjeu n'est pas seulement la croissance du privé, mais la
qualité de l'information disponible sur cette croissance. Tant que les frais, les abandons, l'encadrement,
l'insertion réelle et la valeur exacte des diplômes ne seront pas documentés de manière consolidée et
indépendante, les familles devront décider dans un environnement partiellement opaque et cette opacité ne
touche pas toutes les familles de la même manière.

Des outils complémentaires, comme un formulaire public adressé aux étudiants et alumnis de ces établissements,
peuvent alors aider à faire remonter ce que les bases administratives captent mal. À titre exploratoire, ce
type de collecte peut contribuer à mieux cadrer le secteur.
""")
st.markdown("> *Formulaire exploratoire de collecte :* https://ee.kobotoolbox.org/x/BWSURlfO")
st.divider()
st.caption("Projet Capstone descriptif — données SIES/ATLAS et Parcoursup. "
           "Les graphiques sont interactifs : survolez courbes, barres et secteurs pour afficher les valeurs. "
           "La bibliographie complète figure sur la page « Bibliographie » (menu en haut à gauche).")