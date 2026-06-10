"""
Utilitaires partagés pour le site Capstone.
- Thème / config de page
- Système de citation des sources (chaque chiffre -> source + année)
- Chargement de données mises en cache
"""
from pathlib import Path
import pandas as pd
import streamlit as st

# Racine du projet (dossier CAPSTONE/)
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGURES = ROOT / "figures"

# ---------------------------------------------------------------------------
# Configuration de page (à appeler en tête de chaque page)
# ---------------------------------------------------------------------------
PALETTE = {
    "prive": "#C44E2C",      # terracotta = privé
    "public": "#2C5F8A",     # bleu = public
    "accent": "#D4A017",     # or/amber
    "neutral": "#6B7280",
    "bg": "#FAF8F4",
}


def page_config(title: str, icon: str = "🎓"):
    """Config standard. À appeler tout en haut de chaque page."""
    st.set_page_config(
        page_title=f"{title} · ESR privé en France",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def chapter_header(partie: str, chapitre: str, sous_titre: str = ""):
    """Bandeau de titre homogène pour chaque chapitre."""
    st.markdown(
        f"<p style='color:{PALETTE['neutral']};text-transform:uppercase;"
        f"letter-spacing:2px;font-size:0.8rem;margin-bottom:0;'>{partie}</p>",
        unsafe_allow_html=True,
    )
    st.title(chapitre)
    if sous_titre:
        st.markdown(f"#### {sous_titre}")
    st.divider()


# ---------------------------------------------------------------------------
# Système de citation : chaque chiffre doit pointer vers une source + année
# ---------------------------------------------------------------------------
# Registre central des sources. Clé courte -> (libellé complet, année, url)
SOURCES = {
    "sies_2024_25": (
        "SIES, Note flash « Les effectifs étudiants dans l'enseignement "
        "supérieur en 2024-2025 »",
        2025,
        "https://www.enseignementsup-recherche.gouv.fr/fr/"
        "les-effectifs-etudiants-dans-l-enseignement-superieur-en-2024-2025-99639",
    ),
    "rers_2025": (
        "RERS 2025, chapitre 7 « Les étudiants » (DEPP/SIES)",
        2025,
        "https://www.education.gouv.fr/sites/default/files/2025-07/"
        "rers2025-chapitre-7-441732.pdf",
    ),
    "an_1781": (
        "Assemblée nationale, rapport d'information n°1781",
        2023,
        "https://www.assemblee-nationale.fr/dyn/16/rapports/"
        "cion-cedu/l16b1781-tv_rapport-avis.pdf",
    ),
    "eespig_mesr": (
        "MESR, « La qualification d'EESPIG »",
        2024,
        "https://www.enseignementsup-recherche.gouv.fr/fr/"
        "la-qualification-d-etablissement-d-enseignement-superieur-prive-"
        "d-interet-general-eespig-46277",
    ),
    "loi_fioraso": (
        "Loi n°2013-660 du 22 juillet 2013 (ESR), art. L732-1 code de l'éducation",
        2013,
        "https://www.legifrance.gouv.fr/",
    ),
    # >>> Ajoute ici tes nouvelles sources au fur et à mesure <<<
}


def cite(key: str) -> str:
    """Renvoie une note de citation courte en Markdown : (Source, année)."""
    if key not in SOURCES:
        return f"*(source manquante : {key})*"
    label, year, _ = SOURCES[key]
    return f"<sub>Source : {label}, {year}.</sub>"


def source_list(keys: list[str]):
    """Affiche un bloc 'Sources' en bas de page à partir d'une liste de clés."""
    st.divider()
    st.markdown("##### Sources")
    for k in keys:
        if k in SOURCES:
            label, year, url = SOURCES[k]
            st.markdown(f"- {label}, {year}. [lien]({url})")
        else:
            st.markdown(f"- *(source manquante : {k})*")


# ---------------------------------------------------------------------------
# Chargement de données (mise en cache pour la performance)
# ---------------------------------------------------------------------------
@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    """Charge un CSV depuis data/. Renvoie un DataFrame vide si absent."""
    path = DATA / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def data_status(filename: str):
    """Avertit visuellement si un fichier de données n'est pas encore présent."""
    if not (DATA / filename).exists():
        st.warning(
            f"⚠️ Données non chargées : `data/{filename}` est introuvable. "
            "Les figures de cette page sont des espaces réservés.",
            icon="📂",
        )
        return False
    return True
