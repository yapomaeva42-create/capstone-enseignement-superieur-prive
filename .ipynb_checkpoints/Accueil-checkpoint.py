"""
Page de garde du site Capstone — couverture académique épurée.
Lancer le site avec :  streamlit run app.py
(article1.py et pages/Bibliographie.py restent accessibles par le menu.)

LOGO : place ton logo dans  capstone web/assets/
Noms reconnus automatiquement (dont le tien) :
  CY-Cergy-Paris-Universite_coul.jpg, cy_logo.png, logo_cy.png, CY.png ...
Si le logo est absent, la page s'affiche quand même (nom en texte).
"""
from pathlib import Path
import base64
import streamlit as st

st.set_page_config(page_title="Capstone — ESR privé en France", layout="wide",
                   initial_sidebar_state="expanded")

# ------------------------------------------------------------------
# Logo en base64 (centrage propre + taille maîtrisée en CSS)
# ------------------------------------------------------------------
def logo_data_uri():
    folder = Path("assets")
    if not folder.exists():
        return None
    # 1) noms connus d'abord
    connus = ["CY-Cergy-Paris-Universite_coul.jpg", "CY-Cergy-Paris-Universite_coul.png",
              "cy_logo.png", "cy_logo.jpg", "logo_cy.png", "logo_cy.jpg", "CY.png", "CY.jpg"]
    for nom in connus:
        p = folder / nom
        if p.exists():
            ext = "jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "png"
            return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    # 2) sinon : 1er fichier image trouvé dans assets/
    for p in folder.iterdir():
        if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
            ext = "jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "png"
            return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    return None

LOGO = logo_data_uri()

# ------------------------------------------------------------------
# Style — palette indigo + accents CY, fond très légèrement teinté
# ------------------------------------------------------------------
st.markdown("""
<style>
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stAppViewContainer"] > .main {
    background:
      radial-gradient(900px 520px at 82% -8%, rgba(41,171,226,0.06), transparent 60%),
      radial-gradient(760px 520px at 12% 108%, rgba(83,74,183,0.06), transparent 60%),
      #FCFCFE;
}
.block-container {max-width: 760px; padding-top: 4.2rem; padding-bottom: 3rem;}

/* Carte de couverture centrée, posée sur le fond */
.cover {
    position: relative; background:#FFFFFF; border:1px solid #ECEAF3;
    border-radius:18px; padding:3rem 3.2rem 2.6rem; text-align:center;
    box-shadow: 0 14px 40px -24px rgba(40,34,92,0.30);
    overflow:hidden;
}
/* Liseré tricolore CY en haut de la carte */
.cover::before {
    content:""; position:absolute; top:0; left:0; right:0; height:5px;
    background: linear-gradient(90deg,#5A55B5 0%,#29ABE2 55%,#7AC143 100%);
}
/* Pastille d'angle très discrète */
.cover::after {
    content:""; position:absolute; right:-70px; bottom:-70px; width:180px; height:180px;
    border-radius:50%; background:rgba(83,74,183,0.05);
}

.logo-box {display:flex; justify-content:center; margin-bottom:1.4rem;}
.logo-box img {height:46px; width:auto;}            /* logo discret, jamais géant */
.estab {color:#9A98A8; text-transform:uppercase; letter-spacing:3px;
        font-size:0.72rem; font-weight:600; margin-bottom:1.4rem;}

.eyebrow {color:#534AB7; text-transform:uppercase; letter-spacing:3px;
          font-size:0.74rem; font-weight:700;}
.title {font-size:2.7rem; line-height:1.12; font-weight:800; color:#1B1B2F;
        letter-spacing:-0.6px; margin:0.7rem 0 0.7rem;}
.sub {font-size:1.18rem; font-style:italic; color:#73717F; margin-bottom:1.6rem;}
.rule {width:60px; height:4px; border-radius:2px; margin:1.6rem auto;
       background:linear-gradient(90deg,#5A55B5,#29ABE2,#7AC143);}
.pb {max-width:560px; margin:0 auto; font-size:1.06rem; line-height:1.72; color:#34343F;}
.pb b {color:#534AB7; font-weight:600;}

.meta {margin:2.2rem auto 0; max-width:460px; padding-top:1.5rem;
       border-top:1px solid #EFEDF6;}
.meta .row {display:flex; justify-content:space-between; align-items:baseline;
            gap:1rem; padding:0.32rem 0; font-size:0.96rem; color:#3a3a44;}
.meta .lbl {text-transform:uppercase; letter-spacing:2px; font-size:0.68rem;
            color:#A6A4B4; white-space:nowrap;}
.meta .val {text-align:right;}
.meta .val.name {font-weight:700; color:#1B1B2F;}

.foot {text-align:center; color:#A6A4B4; font-size:0.8rem; margin-top:1.8rem; line-height:1.6;}
.foot a {color:#534AB7; text-decoration:none;}

/* Sidebar épurée : cohérente avec la couverture */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F7F7FC 0%, #FFFFFF 100%);
    border-right: 1px solid #E9E7F4;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #1B1B2F;
}

section[data-testid="stSidebar"] a {
    color: #34343F;
    text-decoration: none;
}

section[data-testid="stSidebar"] a:hover {
    color: #534AB7;
}

/* Page sélectionnée dans le menu */
section[data-testid="stSidebar"] [aria-current="page"],
section[data-testid="stSidebar"] [aria-selected="true"] {
    background: rgba(83, 74, 183, 0.12) !important;
    color: #1B1B2F !important;
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Couverture
# ------------------------------------------------------------------
logo_html = (f'<div class="logo-box"><img src="{LOGO}" alt="CY Cergy Paris Université"></div>'
             if LOGO else
             '<div class="estab">CY Cergy Paris Université</div>')

st.markdown(f"""
<div class="cover">
  {logo_html}
  <div class="eyebrow">Projet Capstone · Master 1 Économie, Data &amp; Transition</div>
  <h1 class="title">L'essor de l'enseignement<br>supérieur privé en France</h1>
  <p class="sub">Acteurs, filières, alternance et nouvelles lignes de régulation</p>
  <div class="rule"></div>
  <p class="pb">Que recouvre réellement la croissance de l'enseignement supérieur privé
  en France : quels acteurs la portent, quelles formations se développent, quels publics
  y accèdent, et comment l'<b>alternance</b>, le <b>for-profit</b> et les
  <b>régimes de reconnaissance</b> transforment-ils ce secteur ?</p>

  <div class="meta">
    <div class="row"><span class="lbl">Réalisé par</span><span class="val name">Maeva Yapo</span></div>
    <div class="row"><span class="lbl">Sous la direction de</span><span class="val name">Gustave Kenedi</span></div>
    <div class="row"><span class="lbl">Mention</span><span class="val">Économie, Data &amp; Transition (M1)</span></div>
    <div class="row"><span class="lbl">Année universitaire</span><span class="val">2025-2026</span></div>
  </div>
</div>

<p class="foot">Panorama descriptif — données SIES/ATLAS (2001-2025) et Parcoursup (2025).<br>
Ouvrez « article1 » dans le menu de gauche pour lire l'étude →</p>
""", unsafe_allow_html=True)
