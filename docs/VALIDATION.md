# Validation de la version initiale

Le chemin de rendu de référence est PIL/CPU, sur médias synthétiques. La démo
produit un MP4 640×360 de 24 secondes, deux overlays, des SFX, une planche de contrôle
et un FCPXML. `python tools/demo.py` vérifie résolution et durée avec FFprobe.
Les tests locaux vérifient découpage/assemblage, plage invalide, média muet,
sortie captionnée si libass existe, refus d'écraser une source et encodage CPU.

La planche de contrôle est inspectée avant publication. Les empreintes du contenu
public sont enregistrées dans catalog/manifest.json; aucun média de test ou log
local n'est commité. `python tools/audit.py` vérifie secrets courants, chemins
personnels, emails, fichiers inattendus et contenu référencé avant publication.

Résultats effectivement obtenus pour cette version, sur Windows/Python 3.12 :

- Démo PIL/CPU : 24,0 s, 640×360, MP4 avec audio et FCPXML produits.
- Contact sheet inspectée; QC final : 0 erreur, 0 avertissement.
- Signal synthétique : -17,3 LUFS, true peak -1,5 dBFS. Ce signal de test ne mesure
  pas la qualité d'une voix réelle; la normalisation vise -14 LUFS sans promettre
  cette valeur exacte sur une tonalité et des bruitages.
- Sept tests d'intégration passent : ordre des clips, durée/silence, captions,
  refus d'écraser une source, plages invalides, composition sans piste audio,
  validation des IDs/timings et parsing XML avec caractères spéciaux.
- Huit skills validés; syntaxe Python/Node et compilation TypeScript Remotion passent.

Le contrôle de plan au premier lancement signale les SFX non encore créés; la
phase suivante les synthétise. Le QC final porte sur le résultat après génération
de ces sons. Les dépendances Remotion utilisées pour la compilation sont externes
au dépôt; ni node_modules ni leur chemin ne sont publiés.

Limites : transcription Whisper non validée par la démo (elle n'a pas de dialogue),
génération cloud non exécutée, aucune promesse de quota gratuit. Remotion/HyperFrames
sont des variantes optionnelles; le rapport de validation indique séparément les
vérifications effectivement faites. La création/parsing XML ne prouve pas l'import
dans DaVinci Resolve. Les cibles audio demandent écoute et mesure sur vos médias.
Le rendu complet navigateur et les plateformes macOS/Linux n'ont pas été validés
dans cette passe; seul le chemin PIL/CPU a fait l'objet d'un rendu de bout en bout.
