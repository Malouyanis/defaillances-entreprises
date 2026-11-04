# DESIGN.md — direction « Registre »

Règles de l'interface du tableau de bord. **Toute modification d'interface part de ce fichier** et
réutilise le thème commun : `src/assets/theme.css` (couleurs, typographie, mise en page) et le
template Plotly `registre` de `src/utils/figures.py`. Rien n'est chargé depuis internet au lancement.

Inspirations : skills de design « Taste » (règles des écrans d'application, style
*achromatic ledger*) et « Impeccable » (mode *Operate* : précision et retenue).

## 1. L'idée

Un registre de banque : le décor ne porte **aucune couleur**. Le texte est à l'encre, les surfaces sont
blanches sur un fond gris-bleu, et **une seule teinte bleue** marque la donnée principale de chaque
graphique (l'année record, la procédure étudiée, le département sélectionné). Le reste est en gris.

## 2. Couleurs (variables CSS de `theme.css`)

| Rôle | Variable | Valeur |
| --- | --- | --- |
| Fond de la page | `--ground` | `#f2f4f7` |
| Cartes | `--surface` | `#ffffff` |
| Bord des cartes | `--border` | `#e3e6ea` |
| Filets des tableaux | `--rule` | `#eef0f3` |
| Bord des contrôles | `--control` | `#c9ced6` |
| Élément actif (menu) | `--active` | `#e4e7ec` |
| Texte | `--text` | `#0a0a0a` |
| Texte secondaire | `--muted` | `#5f6368` (contraste ≥ 4,5:1 sur blanc et sur le fond) |
| Bouton principal | `--primary` | `#141414`, texte blanc |
| Teinte des données | `--hue` | `#1d5fbf` |
| Données secondaires | `--neutral` | `#c9ccd1` |
| Avis (données absentes) | `--notice-*` | fond `#fffbeb`, bord `#fde68a`, texte `#92400e` |

Règles : la teinte occupe environ 1 % de l'écran ; jamais de dégradé, d'ombre, d'effet verre, ni
de couleur sur la barre latérale. Les composants Dash (curseurs, listes, boutons radio) reprennent la
teinte via les variables `--Dash-*` définies dans `theme.css`.

## 3. Typographie

- Une seule police : **Geist** (licence SIL OFL 1.1), fichier `src/assets/fonts/Geist.ttf`, déclaré
  par `@font-face`. Repli : `system-ui`.
- Tailles : titre de page 24 px (600) · titre de carte 16 px (600) · chiffre clé 30 px (500, 24 px
  sur téléphone) · texte 14 px · notes et légendes 13 px · graduations des axes 12 px.
- Chiffres : `font-variant-numeric: tabular-nums` partout où des nombres s'alignent.
- Casse de phrase, jamais de petites capitales espacées, pas de police à chasse fixe.

## 4. Mise en page

- Cadre : barre latérale de 240 px **sur le fond** (marque, périmètre, liens, bouton de mise à jour
  en bas) ; contenu à droite avec 32 px de marge ; pas de barre du haut.
- Chaque page commence par un `h1` et une phrase (`.constat`) qui donne le constat principal.
- Grille de 12 colonnes (`.grille`), un seul écart de 12 px ; blocs `.col-8`, `.col-6`, `.col-4`,
  `.col-12` ; les cartes gardent leur propre hauteur (`align-items: start`).
- Sous 1 100 px, tout passe sur une colonne ; sous 800 px, la barre latérale devient une barre du
  haut avec les liens qui défilent ; sous 640 px, les chiffres clés passent en 2 × 2.

## 5. Composants

- **Carte** (`.carte-bloc`) : blanc, bord 1 px `--border`, rayon 8 px, marge intérieure 20 px, aucune
  ombre. Un `h2` en tête, puis une `.note` si besoin.
- **Chiffres clés** (`.chiffres` + `.chiffre`) : une seule carte divisée en colonnes par des filets ;
  libellé gris, valeur, unité grise. Pas d'icône, pas de mini-graphique.
- **Tableaux** (`table.tableau`) : en-têtes gris 13 px en casse de phrase, filets entre les lignes,
  pas de zèbre, nombres alignés à droite (`.num`).
- **Boutons** : `.bouton` (quasi noir, rayon 6 px) pour l'action principale de la page, une seule ;
  `.bouton-discret` (contour) pour les actions secondaires.
- **Filtres** (`.filtres`) : une carte, trois colonnes (période, procédure, région), libellés liés
  aux contrôles. Textes des listes en français (`LIBELLES_LISTES` dans `filtres.py`).

## 6. Graphiques Plotly (template commun)

Toujours passer la figure par `appliquer_style(figure)` de `src/utils/figures.py` :

- police Geist, fond blanc, séparateurs français (`separators=", "`, format `,~f` : « 50 000 ») ;
- 3 à 5 lignes de grille horizontales `#e8eaee`, pas de ligne d'axe y, pas de graduations ;
- **une teinte par graphique** sur la donnée principale (`TEINTE`), le reste en `NEUTRE` ; les
  procédures gardent toujours la même couleur (`COULEURS_PROCEDURES`) ;
- pas de légende pour une seule série ; le titre est le `h2` de la carte, pas celui de la figure ;
- barres à angles droits, lignes droites de 2 px sans marqueurs ;
- annoter l'événement important (ex. « Record : 54 363 ») ; sur un axe catégoriel d'années,
  placer l'annotation sur l'**index** de la catégorie (un texte « 2024 » étire l'axe) ;
- cartes : `go.Choroplethmap` avec `FOND_CARTE` (fond uni, sans tuiles réseau) et l'échelle
  `ECHELLE_CONTINUE`, toujours accompagnées d'une liste qui donne les valeurs ;
- pas de barre d'outils (`config={"displayModeBar": False}`).

## 7. Chiffres et textes

- Mise en forme par `src/utils/formatage.py` : `entier` (« 272 219 », espace fine), `decimal`
  (« 5,7 »), `pourcentage` (« 70 % »). Un écart dit sa référence : « +18,4 % sur 2023 ».
- Un zéro s'affiche « 0 » ; une valeur manquante s'affiche « — » en gris.
- Vocabulaire du sujet : « ouvertures de procédure », « liquidation judiciaire », « département ».

## 8. États

- Base absente : le titre reste, puis un avis `.avis` qui dit quoi lancer (`get_data.py`, puis
  `clean_data.py`).
- Filtres sans résultat : figure vide avec une phrase (`figure_vide`) et une phrase à la place de la
  liste ; le cadre de la carte reste.
- Focus clavier visible (`outline` 2 px dans la teinte), sélection de texte teintée.

## 9. Vérification avant chaque push qui touche l'interface

1. `uv run pytest` et `uv run ruff check .` passent.
2. `uv run python main.py`, puis chaque page ouverte en largeur ordinateur (1440 px) et téléphone
   (390 px) : rien ne déborde, la police Geist est chargée, aucune requête vers internet.
3. Audit « Impeccable » : accessibilité, performance, thème, responsive, cohérence (notés sur 4).
