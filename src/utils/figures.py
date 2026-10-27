"""Style commun des graphiques Plotly du tableau de bord.

Toutes les pages passent leurs figures par appliquer_style : mêmes couleurs, même
police, mêmes marges. Une procédure garde toujours la même couleur, quel que soit
le graphique ou le filtre choisi.
"""

import plotly.graph_objects as go

POLICE = "Lato, Helvetica Neue, Arial, sans-serif"
COULEUR_TEXTE = "#0b0b0b"
COULEUR_TEXTE_SECONDAIRE = "#52514e"
COULEUR_GRILLE = "#e1e0d9"
COULEUR_AXE = "#c3c2b7"
COULEUR_FOND = "#ffffff"
PALETTE = (
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#6250d6",
    "#e34948",
)
COULEURS_PROCEDURES = {
    "Liquidation judiciaire": PALETTE[0],
    "Redressement judiciaire": PALETTE[1],
    "Sauvegarde": PALETTE[2],
}
ECHELLE_CONTINUE = (
    "#cde2fb",
    "#9ec5f4",
    "#6da7ec",
    "#3987e5",
    "#256abf",
    "#184f95",
    "#0d366b",
)
HAUTEUR_FIGURE = 420


def style_axe() -> dict[str, object]:
    """Réglages communs des axes : grille discrète, pas de ligne de zéro marquée."""
    return {
        "gridcolor": COULEUR_GRILLE,
        "linecolor": COULEUR_AXE,
        "zeroline": False,
        "tickfont": {"color": COULEUR_TEXTE_SECONDAIRE},
        "title": {"font": {"color": COULEUR_TEXTE_SECONDAIRE}},
    }


def appliquer_style(figure: go.Figure, titre: str | None = None) -> go.Figure:
    """Applique le style du projet à une figure et la renvoie."""
    figure.update_layout(
        title={"text": titre, "x": 0, "xanchor": "left"} if titre else None,
        font={"family": POLICE, "size": 13, "color": COULEUR_TEXTE},
        colorway=list(PALETTE),
        paper_bgcolor=COULEUR_FOND,
        plot_bgcolor=COULEUR_FOND,
        height=HAUTEUR_FIGURE,
        margin={"l": 40, "r": 20, "t": 60 if titre else 20, "b": 40},
        hoverlabel={"font": {"family": POLICE}},
        legend={"orientation": "h", "y": -0.15, "x": 0},
        bargap=0.15,
    )
    figure.update_xaxes(**style_axe())
    figure.update_yaxes(**style_axe())
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
        font={"size": 15, "color": COULEUR_TEXTE_SECONDAIRE},
    )
    appliquer_style(figure)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure
