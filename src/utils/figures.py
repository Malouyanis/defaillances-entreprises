"""Style commun des graphiques Plotly : le template « registre » (voir DESIGN.md).

Toutes les pages passent leurs figures par appliquer_style. Une seule teinte (le bleu) va
sur la donnée principale ; le reste est en gris. Une procédure garde toujours la même couleur.
"""

import plotly.graph_objects as go
import plotly.io as pio

POLICE = "Geist, system-ui, -apple-system, Segoe UI, sans-serif"
COULEUR_TEXTE = "#0a0a0a"
COULEUR_TEXTE_SECONDAIRE = "#5f6368"
COULEUR_GRILLE = "#e8eaee"
COULEUR_AXE = "#c9ced6"
COULEUR_FOND = "#ffffff"
TEINTE = "#1d5fbf"
NEUTRE = "#c9ccd1"
NEUTRE_FONCE = "#7d8590"
PALETTE = (TEINTE, NEUTRE_FONCE, NEUTRE)
COULEURS_PROCEDURES = {
    "Liquidation judiciaire": TEINTE,
    "Redressement judiciaire": NEUTRE_FONCE,
    "Sauvegarde": NEUTRE,
}
ECHELLE_CONTINUE = ("#eef3fb", "#bcd0ee", "#7ea4dc", "#3f78c9", "#1d5fbf", "#123d7c")
HAUTEUR_FIGURE = 300
SEPARATEURS_FR = ", "
FORMAT_NOMBRES = ",~f"
NOM_TEMPLATE = "registre"
FOND_CARTE = {
    "version": 8,
    "sources": {},
    "layers": [{"id": "fond", "type": "background", "paint": {"background-color": COULEUR_FOND}}],
}


def creer_template() -> go.layout.Template:
    """Template Plotly du projet : grille discrète, pas de ligne d'axe y, chiffres français."""
    axe = {
        "gridcolor": COULEUR_GRILLE,
        "linecolor": COULEUR_AXE,
        "zeroline": False,
        "ticks": "",
        "tickfont": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 12},
        "title": {"font": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 12}},
        "automargin": True,
    }
    return go.layout.Template(
        layout={
            "font": {"family": POLICE, "size": 13, "color": COULEUR_TEXTE},
            "colorway": list(PALETTE),
            "paper_bgcolor": COULEUR_FOND,
            "plot_bgcolor": COULEUR_FOND,
            "separators": SEPARATEURS_FR,
            "xaxis": {**axe, "showgrid": False, "showline": True},
            "yaxis": {**axe, "showgrid": True, "showline": False, "tickformat": FORMAT_NOMBRES},
            "hoverlabel": {"font": {"family": POLICE}, "bgcolor": COULEUR_FOND},
            "legend": {"orientation": "h", "y": 1.08, "x": 0, "font": {"size": 12}},
            "bargap": 0.25,
            "colorscale": {"sequential": list(ECHELLE_CONTINUE)},
            "coloraxis": {"colorbar": {"tickformat": FORMAT_NOMBRES}},
        }
    )


pio.templates[NOM_TEMPLATE] = creer_template()


def appliquer_style(figure: go.Figure, titre: str | None = None) -> go.Figure:
    """Applique le template du projet, la hauteur et les marges, puis renvoie la figure.

    Le titre d'un graphique est d'habitude dans la carte (un h2) : titre reste optionnel.
    """
    figure.update_layout(
        template=NOM_TEMPLATE,
        title={"text": titre, "x": 0, "xanchor": "left"} if titre else None,
        height=HAUTEUR_FIGURE,
        margin={"l": 8, "r": 8, "t": 40 if titre else 8, "b": 8},
        showlegend=len(figure.data) > 1,
    )
    return figure


def figure_vide(message: str = "Aucune donnée pour ces filtres") -> go.Figure:
    """Renvoie une figure sans axes qui affiche un message (filtres sans résultat)."""
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        showarrow=False,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        font={"size": 14, "color": COULEUR_TEXTE_SECONDAIRE},
    )
    appliquer_style(figure)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure
