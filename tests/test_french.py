"""The French rules: they must reach French machine prose, leave French human prose alone,
and never touch an English document.

The last of those is the load-bearing one. The French rules are additive and gated on
is_french, so a document that does not read as French must score exactly as it did before
this file existed.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import detect  # noqa: E402

CATALOGUE_FR = REPO / "references" / "patterns-fr.md"
FR_KEYS = {"fr_calque", "fr_faux_ami", "fr_not_x_but_y", "fr_signposting", "fr_era_opener",
           "fr_signoff", "fr_conclusion", "fr_marketing", "fr_cta"}

# A French paragraph carrying most of the catalogue.
MACHINE_FR = (
    "Dans le monde d'aujourd'hui, à l'ère du numérique, notre plateforme s'inscrit dans un "
    "paysage numérique en constante évolution et offre une expérience sans couture, un "
    "témoignage du savoir-faire de nos équipes. Il est important de noter qu'il ne s'agit pas "
    "seulement d'un outil, mais d'une véritable transformation. Notre approche holistique et "
    "incontournable permet de tirer parti d'une solution clé en main pour libérer tout le "
    "potentiel de votre organisation. En conclusion, découvrez comment passer à la vitesse "
    "supérieure. Restant à votre disposition, je vous prie d'agréer mes meilleures salutations."
)

# Ordinary French: spoken register, then a short warm letter. Neither is machine prose.
HUMAN_FR = (
    "Bonjour, je te réponds vite fait parce que je suis encore sur la route. On est partis à "
    "six heures et on a roulé jusqu'au col, il faisait un froid pas possible et la piste était "
    "gelée sur les deux derniers kilomètres. J'ai crevé une fois, rien de grave. On dort à "
    "Briançon ce soir et on repart demain vers l'Italie si la météo tient. Je t'appelle en "
    "arrivant. Dis à ton frère que sa carte a bien servi, on aurait tourné en rond sans elle."
)

HUMAN_FR_LETTER = (
    "Bonjour Madame, j'espère que vous allez bien. Je vous envoie les deux documents que vous "
    "m'aviez demandés pour le dossier, ainsi que la facture du garage. Pourriez-vous me "
    "confirmer la bonne réception. S'il manque quelque chose, dites-le moi et je vous l'envoie "
    "tout de suite. Bon week-end, et à bientôt. Cordialement."
)

ENGLISH = (
    "The bike arrived on Tuesday with a bent lever and a flat rear tyre. I straightened the "
    "lever with a vice and left the tyre for the shop, which had it done by Thursday. It runs "
    "fine now, though the fork seal will need doing before winter. I have ridden it twice since."
)


def _fr_fired(text: str) -> set:
    return {k for k in detect.scan(text) if k in FR_KEYS}


def _score(text: str) -> int:
    return detect.scan(text)["_metrics"]["ai_tell_score"]


def test_french_machine_prose_is_reached():
    fired = _fr_fired(MACHINE_FR)
    assert len(fired) >= 6, f"only {len(fired)} French rules fired: {sorted(fired)}"


def test_french_machine_prose_scores_above_the_nudge_threshold():
    assert _score(MACHINE_FR) > 40


def test_ordinary_french_speech_is_left_alone():
    assert _fr_fired(HUMAN_FR) == set()


def test_ordinary_french_letter_is_left_alone():
    """Cordialement, bon week-end and j'espère que vous allez bien are ordinary French."""
    assert _fr_fired(HUMAN_FR_LETTER) == set()


def test_english_never_reaches_the_french_rules():
    assert _fr_fired(ENGLISH) == set()


def test_english_scoring_is_untouched_by_the_gate():
    """The repository's own documents must score as they did before the French rules."""
    for name in ("README.md", "CONTRIBUTING.md", "ETHICS.md"):
        text = (REPO / name).read_text(encoding="utf-8")
        assert _fr_fired(text) == set(), f"a French rule fired on {name}"


def test_is_french_separates_the_two():
    assert detect.is_french(HUMAN_FR)
    assert detect.is_french(MACHINE_FR)
    assert not detect.is_french(ENGLISH)


def test_is_french_declines_a_fragment():
    """Below the word floor there is not enough evidence to call a language."""
    assert not detect.is_french("Bonjour, merci beaucoup.")


# ---- the catalogue has to survive its own rules, in both directions -------------------

def _sections() -> dict:
    body = CATALOGUE_FR.read_text(encoding="utf-8")
    out, key = {}, None
    for line in body.splitlines():
        m = re.match(r"^### (fr_[a-z_]+) ", line)
        if m:
            key = m.group(1); out[key] = []
        elif key:
            out[key].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def _example(body: str, label: str) -> str:
    m = re.search(rf"\*\*{label}:\*\*(.+?)(?=\n\n|\Z)", body, re.S)
    return " ".join(m.group(1).split()) if m else ""


def test_catalogue_documents_every_shipped_rule():
    assert set(_sections()) == FR_KEYS


def test_every_before_example_trips_its_own_rule():
    missed = []
    for key, body in _sections().items():
        before = _example(body, "Before")
        if before and key not in _fr_fired(before):
            missed.append(key)
    assert not missed, f"Before examples that do not trip their own rule: {missed}"


def test_every_after_example_is_clean():
    dirty = []
    for key, body in _sections().items():
        after = _example(body, "After")
        fired = _fr_fired(after)
        if fired:
            dirty.append((key, sorted(fired)))
    assert not dirty, f"After examples that still trip a French rule: {dirty}"


def test_no_example_names_a_real_person_or_company():
    """CONTRIBUTING forbids inventing facts or naming real entities in worked examples."""
    body = CATALOGUE_FR.read_text(encoding="utf-8")
    for token in ("KTM", "Google", "Microsoft", "Amazon", "OpenAI", "Anthropic", "Renault"):
        assert token not in body, f"{token} appears in a worked example"
