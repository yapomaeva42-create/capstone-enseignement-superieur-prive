# Capstone — Le paysage de l'enseignement supérieur privé en France

Site interactif (Streamlit) tenant lieu de rapport descriptif.

## Lancer le site
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```
CAPSTONE/
├── app.py                 # Accueil + chiffres-clés
├── pages/                 # 1 fichier = 1 chapitre (ordre = préfixe numérique)
│   ├── 0_Introduction.py
│   ├── 1_Ch1_Ecosysteme.py
│   ├── 2_Ch2_Cartographie.py
│   ├── 3_Ch3_Domaines.py
│   ├── 4_Ch4_Attractivite.py
│   ├── 5_Ch5_Profils.py
│   ├── 6_Ch6_Parcours.py
│   ├── 7_Ch7_Discours.py
│   ├── 8_Ch8_Limites.py
│   └── 9_Conclusion.py
├── utils/helpers.py       # thème, citations (registre SOURCES), chargement données
├── data/                  # CSV bruts (non versionnés si volumineux)
├── figures/               # 1 script .py par figure => figure régénérable
├── articles/ reports/     # littérature grise, PDF sources
└── notebooks/             # exploration

## Règle d'or
Chaque chiffre cité pointe vers une source + année via le registre `SOURCES`
dans utils/helpers.py. Chaque figure est régénérable depuis un script de figures/.
```
