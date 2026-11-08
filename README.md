# Défaillances d'entreprises en France

Dashboard interactif sur les défaillances de sociétés en France métropolitaine (2019-2025), à partir des données ouvertes du BODACC, des ratios financiers BCE/INPI et de Sirene.

Projet data du cours Python 2 — E4 DSIA, ESIEE Paris.

**Auteurs** : Yanis Malou, Maxime Pierrard

**Question étudiée** : quels profils d'entreprises présentent le plus de risque de crédit ?

## Sommaire

1. [User Guide](#user-guide)
2. [Data](#data)
3. [Developer Guide](#developer-guide)
4. [Rapport d'analyse](#rapport-danalyse)
5. [Copyright](#copyright)

## User Guide

*User Guide : à compléter.*

## Data

### Sources

| Source | Producteur | Ce qu'on en tire |
|---|---|---|
| [BODACC, annonces commerciales](https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/) | DILA | Les jugements d'ouverture de procédure collective (liquidation, redressement, sauvegarde) : date, département, nature du jugement |
| [Ratios financiers BCE/INPI](https://data.economie.gouv.fr/explore/dataset/ratios_inpi_bce/) | DGE, Bercy | Les comptes annuels déposés : chiffre d'affaires, résultat, EBE et ratios (liquidité, endettement, autonomie financière…) |
| [Base Sirene, stock des unités légales](https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/) | INSEE | Le profil de chaque société : catégorie juridique, secteur (code NAF), date de création, tranche d'effectifs |

Les trois sources sont des données publiques, sous [Licence Ouverte Etalab 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/). Elles se croisent par le **SIREN**, l'identifiant de chaque société.

### Périmètre

- Période : jugements de 2019 à 2025.
- France métropolitaine, Corse comprise (les départements d'outre-mer sont exclus).
- Sociétés uniquement : les entrepreneurs individuels sont exclus.
- Une défaillance = l'ouverture d'une liquidation judiciaire, d'un redressement judiciaire ou d'une sauvegarde. Une seule défaillance par société : la première ouverture de la période.

### Du brut au propre

1. **`get_data.py`** télécharge les fichiers bruts dans `data/raw/` (ignoré par Git) et écrit la table **`raw`** : les jugements d'ouverture du BODACC, avec leurs valeurs d'origine.
2. **`clean_data.py`** nettoie les trois sources et écrit deux tables :
   - **`cleaned`** : une ligne par société défaillante (272 219 lignes), avec son profil Sirene, son âge au jugement et, quand ils existent, ses derniers comptes. C'est la table du dashboard.
   - **`scoring`** : les défaillantes qui ont des comptes, plus un échantillon de sociétés saines décrites de la même façon (89 509 lignes, dont 40 045 défaillantes). C'est la table du modèle de risque.

Les choix de nettoyage principaux :

- **Seuls les jugements d'ouverture comptent** : une même procédure publie plusieurs annonces (ouverture, plan, clôture), on ne garde que la première.
- **L'âge est calculé à la date du jugement**, pas à aujourd'hui.
- **Le fichier stock Sirene** remplace l'API, qui ne tient pas le volume d'appels.
- **Les comptes sont ceux du dernier exercice clos avant le jugement**, et au plus deux ans avant (jointure « point-in-time ») : on ne regarde que ce qu'un prêteur aurait pu voir.
- **Les ratios sont ramenés entre leurs percentiles 1 et 99** pour limiter l'effet des valeurs extrêmes ; les comptes confidentiels gardent leurs ratios de bilan, mais leur chiffre d'affaires reste vide.
- **Les sociétés saines** sont des sociétés commerciales encore actives, tirées au hasard (graine fixe) ; chacune reçoit une date de référence tirée parmi les dates de jugement, pour être comparée à la même époque.

La base finale `data/db.sqlite` contient les trois tables `raw`, `cleaned` et `scoring`.

## Developer Guide

*Developer Guide : à compléter.*

## Rapport d'analyse

Tous les chiffres ci-dessous sortent de la base `data/db.sqlite` du dépôt ; les pages du dashboard les recalculent à chaque visite.

### 1. Combien de défaillances, et quand ?

**272 219 sociétés** ont fait défaut en France métropolitaine entre 2019 et 2025.

| Année | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Ouvertures | 38 983 | 24 744 | 21 650 | 33 432 | 45 924 | 54 363 | 53 123 |

- **Le creux de 2020-2021** : en 2021, 44,5 % de défaillances de moins qu'en 2019. Les tribunaux ont tourné au ralenti pendant le premier confinement, puis les aides publiques (prêts garantis par l'État, chômage partiel) ont retardé les défaillances.
- **Le rattrapage** : dès 2023, le niveau de 2019 est dépassé ; **2024 est l'année record** (54 363, +39,5 % sur 2019) et 2025 reste à ce niveau (+36,3 % sur 2019).
- **Chaque mois d'août plonge** (2,6 % des ouvertures de l'année, contre 9 % environ pour un mois ordinaire) : ce sont les vacances judiciaires, pas une embellie économique.

### 2. Quelles sociétés ?

- **70,1 % des ouvertures sont des liquidations directes**, 27,2 % des redressements et 2,7 % des sauvegardes : la plupart des sociétés arrivent au tribunal trop tard pour être sauvées.
- **Âge médian au jugement : 5,7 ans** : la moitié des sociétés défaillantes avaient moins de six ans.
- **Trois secteurs font plus de la moitié des défaillances** : le commerce (22,2 %), la construction (21,2 %) et l'hébergement-restauration (13,7 %).
- **Départements** : Paris (21 375), la Seine-Saint-Denis (12 795) et les Bouches-du-Rhône (12 106) comptent le plus d'ouvertures. Ces nombres bruts suivent aussi le nombre de sociétés installées : la part de liquidations et l'âge médian, sur la carte, se comparent mieux d'un département à l'autre.

### 3. Quels signaux financiers annonçaient la défaillance ?

Sur la table `scoring`, on mesure pour chaque variable sa capacité à séparer défaillantes et saines (AUC univariée : 0,5 = aucun pouvoir, 1 = séparation parfaite).

| Variable (derniers comptes) | Pouvoir discriminant | Chez les défaillantes |
|---|---|---|
| Résultat net | 0,719 | plus bas |
| Ratio de liquidité | 0,711 | plus bas |
| Marge d'EBE | 0,693 | plus basse |
| Autonomie financière | 0,682 | plus basse |

**Le chiffre d'affaires**, en revanche, sépare mal les deux groupes : la médiane est de **307 221 €** chez les défaillantes et de **330 000 €** chez les saines. L'écart se joue aux extrêmes : **8,4 % des saines dépassent 10 M€ de chiffre d'affaires, contre 3,9 % des défaillantes**. La taille protège un peu, mais ce sont la rentabilité et la trésorerie qui annoncent la défaillance.

### 4. Le modèle de scoring

Une **régression logistique** estime la probabilité de défaut à partir des derniers comptes (liquidité, autonomie financière, fonds propres négatifs, endettement, marge d'EBE, résultat négatif, capacité de remboursement), de l'âge et du secteur. Le modèle apprend sur **2019-2023** (53 975 sociétés) et il est jugé sur **2024-2025** (35 534 sociétés), des années qu'il n'a jamais vues.

- **AUC : 0,774 sur l'entraînement, 0,755 sur le test.** Les deux sont proches : le modèle ne fait pas que mémoriser.
- **Les variables qui pèsent le plus** (variables mises à la même échelle) : une liquidité faible (coefficient −0,591), un résultat négatif (+0,550), des fonds propres négatifs (+0,340), une autonomie financière faible (−0,318) et l'âge (−0,243 : plus la société est ancienne, plus le risque baisse). Côté secteurs, la construction augmente nettement le risque.

Les probabilités sont **recalées** sur un taux de défaut annuel de référence de 1 % (le modèle a appris sur un échantillon où presque une société sur deux fait défaut), puis rangées en **cinq notes de A à E** selon les quintiles de l'entraînement :

| Note | Sociétés (2024-2025) | Taux de défaut observé | Probabilité recalée moyenne |
|---|---|---|---|
| A | 8 365 | 14,3 % | 0,23 % |
| B | 7 386 | 29,8 % | 0,57 % |
| C | 7 484 | 41,6 % | 0,91 % |
| D | 6 379 | 60,5 % | 1,65 % |
| E | 5 920 | 74,2 % | 6,01 % |

**Le taux de défaut monte à chaque note** : la notation classe bien le risque sur des années qu'elle n'a pas vues.

### 5. Limites

- **Biais de sélection** : seules 14,7 % des sociétés défaillantes ont des comptes clos dans les deux ans avant le jugement. L'analyse financière porte sur les sociétés qui publient leurs comptes.
- **Biais du survivant** : les sociétés saines sont des sociétés encore actives aujourd'hui ; elles ont forcément survécu, ce qui rend la comparaison un peu optimiste.
- **Le 1 % est une hypothèse** d'ordre de grandeur, pas un chiffre officiel : la Banque de France publie des nombres de défaillances, pas un taux. Il change le niveau des probabilités, pas l'ordre des notes.
- **La carte montre des nombres bruts** : sans le nombre de sociétés par département, on ne peut pas calculer un vrai taux de défaillance local.

### 6. Qualité du code

90 tests automatiques (`pytest`), 0 erreur de types (`mypy`), une note `pylint` de 9,99/10 sur `src/utils`, une complexité moyenne de classe A (`radon`) et un code formaté par `ruff`.

## Copyright

### Usage de l'intelligence artificielle

Nous déclarons que **le code de ce dépôt a été écrit par Claude**, l'assistant d'intelligence artificielle d'Anthropic, sous notre direction. Nous n'avons pas recopié de code d'autres projets ; aucune ligne n'est empruntée à un dépôt existant.

Notre part du travail :

- le **choix du sujet** et de la question étudiée, orientés risque de crédit ;
- le **test de faisabilité** des sources (6 octobre 2026), puis la recherche d'une donnée financière continue, le chiffre d'affaires, demandée par notre enseignant ;
- le **cadrage** : périmètre, définitions, sources retenues, répartition des rôles ;
- le **découpage en missions** quotidiennes : chacun de nous a lancé, relu, exécuté, testé et poussé ses missions par pull request ;
- les **choix de méthode**, discutés avant d'être codés (jugements d'ouverture seulement, âge au jugement, comptes antérieurs au jugement, échantillon de sociétés saines, découpage par années pour le scoring, hypothèse du 1 %) ;
- la **vérification des résultats** sur la vraie base et l'**analyse** présentée dans ce README ;
- le **choix de l'identité visuelle** parmi trois propositions, et les retours sur l'interface (par exemple le bug de la carte qui ne se recolorait pas, repéré par Yanis).

### Prompts structurants

Les demandes qui ont orienté le projet, reformulées et regroupées, fidèles au sens :

1. **Cadrage** : « Nous faisons le projet data du cours Python 2 en binôme, tout en Python avec Dash. Sujet : les défaillances d'entreprises en France, orientées risque de crédit. Question : quels profils d'entreprises présentent le plus de risque de crédit ? Périmètre : 2019-2025, France métropolitaine, sociétés uniquement, liquidations et redressements (sauvegardes à part). Tu écris le code ; nous te donnons une mission à la fois, nous la relisons, la testons et la poussons. »
2. **Donnée financière** : « Notre enseignant veut une vraie donnée financière continue, comme le chiffre d'affaires, en variable principale de l'histogramme, et veut voir d'où viennent les données. Trouve une source ouverte (piste : les ratios financiers BCE/INPI) et teste-la. »
3. **Organisation Git** : « Chaque mission sur une branche feat/ ou fix/, commits en français, fusion dans main par pull request. Aucun secret dans le dépôt. Explique chaque mission pour que nous sachions la défendre. »
4. **Mission type** : « Mission du jour : [la tâche]. Écris le code et ses tests, vérifie-les sur la vraie base, et donne-nous les résultats attendus pour que nous puissions contrôler les nôtres. »
5. **Identité visuelle** : « Le site ressemble aux autres projets faits avec une IA. Propose trois directions artistiques sobres et crédibles pour un recruteur en banque-finance, sans animation. Aucune dépendance JavaScript : l'enseignant doit pouvoir cloner puis lancer avec pip et python. »
6. **Scoring** : « Construis un modèle de probabilité de défaut évalué sur des années qu'il n'a pas vues, puis une notation de A à E comme une banque. »
7. **Qualité** : « L'enseignant note aussi la qualité du code : corrige ce que signalent mypy, pylint, radon et ruff, sans changer les résultats. »

### Données et ressources

- Données : BODACC (DILA), ratios financiers BCE/INPI (DGE), base Sirene (INSEE), sous [Licence Ouverte Etalab 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).
- Contours des départements : `data/departements.geojson`, issu d'Admin Express (IGN), Licence Ouverte Etalab 2.0.
- Police : [Geist](https://github.com/google/fonts/tree/main/ofl/geist), sous SIL Open Font License (`src/assets/fonts/OFL.txt`).
- Bibliothèques : Dash, Plotly, pandas, scikit-learn, requests, pyarrow, sous leurs licences respectives.
