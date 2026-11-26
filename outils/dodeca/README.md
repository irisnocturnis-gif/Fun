# Outils du dodécaèdre

La page `dodeca.html` (à la racine du site) est **générée** par `dodeca_view.py` : le script assemble le code de la
page, le modèle Blockbench et les textures en un seul fichier.

## Régénérer la page
```
cd outils/dodeca
NO_OPEN=1 python3 dodeca_view.py     # écrit dodeca_viewer.html (Python standard, rien à installer)
cp dodeca_viewer.html ../../dodeca.html
```
Le gabarit de la page (HTML, CSS, JavaScript) est dans la variable `HTML` de `dodeca_view.py`.

## Si tu modifies `dodeca.html` directement
Reporte aussi le changement dans `dodeca_view.py`, sinon la prochaine régénération l'écrasera.

## Fichiers
- `dodeca_view.py` : génère la page (utilise les trois fichiers ci-dessous).
- `dodeca_core.bbmodel`, `dodeca_core.png`, `dodeca_core_glowmask.png` : modèle et textures du dodécaèdre.
- `dodeca_core_gen.py` : régénère le modèle et les textures (demande `numpy` et `Pillow`).
