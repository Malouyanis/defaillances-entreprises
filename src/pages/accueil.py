"""Page d'accueil du dashboard (contenu provisoire, complété à la mission des KPI)."""

import dash
from dash import html

dash.register_page(__name__, path="/", name="Accueil", order=0)

layout = html.Div(
    [
        html.H2("Accueil"),
        html.P("Le tableau de bord des défaillances d'entreprises est en construction."),
    ]
)
