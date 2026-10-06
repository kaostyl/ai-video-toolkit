# Plans de montage et d'habillage

Tous les timings sont en secondes. Les fichiers JSON décrivent des décisions
éditoriales prises par l'agent; ils ne sont pas exécutables. Lisez les médias avant
de choisir les timings. Les IDs/projets utilisent lettres, chiffres, `_` ou `-`.

## Montage : edit.json

```json
{
  "resolution": [1920, 1080], "fps": 30,
  "clips": [
    {"source": "clip-a.mp4", "start": 1, "end": 8},
    {"source": "clip-b.mp4", "start": 0, "end": 5}
  ]
}
```

Ordre de lecture = ordre des clips. Chemins relatifs au fichier de plan.
`end` omis = fin du média. Les dimensions sont paires; le FPS est un entier.
Les coupes sont franches. Les clips gardent leur proportion avec bandes si besoin;
le son est converti en stéréo 48 kHz. Les clips muets reçoivent du silence.
`--out` pointe vers un nouveau MP4. Ce montage ne crée pas de FCPXML de coupes.

## Habillage : plan.json

```json
{
  "project": "my_video", "resolution": [1920, 1080], "fps": 30,
  "side": "right",
  "overlays": [
    {"id":"intro", "type":"title_band", "t":2, "dur":6,
     "color":"neutral", "big":"One clear idea", "small":"A useful explanation",
     "sfx_events":[{"at":0,"name":"whoosh","vol":0.4}]}
  ]
}
```

`t` et `dur` sont sur le **master monté**, pas les rushes. `id` est unique et sert
de nom de fichier. `sfx_events.at` est relatif au début de l'overlay; `vol` est
compris entre 0 et 1. Les textes restent courts et aucun overlay ne se chevauche.
Le CLI ajoute le chemin source et les dimensions utilisées à output/render_plan.json.

Couleurs : `problem` rouge, `solution` vert, `neutral` bleu, `gold` jaune, ou `#RRGGBB`.
Sons : whoosh, pop, tick, riser, ding, blip, zap, charge, scan, glitch, impact, shimmer.

| Type | Champs propres (en plus de id/type/t/dur) |
|---|---|
| title_band | big, small facultatif |
| lower_third | title, sub facultatif |
| keyword_pop | text |
| schema_requirements | reqs : paires valeur/libellé; result, note facultatifs |
| schema_bignumber | number; label, line, note facultatifs |
| schema_barcompare | bars : label, ratio entre 0 et 1, value, color |
| schema_table | title; colA et colB : head, color, rows (chaînes) |
| schema_checklist | rows : text et ok (booléen); kicker, note facultatifs |
| broll | query anglais; clé Pexels et connexion nécessaires |

Les champs `mark: "check"/"cross"` existent aussi pour les checklists. Pour le
renderer PIL, `ok: true/false` est portable. `schema_ranking` est un type avancé
présent dans le code; prévisualisez-le avec le renderer choisi avant production.

Pour une vidéo parlée, commencer par un overlay toutes les 15–25 s puis adapter
à ce qui est dit, avec au moins 3 s entre deux. Un titre dure typiquement 4–9 s;
une carte 6–15 s. Ne pas masquer les visages ni les captions. PIL ancre sur un côté;
les variantes navigateur emploient d'autres layouts. Vérifier la prévisualisation.

Exemple de carte :

```json
{"id":"checks","type":"schema_checklist","t":20,"dur":10,"color":"solution",
 "kicker":"BEFORE EXPORT", "rows":[{"text":"Readable image","ok":true},
 {"text":"Clear audio","ok":true}], "sfx_events":[{"at":0,"name":"whoosh","vol":0.4}]}
```

Valider avec `scripts/validate_plan.py --plan PLAN --source MASTER`.
Les avertissements doivent être examinés; `--strict` les traite comme erreurs.
