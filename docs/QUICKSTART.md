# Monter votre vidéo

Installez Python 3.10+, FFmpeg et FFprobe puis les dépendances de README.md.
Les commandes suivantes supposent que le terminal est au dossier racine du dépôt.

## 1. Dossier de travail

Windows PowerShell :

```powershell
$toolkit = (Get-Location).Path
New-Item -ItemType Directory -Force projects/demo | Out-Null
Set-Location projects/demo
```

macOS/Linux :

```sh
toolkit="$PWD"
mkdir -p projects/demo
cd projects/demo
```

Placez les vidéos dans ce dossier. L'agent choisit un nouveau dossier pour chaque
projet. Les commandes Python utilisent `"$toolkit/scripts/..."` dans les deux shells.

## 2. Couper et assembler (optionnel)

Écrivez `edit.json` selon [PLANS.md](PLANS.md) et `examples/edit.json`.
Les chemins des médias sont relatifs au fichier du plan; les clips restent intacts.

```text
python "$toolkit/scripts/edit.py" --plan edit.json --out assembled.mp4
```

Le montage fait des coupes franches, normalise résolution/FPS/audio, puis concatène
les clips dans l'ordre. CPU par défaut. Un clip muet reçoit une piste silencieuse.
Les plages hors durée ou inversées sont rejetées avant tout rendu.

## 3. Transcription et storyboard

Depuis la racine du dépôt, installez l'option :
`python -m pip install -r requirements-transcription.txt`.
De retour dans le dossier du projet :

```text
python "$toolkit/scripts/transcribe.py" --source assembled.mp4 --out out --lang fr --words --device cpu
python "$toolkit/scripts/storyboard.py" --source assembled.mp4 --out out/storyboard.png --every 10
```

Pour une vidéo sans assemblage, remplacez `assembled.mp4` par votre source.
`--lang en` pour l'anglais. Le premier usage de Whisper télécharge le modèle;
CUDA est facultatif et nécessite les dépendances indiquées par faster-whisper.
Lisez et corrigez le SRT; regardez le storyboard. Rien ne génère un jugement
éditorial automatique : l'agent rédige le plan après inspection.

## 4. Titres animés, schémas, SFX et export

Écrivez `plan.json` à partir de `examples/plan.json` et [PLANS.md](PLANS.md).
Le plan d'exemple suppose une source d'au moins 50 secondes : adaptez les timings.

```text
python "$toolkit/scripts/pipeline.py" --source assembled.mp4 --plan plan.json --skip-transcribe --renderer pil --res 1920x1080 --encoder cpu --music none --loudnorm
```

Sorties : `output/<project>_FINAL.mp4`, `output/<project>.fcpxml`,
`output/render_plan.json`, `output/qc/contact_sheet.png` et `assets/*.mov` (alpha).
Le plan de rendu enregistre la résolution réellement demandée.

Musique autorisée facultative : remplacez `--music none` par `--music musique.wav`.
Le pipeline baisse automatiquement la musique sous la voix. Les SFX sont synthétisés
localement. Le rendu préserve la durée du master fourni.

## 5. Sous-titres incrustés (optionnel)

FFmpeg doit inclure le filtre `subtitles` (libass). Après correction du SRT :

```text
python "$toolkit/scripts/captions.py" --source output/demo_overlay_FINAL.mp4 --srt out/transcript.srt --out output/final_captioned.mp4
```

Livrez aussi le SRT si demandé. Gardez les sous-titres séparés tant que le montage
change. Une incrustation produit un nouveau MP4; elle ne modifie pas le FCPXML.

## Autres renderers

Depuis la racine : `npm ci --prefix remotion`. Ajoutez ensuite
`--renderer remotion` au pipeline. Node, un navigateur de rendu et les téléchargements
de polices sont nécessaires; les conditions Remotion s'appliquent.

HyperFrames est une variante avancée : `node hyperframes/build.mjs --plan PLAN
--out ASSETS --res 1920x1080`, puis composition et FCPXML avec ces mêmes assets.
Son premier usage télécharge un CLI, GSAP et des polices. Son rendu n'est pas
couvert par la démo PIL; vérifiez les conditions et prévisualisez avant une série.

## Contrôle final

Regardez la planche de contrôle, les entrées/sorties d'animations et écoutez la voix.
Vérifiez durée, lisibilité, sous-titres et absence d'informations privées. Importez
le FCPXML dans votre éditeur, avec les assets et SFX accessibles; reliez les médias
si nécessaire. Les effets de mixage du MP4 ne sont pas recréés dans le FCPXML.
