# Pattern Catalogue — Full Before / After

Companion to `../SKILL.md`. Read the matching section for the precise phrasing list and worked examples when applying a specific pattern. The catalogue is organized by function into seven groups; it folds the community-documented signs of AI writing together with this project's additions, including newer model-specific tells, rather than ordering them by origin. Every worked example below is original.

The catalogue holds 71 patterns. 62 of them have a detector in `scripts/detect.py` and the other 9 need a reading during the rewrite; of the 62, 50 can move the score and 12 are reported as writing advice and count for nothing. A pattern here describes prose, never a writer: see [../ETHICS.md](../ETHICS.md).

Patterns split into two classes:

- **Era-stable** (everything except §1): structural, syntactic, and rhetorical patterns that persist across model generations.
- **Era-variable** (§1 AI vocabulary): lexical fingerprints that shift every 12–18 months. See [§1](#1-ai-vocabulary) for the maintained word lists per era.

## Lexical tells

### 1. AI vocabulary

Era-variable. The detector deliberately keeps this list short; individual words
are common in human prose, so only a dense cluster affects the score.

**Current detector vocabulary:** additionally, align with, crucial, delve,
tapestry, pivotal, vibrant, meticulous, testament, underscore, intricate,
interplay, garner, bolster, foster, showcase, emphasize, enduring, enhance,
leverage, utilize, facilitate, encompass, harness, holistic, paradigm,
transformative, unprecedented, myriad, plethora, robust, seamless, navigate,
embark, and craft, including ordinary inflections. Closed phrases such as “captures
the essence” are also included. This is a functional specification of the
published rule, not a frequency claim about any individual word.

**Before:** Additionally, the enduring appeal of Vantry's grey-iron skillets is a testament to the foundry's craftsmanship, showcasing how traditional casting methods continue to integrate seamlessly into the modern culinary landscape.

**After:** Vantry still sells about 40,000 grey-iron skillets a year. The pattern has not changed since 1911, and each cooking face is ground smooth by hand.

### 2. Model-dialect vocabulary

Beyond the shared AI lexicon (#1), each model family over-uses its own words. Claude-family drafts lean on earnest intensifiers (`genuinely`, `fascinating`, `nuanced`, `refreshingly`, `quietly powerful`); GPT-family drafts lean on hype verbs (`game-changer`, `supercharge`, `skyrocket`, `unlock the potential`, `take X to the next level`, `dive deeper into`). Individually these are common human words, so the detector fires only at two or more combined hits, and the samples name the dialect.

**Watch for:** clusters of one dialect's favourites in a single passage. A cluster says the prose carries that dialect. It does not establish who or what wrote the document, and must not be read that way.

**Before:** This genuinely fascinating approach is a game-changer that will supercharge your team's workflow.

**After:** This approach cuts review time roughly in half, mostly by removing the second approval step.

### 3. Promotional language

**Watch for:** boasts, vibrant, rich (figurative), nestled, in the heart of, breathtaking, must-visit, stunning, picturesque, charming, idyllic, groundbreaking (figurative), renowned, world-class, premier, leading, top-tier, unparalleled.

**Before:** Nestled in the heart of the picturesque Ashcombe Valley, Marden Bridge is a charming village that boasts a rich industrial heritage and a stunning stone viaduct.

**After:** Marden Bridge is a village in the Ashcombe Valley, at the point where the old tramway crossed the river on a six-arch stone viaduct. The viaduct was built in 1841 and carried coal until 1958.

### 4. Hyphenated word-pair overuse

**Cliché pairs to de-hyphenate:** mission-critical, battle-tested, out-of-the-box, enterprise-grade, best-of-breed, plug-and-play, industry-leading, purpose-built, bleeding-edge, turn-key, value-added, first-class, laser-focused, tried-and-true, ready-made, best-in-class, future-proof, cutting-edge, results-driven, customer-centric.

**Do NOT touch** technical compound modifiers: thin-walled, load-bearing, strength-to-weight, signal-to-noise, cross-sectional, air-filled, CO2-equivalent, three-segment compounds. These carry meaning.

**Before:** Slipstream is a best-in-class, battle-tested ingestion service with out-of-the-box support for read-after-write consistency.

**After:** Slipstream is a battle tested ingestion service with out of the box support for read-after-write consistency.

### 5. "Simple yet X" cliché

**Watch for:** "simple yet effective", "simple yet powerful", "simple yet profound", "simple yet elegant", "simple yet transformative".

**Before:** The interface is simple yet powerful, giving users access to advanced features without complexity.

**After:** The interface keeps the controls minimal. Advanced features are one menu deep.

### 6. Stacked adjective chains

Four or more adjectives before a noun with no rhythm: "a dynamic, innovative, transformative, and groundbreaking initiative."

**Before:** They launched a bold, ambitious, transformative, and forward-thinking initiative.

**After:** They launched a research program that targets carbon capture at industrial scale.

### 7. Rule of three overuse

**Only flag when all three items are single-word generic descriptors** ("agile, scalable, and dynamic"). Three-item lists of multi-word concrete things ("composite blades, turbine housings, and structural panels") are normal factual enumerations.

**Before:** Harlow Metals says its new bearing alloy is stronger, lighter, and greener.

**After:** Harlow Metals says the new bearing alloy is 12 percent stronger than the grade it replaces and slightly lighter. It contains no cobalt.

### 8. Synonym cycling

AI cycles synonyms for the same referent across consecutive sentences. If three or more synonyms from one cluster refer to the same thing, flag it.

**Common AI clusters:**
- protagonist / main character / central figure / hero
- company / firm / organization / enterprise / business
- author / writer / novelist / scribe
- report / study / analysis / investigation / examination
- technology / tool / system / platform / solution
- technique / method / approach / strategy / tactic
- challenge / obstacle / difficulty / hurdle / barrier
- benefit / advantage / upside / strength

**Before:** The company was founded in a rented shed. The firm took on its first apprentice in 1974. By 1990 the organization employed sixty people. The business was casting for the whole county.

**After:** The company was founded in a rented shed and took on its first apprentice in 1974. By 1990 it employed sixty people and cast for the whole county.

### 9. Generic character naming in fiction

**Apply in fiction only.** A familiar given name is never a tell by itself.

**Watch for:** a character receiving the first generic name that fits the prompt,
with no surname, background, or detail that makes the choice feel deliberate.

**Before:** Ava walked into the office, her coffee in one hand and her laptop in the other.

**After:** Marjit walked into the office with her coffee and laptop, already late for the 9:15.

## Rhetorical filler

### 10. Significance inflation

**Watch for:** stands / serves as, is a testament / reminder, vital / significant / crucial / pivotal / key role, underscores its importance, reflects broader, symbolizing its ongoing / enduring, setting the stage for, marking a turning point, evolving landscape, indelible mark, has shaped, has sparked, plays a crucial role.

**Before:** Founded in 1994, the Brayton Mill Heritage Trust marked a turning point in the preservation of the region's industrial landscape and stands as a testament to the enduring importance of its textile past.

**After:** The Brayton Mill Heritage Trust was founded in 1994 to buy derelict textile mills and repair them. It now owns four, two of which are open to the public.

### 11. Notability name-dropping

**Watch for:** independent coverage, has been featured in [list], active social media presence, [N] followers, strong digital presence, widely covered by.

**Before:** Halloran's work has been featured in Reclaimed Quarterly, the Ashcombe Gazette, and Beam & Board. He maintains an active social media presence with more than 200,000 followers.

**After:** In a 2023 interview with Reclaimed Quarterly, Halloran argued that a rotted oak beam should be spliced at the damaged end rather than replaced whole.

### 12. Vague attributions

**Watch for:** industry reports, observers have cited, experts argue, several sources, some critics argue, researchers have found, studies suggest, it is widely believed.

**Before:** The Ashcombe peat beds have drawn attention from ecologists and the county flood board. Studies suggest they play a crucial role in flood control, and experts argue that draining them would be significant.

**After:** The Ashcombe peat beds soak up rain that would otherwise run straight into the Marden. What draining them would do to peak flow downstream has not been measured.

**Do not repair a vague attribution by inventing a source.** "Studies suggest" is empty because the draft has no study, and naming one to fill the gap is fabrication. Either the source is in the input, in which case cite it, or the claim goes back to what is actually known.

### 13. Article-titles-as-proper-nouns

When writing about a category, list, or article, AI treats the title as a real-world entity: "The List of Songs About Mexico is a curated compilation that highlights..."

**Before:** The List of Renewable Energy Projects in Germany is a comprehensive resource that catalogues installations across the country.

**After:** Germany has roughly 30,000 wind turbines and more than 4 million solar installations as of the end of 2024.

### 14. Conservation status and ecosystem padding

When asked to describe a species, AI reflexively appends sentences about ecological role, conservation status, and broader environmental significance, even when no such context was requested and no specific data supports it.

**Watch for:** unprompted sentences ending an animal/plant entry with `plays a vital role in its ecosystem`, `conservation efforts are underway`, `serves as an indicator species`, `contributes to biodiversity in the region`, when no data has actually been supplied to support the claim.

**Before:** The Eurasian magpie is a black-and-white corvid found across Europe and Asia. It plays a vital role in its ecosystem and conservation efforts are underway to protect its habitat.

**After:** The Eurasian magpie is a black-and-white corvid found across Europe and Asia. It is listed as Least Concern by the IUCN and population estimates have been stable since 1980.

### 15. False ranges

**Watch for:** "from X to Y" where X and Y are not on a meaningful scale.

**Before:** The museum's collection takes the visitor from the humble hand-forged nail to the mighty beam engine, from the first canal lock to the vanished crafts of the coalfield.

**After:** The museum holds hand tools, a working beam engine, and models of the canal locks built for the coalfield.

### 16. Superficial -ing tail clauses

Flag trailing `, ___ing` clauses with these verbs: **highlighting, reflecting, symbolizing, emphasizing, underscoring, showcasing, fostering, cultivating, encompassing, signaling, demonstrating, illustrating, representing, suggesting, indicating, reinforcing, leveraging, aligning, embodying.**

**Do not flag** factual-consequence -ing clauses: `, resulting in...`, `, making it...`, `, creating...`, `, providing...`, `, enabling...`. These describe real outcomes.

**Before:** The station's cast-iron platform canopies were made a mile up the line at Fenwick & Sons, reflecting the town's foundry heritage and underscoring its long connection to the railway.

**After:** The station's platform canopies were cast a mile up the line at Fenwick & Sons. The foundry supplied most of the railway's ironwork until it closed in 1962, and the canopies are the largest piece of its work still standing.

### 17. Negative parallelisms and tailing negations

**Watch for:** "Not only... but...", "It's not just about... it's...", "It doesn't just X, it Y", clipped tailing negations ("no guessing", "no wasted motion", "no fluff", "no hassle").

**Before:** It's not just about the resin holding the fibres in place; it's about how the laminate fails under load.

**After:** The resin holds the fibres in place. It also governs how the laminate fails under load.

**Before (tailing negation):** The jig sets the stops once at the start of the run, no wasted motion.

**After:** The jig sets the stops once at the start of the run, so the operator never has to re-measure a part.

### 18. "Not X, just Y" / "No X, just Y"

**Watch for:** "No fluff, just results", "No jargon, just clarity", "Not just X, but Y", "Not merely X — Y".

**Before:** No fluff, just results. No jargon, just clarity.

**After:** The dashboard surfaces three metrics and skips the rest.

### 19. Filler phrases

- "The board will make a decision on Thursday" → "The board decides Thursday"
- "Inspectors will conduct an investigation of the plant" → "Inspectors will investigate the plant"
- "In terms of battery life, the laptop disappoints" → "The laptop's battery life disappoints"
- "When it comes to safety, the sedan scores well" → "The sedan scores well on safety"
- "With regard to your refund, it was processed on Monday" → "Your refund was processed on Monday"
- "A large number of subscribers cancelled" → "Many subscribers cancelled"
- "The clinic is in close proximity to the tram stop" → "The clinic is near the tram stop"
- "Prior to the start of the workshop, collect the consent forms" → "Before the workshop, collect the consent forms"
- "During the course of the trial, three patients withdrew" → "Three patients withdrew during the trial"
- "Nurses check the readings on a regular basis" → "Nurses check the readings regularly"
- "In spite of the fact that the grant ended, the lab kept running" → "Although the grant ended, the lab kept running"
- "For all intents and purposes, the pilot is over" → "The pilot is over"
- "The fact of the matter is that shipping slipped by a week" → "Shipping slipped by a week"
- "In a manner of speaking, the merger was a rescue" → "The merger was effectively a rescue"
- "As many of you already know," → cut entirely

### 20. Empty pivot phrases

Phrases that announce a point is coming instead of making it. They survive standard filler stripping because they look more meaningful than they are.

**Watch for:** "It's worth noting that", "It bears mentioning that", "One thing to consider is", "It is interesting to note that", "A key consideration is", "A point to highlight is".

**Before:** It's worth noting that the API returns null on missing keys rather than throwing.

**After:** The API returns null on missing keys rather than throwing.

### 21. Outcome speculation tails

AI tacks vague future-implication phrases onto otherwise factual sentences.

**Watch for:** ", raising questions about", ", prompting reflection on", ", sparking debate about", ", with broader implications for", ", reshaping our understanding of", ", paving the way for".

**Before:** The court ruled against the company in March, raising questions about the future of digital privacy regulation.

**After:** The court ruled against the company in March. The decision is the first to apply the 2023 privacy law to a US-based platform.

### 22. Persuasive authority tropes

**Watch for:** "here's the thing", "make no mistake", "the truth is", "let's be honest", "the simple fact is", "at its core", "what really matters", "more than anything", "at the end of the day", "the bottom line is", "in reality", "fundamentally", "the real question is", "the heart of the matter", "the deeper issue", "when you get down to it".

**Before:** Here's the thing: make no mistake, the bottom line is that slow builds are a culture problem. At its core, what really matters is whether engineers trust the cache.

**After:** Slow builds are a culture problem as much as a technical one. Engineers who do not trust the cache will clear it, and then nobody's build is fast.

### 23. Editorial interjections

AI inserts an editorial voice claiming the next point is important.

**Watch for:** "It is important to", "One must note that", "It is worth pointing out", "It cannot be overstated that", "It must be emphasized that".

**Before:** It is important to remember that distributed systems fail in unpredictable ways.

**After:** Distributed systems fail in unpredictable ways.

### 24. Self-thoroughness phrases

AI advertises its own comprehensiveness inside the prose.

**Watch for:** "this comprehensive guide", "this in-depth analysis", "this complete overview", "a thorough examination of", "everything you need to know about".

**Before:** This comprehensive guide covers everything you need to know about TypeScript generics.

**After:** TypeScript generics let functions and types operate over multiple input types without losing type information.

### 25. Question-answer rhetorical pattern

AI uses "Question? One-word answer." structures for fake drama.

**Watch for:** "Is it perfect? No.", "Will it scale? Yes.", "Does this matter? Absolutely.", "A? Yes. B? No." sequences.

**Before:** Will the new model replace human writers? No. Will it change how writing gets done? Absolutely.

**After:** The new model will not replace human writers, but it will change how writing gets done — already, drafting and editing happen in shorter cycles.

### 26. "Concrete evidence" defense phrase

When challenged about whether text was AI-generated, AI-rewritten responses characteristically reach for `concrete evidence` or `concrete examples`. The phrase is so distinctive it is itself a fingerprint.

**Watch for:** "without concrete evidence", "do you have concrete evidence", "I would need concrete examples to", "absent concrete proof".

**Before:** Without concrete evidence that the text was AI-generated, the accusation cannot stand.

**After:** The accusation does not hold up: the timestamps on the draft history show the student rewrote each paragraph by hand over four sittings.

## Structure and discourse

### 27. Compulsive intro hooks

**Watch for:** "In today's fast-paced world,", "In a world where,", "In an era of,", "In recent years,", "More than ever before,", "We live in a time when".

**Before:** In today's fast-paced world, businesses need to adapt to survive.

**After:** Quarterly product cycles are now the norm in consumer hardware. Two years ago they were annual.

### 28. Meandering intro

Several paragraphs of background, context, and stage-setting before the first concrete fact or stake. The model warms up instead of starting. Common in essays and reports.

**Watch for:** an opening that defines terms, surveys history, and explains why the topic matters before saying anything specific; the real point arriving only in paragraph three or four.

**Fix:** start with the concrete claim, fact, or tension. Fold the necessary context into later sentences; cut the rest.

### 29. Prompt echo

AI restates or paraphrases the user's prompt as the first sentence of its output.

**Before (prompt: "explain CRDTs"):** CRDTs, or conflict-free replicated data types, are a class of data structures that allow concurrent updates across distributed nodes without coordination.

**After:** A CRDT is a data structure designed so that concurrent edits on different replicas always converge without coordination. The trade-off is restricted operations.

### 30. Diff-anchored writing

The text describes a *change or version* rather than the thing itself — it reads like a changelog or an answer to "what did you update?" instead of standalone prose. The reader has no diff to anchor against, so the framing is empty.

**Watch for:** `The update adds…`, `Unlike the previous version…`, `This has been changed to…`, `Now includes…`, `We've improved…`, opening clauses that presume a prior state the reader never saw.

**Before:** The new design adds a darker palette and improves the navigation. It also now includes a search bar that wasn't there before.

**After:** The interface uses a dark palette. A search bar sits in the top navigation bar.

### 31. Signposting and announcements

**Watch for:** "buckle up", "stay with me", "bear with me", "let's unpack this", "here's the rundown", "we'll get to that in a moment", "first, some context", "before we begin", "what follows is", "let's take a look", "let's dive in", "without further ado".

**Before:** Now let's look at how Halyard resolves plugins. Buckle up, there's a lot to unpack here.

**After:** Halyard resolves plugins in three passes: the lockfile first, then the workspace config, then the CLI flags. Later passes win.

### 32. Cataloguing lead-ins

AI announces a list before delivering it, often with a generic pivot sentence.

**Watch for:** `used / employed / relied on / utilizes` + `several / various / a number of / multiple / different / numerous` + a noun. Followed by a sentence opening with `These [X] provide / offer / give / reveal / show…`

**Before:** Verge Systems relied on several methods to bring query latency down. These methods give the platform team more headroom during peak hours.

**After:** Verge Systems moved the hot partitions onto SSD and put a result cache in front of the planner. Peak-hour queries that used to take nine seconds now finish in under two.

### 33. Inline-header vertical lists

**Before:**
- **Cold starts:** Cold start times have been significantly reduced with a new snapshot loader.
- **Memory:** Memory usage has been optimized through improved buffer reuse.
- **Logging:** Logging has been enhanced with structured JSON output.

**After:** A snapshot loader cuts cold starts, buffer reuse lowers memory use, and logs now come out as structured JSON.

### 34. Mid-essay bullet injection

AI breaks flowing prose into bullet lists where paragraphs would be appropriate. Reserve bullets for genuinely enumerable items (configuration options, ingredient lists). Argument and exposition stay in prose.

**Before:**
> The framework offers several advantages:
> - Faster build times
> - Better tree shaking
> - Improved type inference

**After:** The framework builds faster than its predecessor, removes unused code more aggressively, and infers types more often.

### 35. Fragmented headers

A section opens with a sentence that says nothing the heading did not already say, and only then gets to the point. Cut the echo; start with the point.

**Before:**
> ## Rate limits
> Rate limits protect the API.
> Tessera allows 600 requests per minute per key and returns 429 with a `Retry-After` header once you cross it.

**After:**
> ## Rate limits
> Tessera allows 600 requests per minute per key and returns 429 with a `Retry-After` header once you cross it.

### 36. Formulaic "Challenges" sections

**Watch for:** despite challenges, despite these challenges, Challenges and Legacy, Future Outlook, continues to thrive, typical of emerging / urban, despite its [positive], faces challenges including.

**Before:** Despite its manufacturing legacy, Tarnbeck faces challenges typical of post-industrial towns, including retail vacancy. Despite these challenges, with its strong community spirit, Tarnbeck continues to thrive.

**After:** By 2019 a third of the high street's shop units stood empty, up from one in ten a decade earlier. The council began offering two-year rent holidays to new tenants in 2021, and eleven units have been let since.

### 37. Transition cluster overuse

A single transition word per paragraph is fine. AI strings three or four into the same paragraph: `Additionally`, then `Furthermore`, then `Moreover`, then `However`.

**Flag** when 2+ of these appear at sentence starts in one paragraph: Additionally, Furthermore, Moreover, However, Nevertheless, Consequently, Subsequently.

**Before:** The team launched the product in Q1. Additionally, they expanded to three new markets. Furthermore, customer satisfaction scores improved. Moreover, churn dropped below 5%.

**After:** The team launched the product in Q1 and expanded to three new markets. Customer satisfaction scores improved and churn dropped below 5%.

### 38. Compulsive conclusion phrases

AI reflexively summarizes what it just said. The closing paragraph restates the opening in different words.

**Watch for:** "In conclusion,", "Overall,", "In summary,", "To summarize,", "To conclude,", "All in all,", "In essence,", "Ultimately,".

**Before:** In conclusion, the rise of renewable energy represents a major shift in global power generation. Overall, this transition will reshape economies for decades to come.

**After:** Renewables overtook coal as the largest source of global electricity generation in 2025. Installation rates suggest the gap will widen through the decade.

### 39. Generic positive conclusions

**Before:** The outlook for Harrowgate Dairy is bright. With a passionate team and a clear vision, the creamery is well positioned for whatever comes next.

**After:** Harrowgate Dairy signed supply deals with two supermarket chains in April. A second bottling line opens in autumn.

## Rhythm and cadence

### 40. Sentence-length monotony

Human writing varies sentence length. AI produces sentences of roughly the same length, which reads as a flat hum even when the words are fine.

**Target:** at least one sentence under 10 words per paragraph; sentence-length variance above ~0.35 coefficient of variation across the passage.

**Before:** The nightly job pulls yesterday's events from the warehouse into staging. It then deduplicates the rows against a rolling seven-day window. The cleaned rows are written back to the reporting schema each morning. Analysts query that schema through the dashboards they already use.

**After:** Every night the job copies yesterday's events into staging and drops duplicates against a rolling seven-day window. The clean rows land in the reporting schema by morning. Analysts never see any of this. They just open the dashboard.

### 41. Mechanical sentence-length alternation

The 2026-era evolution of monotony (#40): models trained against uniform sentence length now alternate short-long-short-long on a metronome. The length *varies*, so the plain CV check passes — but the variation itself is periodic. `detect.py` reports it as `_metrics.cadence_zigzag` (share of successive length-difference sign flips); a value near 1.0 over six or more sentences flags `41_mechanical_alternation`.

**Watch for:** every short sentence followed by exactly one long sentence, for a whole paragraph; rhythm you can conduct.

**Before:** It works. The design combines three separate caching layers into one coherent pipeline that scales. It ships today. Users on the free tier get the same performance improvements as enterprise customers do.

**After:** It works, and it ships today. The design combines three caching layers into one pipeline. Free-tier users get the same performance as enterprise customers — same code path, same limits, no artificial throttling.

### 42. Opener repetition

AI starts consecutive sentences with the same two-word frame. Humans drift through openers.

**Flag** when three or more sentences in a paragraph open with identical two-word frames (`The system... The system... The system...`).

**Before:** The Tessera client retries idempotent calls twice. The Tessera client waits longer between each attempt. The Tessera client gives up after 30 seconds and raises `TimeoutError`.

**After:** The Tessera client retries idempotent calls twice, with an exponential backoff between attempts. After 30 seconds it gives up and raises `TimeoutError`.

### 43. Avoidance of fragments and run-ons

AI maintains "perfect" grammar. It rarely starts sentences with `And` or `But`, never uses fragments for emphasis, never runs two thoughts together with a comma splice for rhythm. Human writing — especially opinion and journalism — uses all of these on purpose.

**Apply in drastic mode only.** Encyclopedic content stays grammatically tight.

**Watch for:** absence of any sentence opening with `And`, `But`, `So`, `Because`, `Or`, when the surrounding tone is conversational. Absence of any sentence shorter than 5 words across a long passage.

**Before:** Halyard's error messages are unusually clear. They tell you which rule failed and where it was defined. This makes debugging a broken build considerably less frustrating than it used to be.

**After:** Halyard's error messages are unusually clear. They name the rule that failed and the file that defined it. Which is rare. And it turns a broken build into something you fix, not something you dread.

### 44. Uniform paragraph length

AI produces paragraphs of nearly identical size (3–5 sentences each). Real writing varies — sometimes a one-sentence paragraph, sometimes a long block.

**Target:** paragraph length coefficient of variation above ~0.4 across a document with 4+ paragraphs.

**Before:** Four consecutive paragraphs of 4 sentences each.

**After:** A 1-sentence paragraph for emphasis, followed by a 6-sentence paragraph that builds context, followed by a 3-sentence paragraph that turns the argument.

### 45. Identical paragraph structure

Three or more paragraphs marching through the same shape — claim, then evidence, then a takeaway clause — reads as templated. Real writing varies the move: sometimes the example comes first, sometimes the point lands with no wrap-up. Supported by the low `_metrics.paragraph_cv` signal.

**Watch for:** every paragraph opening with a topic-sentence claim and closing with an "implication" sentence (`This shows that…`, `As a result…`, `This means…`).

**Fix:** break the lockstep — lead one paragraph with the example, let another end on the evidence, cut a takeaway clause that only restates the opener.

### 46. Semicolon and parenthesis underuse

Across a passage of at least 500 words, the detector reports this advice when it
finds no semicolon and fewer than two parenthetical pairs. The rule carries no
score weight because punctuation varies with register and house style.

**Apply only as a document-level diagnostic, not a sentence-level rewrite rule.** Do not insert semicolons mechanically; instead, rewrite a passage to use one where the rhythm calls for it.

**Before (zero punctuation diversity):** The library opened in 1962. It was designed by a Finnish architect. Almost every wall is poured concrete. The reading room sits on the top floor.

**After:** The library opened in 1962; the Finnish architect who designed it lined almost every wall with poured concrete. The reading room sits on the top floor.

## Register and voice

### 47. Chatbot artifacts

**Watch for:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a..., feel free to ask, happy to help, hope this email finds you well.

**Before:** Of course! Below is a summary of Larkspur Foods' updated expense policy. Staff must file claims within 30 days of travel, and mileage is reimbursed at the rate published each January. Happy to help if you need the archived version too!

**After:** Larkspur Foods has updated its expense policy. Staff file claims within 30 days of travel, and mileage is reimbursed at the rate published each January.

### 48. Sycophantic / servile tone

**Before:** What a thoughtful question! You are absolutely right to worry about the sample size, and I love how carefully you read the methods section. With only 30 students per group, the study can detect large differences and little else.

**After:** The sample size is worth worrying about. With 30 students per group, the study can detect large differences in scores and little else.

### 49. RLHF / helpful-assistant register

Instruction-tuning artifacts — the servile-tutor scaffolding a chat model adds by reflex. Detectors increasingly fire on *this register* rather than vocabulary. Strip the forced balance and the pedagogical hand-holding.

**Watch for:** reflexive both-sidesing (`on one hand… on the other hand`, `while X, it's also true that Y`), `it's important to consider both perspectives`, `there are pros and cons to each`, balanced-summary closers that refuse to land a point, and tutor-ish framing (`Let's explore`, `It's worth understanding that`).

**Before:** There are valid arguments on both sides. On one hand, remote work boosts flexibility; on the other, it can weaken collaboration. Ultimately, it depends on the team.

**After:** Remote work boosts flexibility but weakens spontaneous collaboration. Teams that adopt it usually add deliberate sync points to compensate.

### 50. Knowledge-cutoff disclaimers

**Watch for:** "as of [date]", "up to my last training update", "while specific details are limited", "based on available information", "as of my knowledge cutoff".

**Before:** Based on available information, the Wexley Institute appears to have scaled back its air-quality monitoring at some point in recent years, though specific details are limited.

**After:** The Wexley Institute cut its air-quality network from twelve monitoring stations to four in March 2024. Its annual report gives the loss of a regional grant as the reason.

### 51. Copula avoidance

**Watch for:** serves as, stands as, functions as, marks, represents, boasts, features, offers, refers to, acts as (when "is" or "has" would work).

**Before:** The Aldwick Toolworks Museum serves as the home of the county's edge-tool collection. The building features three galleries and boasts more than 4,000 square feet of floor space.

**After:** The Aldwick Toolworks Museum is home to the county's edge-tool collection. It has three galleries, about 4,000 square feet in all.

### 52. Passive voice and subjectless fragments

**Watch for:** "No X needed", "X is performed automatically", dropped subjects when the actor matters.

**Before:** No manual calibration needed. Each reading is logged automatically.

**After:** You do not have to calibrate the gauge by hand. The logger writes each reading to its memory card.

### 53. Two-way passive-voice drift

The old tell was passive overuse; newer models overcorrect and produce *less* passive voice than humans do in genres where passive is conventional (methods sections, incident reports, legal and technical writing). Both directions are drift. `_metrics.passive_voice_ratio` gives the document's rate; judge it against the genre, not against zero.

**Watch for:** a methods section with zero passives ("We heated the sample… We recorded the mass…" throughout), or the reverse — agentless passives hiding responsibility in prose that should name actors.

**Fix:** match the genre's convention. Restore conventional passives in formal-technical genres; convert agentless passives to active voice where the actor matters.

### 54. Excessive hedging (hedge stacking)

A single hedge ("may", "could", "seems") is normal English. AI **stacks** two or more in one sentence, producing prose that asserts almost nothing.

**Hedge words:** may, might, could, possibly, potentially, arguably, perhaps, seems / seems to, appears to, somewhat, relatively, fairly, kind of, sort of.

**Rule:** 2+ hedges in one sentence → flag. Rewrite down to one hedge. Never to none: the stack is the defect, the qualification is not, and cutting the last hedge turns a qualified claim into an absolute one. `there is the risk of X` and `X may occur` are hedges even though the words below do not list them.

**Before:** The revised screening schedule could potentially reduce late-stage diagnoses somewhat, and might arguably prove relatively cost-effective for most regional clinics.

**After:** The revised screening schedule may cut late-stage diagnoses. In most regional clinics it also costs less to run than the current one.

### 55. Contraction absence

In informal or conversational registers, AI defaults to formal "it is" / "do not" / "you are". Real humans use "it's", "don't", "you're". In encyclopedic mode, leave full forms alone; in opinion mode, contract.

**Before (opinion mode):** I do not think the approach is wrong, but it is not what I would have chosen.

**After:** I don't think the approach is wrong, but it's not what I would've chosen.

## Formatting and typography

### 56. Boldface overuse

**Before:** Tessera 3.0 adds **idempotency keys**, **webhook retries with exponential backoff**, and a **batch endpoint** that accepts up to **500 records per call**.

**After:** Tessera 3.0 adds idempotency keys, webhook retries with exponential backoff, and a batch endpoint that takes up to 500 records per call.

### 57. Emojis

**Before:** ✅ **Shipped:** The batch endpoint is live in v3.0. ⚠️ **Heads up:** The old `/bulk` route retires in June.

**After:** The batch endpoint is live in v3.0. The old `/bulk` route retires in June.

### 58. Em-dash overuse

At most one em-dash per paragraph, only for genuine contrast or range (`kg/m³ — one of the lightest of any wood`). Decorative em-dashes inside asides become commas or parentheses.

**Before:** The migration guide ships with the release—but almost nobody reads it. Halyard 4 renames every flag—`--watch` becomes `--follow`—and the old names keep working for one more version—which is why the breakage lands in April, not now.

**After:** The migration guide ships with the release, but almost nobody reads it. Halyard 4 renames every flag (`--watch` becomes `--follow`) and the old names keep working for one more version. The breakage lands in April, not now.

### 59. Title case in headings

**Before:** `## Configuring The Retry Budget And Backoff Policy`

**After:** `## Configuring the retry budget and backoff policy`

### 60. Curly quotation marks

**Before:** The changelog calls the endpoint “deprecated, not removed,” which the on-call team read as ‘safe to ignore.’

**After:** The changelog calls the endpoint "deprecated, not removed," which the on-call team read as 'safe to ignore.'

### 61. Hyphen-for-en-dash in ranges

AI consistently uses a hyphen (`-`) where typographic convention calls for an en dash (`–`). Affects date ranges (`1990-2000`), score ranges (`3-2`), page references (`pp. 14-22`), and numeric spans.

**Before:** The conflict (1939-1945) reshaped European borders. Final score: 3-2.

**After:** The conflict (1939–1945) reshaped European borders. Final score: 3–2.

## Machine artifacts (plus §69, a lexical addition placed here for continuity with the index)

### 62. Invisible / zero-width characters

Characters that are invisible when rendered reach a draft from many directions: copy-paste out of a rendered page, paraphrasing tools, editors, and deliberate hidden-text insertion. The rule is written on the character category, so it does not know or care what put a given codepoint there, and it identifies nothing about the source. Anything hidden in these planes is removed along with the debris, because a category rule cannot tell the two apart and is not asked to try. Detection is **driven by the Unicode character database**, not a hand-maintained list: `scripts/detect.py` flags any character whose `General_Category` is `Cf`, `Cc` (except the legitimate `\t` / `\n` / `\r`), `Zl`, or `Zp`, plus every `Default_Ignorable_Code_Point` whose category is not `Cf`, plus the whole `U+E0000`–`U+E0FFF` tag/variation-selector plane. Because it is category-driven it tracks the Unicode version bundled with the runtime rather than a hand-maintained range table. The categories cover, by example:

- **Zero-width** — `U+200B` (space), `U+200C` (non-joiner), `U+200D` (joiner), `U+2060` (word joiner), `U+FEFF` (BOM / zero-width no-break space).
- **Bidi controls** — `U+200E`/`U+200F` (LRM/RLM), `U+202A`–`U+202E` (embeddings/overrides), `U+2066`–`U+2069` (isolates).
- **Invisible math operators** — `U+2061`–`U+2064` (function application, invisible times/separator/plus).
- **TAG block** — `U+E0000`–`U+E007F`. Deprecated, and a run of them can encode an entire hidden message that survives copy-paste ("ASCII smuggling"). Caught by the category, like every other line here; the rule makes no claim about what the run encodes or who put it there.
- **Variation-selector supplement** — `U+E0100`–`U+E01EF`, which can carry hidden text the same way.
- **Other** — soft hyphen (`U+00AD`), Arabic letter mark (`U+061C`), Mongolian vowel separator (`U+180E`), combining grapheme joiner (`U+034F`), Hangul/Khmer fillers, line/paragraph separators (`U+2028`/`U+2029`), and other C0/C1 control characters. `\t`, `\n`, and `\r` are **not** stripped — they are legitimate layout whitespace (see §68).

To scrub a draft deterministically, run `python scripts/detect.py --clean < draft.txt`. It removes every character in this set, normalizes non-standard spaces (§67), trims stray whitespace (§68), and leaves visible content (letters, digits, punctuation, math symbols, accents, CJK, emoji bases) byte-for-byte intact. Note: a variation selector (`U+FE0F`) following an emoji base is legitimate emoji rendering; since emoji is itself a tell (§57), `--clean` removes it along with the emoji rather than treating it as a hidden character on its own.

**Before:** `Hello​world — the​word count looks fine but the text carries stray control characters.`

**After:** `Hello world` — same visible text, same word count, no stray control characters.

### 63. Placeholder / Mad-Libs text

The model emitted a template and never filled the slots. A near-zero-false-positive tell: real published text does not contain bracketed instructions to itself.

**Watch for:** `[Your Name]`, `[INSERT URL]`, `[COMPANY]`, `[DATE]`, `[XX]`, `[TODO]`, `[placeholder]`, and `lorem ipsum`.

**Before:** Thank you for your interest. Please contact [Your Name] at [INSERT EMAIL] to schedule a call.

**After:** Thank you for your interest. *(The slots stay as they are; see below.)*

**Do not fill a slot by inventing what belongs in it.** A name and an address written to clear this rule are fabrication, and the tell was the model failing to fill the template, not the template. Leave `[Your Name]` exactly as written and say the draft is unfinished. The same holds for merge fields a sending system will fill, `[Name]` and `{{first_name}}` alike: rewriting one into the other breaks the merge and is not a fix.

### 64. Chatbot reference-markup leak

Internal citation or tool-call tokens that should never have rendered escaped into the pasted output. Decisive — these strings exist only inside an assistant's machinery.

**Watch for:** `citeturn0search0`, `oai_citation`, `contentReference`, `navlist`, and the `【12†source】` citation bracket.

**Before:** The market grew 14% last year oai_citation and is forecast to double by 2030 citeturn0search3.

**After:** The market grew 14% last year and is forecast to double by 2030.

**Do not "repair" the leak by inventing a citation.** The tokens are machinery, not a source: strip them and leave the claim as the draft made it. Naming a real firm or a plausible-looking report to fill the gap is fabrication, which is worse than the leak was — see *Critical content preservation* in `SKILL.md`.

### 65. AI tracking params

A link copied straight out of a chat interface carries that interface's UTM source. It records where the link was copied from, and nothing about who wrote the text around it. Strip it because it is a stray tracking parameter that was never meant to ship.

**Watch for:** `utm_source=chatgpt.com`, `utm_source=perplexity.ai`, `utm_source=claude.ai`, `utm_source=gemini.google.com`, `utm_source=copilot.microsoft.com`.

**Before:** See the full guide at https://example.com/guide?utm_source=chatgpt.com for details.

**After:** See the full guide at https://example.com/guide for details.

### 66. Homoglyph / mixed-script confusables

Visible look-alike letters from another script (Cyrillic `а`/`о`/`е`, Greek `ο`, etc.) substituted into otherwise-Latin words to defeat tokenizers and plagiarism/identity checks. They survive an invisible-character scrub because they are ordinary visible letters in valid Unicode categories. The fix folds them to their ASCII skeleton — but only inside a **mixed-script token** (one that also contains ASCII Latin), so a genuine single-script word like `Москва` is never touched.

**Watch for:** a word that mixes scripts — e.g. `pаssword` where `а` is U+0430 (Cyrillic), `wrоng` where `о` is U+043E. `scripts/detect.py --clean` folds these automatically.

**Before:** The p**а**ssword field shows wr**о**ng when the entry is invalid. *(Cyrillic а / о hidden inside Latin words.)*

**After:** The password field shows wrong when the entry is invalid. *(All-ASCII; genuine non-Latin prose elsewhere is left intact.)*

### 67. Non-standard spaces

Distinct from §62: these characters are *visible* — they render as a blank — but they are not the regular space `U+0020`. AI output and rich-text copy-paste introduce them, and they break word counts, search, diffing, and justification. Unlike §62 (strip), the fix is to **normalize them to a regular space**, because a space is genuinely meant to be there.

**Watch for:** no-break space (`U+00A0`), narrow no-break space (`U+202F`), the en-quad-through-hair-space block (`U+2000`–`U+200A`), medium mathematical space (`U+205F`), and ideographic space (`U+3000`).

**Before:** `These two words` are joined by a no-break space and these by a narrow one — invisible to the eye, but a single token to a detector.

**After:** `These two words` use ordinary spaces; the rendered text looks identical and the token boundaries are clean.

### 68. Trailing / stray whitespace

Paste-tool gimmicks flag a lone trailing newline as a "hidden character." A single trailing `\n` is normal POSIX file convention and not an AI tell — but stray whitespace beyond it is a paste artifact worth removing. **Trim it from the final output** regardless; never strip whitespace from inside the body.

**Watch for:** trailing spaces or tabs at end of file, a blank trailing line (two or more `\n` at EOF), spaces or tabs before a line break (`text   \n`), and leading whitespace before the first character. The lone trailing `U+000A` is reported in `_metrics.trailing_newlines` and trimmed, but does not raise the pattern flag on its own.

**Before:** `The report is final.   ⏎⏎` — two blank lines and three trailing spaces left over from a paste.

**After:** `The report is final.` — trimmed to a single clean line, no trailing newline carried into the rewrite.

### 69. Canonical marketing-slop phrases

A bank of multi-word clichés that are near-absent from genuine human writing, so they flag with high precision: `unlock the full potential`, `navigate the complexities of`, `a testament to the power of`, `stay ahead of the curve`, `turn challenges into opportunities`, `the future is full of possibilities`, `something for everyone`, `whether you are a beginner or a pro`, `the key takeaway`, `seamlessly integrate`, `take it to the next level`, `working smarter, not harder`, `more important than ever`, `drive meaningful impact`. One or two in a paragraph is the strongest single-phrase slop signal there is.

**Watch for:** any of the phrases above, especially clustered. Unlike single AI-vocabulary words (which appear in legitimate business prose), these full templates almost never survive a human writer's edit.

**Before:** Unlock the full potential of your team and stay ahead of the curve by embracing a holistic approach that turns challenges into opportunities.

**After:** Give the team the training budget and the two days a month it has asked for. That is what has moved the numbers in the pilot group.

### 70. Decorative horizontal rules

Markdown post-training leaves horizontal rules behind as section furniture. Human markdown uses one, or none. Fires at three or more standalone rules in a document of at least 25 lines, so a single rule above a licence footer stays silent.

**Before:** a document alternating `---` and `##` headings every few paragraphs, with no rule carrying meaning.

**After:** headings alone carry the structure; rules are kept for a genuine break, such as before an appendix.

### 71. Degenerate repetition

A model that loses the thread emits the same span until the window closes. This
is not the repetition of a term of art, which careful academic prose does
constantly, but a stuck loop. It is the only tell present in small-model
continuations, which carry none of the vocabulary the rest of this catalogue is
built around.

Measured as the share of six-word spans that occur more than once. The bar is
high because legitimate repetition is common: 15.1% of PubMed abstracts and
10.5% of textbook passages repeat more than 2% of their spans, and no human
corpus measured reaches 13% at the 99th percentile. Degeneration runs an order
of magnitude higher. Fires above 20%, where it flags none of the PubMed,
textbook or web human arms, 0.2% of arXiv abstracts, and 18.6% of machine SQuAD
continuations.

**Before:** "A shortage of affordable housing is caused in part by a lack of new
supply, is caused in part by a lack of new supply, is caused in part by a lack of
new supply in most large cities."

**After:** "A shortage of affordable housing has several causes; in the US, the
supply of new units is the largest."

## Style Profiles (positive targets)

These are the rebuild targets offered by the picker. They do not change which tells are removed — they set the voice the cleaned text is rebuilt into. Full descriptions live in `SKILL.md` → *Style Profiles*.

- **2000s textbook** *(default)* — clear declarative SVO sentences; real length variation; concrete worked examples; expository "we"/"consider"; semicolons natural, em-dash sparing; zero hype / signposting / hedging / generic conclusions. Neutral, authoritative, conservative mode.
- **Plain / clear (Zinsser)** — short words, cut clutter, concrete nouns and active verbs, one thought per sentence.
- **Conversational essay** — first person, contractions, asides, reactions; drastic mode; only for already-personal content.
- **Journalistic / news** — AP style; key fact in the lede; inverted pyramid; attributed claims; plain verbs; no editorializing.
