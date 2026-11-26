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

## Pages de test (non liées depuis le site, en cours de réglage du son)
- `dodeca-test.html` : mode téléphone (travail de Codex) + variantes `?mix=1`/`?mix=2` (compresseur) et `?lite=1`/`?lite=2` (tampon audio, réverbération courte).
- `dodeca-lite.html` : version retenue pour l'instant (tampon audio large, réverbération 1,5 s, volume 0,8, pause de 10 s entre deux lectures, dragon à 8 itérations). Ces changements ne sont pas encore dans `dodeca_view.py` ni dans `dodeca.html`.

