# Pattern Catalogue — French (experimental)

Companion to [`patterns.md`](patterns.md), which is the English catalogue. These nine rules fire **only
when the document reads as French** (`is_french` in `scripts/detect.py`), so English scoring is
unaffected — verified byte-identical on the repository's own documents.

They carry no catalogue number on purpose. The numbered series and its published totals (71 patterns,
62 with a detector, 50 scoring) are claims about the English catalogue; renumbering it from a French
addition would rewrite those figures everywhere they are quoted. These sit in their own namespace
until the maintainer decides whether French belongs in the headline count.

A band describes the prose, never a writer — same stance as [`../ETHICS.md`](../ETHICS.md).

## Why the English rules do not reach French

French machine prose is not English machine prose with French words. A paragraph carrying every tell
below scores **1/100 `clean`** on the English set. Two families exist only here:

- **The calque** — vocabulary translated so literally it is rare or wrong in native French. *« une
  riche tapisserie »*, *« sans couture »*, *« un témoignage de »*. A French writer does not reach for
  these; a model translating from English does.
- **The faux-ami** — the French word that *looks* right to an English-trained model.
  *« définitivement »* is the cleanest case: it means **permanently**, not *definitely*, so
  *« c'est définitivement le meilleur »* is a translation error rather than emphasis. Likewise
  *adresser* un problème (→ traiter), *supporter* (→ soutenir), *délivrer* de la valeur (→ fournir).

Neither has an English original to translate from, which is why porting the English list would have
produced a catalogue that misses the signal.

---

### fr_calque — Calque from English

Vocabulary rendered word-for-word out of English AI prose.

**Before:** Notre plateforme s'inscrit dans un paysage numérique en constante mutation et offre une
expérience sans couture, un témoignage du savoir-faire de nos équipes. Plongeons dans cette riche
tapisserie de fonctionnalités pour libérer tout le potentiel de votre organisation.

**After:** La plateforme a changé trois fois de forme en deux ans. Elle fait maintenant une chose
correctement : elle range les devis par client et retrouve celui de mars en deux clics.

---

### fr_faux_ami — Faux-ami mistranslation

The French word an English-trained model picks because it looks like the English one.

**Before:** C'est définitivement la meilleure approche. Nous adressons les problèmes de nos clients,
nous supportons votre croissance et nous délivrons de la valeur à chaque étape.

**After:** C'est la meilleure approche que nous ayons trouvée. Nous traitons les incidents des
clients, nous accompagnons la croissance, et nous livrons quelque chose d'utile à chaque étape.

---

### fr_not_x_but_y — « Il ne s'agit pas seulement de X, mais de Y »

The French form of the not-just-X-but-Y pivot.

**Before:** Il ne s'agit pas seulement d'un outil de gestion, mais d'une véritable transformation
de votre manière de travailler au quotidien. Non seulement il centralise vos documents, mais il
réinvente également la collaboration entre vos équipes sur l'ensemble de vos projets.

**After:** C'est un outil de gestion. Il range les documents au même endroit et permet à deux
personnes d'écrire dans le même dossier sans se marcher dessus. Il fait gagner à peu près une heure
par semaine, et rien de plus.

---

### fr_signposting — « Il est important de noter »

Announcing that something matters instead of writing the thing that matters.

**Before:** Il est important de noter que les délais de traitement varient selon la période de
l'année. Il convient également de souligner que chaque dossier est étudié individuellement par nos
équipes, et il est à noter que des pièces complémentaires peuvent vous être demandées.

**After:** Les délais varient : comptez trois jours en semaine normale, dix en août quand la moitié
du bureau est en congé. Si le dossier est incomplet nous vous écrivons dans les deux jours pour
demander la pièce qui manque.

---

### fr_era_opener — « Dans le monde d'aujourd'hui »

The era-framing opener that says nothing about the subject.

**Before:** Dans le monde d'aujourd'hui, à l'ère du numérique et face à un marché en constante
évolution, les entreprises doivent impérativement s'adapter pour rester compétitives. Dans un monde
où tout va plus vite, savoir anticiper est devenu la condition de la réussite durable.

**After:** Deux de nos concurrents ont fermé cette année. Les deux avaient le même problème de
trésorerie que nous avons eu en 2023 : trop de stock acheté en janvier, payé en mars, vendu en
septembre. Nous achetons désormais deux fois moins, deux fois plus souvent.

---

### fr_signoff — Translated politeness formula

Corporate boilerplate where a French letter would simply close.

**Before:** Je vous remercie par avance de l'attention que vous porterez à ce dossier. Restant à
votre entière disposition pour tout complément d'information, et dans l'attente de votre réponse,
je vous prie d'agréer, Madame, l'expression de mes meilleures salutations.

**After:** Merci d'avoir regardé ce dossier. Si quelque chose manque, dites-le moi et je vous
l'envoie tout de suite, ça ne me prend pas deux minutes. Bonne fin de semaine à vous, et à bientôt.
Bien à vous.

*Note: « Cordialement » and « Bien à vous » are ordinary French and are deliberately not matched.
Only the translated-corporate register is.*

---

### fr_conclusion — « En conclusion »

The compulsory summary paragraph.

**Before:** En conclusion, cette solution représente un choix judicieux pour toute structure
souhaitant gagner en efficacité. Pour résumer, elle répond à l'ensemble de vos besoins actuels tout
en accompagnant votre croissance future, et constitue à ce titre un investissement pertinent.

**After:** Si le budget tient cette année, prenez la version simple : elle couvre ce que vous faites
aujourd'hui. Sinon attendez janvier, le prix baisse d'environ un tiers au changement de gamme et
rien ne presse d'ici là.

---

### fr_marketing — French marketing vocabulary

Abstract register that survives translation into any subject.

**Before:** Une approche holistique et incontournable, en synergie avec votre écosystème numérique,
pour façonner l'avenir de votre activité et tirer parti d'une solution clé en main.

**After:** On installe le logiciel, on forme deux personnes, et on part. Trois jours en tout.

---

### fr_cta — French call to action

The closing push, usually attached to nothing concrete.

**Before:** Découvrez comment passer à la vitesse supérieure et donner une nouvelle dimension à
votre activité dès aujourd'hui. Ne manquez pas cette occasion unique de rejoindre les nombreuses
structures qui nous font déjà confiance, et n'hésitez pas à nous contacter pour en savoir plus.

**After:** Le prochain créneau libre est le 12 au matin, le suivant début décembre. Répondez à ce
message si vous en voulez un, sinon je vous relance en janvier et nous verrons à ce moment-là.

---

## Measurement

`CONTRIBUTING.md` requires that a scored pattern may not fire more on human writing than on
machine writing. Measured against **59,733 words of human French** — spoken-word transcripts and
warm, colloquial business correspondence:

| Rule | Hits per 10,000 words of human French |
|---|---|
| every rule above | **0.00** |

**Limitation, stated plainly:** that corpus is narrow. It is dominated by one author's speech and one
team's correspondence, both informal registers, and it contains no formal administrative French, no
journalism and no academic prose — the registers where *« il convient de souligner »* and
*« n'hésitez pas à »* legitimately appear. `fr_signposting` and `fr_cta` are the two most likely to
need demotion to `_SCORE_REPORT_ONLY` once measured against a broader corpus. The maintainer's
private harness is the right instrument for that; this contribution arrives with its own measurement
as `CONTRIBUTING.md` asks, not with a claim to have replaced it.

The machine-French side was author-constructed rather than sampled, since no French AI corpus was
available here. Every example in this file is original and names no real person or company.
