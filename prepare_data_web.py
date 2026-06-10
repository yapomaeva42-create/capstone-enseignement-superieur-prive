from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path('data')
OUT_DIR = Path('data_web')
OUT_DIR.mkdir(exist_ok=True)

def read_csv(path):
    return pd.read_csv(path, sep=';', encoding='utf-8-sig', low_memory=False)

def num(s):
    return pd.to_numeric(s, errors='coerce').fillna(0)

def find_col(df, candidates, required=True):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError('Colonnes introuvables : ' + ' | '.join(candidates))
    return None

def clean_region_name(s):
    if pd.isna(s):
        return s
    s = str(s).strip()
    replacements = {
        'Provence-Alpes-Côte d’Azur': "Provence-Alpes-Côte d'Azur",
        'Auvergne Rhône Alpes': 'Auvergne-Rhône-Alpes',
        'Bourgogne Franche Comté': 'Bourgogne-Franche-Comté',
        'Centre Val de Loire': 'Centre-Val de Loire',
        'Grand-Est': 'Grand Est',
    }
    return replacements.get(s, s)

atlas_files = list(DATA_DIR.glob('fr-esr-atlas*.csv'))
if not atlas_files:
    raise FileNotFoundError('Aucun fichier ATLAS trouvé dans data/. Remets-le localement pour préparer data_web.')
atlas = read_csv(atlas_files[0])
parcoursup_2025 = read_csv(DATA_DIR / 'fr-esr-parcoursup_2025.csv')
appr = read_csv(DATA_DIR / 'fr-esr-parcoursup-apprentissage.csv')

C_AN = 'Année universitaire'
C_REG = find_col(atlas, ['Regroupements de formations ou d’établissements', 'regroupement'])
C_SEC = 'Secteur de l’établissement d’inscription'
C_EFF = 'Nombre total d’étudiants inscrits'

# 1. Évolution total inscrits
d = atlas[(atlas['Niveau géographique'] == 'Pays') & (atlas[C_REG] == "Total des formations d'enseignement supérieur")].copy()
d[C_EFF] = num(d[C_EFF])
out = d.groupby(C_AN, as_index=False)[C_EFF].sum().sort_values(C_AN)
out.rename(columns={C_AN: 'annee', C_EFF: 'inscrits'}).to_csv(OUT_DIR / 'evolution_inscrits.csv', index=False, encoding='utf-8-sig')

# 2. Privé vs public
d = atlas[(atlas['Niveau géographique'] == 'Pays') & (atlas[C_REG] == "Total des formations d'enseignement supérieur")].copy()
d[C_EFF] = num(d[C_EFF])
d['secteur'] = d[C_SEC].map({'Établissements privés': 'prive', 'Établissements publics': 'public'})
piv = d.pivot_table(index=C_AN, columns='secteur', values=C_EFF, aggfunc='sum', fill_value=0).sort_index().reset_index()
piv = piv.rename(columns={C_AN: 'annee'})
for col in ['prive', 'public']:
    if col not in piv.columns:
        piv[col] = 0
piv[['annee','prive','public']].to_csv(OUT_DIR / 'prive_vs_public.csv', index=False, encoding='utf-8-sig')

# Types privés
etabs = ['UNIV', 'EC_COM', 'EC_PARAM', 'EC_ART', 'EC_JUR', 'EC_autres', 'EPEU', 'GE', 'ENS', 'INP', 'UT']
mapping = {
    'EC_COM': 'Écoles de commerce',
    'EC_ART': "Écoles d'art & culture",
    'EC_PARAM': 'Paramédical & social',
    'EC_autres': 'Autres écoles spécialisées',
    'EPEU': 'Universités privées'
}
ordre = ["Écoles de commerce", "Écoles d'art & culture", 'Paramédical & social',
         'Autres écoles spécialisées', 'Universités privées', 'Autres']

def eff_type(an):
    dd = atlas[(atlas['Niveau géographique'] == 'Pays') & (atlas[C_SEC] == 'Établissements privés') &
               (atlas[C_REG].isin(etabs)) & (atlas[C_AN] == an)].copy()
    dd[C_EFF] = num(dd[C_EFF])
    dd['type'] = dd[C_REG].map(mapping).fillna('Autres')
    return dd.groupby('type')[C_EFF].sum().reindex(ordre).fillna(0)

# 3. Répartition type privé 2001/2024
rows = []
for an, label in [('2001-02','2001'), ('2024-25','2024')]:
    s = eff_type(an)
    for typ, val in s.items():
        rows.append({'annee': label, 'type': typ, 'effectif': int(val)})
pd.DataFrame(rows).to_csv(OUT_DIR / 'repartition_prive_type.csv', index=False, encoding='utf-8-sig')

# 4. Contribution croissance type
s2001, s2024 = eff_type('2001-02'), eff_type('2024-25')
g = pd.concat([s2001.rename('effectif_2001'), s2024.rename('effectif_2024')], axis=1).fillna(0)
g['gain'] = g['effectif_2024'] - g['effectif_2001']
g['contribution'] = np.where(g['gain'].sum() != 0, g['gain'] / g['gain'].sum() * 100, np.nan)
g['croissance'] = np.where(g['effectif_2001'] > 0, (g['effectif_2024'] / g['effectif_2001'] - 1) * 100, np.nan)
g.reset_index().rename(columns={'index':'type'}).to_csv(OUT_DIR / 'contribution_croissance_type.csv', index=False, encoding='utf-8-sig')

# 5. Part du privé par région 4 dates
dates = ['2001-02', '2013-14', '2018-19', '2024-25']
C_GEO = 'Unité géographique'
reg = atlas[(atlas['Niveau géographique'] == 'Région') & (atlas[C_REG] == "Total des formations d'enseignement supérieur") & (atlas[C_AN].isin(dates))].copy()
reg[C_GEO] = reg[C_GEO].map(clean_region_name)
hors = ['La Réunion', 'Martinique', 'Guadeloupe', 'Guyane', 'Mayotte', "Collectivités d'outre-mer", 'Collectivités d’outre-mer', 'Étranger', 'Corse']
reg = reg[~reg[C_GEO].isin(hors)]
reg[C_EFF] = num(reg[C_EFF])
reg['secteur'] = reg[C_SEC].map({'Établissements privés': 'Privé', 'Établissements publics': 'Public'})
piv = reg.pivot_table(index=[C_AN, C_GEO], columns='secteur', values=C_EFF, aggfunc='sum', fill_value=0).reset_index()
piv['total'] = piv.get('Privé', 0) + piv.get('Public', 0)
piv['part'] = piv.get('Privé', 0) / piv['total'] * 100
piv['annee'] = piv[C_AN].str[:4]
piv.rename(columns={C_GEO:'region'})[['annee','region','part']].to_csv(OUT_DIR / 'part_prive_regions.csv', index=False, encoding='utf-8-sig')

# 6. Croissance régions
reg = atlas[(atlas['Niveau géographique'] == 'Région') & (atlas[C_REG] == "Total des formations d'enseignement supérieur") &
            (atlas[C_SEC] == 'Établissements privés') & (atlas[C_AN].isin(['2001-02','2024-25']))].copy()
reg[C_GEO] = reg[C_GEO].map(clean_region_name)
reg[C_EFF] = num(reg[C_EFF])
piv = reg.pivot_table(index=C_GEO, columns=C_AN, values=C_EFF, aggfunc='sum', fill_value=0)
piv = piv.rename(columns={'2001-02':'prive_2001', '2024-25':'prive_2024'})
piv['croissance'] = np.where(piv['prive_2001'] > 0, (piv['prive_2024'] / piv['prive_2001'] - 1) * 100, np.nan)
piv.reset_index().rename(columns={C_GEO:'region'}).to_csv(OUT_DIR / 'croissance_regions.csv', index=False, encoding='utf-8-sig')

# 7. BTS apprentis total privé public
C_APP = 'Nombre d’étudiants inscrits en STS et assimilés sous statut d’apprenti'
C_STS = 'Sections de techniciens supérieurs (STS) et assimilés'
d = atlas[(atlas[C_REG] == C_STS) & (atlas['Niveau géographique'] == 'Pays')].copy()
d[C_APP] = num(d[C_APP])
d['secteur'] = d[C_SEC].map({'Établissements privés':'prive', 'Établissements publics':'public'})
piv = d.groupby([C_AN,'secteur'])[C_APP].sum().unstack(fill_value=0).sort_index()
piv['total'] = piv.get('prive', 0) + piv.get('public', 0)
piv = piv[piv['total'] > 0].reset_index().rename(columns={C_AN:'annee'})
for col in ['total','prive','public']:
    if col not in piv.columns:
        piv[col] = 0
piv[['annee','total','prive','public']].to_csv(OUT_DIR / 'apprentis_bts.csv', index=False, encoding='utf-8-sig')

# 8. Part apprentissage BTS secteur
d = atlas[(atlas[C_REG] == C_STS) & (atlas['Niveau géographique'] == 'Pays')].copy()
d[C_APP] = num(d[C_APP]); d[C_EFF] = num(d[C_EFF])
d['secteur'] = d[C_SEC].map({'Établissements privés':'Privé', 'Établissements publics':'Public'})
g = d.groupby([C_AN,'secteur']).agg(apprentis=(C_APP,'sum'), total=(C_EFF,'sum')).reset_index()
annees_ok = g[g['apprentis'] > 0][C_AN].unique()
g = g[g[C_AN].isin(annees_ok)].sort_values(C_AN)
g['part'] = g['apprentis'] / g['total'] * 100
g.rename(columns={C_AN:'annee'}).to_csv(OUT_DIR / 'part_apprentissage_bts.csv', index=False, encoding='utf-8-sig')

# Apprenticeship Parcoursup
# 9. Composition statut/région
C_STAT = 'Statut de l’établissement de la filière de formation'
C_REG_APP = 'Région de l’établissement'
da = appr[appr['Session'] == 2025].copy()
rep = pd.crosstab(da[C_REG_APP], da[C_STAT], normalize='index') * 100
drom = ['Mayotte', 'Guyane', 'Guadeloupe', 'Martinique', 'La Réunion', 'Corse']
rep = rep[~rep.index.isin(drom)].reset_index()
long = rep.melt(id_vars=C_REG_APP, var_name='statut', value_name='part').rename(columns={C_REG_APP:'region'})
long.to_csv(OUT_DIR / 'apprentissage_region_statut.csv', index=False, encoding='utf-8-sig')

# 10. Treemap filières privé apprentissage
C_FIL = 'Filière de formation très agrégée'
da['secteur'] = da[C_STAT].apply(lambda s: 'Public' if s == 'Public' else 'Privé')
vol = da[da['secteur'] == 'Privé'].groupby(C_FIL).size().reset_index(name='formations').sort_values('formations', ascending=False)
total = vol['formations'].sum()
vol['part'] = vol['formations'] / total * 100
vol['nom'] = vol[C_FIL].astype(str).str.replace(r'^\d+_', '', regex=True)
vol.rename(columns={C_FIL:'filiere'}).to_csv(OUT_DIR / 'apprentissage_filiere_prive.csv', index=False, encoding='utf-8-sig')

# 11. Recherche contrat
CAND = 'Effectif total des candidats pour la formation'
RECH = 'Nombre de de vœux placés en « Recherche de contrat » par la formation'
da[CAND] = num(da[CAND]); da[RECH] = num(da[RECH])
g = da.groupby(C_STAT).agg(candidats=(CAND,'sum'), recherche=(RECH,'sum'), formations=(C_STAT,'size')).reset_index().rename(columns={C_STAT:'statut'})
g['securises'] = g['candidats'] - g['recherche']
g['part_recherche'] = g['recherche'] / g['candidats'] * 100
g.to_csv(OUT_DIR / 'recherche_contrat_statut.csv', index=False, encoding='utf-8-sig')

# Parcoursup 2025
p25 = parcoursup_2025.copy()
STAT = [c for c in p25.columns if 'tatut' in c][0]

# 12. Remplissage filière
FIL = 'Filière de formation détaillée bis'
CAPA = 'Capacité de l’établissement par formation'
ADM = 'Effectif total des candidats ayant accepté la proposition de l’établissement (admis)'
p25[CAPA] = num(p25[CAPA]); p25[ADM] = num(p25[ADM])
p25['secteur'] = p25[STAT].apply(lambda s: 'Public' if s == 'Public' else 'Privé')
g = p25.groupby([FIL,'secteur']).agg(capa=(CAPA,'sum'), adm=(ADM,'sum')).reset_index()
g['remplissage'] = g['adm'] / g['capa'] * 100
g = g.replace([np.inf, -np.inf], np.nan).dropna(subset=['remplissage'])
top = g[g['secteur'] == 'Privé'].set_index(FIL)['capa'].sort_values(ascending=False).head(14).index
g = g[g[FIL].isin(top)].copy().rename(columns={FIL:'filiere'})
g.to_csv(OUT_DIR / 'remplissage_filiere.csv', index=False, encoding='utf-8-sig')

# 13. Profil social académique
cols = {
    'neobac': 'Effectif des admis néo bacheliers',
    'boursiers': 'Dont effectif des admis boursiers néo bacheliers',
    'TB': 'Dont effectif des admis néo bacheliers avec mention Très Bien au bac',
    'TBF': 'Dont effectif des admis néo bacheliers avec mention Très Bien avec félicitations au bac',
    'sansmention': 'Dont effectif des admis néo bacheliers sans mention au bac'
}
for c in cols.values():
    p25[c] = num(p25[c])
g = p25.groupby(STAT).agg(**{k:(c,'sum') for k,c in cols.items()}).reset_index().rename(columns={STAT:'statut'})
g['% boursiers'] = g['boursiers'] / g['neobac'] * 100
g['% TB+'] = (g['TB'] + g['TBF']) / g['neobac'] * 100
g['% sans mention'] = g['sansmention'] / g['neobac'] * 100
g.to_csv(OUT_DIR / 'profil_social_academique.csv', index=False, encoding='utf-8-sig')

# 14. Boursiers filière
FILA = 'Filière de formation très agrégée'
NEO = 'Effectif des admis néo bacheliers'
BRS = 'Dont effectif des admis boursiers néo bacheliers'
p25[NEO] = num(p25[NEO]); p25[BRS] = num(p25[BRS])
p25['secteur'] = p25[STAT].apply(lambda s: 'Public' if s == 'Public' else 'Privé')
g = p25.groupby([FILA,'secteur']).agg(neobac=(NEO,'sum'), boursiers=(BRS,'sum')).reset_index()
g = g[g['neobac'] >= 200].copy()
g['part'] = g['boursiers'] / g['neobac'] * 100
g['nom'] = g[FILA].astype(str).str.replace(r'^\d+_', '', regex=True)
g.rename(columns={FILA:'filiere'}).to_csv(OUT_DIR / 'boursiers_filiere.csv', index=False, encoding='utf-8-sig')

print('Données web créées dans', OUT_DIR.resolve())
print('Fichiers :')
for f in sorted(OUT_DIR.glob('*.csv')):
    print(' -', f.name, f.stat().st_size, 'octets')
