# AI Video Toolkit

**Donnez ce dépôt à votre agent IA pour monter et habiller vos vidéos.**

Un atelier vidéo partageable : vrais scripts de montage, compétences originales
pour l'agent, exemples, motion design, sous-titres, audio et contrôle qualité.
Le guide principal est [AGENTS.md](AGENTS.md). English instructions are available
in the skills, code help and [English quick start](docs/QUICKSTART_EN.md).

## À copier dans ChatGPT, Codex ou un autre agent

```text
Lis https://github.com/kaostyl/ai-video-toolkit et son fichier AGENTS.md.
Utilise les compétences vidéo pertinentes pour monter mes médias.
Commence par vérifier les outils réellement disponibles dans ton environnement.
Si tu peux exécuter du code, clone le dépôt, installe les dépendances nécessaires
et réalise le montage jusqu'au MP4 final et au contrôle qualité.
Si tu peux seulement consulter le dépôt, prépare le plan et les commandes exactes
pour mon environnement; explique ce qui manque pour produire le fichier.
Ne lance aucune génération payante sans budget accepté.
Voici mon brief : [objectif, médias, durée, langue, format, style].
```

**Le lien transmet les méthodes et le code.** Le rendu nécessite que l'agent ait
accès aux médias et puisse exécuter Python et FFmpeg dans un environnement adapté.
Un chat qui peut uniquement lire des pages ne peut pas réaliser un export vidéo
grâce au lien seul. Aucun compte ni abonnement n'est transféré.

## Ce que vous pouvez faire

| Besoin | Outil inclus |
|---|---|
| Couper et assembler plusieurs clips | `scripts/edit.py` + plan JSON |
| Transcrire et exporter du SRT | `scripts/transcribe.py` (optionnel) |
| Incruster des sous-titres | `scripts/captions.py` (FFmpeg avec libass) |
| Ajouter titres, mots-clés, cartes, comparaisons | `scripts/pipeline.py` + renderer PIL |
| Animer avec React ou HTML | Renderers Remotion et HyperFrames optionnels |
| Mixer bruitages et musique sous la voix | `scripts/sfx.py` + `scripts/compose.py` |
| Préparer un export éditable d'habillage | `scripts/davinci_timeline.py` → FCPXML |
| Vérifier cadrage, durée et audio | Storyboard, contact sheet et mesures audio |
| Produire scénario, découpage et miniature | Skills vidéo; outils d'image selon l'hôte |
| Générer des plans IA avec votre fournisseur | Skill de production cloud; connexion requise |

Le montage d'assemblage fait des coupes franches; il n'est pas un éditeur graphique.
Le FCPXML représente le master d'entrée, les overlays et les SFX : il ne reconstitue
pas les coupes internes d'un master assemblé, le ducking, la normalisation ou les
sous-titres incrustés. L'import réel doit être vérifié dans votre éditeur.

## Essai local sans compte ni génération payante

Python 3.10+ et [FFmpeg/FFprobe](https://ffmpeg.org/download.html) sur le PATH.

```text
git clone https://github.com/kaostyl/ai-video-toolkit.git
cd ai-video-toolkit
python -m venv .venv
```

Activez l'environnement : Windows `.\.venv\Scripts\Activate.ps1`, macOS/Linux
`source .venv/bin/activate`. Puis :

```text
python -m pip install -r requirements.txt
python tools/doctor.py
python tools/demo.py
```

La démo génère une vidéo synthétique de 24 secondes, deux overlays animés,
des bruitages, un MP4, un FCPXML et une planche de contrôle dans `.work/demo/`.
Le rendu PIL fonctionne sur CPU; aucun GPU, service cloud ou Node n'est requis.
L'installation initiale télécharge les dépendances; le rendu de cette démo est local.

## Votre première vidéo

[Guide pas à pas](docs/QUICKSTART.md) · [Formats JSON](docs/PLANS.md) ·
[Génération IA et budget](docs/CLOUD.md) · [Validation](docs/VALIDATION.md)

Chaque projet travaille dans son propre dossier pour éviter de réutiliser la
transcription ou les médias d'un autre montage. Les médias restent hors de Git.
Les huit skills dans [skills/](skills/) couvrent uniquement la production vidéo.

Le dépôt démarre sans clé API. Les options Pexels, transcription, Remotion,
HyperFrames et fournisseurs IA ont leurs propres dépendances et conditions.
Voir [THIRD_PARTY.md](THIRD_PARTY.md). Les méthodes et sources sont sous [MIT](LICENSE).
