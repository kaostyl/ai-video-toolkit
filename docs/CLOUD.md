# Génération de plans IA avec votre connexion

Le montage local fonctionne sans compte cloud. Pour créer des plans, voix,
présentateurs ou miniatures, l'agent utilise un fournisseur disponible dans **son**
environnement : par exemple Higgsfield ou un moteur d'images de l'hôte.
Le dépôt ne contient ni connecteur exécutable, ni compte, ni abonnement.

1. Chercher un outil actuel de découverte/modèles dans l'environnement de l'agent,
   ou lire la documentation officielle de l'API réellement configurée. Vérifier
   les entrées prises en charge, audio natif/lip-sync, durée, résolution et ratios.
2. Préparer script, shot list et prompts avant de générer. Un visage animé ne
   garantit pas qu'il parle; demander explicitement dialogue/audio et lip-sync.
3. Obtenir un devis actuel sans créer de job. Présenter quantité, secondes **générées**,
   résolution, audio, coût des images/voix et marge de reprises. La durée finale
   peut aussi inclure des médias fournis ou du motion design local.
4. Utiliser le budget accepté pour ce projet. Ne pas lancer des essais payants
   avant ce budget; comptabiliser chaque job et arrêter avant de dépasser le plafond.
5. Générer un extrait court approuvé, inspecter image/audio, puis produire la série.
   Reprendre les jobs existants après interruption plutôt que dupliquer une commande.
6. Récupérer les fichiers via le mécanisme permis par le fournisseur; enregistrer
   dans le dossier privé du projet. Monter avec les mêmes outils locaux.

Calculateur local (les valeurs ci-dessous sont fictives, pas un tarif fournisseur) :

```text
python tools/budget.py --credits-per-second 2 --seconds 30 --retake-percent 20
```

Une offre illimitée dans l'interface web peut exclure l'API et l'automatisation.
Vérifier les conditions actuelles; ne pas déduire « gratuit » de l'accès à un modèle.
Demander au propriétaire de connecter son compte si l'étape l'exige. Aucun upload
des médias à un service externe sans autorisation pour ce service et ce projet.

Documentation fournisseur : https://higgsfield.ai/ (choisir la documentation et
les outils actuellement proposés). Aucun prix, quota ou modèle disponible n'est garanti.
