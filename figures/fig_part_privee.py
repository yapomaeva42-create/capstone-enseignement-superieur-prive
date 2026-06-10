"""
Figure : part du privé dans les effectifs du supérieur.
Régénère figures/fig_part_privee.html depuis data/effectifs.csv.
Usage : python figures/fig_part_privee.py
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "effectifs.csv"   # colonnes attendues: annee, part_privee
OUT = Path(__file__).with_suffix(".html")

def build():
    if not SRC.exists():
        # données de démonstration tant que le CSV réel n'est pas là
        df = pd.DataFrame({"annee": [2010, 2016, 2020, 2024],
                           "part_privee": [17.0, 21.0, 24.5, 26.5]})
    else:
        df = pd.read_csv(SRC)
    fig = go.Figure(go.Scatter(x=df["annee"], y=df["part_privee"],
                               mode="lines+markers", line=dict(color="#C44E2C")))
    fig.update_layout(title="Part du privé dans les effectifs (%)",
                      xaxis_title="Année", yaxis_title="%")
    fig.write_html(OUT)
    print("écrit:", OUT)

if __name__ == "__main__":
    build()
