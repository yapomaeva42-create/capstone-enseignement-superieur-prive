# prepare_data_web.py
# Version corrigée et plus rapide.
# Crée les petits CSV pour Streamlit Cloud à partir des grosses bases locales.
# Lancement local : python prepare_data_web.py

from pathlib import Path
import unicodedata
import numpy as np
import pandas as pd

DATA_DIR = Path("data")
OUT_DIR = Path("data_web")
OUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Outils robustes accents / apostrophes / encodage
# ------------------------------------------------------------
def norm_txt(x):
    if pd.isna(x):
        return ""
    s = str(x).replace("’", "'").replace("‘", "'").replace("`", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.lower().strip().split())

def norm_series(s):
    out = s.astype("string").fillna("")
    out = out.str.replace("’", "'", regex=False).str.replace("‘", "'", regex=False).str.replace("`", "'", regex=False)
    out = out.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
    out = out.str.lower().str.strip().str.replace(r"\s+", " ", regex=True)
    return out

def read_csv(path, usecols=None):
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc, low_memory=False, usecols=usecols)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, sep=";", low_memory=False, usecols=usecols)

def read_header(path):
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc, nrows=0).columns.tolist()
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, sep=";", nrows=0).columns.tolist()

def find_col_from_cols(columns, candidates, required=True):
    norm_cols = {norm_txt(c): c for c in columns}
    for cand in candidates:
        n = norm_txt(cand)
        if n in norm_cols:
            return norm_cols[n]

    for cand in candidates:
        words = [w for w in norm_txt(cand).split() if len(w) > 2]
        for nc, real in norm_cols.items():
            if all(w in nc for w in words):
                return real

    if required:
        raise KeyError("Colonnes introuvables : " + " | ".join(candidates))
    return None

def find_col(df, candidates, required=True):
    return find_col_from_cols(df.columns.tolist(), candidates, required=required)

def num(s):
    # retire espaces insécables / espaces puis convertit
    return pd.to_numeric(
        s.astype("string")
         .str.replace("\u00a0", "", regex=False)
         .str.replace(" ", "", regex=False)
         .str.replace(",", ".", regex=False),
        errors="coerce"
    ).fillna(0)

def clean_region_name(s):
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

def safe_write(df, name):
    df.to_csv(OUT_DIR / name, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------
# Chargement ciblé des bases locales
# ------------------------------------------------------------
atlas_files = list(DATA_DIR.glob("fr-esr-atlas*.csv"))
if not atlas_files:
    raise FileNotFoundError("Aucun fichier ATLAS trouvé dans data/. Le fichier doit commencer par fr-esr-atlas.")

atlas_path = atlas_files[0]
atlas_cols = read_header(atlas_path)

C_AN = find_col_from_cols(atlas_cols, ["Année universitaire"])
C_NIV = find_col_from_cols(atlas_cols, ["Niveau géographique"])
C_REGROUP = "regroupement"
C_SEC = find_col_from_cols(atlas_cols, ["Secteur de l’établissement d’inscription"])
C_EFF = find_col_from_cols(atlas_cols, ["Nombre total d’étudiants inscrits"])
C_GEO = find_col_from_cols(atlas_cols, ["Unité géographique"])
C_APP = find_col_from_cols(atlas_cols, ["Nombre d’étudiants inscrits en STS et assimilés sous statut d’apprenti"], required=False)

atlas_usecols = [C_AN, C_NIV, C_REGROUP, C_SEC, C_EFF, C_GEO] + ([C_APP] if C_APP else [])
atlas = read_csv(atlas_path, usecols=atlas_usecols)

atlas[C_EFF] = num(atlas[C_EFF])
if C_APP:
    atlas[C_APP] = num(atlas[C_APP])

# colonnes normalisées une seule fois : plus rapide que .map sur chaque ligne
N_NIV = norm_series(atlas[C_NIV])
N_REGROUP = norm_series(atlas[C_REGROUP])
N_SEC = norm_series(atlas[C_SEC])

M_PAYS = N_NIV.eq("pays")
M_REGION = N_NIV.eq("region")
M_TOTAL_SUP = N_REGROUP.eq("total")
M_STS = N_REGROUP.eq("sts")
M_PRIVE = N_SEC.str.contains("prive", na=False)
M_PUBLIC = N_SEC.str.contains("public", na=False)

# ------------------------------------------------------------
# 1. Évolution totale des inscrits
# ------------------------------------------------------------
d = atlas[M_PAYS & M_TOTAL_SUP].copy()
out = d.groupby(C_AN, as_index=False)[C_EFF].sum().sort_values(C_AN)
safe_write(out.rename(columns={C_AN: "annee", C_EFF: "inscrits"}), "evolution_inscrits.csv")

# ------------------------------------------------------------
# 2. Privé vs public
# ------------------------------------------------------------
d = atlas[M_PAYS & M_TOTAL_SUP].copy()
m_priv = M_PRIVE.loc[d.index]
m_pub = M_PUBLIC.loc[d.index]
d["secteur"] = None
d.loc[m_priv, "secteur"] = "prive"
d.loc[m_pub, "secteur"] = "public"
d = d.dropna(subset=["secteur"])
piv = d.pivot_table(index=C_AN, columns="secteur", values=C_EFF, aggfunc="sum", fill_value=0).sort_index().reset_index()
piv = piv.rename(columns={C_AN: "annee"})
for col in ["prive", "public"]:
    if col not in piv.columns:
        piv[col] = 0
safe_write(piv[["annee", "prive", "public"]], "prive_vs_public.csv")

# ------------------------------------------------------------
# 3. Répartition du privé par type d'établissement
# ------------------------------------------------------------
codes_etabs = ["UNIV", "EC_COM", "EC_PARAM", "EC_ART", "EC_JUR", "EC_autres", "EPEU", "GE", "ENS", "INP", "UT"]
mapping = {
    "EC_COM": "Écoles de commerce",
    "EC_ART": "Écoles d'art & culture",
    "EC_PARAM": "Paramédical & social",
    "EC_autres": "Autres écoles spécialisées",
    "EPEU": "Universités privées",
}
ordre = ["Écoles de commerce", "Écoles d'art & culture", "Paramédical & social",
         "Autres écoles spécialisées", "Universités privées", "Autres"]

def eff_type(an):
    mask = M_PAYS & M_PRIVE & atlas[C_REGROUP].isin(codes_etabs) & (atlas[C_AN].astype(str) == an)
    dd = atlas[mask].copy()
    dd["type"] = dd[C_REGROUP].map(mapping).fillna("Autres")
    return dd.groupby("type")[C_EFF].sum().reindex(ordre).fillna(0)

rows = []
for an, label in [("2001-02", "2001"), ("2024-25", "2024")]:
    s = eff_type(an)
    for typ, val in s.items():
        rows.append({"annee": label, "type": typ, "effectif": int(round(float(val)))})
df_rep = pd.DataFrame(rows)
safe_write(df_rep, "repartition_prive_type.csv")

s2001, s2024 = eff_type("2001-02"), eff_type("2024-25")
g = pd.concat([s2001.rename("effectif_2001"), s2024.rename("effectif_2024")], axis=1).fillna(0)
g["gain"] = g["effectif_2024"] - g["effectif_2001"]
g["contribution"] = np.where(g["gain"].sum() != 0, g["gain"] / g["gain"].sum() * 100, np.nan)
g["croissance"] = np.where(g["effectif_2001"] > 0, (g["effectif_2024"] / g["effectif_2001"] - 1) * 100, np.nan)
safe_write(g.reset_index().rename(columns={"index": "type"}), "contribution_croissance_type.csv")

# ------------------------------------------------------------
# 4. Part du privé par région
# ------------------------------------------------------------
dates = ["2001-02", "2013-14", "2018-19", "2024-25"]
reg = atlas[M_REGION & M_TOTAL_SUP & atlas[C_AN].isin(dates)].copy()
reg[C_GEO] = reg[C_GEO].map(clean_region_name)
hors = ["La Réunion", "Martinique", "Guadeloupe", "Guyane", "Mayotte",
        "Collectivités d'outre-mer", "Collectivités d’outre-mer", "Étranger", "Corse"]
reg = reg[~reg[C_GEO].isin(hors)].copy()
reg["secteur"] = None
reg.loc[M_PRIVE.loc[reg.index], "secteur"] = "Privé"
reg.loc[M_PUBLIC.loc[reg.index], "secteur"] = "Public"
reg = reg.dropna(subset=["secteur"])
piv = reg.pivot_table(index=[C_AN, C_GEO], columns="secteur", values=C_EFF, aggfunc="sum", fill_value=0).reset_index()
for col in ["Privé", "Public"]:
    if col not in piv.columns:
        piv[col] = 0
piv["total"] = piv["Privé"] + piv["Public"]
piv["part"] = np.where(piv["total"] > 0, piv["Privé"] / piv["total"] * 100, 0)
piv["annee"] = piv[C_AN].astype(str).str[:4]
safe_write(piv.rename(columns={C_GEO: "region"})[["annee", "region", "part"]], "part_prive_regions.csv")

# ------------------------------------------------------------
# 5. Croissance privée par région
# ------------------------------------------------------------
reg2 = atlas[M_REGION & M_TOTAL_SUP & M_PRIVE & atlas[C_AN].isin(["2001-02", "2024-25"])].copy()
reg2[C_GEO] = reg2[C_GEO].map(clean_region_name)
piv = reg2.pivot_table(index=C_GEO, columns=C_AN, values=C_EFF, aggfunc="sum", fill_value=0)
for col in ["2001-02", "2024-25"]:
    if col not in piv.columns:
        piv[col] = 0
piv = piv.rename(columns={"2001-02": "prive_2001", "2024-25": "prive_2024"})
piv["croissance"] = np.where(piv["prive_2001"] > 0, (piv["prive_2024"] / piv["prive_2001"] - 1) * 100, np.nan)
safe_write(piv.reset_index().rename(columns={C_GEO: "region"}), "croissance_regions.csv")

# ------------------------------------------------------------
# 6. BTS apprentis
# ------------------------------------------------------------
if C_APP:
    d = atlas[M_STS & M_PAYS].copy()
    d["secteur"] = None
    d.loc[M_PRIVE.loc[d.index], "secteur"] = "prive"
    d.loc[M_PUBLIC.loc[d.index], "secteur"] = "public"
    d = d.dropna(subset=["secteur"])
    piv = d.groupby([C_AN, "secteur"])[C_APP].sum().unstack(fill_value=0).sort_index()
    piv["total"] = piv.get("prive", 0) + piv.get("public", 0)
    piv = piv[piv["total"] > 0].reset_index().rename(columns={C_AN: "annee"})
    for col in ["total", "prive", "public"]:
        if col not in piv.columns:
            piv[col] = 0
    safe_write(piv[["annee", "total", "prive", "public"]], "apprentis_bts.csv")

    d = atlas[M_STS & M_PAYS].copy()
    d["secteur"] = None
    d.loc[M_PRIVE.loc[d.index], "secteur"] = "Privé"
    d.loc[M_PUBLIC.loc[d.index], "secteur"] = "Public"
    d = d.dropna(subset=["secteur"])
    g = d.groupby([C_AN, "secteur"]).agg(apprentis=(C_APP, "sum"), total=(C_EFF, "sum")).reset_index()
    annees_ok = g[g["apprentis"] > 0][C_AN].unique()
    g = g[g[C_AN].isin(annees_ok)].sort_values(C_AN)
    g["part"] = np.where(g["total"] > 0, g["apprentis"] / g["total"] * 100, 0)
    safe_write(g.rename(columns={C_AN: "annee"}), "part_apprentissage_bts.csv")
else:
    safe_write(pd.DataFrame(columns=["annee", "total", "prive", "public"]), "apprentis_bts.csv")
    safe_write(pd.DataFrame(columns=["annee", "secteur", "apprentis", "total", "part"]), "part_apprentissage_bts.csv")

# ------------------------------------------------------------
# Parcoursup apprentissage
# ------------------------------------------------------------
appr_path = DATA_DIR / "fr-esr-parcoursup-apprentissage.csv"
appr_cols = read_header(appr_path)
C_SESSION = find_col_from_cols(appr_cols, ["Session"])
C_STAT_APP = find_col_from_cols(appr_cols, ["Statut de l’établissement de la filière de formation"])
C_REG_APP = find_col_from_cols(appr_cols, ["Région de l’établissement"])
C_FIL_APP = find_col_from_cols(appr_cols, ["Filière de formation très agrégée"])
CAND = find_col_from_cols(appr_cols, ["Effectif total des candidats pour la formation"])
RECH = find_col_from_cols(appr_cols, ["Nombre de de vœux placés en « Recherche de contrat » par la formation"])
appr = read_csv(appr_path, usecols=[C_SESSION, C_STAT_APP, C_REG_APP, C_FIL_APP, CAND, RECH])

da = appr[appr[C_SESSION] == 2025].copy()

rep = pd.crosstab(da[C_REG_APP], da[C_STAT_APP], normalize="index") * 100
drom = ["Mayotte", "Guyane", "Guadeloupe", "Martinique", "La Réunion", "Corse"]
rep = rep[~rep.index.isin(drom)].reset_index()
safe_write(rep.melt(id_vars=C_REG_APP, var_name="statut", value_name="part").rename(columns={C_REG_APP: "region"}),
           "apprentissage_region_statut.csv")

da["secteur"] = np.where(norm_series(da[C_STAT_APP]).eq("public"), "Public", "Privé")
vol = da[da["secteur"] == "Privé"].groupby(C_FIL_APP).size().reset_index(name="formations").sort_values("formations", ascending=False)
total = vol["formations"].sum()
vol["part"] = np.where(total > 0, vol["formations"] / total * 100, 0)
vol["nom"] = vol[C_FIL_APP].astype(str).str.replace(r"^\d+_", "", regex=True)
safe_write(vol.rename(columns={C_FIL_APP: "filiere"}), "apprentissage_filiere_prive.csv")

da[CAND] = num(da[CAND]); da[RECH] = num(da[RECH])
g = da.groupby(C_STAT_APP).agg(candidats=(CAND, "sum"), recherche=(RECH, "sum"), formations=(C_STAT_APP, "size")).reset_index().rename(columns={C_STAT_APP: "statut"})
g["securises"] = g["candidats"] - g["recherche"]
g["part_recherche"] = np.where(g["candidats"] > 0, g["recherche"] / g["candidats"] * 100, 0)
safe_write(g, "recherche_contrat_statut.csv")

# ------------------------------------------------------------
# Parcoursup 2025
# ------------------------------------------------------------
p25_path = DATA_DIR / "fr-esr-parcoursup_2025.csv"
p25_cols = read_header(p25_path)
STAT = [c for c in p25_cols if "tatut" in c][0]
FIL = find_col_from_cols(p25_cols, ["Filière de formation détaillée bis"])
CAPA = find_col_from_cols(p25_cols, ["Capacité de l’établissement par formation"])
ADM = find_col_from_cols(p25_cols, ["Effectif total des candidats ayant accepté la proposition de l’établissement (admis)"])
NEOBAC = find_col_from_cols(p25_cols, ["Effectif des admis néo bacheliers"])
BOURSIERS = find_col_from_cols(p25_cols, ["Dont effectif des admis boursiers néo bacheliers"])
TB = find_col_from_cols(p25_cols, ["Dont effectif des admis néo bacheliers avec mention Très Bien au bac"])
TBF = find_col_from_cols(p25_cols, ["Dont effectif des admis néo bacheliers avec mention Très Bien avec félicitations au bac"])
SANS = find_col_from_cols(p25_cols, ["Dont effectif des admis néo bacheliers sans mention au bac"])
FILA = find_col_from_cols(p25_cols, ["Filière de formation très agrégée"])
p25_usecols = [STAT, FIL, CAPA, ADM, NEOBAC, BOURSIERS, TB, TBF, SANS, FILA]
p25 = read_csv(p25_path, usecols=p25_usecols)

p25[CAPA] = num(p25[CAPA]); p25[ADM] = num(p25[ADM])
p25["secteur"] = np.where(norm_series(p25[STAT]).eq("public"), "Public", "Privé")
g = p25.groupby([FIL, "secteur"]).agg(capa=(CAPA, "sum"), adm=(ADM, "sum")).reset_index()
g["remplissage"] = np.where(g["capa"] > 0, g["adm"] / g["capa"] * 100, np.nan)
g = g.replace([np.inf, -np.inf], np.nan).dropna(subset=["remplissage"])
top = g[g["secteur"] == "Privé"].set_index(FIL)["capa"].sort_values(ascending=False).head(14).index
g = g[g[FIL].isin(top)].copy().rename(columns={FIL: "filiere"})
safe_write(g, "remplissage_filiere.csv")

for c in [NEOBAC, BOURSIERS, TB, TBF, SANS]:
    p25[c] = num(p25[c])
g = p25.groupby(STAT).agg(
    neobac=(NEOBAC, "sum"),
    boursiers=(BOURSIERS, "sum"),
    TB=(TB, "sum"),
    TBF=(TBF, "sum"),
    sansmention=(SANS, "sum")
).reset_index().rename(columns={STAT: "statut"})
g["% boursiers"] = np.where(g["neobac"] > 0, g["boursiers"] / g["neobac"] * 100, 0)
g["% TB+"] = np.where(g["neobac"] > 0, (g["TB"] + g["TBF"]) / g["neobac"] * 100, 0)
g["% sans mention"] = np.where(g["neobac"] > 0, g["sansmention"] / g["neobac"] * 100, 0)
safe_write(g, "profil_social_academique.csv")

p25[NEOBAC] = num(p25[NEOBAC]); p25[BOURSIERS] = num(p25[BOURSIERS])
p25["secteur"] = np.where(norm_series(p25[STAT]).eq("public"), "Public", "Privé")
g = p25.groupby([FILA, "secteur"]).agg(neobac=(NEOBAC, "sum"), boursiers=(BOURSIERS, "sum")).reset_index()
g = g[g["neobac"] >= 200].copy()
g["part"] = np.where(g["neobac"] > 0, g["boursiers"] / g["neobac"] * 100, 0)
g["nom"] = g[FILA].astype(str).str.replace(r"^\d+_", "", regex=True)
safe_write(g.rename(columns={FILA: "filiere"}), "boursiers_filiere.csv")

# ------------------------------------------------------------
# Messages de contrôle
# ------------------------------------------------------------
print("Données web créées dans", OUT_DIR.resolve())
for f in sorted(OUT_DIR.glob("*.csv")):
    print(" -", f.name, f.stat().st_size, "octets")

print("\nContrôle repartition_prive_type.csv :")
print(pd.read_csv(OUT_DIR / "repartition_prive_type.csv").to_string(index=False))
