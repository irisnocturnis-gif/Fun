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
- `son_dodeca_lisible.js` : le code du son, découpé en sections commentées (même son que la page de test, pour le lire et le régler).

## État des pages
- `dodeca.html` : la page publiée. Elle contient le mode téléphone (travail de Codex), le son stable (tampon audio large, réverbération 1,5 s), le volume 0,8, une pause de 10 s entre deux lectures et le dragon à 8 itérations. Elle est générée par `dodeca_view.py`.
- `dodeca-lite.html` et `dodeca-test.html` : pages de test non liées, gardées pour chercher le son du début. `dodeca-test.html` accepte `?mix=1`/`?mix=2` (compresseur) et `?lite=0`/`?lite=1`/`?lite=2` (tampon audio, réverbération).
