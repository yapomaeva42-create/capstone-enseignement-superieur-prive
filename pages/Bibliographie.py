# Bibliographie.py
# Page bibliographie du site Capstone.
# Pour qu'elle apparaisse dans le menu Streamlit À CÔTÉ de l'article :
#   - placer ce fichier dans un dossier "pages/" situé à côté de article1.py
#   - le fichier devient alors : capstone web/pages/Bibliographie.py
# Lancement du site :  streamlit run article1.py
# (Streamlit détecte automatiquement le dossier pages/ et ajoute la page au menu.)

import streamlit as st

st.set_page_config(page_title="Bibliographie — Capstone ESR privé", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 860px; padding-top: 2rem;}
h2 {margin-top: 2rem; color:#534AB7;}
a {color:#534AB7;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p style='color:#D4A017;text-transform:uppercase;letter-spacing:3px;font-size:0.8rem;'>"
            "Projet Capstone · Sources</p>", unsafe_allow_html=True)
st.title("Bibliographie et sources")
st.markdown("""
Les chiffres présentés sur ce site proviennent principalement de calculs réalisés à partir des bases ouvertes
du SIES (base ATLAS) et de Parcoursup. Les analyses qualitatives, les éléments sur les groupes privés à but
lucratif, les enjeux de régulation et les limites de transparence s'appuient sur des rapports parlementaires,
des documents institutionnels et plusieurs ressources complémentaires.
""")

st.header("1. Rapports parlementaires et institutionnels")
st.markdown("""
- **Assemblée nationale — Rapport d'information n°2458 sur l'enseignement supérieur privé à but lucratif**, B. Descamps et E. Folest, 10 avril 2024.
  https://www.assemblee-nationale.fr/dyn/16/rapports/cion-cedu/l16b2458_rapport-information.pdf
- **Assemblée nationale — Questions écrites n°2735 et n°6488**, questions orales sans débat n°200 et n°377.
- **Assemblée nationale — Dossier législatif** relatif à l'enseignement supérieur privé : DLR5L17N52116.
- **Sénat — Rapport n°350 sur l'enseignement supérieur privé lucratif**, 2025.
  https://www.senat.fr/rap/l25-350/l25-3502.html
- **Sénat — Proposition de loi** relative à l'encadrement de l'enseignement supérieur privé (ppl25-351).
  https://www.senat.fr/leg/ppl25-351.html
- **MESR — Projet de loi sur la régulation de l'enseignement supérieur privé : garantir la qualité des formations.**
  https://www.enseignementsup-recherche.gouv.fr/fr/projet-de-loi-sur-la-regulation-de-l-enseignement-superieur-prive-garantir-la-qualite-des-formations-101544
""")

st.header("2. Données publiques et bases statistiques")
st.markdown("""
- **SIES / MESR — Base ATLAS régionale des effectifs d'étudiants inscrits** (2001-2025).
  https://data.enseignementsup-recherche.gouv.fr/
- **Parcoursup — Données ouvertes d'admission** (session 2025).
  https://data.enseignementsup-recherche.gouv.fr/
- **Parcoursup — Base apprentissage** (offre d'apprentissage, session 2025).
- **MESR — État de l'enseignement supérieur : niveau d'études selon le milieu social** (2024).
  https://publication.enseignementsup-recherche.gouv.fr/eesr/
- **France Compétences — RNCP.**
  https://www.francecompetences.fr/recherche_certificationprofessionnelle/
- **InserJeunes.**
  https://www.inserjeunes.education.gouv.fr/diffusion/accueil
""")

st.header("3. Organismes et institutions du secteur")
st.markdown("""
- **Conférence des grandes écoles (CGE)** — https://www.cge.asso.fr/
- **CDEFI** — https://www.cdefi.fr/
- **UDESCA** — https://www.udesca.fr/
- **FESIC** — https://www.fesic.org/
- **HCERES** — https://www.hceres.fr/
""")

st.header("4. Littérature grise et analyses complémentaires")
st.markdown("""
- **Calvel et Chareyron — Le financement de l'enseignement supérieur en France**, Right to Education, 2023.
- **J. Gossa — « Mesurer l'immesuré : le développement de l'enseignement supérieur privé »**, EducPros, 2024.
  https://blog.educpros.fr/julien-gossa/2024/03/09/mesurer-limmesure-le-developpement-de-lenseignement-superieur-prive/
- **Document HAL-SHS** sur l'enseignement supérieur privé — https://shs.hal.science/halshs-05003516/document
- **Cour des comptes** — https://www.ccomptes.fr/fr/publications
- **IGÉSR — Rapports** — https://www.enseignementsup-recherche.gouv.fr/fr/rapports-de-l-igesr-48431
""")

st.header("5. Sources sur les groupes privés")
st.markdown("""
- **Galileo Global Education** — https://www.ggeedu.com/
- **Eduservices** — https://www.eduservices.org/
- **Omnes Education** — https://www.omneseducation.com/
- **IONIS Education Group** — https://www.ionis-group.com/
- **AD Education** — https://ad-education.com/
- **Compétences & Développement** — https://www.competences-developpement.com/
- **Ynov Campus** — https://www.ynov.com/
""")

st.divider()
st.caption("Les sources ouvertes ne couvrent pas tous les aspects du sujet. Les frais de scolarité, les taux "
           "d'abandon, la qualité de l'encadrement, l'insertion professionnelle détaillée et l'actionnariat des "
           "établissements restent partiellement documentés — ce qui justifie le croisement des données "
           "statistiques avec les rapports institutionnels et les travaux d'analyse existants.")
