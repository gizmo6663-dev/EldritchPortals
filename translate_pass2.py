#!/usr/bin/env python3
"""Second-pass translation: replace all remaining Norwegian text in main.py."""

import re

with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Each entry: (old, new) — order matters for multi-word phrases before single words.
REPLACEMENTS = [

    # ── Version string ────────────────────────────────────────────────
    ('v0.4.0 Necronomicon', 'v0.4.5 Necronomicon'),

    # ── Constant-section comments (lines ~92-111) ─────────────────────
    ('# Scenario file: primær lagring i user_data_dir (app-private,',
     '# Scenario file: primary storage in user_data_dir (app-private,'),
    ('# midlertidig; overstyres i build()',
     '# temporary; overridden in build()'),
    ('# bruk den (lar brukeren overstyre med egen fil hvis mulig).',
     '# use it (allows the user to override with their own file if possible).'),
    ('# Favoritter lagres i user_data_dir (app-private, alltid skrivbar).',
     '# Favourites stored in user_data_dir (app-private, always writable).'),

    # ── PULP_MADNESS_RT descriptions ──────────────────────────────────
    ('"Karakteren mister hukommelsen for de siste hendelsene "\n'
     '         "(siste 1d10 minutter)."),',
     '"The character loses memory of recent events "\n'
     '         "(last 1d10 minutes)."),'),
    ('"keeper bestemmer).',
     '"keeper decides).'),
    ('"Mistenker alle og alt; ser konspirasjoner overalt "\n'
     '         "i 1d10 runder."),',
     '"Suspects everyone and everything; sees conspiracies everywhere "\n'
     '         "for 1d10 rounds."),'),
    ('"Forveksler en tilstedeværende med en viktig person fra "\n'
     '         "fortiden; oppfører seg deretter i 1d10 runder."),',
     '"Mistakes someone present for an important person from "\n'
     '         "the past; acts accordingly for 1d10 rounds."),'),
    ('"Gråter, ler eller skriker ukontrollert i 1d10 runder; "\n'
     '         "ute av stand til å handle."),',
     '"Cries, laughs, or screams uncontrollably for 1d10 rounds; "\n'
     '         "unable to act."),'),
    ('"Utvikler en ny fobi knyttet til kilden av sjokket; "\n'
     '         "varer i 1d10 runder."),',
     '"Develops a new phobia tied to the source of the shock; "\n'
     '         "lasts 1d10 rounds."),'),
    ('"Utvikler en ny mani knyttet til kilden av sjokket; "\n'
     '         "varer i 1d10 runder."),',
     '"Develops a new mania tied to the source of the shock; "\n'
     '         "lasts 1d10 rounds."),'),
    # Fix typos: Hysteriaa → Hysteria, Maniaa → Mania
    ('"Physical Hysteriaa"', '"Physical Hysteria"'),
    ('"Maniaa"', '"Mania"'),
    ('"Hysteriaa"', '"Hysteria"'),

    # ── PULP_MADNESS_SUM descriptions ────────────────────────────────
    ('"Våkner et trygt sted uten minne om hva som hendte de siste "\n'
     '         "1d10 timene."),',
     '"Wakes up somewhere safe with no memory of what happened "\n'
     '         "in the last 1d10 hours."),'),
    ('"Forsvinner i 1d10 dager; ingen — heller ikke karakteren "\n'
     '         "selv — vet hvor han har vært."),',
     '"Disappears for 1d10 days; no one — not even the character "\n'
     '         "themselves — knows where they have been."),'),
    ('"Begår voldelige handlinger i 1d10 dager; må forklare seg "\n'
     '         "for myndighetene etterpå."),',
     '"Commits violent acts for 1d10 days; must answer "\n'
     '         "to the authorities afterward."),'),
    ('"Sterk paranoia i 1d10 dager; ser fiender i skygger og "\n'
     '         "venner."),',
     '"Intense paranoia for 1d10 days; sees enemies in shadows "\n'
     '         "and friends."),'),
    ('"Identifiserer noen som ekstremt betydningsfull og følger "\n'
     '         "eller jakter dem i 1d10 dager."),',
     '"Identifies someone as extremely significant and follows "\n'
     '         "or pursues them for 1d10 days."),'),
    ('"Våkner i et sykehus, asyl eller fengsel uten å vite "\n'
     '         "hvordan; 1d10 dagers opphold."),',
     '"Wakes up in a hospital, asylum, or prison with no idea "\n'
     '         "how; 1d10 days of confinement."),'),
    ('"Drar instinktivt mot hjemmet eller barndomstedet; reisen "\n'
     '         "tar 1d10 dager."),',
     '"Instinctively heads home or to a childhood location; "\n'
     '         "the journey takes 1d10 days."),'),
    ('"Overveldende emosjonell tilstand i 1d10 dager; må "\n'
     '         "stabiliseres av andre."),',
     '"Overwhelmed by emotion for 1d10 days; must be "\n'
     '         "calmed by others."),'),
    ('"Utvikler en ny vedvarende fobi som varer 1d10 måneder."),',
     '"Develops a new persistent phobia lasting 1d10 months."),'),
    ('"Utvikler en ny vedvarende mani som varer 1d10 måneder."),',
     '"Develops a new persistent mania lasting 1d10 months."),'),

    # ── make_glow_bar_tex docstring ───────────────────────────────────
    ('    def make_glow_bar_tex(rgb, width=256, height=12):\n'
     '        """En horisontal lys-stripe med myk falloff på begge akser.\n'
     '        Brukt som indikator for aktive faner — ser ut som et lysskjær\n'
     '        i stedet for en hard stripe.\n'
     '\n'
     '        - rgb: 3-tuple (r, g, b) 0..1 (alpha bygges fra falloff).\n'
     '        - Horisontal: sterk fade på begge ender (~sin^1.35).\n'
     '        - Vertikal: bred lys-kjerne med litt mykere topp/bunn (~sin^0.45).\n'
     '        """',
     '    def make_glow_bar_tex(rgb, width=256, height=12):\n'
     '        """A horizontal light strip with soft falloff on both axes.\n'
     '        Used as an indicator for active tabs — looks like a glow\n'
     '        rather than a hard stripe.\n'
     '\n'
     '        - rgb: 3-tuple (r, g, b) 0..1 (alpha built from falloff).\n'
     '        - Horizontal: strong fade at both ends (~sin^1.35).\n'
     '        - Vertical: wide bright core with slightly softer top/bottom (~sin^0.45).\n'
     '        """'),

    # get_glow_bar_tex comments
    ('            # Varm amber-gull — midt mellom GOLD og pale-gold.\n'
     '            # Lysere enn det rene GOLD-en, men fortsatt tydelig gull\n'
     '            # snarere enn nesten-hvit.',
     '            # Warm amber-gold — midway between GOLD and pale-gold.\n'
     '            # Brighter than pure GOLD, but still clearly gold\n'
     '            # rather than near-white.'),

    # ── make_pulse_glow_tex docstring ────────────────────────────────
    ('    def make_pulse_glow_tex(rgb, size=128, inset_ratio=0.32):\n'
     '        """Generer en 2D glow-tekstur for puls-effekten på faner.\n'
     '\n'
     '        Strukturen er en distansefelt-basert "blurret avrundet\n'
     '        rektangel":\n'
     '        - Et indre kjerne-rektangel (inset_ratio * size fra kantene)\n'
     '          har full alpha.\n'
     '        - Utenfor kjernen faller alpha kontinuerlig av med en cosine-\n'
     '          falloff til 0 ved teksturens kant.\n'
     '\n'
     '        Cosine gir mykere fall enn ren gaussian — vi treffer nøyaktig\n'
     '        alpha=0 ved kantene, slik at det IKKE er en synlig "klipping"\n'
     '        der teksturen ender. Tilsvarende metode som lysstripen.\n'
     '        """',
     '    def make_pulse_glow_tex(rgb, size=128, inset_ratio=0.32):\n'
     '        """Generate a 2D glow texture for the pulse effect on tabs.\n'
     '\n'
     '        The structure is a distance-field-based "blurred rounded\n'
     '        rectangle":\n'
     '        - An inner core rectangle (inset_ratio * size from the edges)\n'
     '          has full alpha.\n'
     '        - Outside the core, alpha falls off continuously with a cosine\n'
     '          falloff to 0 at the texture edge.\n'
     '\n'
     '        Cosine gives softer falloff than pure Gaussian — we hit exactly\n'
     '        alpha=0 at the edges, so there is NO visible "clipping"\n'
     '        where the texture ends. Same method as the light strip.\n'
     '        """'),

    # make_pulse_glow_tex trailing comment
    ('        # Maks distanse fra kjernen til teksturens kant',
     '        # Max distance from the core to the texture edge'),

    # ── RULES section: Grunnregler ────────────────────────────────────
    ('      ("Grunnregler", "", [', '      ("Core Rules", "", ['),
    ('        ("Ferdighetskast", [', '        ("Skill Rolls", ['),
    ('"Automatisk suksess: 01 alltid suksess.',
     '"Automatic success: 01 always succeeds.'),
    ('"Fumble (based on THRESHOLD, not base skill):',
     '"Fumble (based on THRESHOLD, not base skill):'),
    ('"  Krav \u2265 50: kun 100 er fumble"',
     '"  Requirement \u2265 50: only 100 is a fumble"'),
    ('"  Krav < 50: 96\u2013100 er fumble"',
     '"  Requirement < 50: 96\u2013100 is a fumble"'),
    ('"  Eks: skill 60, Hard diff (krav 30)"',
     '"  Ex: skill 60, Hard diff (requirement 30)"'),
    ('"    -> fumble på 96\u2013100"',
     '"    -> fumble on 96\u2013100"'),

    ('        ("Vanskelighetsgrad", [', '        ("Difficulty", ['),
    ('"Keeper setter vanskelighetsgrad:"',
     '"Keeper sets difficulty:"'),
    ('"  Regular: skill-verdi (standard)"',
     '"  Regular: skill value (default)"'),
    ('"  Hard: halv skill-verdi"',
     '"  Hard: half skill value"'),
    ('"  Extreme: femtedel av skill-verdi"',
     '"  Extreme: one-fifth of skill value"'),
    ('"Mot levende motstandere:"',
     '"Against living opponents:"'),
    ('"  Motstanders skill < 50: Regular"',
     '"  Opponent skill < 50: Regular"'),
    ('"  Motstanders skill \u2265 50: Hard"',
     '"  Opponent skill \u2265 50: Hard"'),
    ('"  Motstanders skill \u2265 90: Extreme"',
     '"  Opponent skill \u2265 90: Extreme"'),

    ('"Bonus die: rull 2 tier-terninger,"',
     '"Bonus die: roll 2 tens dice,"'),
    ('"  bruk den LAVESTE."',
     '"  use the LOWEST."'),
    ('"Penalty die: rull 2 tier-terninger,"',
     '"Penalty die: roll 2 tens dice,"'),
    ('"Maks 2 bonus ELLER 2 penalty."',
     '"Max 2 bonus OR 2 penalty."'),
    ('"Bonus og penalty kansellerer 1:1."',
     '"Bonus and penalty cancel 1:1."'),

    ('        ("Pushed Rolls", [', '        ("Pushed Rolls", ['),
    ('"Spiller kan pushe ETT mislykket kast."',
     '"Player may push ONE failed roll."'),
    ('"Mislykket push = ALVORLIG konsekvens"',
     '"Failed push = SERIOUS consequence"'),
    ('"(verre enn vanlig feil)."',
     '"(worse than a normal failure)."'),
    ('"KAN IKKE pushes:"',
     '"CANNOT be pushed:"'),
    ('"  SAN-sjekker"',
     '"  SAN checks"'),
    ('"  Luck-sjekker"',
     '"  Luck checks"'),
    ('"  Kamp-kast"',
     '"  Combat rolls"'),
    ('"  Allerede pushede kast"',
     '"  Already pushed rolls"'),

    ('"Begge parter ruller sine skills."',
     '"Both parties roll their skills."'),
    ('"Ingen suksess: status quo."',
     '"No success: status quo."'),
    ('"Vanlige opposed rolls:"',
     '"Common opposed rolls:"'),
    ('"  STR vs STR (bryte, holde)"',
     '"  STR vs STR (break, hold)"'),
    ('"  DEX vs DEX (gripe, unnvike)"',
     '"  DEX vs DEX (grab, dodge)"'),

    ('"Luck-verdi: 3d6 x 5 (ved opprettelse)."',
     '"Luck value: 3d6 x 5 (at creation)."'),
    ('"Luck-sjekk: d100 \u2264 Luck."',
     '"Luck check: d100 \u2264 Luck."'),
    ('"  Etter et skill-kast: trekk Luck-poeng"',
     '"  After a skill roll: subtract Luck points"'),
    ('"  Eks: kast 55, skill 50 -> spend 5 Luck."',
     '"  Ex: roll 55, skill 50 -> spend 5 Luck."'),
    ('"Luck regenereres IKKE i standard CoC."',
     '"Luck does NOT regenerate in standard CoC."'),
    ('"Pulp: regenerer 2d10 Luck per sesjon."',
     '"Pulp: regenerate 2d10 Luck per session."'),
    ('"Group Luck: laveste Luck i gruppen"',
     '"Group Luck: lowest Luck in the group"'),
    ('"  brukes for tilfeldige hendelser."',
     '"  used for random events."'),

    ('        ("Erfaring & utvikling", [', '        ("Experience & Advancement", ['),
    ('"Etter scenario: marker brukte skills."',
     '"After scenario: mark used skills."'),
    ('"Rull d100 for hver markert skill:"',
     '"Roll d100 for each marked skill:"'),
    ('"  Resultat > skill = +1d10 til skill."',
     '"  Result > skill = +1d10 to skill."'),
    ('"  Resultat \u2264 skill = ingen økning."',
     '"  Result \u2264 skill = no increase."'),
    ('"Skill-maks: 99 (unntatt CM: 99)."',
     '"Skill max: 99 (except CM: 99)."'),
    ('"Alderseffekter kan senke stats."',
     '"Age effects may lower stats."'),

    # ── RULES section: Kamp ───────────────────────────────────────────
    ('      ("Kamp", "", [', '      ("Combat", "", ['),
    ('        ("Kampflyt", [', '        ("Combat Flow", ['),
    ('"   - Angripe (melee eller ranged)"',
     '"   - Attack (melee or ranged)"'),
    ('"   - Flee (trekke seg ut)"',
     '"   - Flee (withdraw)"'),
    ('"   - Kaste besvergelse"',
     '"   - Cast a spell"'),
    ('"   - Bruke gjenstand / First Aid"',
     '"   - Use item / First Aid"'),
    ('"   - Annet (snakke, lete, etc.)"',
     '"   - Other (talk, search, etc.)"'),
    ('"4. Gjenta til kamp er over."',
     '"4. Repeat until combat ends."'),

    ('"  Begge feiler -> ingenting skjer"',
     '"  Both fail -> nothing happens"'),

    ('"  -> alle etterfølgende angrep får"',
     '"  -> all subsequent attacks gain"'),
    ('"  kan dodge/fight back like mange ganger."',
     '"  can dodge/fight back the same number of times."'),
    ('"  Gjelder IKKE skytevåpen."',
     '"  Does NOT apply to firearms."'),

    ('        ("Skytevåpen", [', '        ("Firearms", ['),
    ('"Rull Firearms-skill. INGEN opposed roll."',
     '"Roll Firearms skill. NO opposed roll."'),
    ('"Forsvarer kan KUN dodge ved point-blank."',
     '"Defender can ONLY dodge at point-blank."'),
    ('"Ellers: bare dekke/bevege seg ut."',
     '"Otherwise: only cover/move away."'),
    ('"Rekkevidde-modifikatorer:"',
     '"Range modifiers:"'),
    ('"  Point-blank (\u2264 1/5 range): +1 bonus"',
     '"  Point-blank (\u2264 1/5 range): +1 bonus"'),
    ('"  Mellomdistanse (base range): normal"',
     '"  Medium range (base range): normal"'),
    ('"  Lang (inntil 2x base): +1 penalty"',
     '"  Long (up to 2x base): +1 penalty"'),
    ('"  Ekstrem (inntil 4x base): +2 penalty"',
     '"  Extreme (up to 4x base): +2 penalty"'),
    ('"Andre modifikatorer:"',
     '"Other modifiers:"'),
    ('"  Sikte (bruker handling): +1 bonus"',
     '"  Aim (uses action): +1 bonus"'),
    ('"  impaling weapon"',
     '"  impaling weapon"'),
    ('"  = max weapon damage + extra roll."',
     '"  = max weapon damage + extra roll."'),

    ('        ("Manøvrer", [', '        ("Manoeuvres", ['),
    ('"  Disarm: mål mister våpen"',
     '"  Disarm: target loses weapon"'),
    ('"  Kaste: dytte/kaste motstanderen"',
     '"  Throw: push/throw the opponent"'),
    ('"Krever: vinn opposed Fighting-sjekk."',
     '"Requires: win opposed Fighting check."'),
    ('"Build-differanse kan gi bonus/penalty:"',
     '"Build difference may give bonus/penalty:"'),
    ('"  Angriper Build \u2265 mål + 2: +1 bonus"',
     '"  Attacker Build \u2265 target + 2: +1 bonus"'),
    ('"  Angriper Build \u2264 mål - 2: +1 penalty"',
     '"  Attacker Build \u2264 target - 2: +1 penalty"'),

    ('"Build-verdi:"',
     '"Build value:"'),

    ('        ("Skade & heling", [', '        ("Damage & Healing", ['),
    ('"SKADENIVÅER:"', '"DAMAGE LEVELS:"'),
    ('"  Minor wound: tap < halve maks HP"',
     '"  Minor wound: loss < half max HP"'),
    ('"  Major wound: tap \u2265 halve maks HP"',
     '"  Major wound: loss \u2265 half max HP"'),
    ('"MAJOR WOUND-konsekvenser:"',
     '"MAJOR WOUND consequences:"'),
    ('"  CON-sjekk eller besvime"',
     '"  CON check or fall unconscious"'),
    ('"  First Aid/Medicine within 1 round"',
     '"  First Aid/Medicine within 1 round"'),
    ('"  Må stabiliseres ellers dør"',
     '"  Must be stabilised or will die"'),
    ('"  CON-check per round"',
     '"  CON check per round"'),
    ('"  Feil = død"', '"  Failure = death"'),
    ('"HELING:"', '"HEALING:"'),
    ('"  Naturlig: 1 HP/uke (minor)"',
     '"  Natural: 1 HP/week (minor)"'),
    ('"  Major wound: 1d3 HP/uke m/pleie"',
     '"  Major wound: 1d3 HP/week with care"'),

    ('        ("Automatiske våpen", [', '        ("Automatic Weapons", ['),
    ('"Full auto: velg antall mål,"',
     '"Full auto: choose number of targets,"'),
    ('"  fordel kuler, rull for hvert mål."',
     '"  distribute bullets, roll for each target."'),
    ('"  1 bonus die per 10 kuler på målet."',
     '"  1 bonus die per 10 bullets on target."'),
    ('"  Dekker et område, alle i området"',
     '"  Covers an area, everyone in the area"'),
    ('"  må Dodge eller ta 1 treff."',
     '"  must Dodge or take 1 hit."'),

    # ── RULES section: Sanity ─────────────────────────────────────────
    ('        ("SAN-sjekk", [', '        ("SAN Check", ['),
    ('"Rull d100 \u2264 nåværende SAN."',
     '"Roll d100 \u2264 current SAN."'),
    ('"  Suksess: tap = X"',
     '"  Success: loss = X"'),
    ('"  Feil: tap = Y"',
     '"  Failure: loss = Y"'),
    ('"  Eks: \'1/1d6\' = suksess taper 1,"',
     '"  Ex: \'1/1d6\' = success loses 1,"'),
    ('"    feil taper 1d6 SAN."',
     '"    failure loses 1d6 SAN."'),
    ('"SAN fumble: automatisk maks SAN-tap."',
     '"SAN fumble: automatic maximum SAN loss."'),

    ('"TRIGGER: 5+ SAN tapt i ETT kast."',
     '"TRIGGER: 5+ SAN lost in ONE roll."'),
    ('"Keeper krever INT-sjekk:"',
     '"Keeper requires INT check:"'),
    ('"  INT suksess = investigator innser"',
     '"  INT success = investigator realises"'),
    ('"    sannheten -> MIDLERTIDIG GAL"',
     '"    the truth -> TEMPORARILY INSANE"'),
    ('"  INT feil = fortrengt minne,"',
     '"  INT failure = repressed memory,"'),
    ('"    investigator forblir ved sine fulle fem"',
     '"    investigator remains apparently sane"'),
    ('"Midlertidig insanity varer 1d10 timer."',
     '"Temporary insanity lasts 1d10 hours."'),
    ('"Etterfølges av Underlying Insanity."',
     '"Followed by Underlying Insanity."'),

    ('"Keeper velger Real-Time eller Summary."',
     '"Keeper chooses Real-Time or Summary."'),
    ('"  1: Amnesi (husker ingenting)"',
     '"  1: Amnesia (remembers nothing)"'),
    ('"  2: Psykosomatisk (blind/døv/lam)"',
     '"  2: Psychosomatic (blind/deaf/lame)"'),
    ('"  3: Vold (angrip nærmeste)"',
     '"  3: Violence (attack nearest)"'),
    ('"  5: Fysisk (kvalme/besvimelse)"',
     '"  5: Physical (nausea/fainting)"'),
    ('"  6: Flight (løp i panikk)"',
     '"  6: Flight (run in panic)"'),
    ('"  7: Hallusinasjoner"',
     '"  7: Hallucinations"'),
    ('"  8: Ekko (gjenta handlinger meningsløst)"',
     '"  8: Echo (repeat actions pointlessly)"'),
    ('"  10: Katatoni (stivner helt)"',
     '"  10: Catatonia (freezes completely)"'),

    ('        ("Summary (1d10 timer)", [', '        ("Summary (1d10 hours)", ['),
    ('"Etter real-time bout, varig effekt:"',
     '"After real-time bout, lasting effect:"'),
    ('"  1: Amnesi for hele hendelsen"',
     '"  1: Amnesia for the entire episode"'),
    ('"  2: Tvangstanker / ritualer"',
     '"  2: Obsessive thoughts / rituals"'),
    ('"  3: Hallusinasjoner (vedvarende)"',
     '"  3: Hallucinations (persistent)"'),
    ('"  4: Irrasjonelt hat/frykt"',
     '"  4: Irrational hatred/fear"'),
    ('"  5: Phobia (spesifikk, ny eller forsterket)"',
     '"  5: Phobia (specific, new or intensified)"'),
    ('"  6: Mania (kompulsiv adferd)"',
     '"  6: Mania (compulsive behaviour)"'),
    ('"  7: Paranoia (stoler på ingen)"',
     '"  7: Paranoia (trusts no one)"'),
    ('"  8: Dissosiasjon (fjern, uvirkelig)"',
     '"  8: Dissociation (detached, unreal)"'),
    ('"  9: Spiseforstyrrelse / søvnløshet"',
     '"  9: Eating disorder / insomnia"'),
    ('"  10: Mythos-besettelse (studerer forbudt)"',
     '"  10: Mythos obsession (studies the forbidden)"'),

    ('        ("Phobiaer (utvalg)", [', '        ("Phobias (selection)", ['),
    ('"Acrophobia \u2013 høydefobi"',
     '"Acrophobia \u2013 fear of heights"'),
    ('"Agoraphobia \u2013 åpne plasser"',
     '"Agoraphobia \u2013 open spaces"'),
    ('"Arachnophobia \u2013 edderkopper"',
     '"Arachnophobia \u2013 spiders"'),
    ('"Claustrophobia \u2013 trange rom"',
     '"Claustrophobia \u2013 confined spaces"'),
    ('"Demophobia \u2013 folkemengder"',
     '"Demophobia \u2013 crowds"'),
    ('"Hemophobia \u2013 blod"',
     '"Hemophobia \u2013 blood"'),
    ('"Hydrophobia \u2013 vann"',
     '"Hydrophobia \u2013 water"'),
    ('"Mysophobia \u2013 smitte/skitt"',
     '"Mysophobia \u2013 contamination/filth"'),
    ('"Necrophobia \u2013 døde/lik"',
     '"Necrophobia \u2013 the dead/corpses"'),
    ('"Nyctophobia \u2013 mørke"',
     '"Nyctophobia \u2013 darkness"'),
    ('"Pyrophobia \u2013 ild"',
     '"Pyrophobia \u2013 fire"'),
    ('"Thalassophobia \u2013 havet/dypt vann"',
     '"Thalassophobia \u2013 the ocean/deep water"'),
    ('"Xenophobia \u2013 fremmede/ukjente"',
     '"Xenophobia \u2013 foreigners/strangers"'),
    ('"Zoophobia \u2013 dyr"',
     '"Zoophobia \u2013 animals"'),

    ('        ("Maniaer (utvalg)", [', '        ("Manias (selection)", ['),
    ('"Dipsomania \u2013 trang til alkohol"',
     '"Dipsomania \u2013 craving for alcohol"'),
    ('"Kleptomania \u2013 trang til å stjele"',
     '"Kleptomania \u2013 urge to steal"'),
    ('"Megalomania \u2013 storhetstanker"',
     '"Megalomania \u2013 delusions of grandeur"'),
    ('"Mythomania \u2013 tvangsløgner"',
     '"Mythomania \u2013 compulsive lying"'),
    ('"Necromania \u2013 besettelse med døden"',
     '"Necromania \u2013 obsession with death"'),
    ('"Pyromania \u2013 brannstifting"',
     '"Pyromania \u2013 fire-setting"'),
    ('"Thanatomania \u2013 dødslengsel"',
     '"Thanatomania \u2013 death wish"'),
    ('"Xenomania \u2013 besettelse med fremmede"',
     '"Xenomania \u2013 obsession with foreigners"'),

    ('"Trigges når investigator har tapt"',
     '"Triggered when investigator has lost"'),
    ('"  1/5 av nåværende SAN totalt."',
     '"  1/5 of current SAN in total."'),
    ('"Effekt: langvarig galskap."',
     '"Effect: prolonged madness."'),
    ('"  Spiller mister kontroll over karakter."',
     '"  Player loses control of the character."'),
    ('"  Keeper bestemmer adferd."',
     '"  Keeper determines behaviour."'),
    ('"  Varer måneder/år."',
     '"  Lasts months/years."'),
    ('"Behandling:"', '"Treatment:"'),
    ('"  Institusjonalisering"', '"  Institutionalisation"'),
    ('"  Psychoanalysis over tid"', '"  Psychoanalysis over time"'),
    ('"  +1d3 SAN per måned (maks)"',
     '"  +1d3 SAN per month (max)"'),
    ('"  Mislykket behandling: -1d6 SAN"',
     '"  Failed treatment: -1d6 SAN"'),

    ('        ("SAN-gjenoppretting", [', '        ("SAN Recovery", ['),
    ('"Psychoanalysis: +1d3 SAN (1/måned)"',
     '"Psychoanalysis: +1d3 SAN (1/month)"'),
    ('"Self-help: forbedre skill = +1d3 SAN"',
     '"Self-help: improve skill = +1d3 SAN"'),
    ('"Fullføre scenario: Keeper-belønning"',
     '"Complete scenario: Keeper reward"'),
    ('"Permanent SAN-tap kan ikke gjenopprettes"',
     '"Permanent SAN loss cannot be recovered"'),
    ('"  utover denne grensen."',
     '"  beyond this limit."'),

    # ── RULES section: Chase ──────────────────────────────────────────
    ('      ("Forfølgelse", "", [', '      ("Chase", "", ['),
    ('        ("Oppsett", [', '        ("Setup", ['),
    ('"1. Type: fot eller kjøretøy."',
     '"1. Type: on foot or vehicle."'),
    ('"2. Antall locations: 5\u201310 (Keeper velger)."',
     '"2. Number of locations: 5\u201310 (Keeper chooses)."'),
    ('"3. Deltakere:"', '"3. Participants:"'),
    ('"   Fot: MOV basert på DEX, STR, SIZ."',
     '"   On foot: MOV based on DEX, STR, SIZ."'),
    ('"   Bil: speed-rating."',
     '"   Vehicle: speed rating."'),
    ('"4. Speed Roll (CON-sjekk):"',
     '"4. Speed Roll (CON check):"'),
    ('"   Extreme suksess: +1 MOV for chasen"',
     '"   Extreme success: +1 MOV for the chase"'),
    ('"   Suksess: ingen endring"',
     '"   Success: no change"'),
    ('"   Feil: -1 MOV for chasen"',
     '"   Failure: -1 MOV for the chase"'),
    ('"   (kjøretøy: Drive Auto i stedet)"',
     '"   (vehicle: Drive Auto instead)"'),
    ('"5. Sammenlign MOV: høyere MOV flykter"',
     '"5. Compare MOV: higher MOV escapes"'),
    ('"   umiddelbart. Ellers -> full chase."',
     '"   immediately. Otherwise -> full chase."'),
    ('"6. Sett startposisjoner på tracken."',
     '"6. Set starting positions on the track."'),
    ('"7. Plasser barrierer/farer på locations."',
     '"7. Place barriers/hazards on locations."'),
    ('"MOV (Movement Rate):"', '"MOV (Movement Rate):"'),
    ('"  Hvis DEX & STR begge > SIZ: MOV 9"',
     '"  If DEX & STR both > SIZ: MOV 9"'),
    ('"  Hvis enten DEX eller STR > SIZ: MOV 8"',
     '"  If either DEX or STR > SIZ: MOV 8"'),
    ('"  Hvis begge \u2264 SIZ: MOV 7"',
     '"  If both \u2264 SIZ: MOV 7"'),
    ('"  Alder 40\u201349: MOV -1"',
     '"  Age 40\u201349: MOV -1"'),
    ('"  Alder 50\u201359: MOV -2 (etc.)"',
     '"  Age 50\u201359: MOV -2 (etc.)"'),

    ('        ("Bevegelse & handlinger", [', '        ("Movement & Actions", ['),
    ('"Runder i DEX-rekkefølge (høy først)."',
     '"Rounds in DEX order (highest first)."'),
    ('"  - Bevege seg (MOV locations)"',
     '"  - Move (MOV locations)"'),
    ('"  - Utføre 1 handling:"',
     '"  - Perform 1 action:"'),
    ('"    Speed: CON-sjekk for +1 location"',
     '"    Speed: CON check for +1 location"'),
    ('"    Angrep: Fighting/Firearms"',
     '"    Attack: Fighting/Firearms"'),
    ('"    Barriere: skill-sjekk for å passere"',
     '"    Barrier: skill check to pass"'),
    ('"    Hinder: lag barriere for forfølger"',
     '"    Hinder: create barrier for pursuer"'),

    ('        ("Barrierer", [', '        ("Barriers", ['),
    ('"Keeper plasserer barrierer på locations."',
     '"Keeper places barriers on locations."'),
    ('"Skill-sjekk for å passere:"',
     '"Skill check to pass:"'),
    ('"  Hopp over gjerde: Jump / Climb"',
     '"  Jump fence: Jump / Climb"'),
    ('"  Trang passasje: DEX / Dodge"',
     '"  Narrow passage: DEX / Dodge"'),
    ('"  Folkemengde: STR / Charm / Intimidate"',
     '"  Crowd: STR / Charm / Intimidate"'),
    ('"  Gjørme/glatt: DEX / Luck"',
     '"  Mud/slippery: DEX / Luck"'),
    ('"  Låst dør: Locksmith / STR"',
     '"  Locked door: Locksmith / STR"'),
    ('"  Trafikkert gate: Drive Auto / DEX"',
     '"  Busy street: Drive Auto / DEX"'),
    ('"Feil: mist 1 location bevegelse."',
     '"Failure: lose 1 location of movement."'),
    ('"Fumble: fall, damage, stuck, etc."',
     '"Fumble: fall, damage, stuck, etc."'),

    ('        ("Seier & tap", [', '        ("Victory & Defeat", ['),
    ('"FLUKT lykkes når:"',
     '"ESCAPE succeeds when:"'),
    ('"  Avstand mellom = antall locations + 1"',
     '"  Distance between = number of locations + 1"'),
    ('"  (forfølger kan ikke se målet)."',
     '"  (pursuer cannot see the target)."'),
    ('"FANGET når:"',
     '"CAUGHT when:"'),
    ('"  Forfølger er på SAMME location."',
     '"  Pursuer is at the SAME location."'),
    ('"  Kamp eller interaksjon kan begynne."',
     '"  Combat or interaction may begin."'),
    ('"UTMATTELSE:"',
     '"EXHAUSTION:"'),
    ('"  Feil: MOV reduseres med 1."',
     '"  Failure: MOV reduced by 1."'),
    ('"  MOV 0: kan ikke bevege seg."',
     '"  MOV 0: cannot move."'),

    # ── RULES section: Magic ──────────────────────────────────────────
    ('      ("Magi & Tomer", "", [', '      ("Magic & Tomes", "", ['),
    ('        ("Besvergelse", [', '        ("Spells", ['),
    ('"Kostnader varierer per spell:"',
     '"Costs vary per spell:"'),
    ('"  Magic Points (MP): vanligst"',
     '"  Magic Points (MP): most common"'),
    ('"  SAN: nesten alltid"',
     '"  SAN: almost always"'),
    ('"  HP: noen kraftige spells"',
     '"  HP: some powerful spells"'),
    ('"  POW: permanent offer (sjeldent)"',
     '"  POW: permanent sacrifice (rare)"'),
    ('"Noen krever komponenter/ritualer."',
     '"Some require components/rituals."'),
    ('"MP regenereres: 1 per 2 timer hvile."',
     '"MP regenerates: 1 per 2 hours of rest."'),
    ('"MP = 0: bevisstløs i 1d8 timer."',
     '"MP = 0: unconscious for 1d8 hours."'),
    ('"POW-offer: permanent, gjenopprettes IKKE."',
     '"POW sacrifice: permanent, CANNOT be restored."'),

    ('        ("Mythos-tomer", [', '        ("Mythos Tomes", ['),
    ('"Lesing av Mythos-tome:"',
     '"Reading a Mythos tome:"'),
    ('"  Initial reading: uker til måneder"',
     '"  Initial reading: weeks to months"'),
    ('"  Full study: måneder til år"',
     '"  Full study: months to years"'),
    ('"Belønning: +Cthulhu Mythos skill."',
     '"Reward: +Cthulhu Mythos skill."'),
    ('"Kostnad: SAN-tap (varierer per tome)."',
     '"Cost: SAN loss (varies per tome)."'),
    ('"Kan også lære spells fra tomen."',
     '"Can also learn spells from the tome."'),

    ('        ("Mythos-vesener (SAN)", [', '        ("Mythos Creatures (SAN)", ['),
    ('"Vesen: suksess / feil SAN-tap"',
     '"Creature: success / failure SAN loss"'),

    # ── RULES section: Pulp Cthulhu ───────────────────────────────────
    ('      ("Pulp Cthulhu", "", [', '      ("Pulp Cthulhu", "", ['),
    ('        ("Pulp-regler", [', '        ("Pulp Rules", ['),
    ('"Helter er TØFFERE enn standard CoC."',
     '"Heroes are TOUGHER than standard CoC."'),
    ('"  Effektivt DOBBEL HP."',
     '"  Effectively DOUBLE HP."'),
    ('"  Valgfritt lavnivå: (CON+SIZ)/10"',
     '"  Optional low-powered: (CON+SIZ)/10"'),
    ('"Luck: 2d6+6 x 5 (høyere enn standard)"',
     '"Luck: 2d6+6 x 5 (higher than standard)"'),
    ('"  Regenerer 2d10 Luck per sesjon."',
     '"  Regenerate 2d10 Luck per session."'),
    ('"Pulp Talents: 2 stk (standard)."',
     '"Pulp Talents: 2 (standard)."'),
    ('"  Lavnivå pulp: 1 talent"',
     '"  Low-powered pulp: 1 talent"'),
    ('"  Høynivå pulp: 3 talents"',
     '"  High-powered pulp: 3 talents"'),
    ('"Kampkast kan IKKE pushes (som standard)."',
     '"Combat rolls CANNOT be pushed (as standard)."'),
    ('"Spending Luck: kan også brukes til:"',
     '"Spending Luck: can also be used to:"'),
    ('"  - Unngå dying (5 Luck = stabiliser)"',
     '"  - Avoid dying (5 Luck = stabilise)"'),

    ('        ("Arketyper", [', '        ("Archetypes", ['),
    ('"Gir bonuser og Pulp Talents."',
     '"Grants bonuses and Pulp Talents."'),
    ('"  Adventurer: allsidig eventyrer"',
     '"  Adventurer: versatile adventurer"'),
    ('"  Beefcake: fysisk sterk, ekstra HP"',
     '"  Beefcake: physically strong, extra HP"'),
    ('"  Bon Vivant: sjarmerende, sosialt dyktig"',
     '"  Bon Vivant: charming, socially skilled"'),
    ('"  Cold Blooded: hensynsløs, presist"',
     '"  Cold Blooded: ruthless, precise"'),
    ('"  Dreamer: kreativ, Mythos-sensitiv"',
     '"  Dreamer: creative, Mythos-sensitive"'),
    ('"  Egghead: intellektuell, kunnskapsrik"',
     '"  Egghead: intellectual, knowledgeable"'),
    ('"  Explorer: utforsker, overlevelse"',
     '"  Explorer: explorer, survival"'),
    ('"  Femme/Homme Fatale: forførende"',
     '"  Femme/Homme Fatale: seductive"'),
    ('"  Grease Monkey: mekaniker, oppfinnsom"',
     '"  Grease Monkey: mechanic, inventive"'),
    ('"  Hard Boiled: tøff, utholdende"',
     '"  Hard Boiled: tough, resilient"'),
    ('"  Harlequin: entertainer, distraherende"',
     '"  Harlequin: entertainer, distracting"'),
    ('"  Hunter: jeger, naturkyndig"',
     '"  Hunter: hunter, nature-savvy"'),
    ('"  Mystic: spirituell, spådomsevne"',
     '"  Mystic: spiritual, prophetic"'),
    ('"  Outsider: ensom, selvlært"',
     '"  Outsider: lone, self-taught"'),
    ('"  Reckless: våghals, risikotaker"',
     '"  Reckless: daredevil, risk-taker"'),
    ('"  Sidekick: lojal, støttende"',
     '"  Sidekick: loyal, supportive"'),
    ('"  Swashbuckler: akrobatisk fighter"',
     '"  Swashbuckler: acrobatic fighter"'),
    ('"  Thrill Seeker: adrenalinjansen"',
     '"  Thrill Seeker: adrenaline junkie"'),
    ('"  Two-Fisted: nevekamp-spesialist"',
     '"  Two-Fisted: brawling specialist"'),

    ('        ("Pulp Talents (utvalg)", [', '        ("Pulp Talents (selection)", ['),
    ('"  Quick Healer: dobbel heling"',
     '"  Quick Healer: double healing"'),
    ('"  Tough Guy: +1d6 ekstra HP"',
     '"  Tough Guy: +1d6 extra HP"'),
    ('"  Gadget: lag improvisert gjenstand"',
     '"  Gadget: create improvised item"'),
    ('"  Lucky: +1d10 ekstra Luck-regen"',
     '"  Lucky: +1d10 extra Luck regen"'),
    ('"KAMP:"', '"COMBAT:"'),
    ('"  Outmaneuver: +1 bonus på manøvrer"',
     '"  Outmaneuver: +1 bonus on manoeuvres"'),

    # ── RULES section: Tables ─────────────────────────────────────────
    ('      ("Tabeller", "", [', '      ("Tables", "", ['),
    ('        ("Våpentabell \u2013 melee", [',
     '        ("Weapon Table \u2013 melee", ['),
    ('"  Unarmed (knytneve): 1d3+DB / 1"',
     '"  Unarmed (fist): 1d3+DB / 1"'),
    ('"  Kniv (liten): 1d4+DB / 1"',
     '"  Knife (small): 1d4+DB / 1"'),
    ('"  Kniv (stor): 1d6+DB / 1"',
     '"  Knife (large): 1d6+DB / 1"'),
    ('"  Klubbe/kølle: 1d8+DB / 1"',
     '"  Club/mace: 1d8+DB / 1"'),
    ('"  Sverd/sabel: 1d8+DB / 1"',
     '"  Sword/sabre: 1d8+DB / 1"'),
    ('"  Øks (stor): 1d8+2+DB / 1"',
     '"  Axe (large): 1d8+2+DB / 1"'),
    ('"  Spyd: 1d8+1+DB / 1"',
     '"  Spear: 1d8+1+DB / 1"'),
    ('"  Motorsag: 2d8 / 1"',
     '"  Chainsaw: 2d8 / 1"'),

    ('        ("Våpentabell \u2013 skytevåpen", [',
     '        ("Weapon Table \u2013 firearms", ['),

    ('        ("SAN-tap oversikt", [', '        ("SAN Loss Overview", ['),
    ('"HENDELSE: suksess / feil"',
     '"EVENT: success / failure"'),
    ('"  Se et lik: 0/1d3"',
     '"  See a corpse: 0/1d3"'),
    ('"  Se en venn dø: 0/1d4"',
     '"  See a friend die: 0/1d4"'),
    ('"  Se noe uforklarlig: 0/1d2"',
     '"  See something inexplicable: 0/1d2"'),
    ('"  Se et grusomt drap: 1/1d4+1"',
     '"  See a gruesome murder: 1/1d4+1"'),
    ('"  Se massedrap: 1d3/1d6+1"',
     '"  See mass murder: 1d3/1d6+1"'),
    ('"  Finne en grusomhet: 0/1d3"',
     '"  Find an atrocity: 0/1d3"'),
    ('"  Oppdage Mythos-bevis: 0/1d2"',
     '"  Discover Mythos evidence: 0/1d2"'),
    ('"  Lese Mythos-tome: 1/1d4"',
     '"  Read Mythos tome: 1/1d4"'),
    ('"  Se Mythos-ritual: 1/1d6"',
     '"  See Mythos ritual: 1/1d6"'),
    ('"  Bli utsatt for besvergelse: 1/1d6"',
     '"  Subjected to a spell: 1/1d6"'),

    ('        ("Alderseffekter", [', '        ("Age Effects", ['),
    ('"Alder påvirker stats ved opprettelse:"',
     '"Age affects stats at creation:"'),
    ('"  15\u201319: -5 SIZ/STR, -5 EDU,"',
     '"  15\u201319: -5 SIZ/STR, -5 EDU,"'),
    ('"    Luck: rull 2x, bruk best"',
     '"    Luck: roll 2x, use best"'),
    ('"  20\u201339: EDU-forbedring: +1"',
     '"  20\u201339: EDU improvement: +1"'),
    ('"  40\u201349: EDU +2, -5 fritt STR/CON/DEX,"',
     '"  40\u201349: EDU +2, -5 free STR/CON/DEX,"'),
    ('"  50\u201359: EDU +3, -10 fritt STR/CON/DEX,"',
     '"  50\u201359: EDU +3, -10 free STR/CON/DEX,"'),
    ('"  60\u201369: EDU +4, -20 fritt STR/CON/DEX,"',
     '"  60\u201369: EDU +4, -20 free STR/CON/DEX,"'),
    ('"  70\u201379: EDU +4, -40 fritt STR/CON/DEX,"',
     '"  70\u201379: EDU +4, -40 free STR/CON/DEX,"'),
    ('"  80\u201389: EDU +4, -80 fritt STR/CON/DEX,"',
     '"  80\u201389: EDU +4, -80 free STR/CON/DEX,"'),

    ('"Credit Rating = formue/sosial status:"',
     '"Credit Rating = wealth/social status:"'),
    ('"  0: fattig, hjemløs"',
     '"  0: poor, homeless"'),
    ('"  1\u20139: fattig, kun nødvendig"',
     '"  1\u20139: poor, necessities only"'),
    ('"  10\u201349: gjennomsnittlig"',
     '"  10\u201349: average"'),
    ('"  50\u201389: velstående"',
     '"  50\u201389: wealthy"'),
    ('"  90\u201398: rik"',
     '"  90\u201398: rich"'),
    ('"  99: enormt rik"',
     '"  99: extremely rich"'),

    # ── Android helper functions ──────────────────────────────────────
    ('    def has_all_files_access():\n'
     '        """Sjekk om appen har MANAGE_EXTERNAL_STORAGE (Android 11+).\n'
     '        Returnerer True hvis ja, False hvis nei, None hvis ikke\n'
     '        Android eller ikke relevant."""',
     '    def has_all_files_access():\n'
     '        """Check whether the app has MANAGE_EXTERNAL_STORAGE (Android 11+).\n'
     '        Returns True if yes, False if no, None if not\n'
     '        Android or not relevant."""'),
    ('            # Kun relevant på Android 11 (API 30) og nyere',
     '            # Only relevant on Android 11 (API 30) and newer'),
    ('            log(f"has_all_files_access sjekk feilet: {e}")',
     '            log(f"has_all_files_access check failed: {e}")'),

    ('    def request_all_files_access():\n'
     '        """Åpne Android-innstillinger hvor brukeren kan gi appen\n'
     '        \'All files access\'. Krever Android 11+ og at appen\n'
     '        deklarerer MANAGE_EXTERNAL_STORAGE i manifestet."""',
     '    def request_all_files_access():\n'
     '        """Open Android settings where the user can grant the app\n'
     '        \'All files access\'. Requires Android 11+ and that the app\n'
     '        declares MANAGE_EXTERNAL_STORAGE in the manifest."""'),

    # ── FilePicker class ──────────────────────────────────────────────
    ('    class FilePicker:\n'
     '        """Android Storage Access Framework-filvelger.\n'
     '\n'
     '        Åpner systemets filvelger og leser valgt fil via URI —\n'
     '        krever ingen storage-tillatelser, fungerer på alle\n'
     '        Android-versjoner, og brukeren kan velge fra hvor som\n'
     '        helst (Documents, Downloads, Google Drive, osv).\n'
     '        """',
     '    class FilePicker:\n'
     '        """Android Storage Access Framework file picker.\n'
     '\n'
     '        Opens the system file picker and reads the selected file via URI —\n'
     '        requires no storage permissions, works on all\n'
     '        Android versions, and the user can choose from anywhere\n'
     '        (Documents, Downloads, Google Drive, etc).\n'
     '        """'),
    ('            """Koble på Android activity-result-listener."""',
     '            """Attach to Android activity-result listener."""'),
    ('            """Åpne filvelger. callback(ok, text_or_err) kalles\n'
     '            når brukeren har valgt (eller avbrutt)."""',
     '            """Open file picker. callback(ok, text_or_err) is called\n'
     '            when the user has selected (or cancelled)."""'),
    ('            """Åpne filvelger og returner URI/meta for valgt fil."""',
     '            """Open file picker and return URI/meta for the selected file."""'),
    ('            """Intern åpning av Android filvelger."""',
     '            """Internal opening of Android file picker."""'),
    ('                callback(False, "Filvelger kun tilgjengelig på Android")',
     '                callback(False, "File picker only available on Android")'),
    ('                callback(False, f"Kunne ikke åpne filvelger: {e}")',
     '                callback(False, f"Could not open file picker: {e}")'),
    ('            """Mottatt resultat fra filvelgeren."""',
     '            """Received result from the file picker."""'),
    ('                    lambda dt: cb(False, "Avbrutt"), 0)',
     '                    lambda dt: cb(False, "Cancelled"), 0)'),
    ('                        lambda dt: cb(False, "Ingen fil valgt"), 0)',
     '                        lambda dt: cb(False, "No file selected"), 0)'),
    ('                # Åpne input stream via content resolver',
     '                # Open input stream via content resolver'),
    ('                # Les innhold (byte-vis gjennom InputStreamReader)',
     '                # Read content (byte-by-byte through InputStreamReader)'),
    ('                log(f"FilePicker bundet til Android activity")',
     '                log(f"FilePicker bound to Android activity")'),
    ('                log(f"FilePicker bind-feil: {e}")',
     '                log(f"FilePicker bind error: {e}")'),
    ('                log(f"FilePicker persist-uri feil: {e}")',
     '                log(f"FilePicker persist-uri error: {e}")'),
    ('                log(f"FilePicker navn-feil: {e}")',
     '                log(f"FilePicker name error: {e}")'),

    # ── build() method ────────────────────────────────────────────────
    ('            # Skroll innholdet opp så tastaturet ikke dekker aktivt input',
     '            # Scroll content up so keyboard does not cover the active input'),
    ('            # Våpen: favoritt-fil går i app-private storage (alltid skrivbar)',
     '            # Weapons: favourites file goes in app-private storage (always writable)'),
    ('            # Scenario: også app-private (unngår scoped storage-feil\n'
     '            # ved lesing av .json i /sdcard/Documents/ på Android 13+)',
     '            # Scenario: also app-private (avoids scoped storage errors\n'
     '            # when reading .json in /sdcard/Documents/ on Android 13+)'),
    ('            # FloatLayout som rot – lar oss legge splash oppå',
     '            # FloatLayout as root – lets us place splash on top'),
    ('            # Et samlet panel for hovedfaner + sub-faner. Når man bytter\n'
     '            # til en fane med sub-faner (Lyd/Kamp/Verktøy) utvides\n'
     '            # panelet nedover for å gi plass til sub-faner. Når man\n'
     '            # bytter til en fane uten sub-faner, kollapser det igjen.\n'
     '            # NB: spacing starter på 0 og animeres til dp(4) når panelet\n'
     '            # utvides — ellers ville den 4dp mellomraden tatt plass selv\n'
     '            # når sub-raden er tom, og dyttet hovedfanene ut av panelet.',
     '            # A single panel for main tabs + sub-tabs. When switching\n'
     '            # to a tab with sub-tabs (Sound/Combat/Tools) the panel\n'
     '            # expands downward to make room for sub-tabs. When\n'
     '            # switching to a tab without sub-tabs, it collapses again.\n'
     '            # NB: spacing starts at 0 and animates to dp(4) when the panel\n'
     '            # expands — otherwise the 4dp gap row would take space even\n'
     '            # when the sub-row is empty, pushing main tabs out of the panel.'),
    ("                ('tool', 'Verktøy'),", "                ('tool', 'Tools'),"),
    ('            # Sub-fane-rad (kollapset i utgangspunktet, fylles dynamisk\n'
     '            # av _update_subtabs når aktiv tab har sub-faner).',
     '            # Sub-tab row (collapsed by default, filled dynamically\n'
     '            # by _update_subtabs when the active tab has sub-tabs).'),

    # ── tab labels ────────────────────────────────────────────────────
    ("                ('img', 'Bilder'),", "                ('img', 'Images'),"),
    ("                ('snd', 'Lyd'),", "                ('snd', 'Sound'),"),
    ("                ('cmb', 'Kamp'),", "                ('cmb', 'Combat'),"),
    ("                ('rules', 'Regler'),", "                ('rules', 'Rules'),"),
    # Also handle any remaining standalone tab string literals
    ("text='Verktøy'", "text='Tools'"),
    ("text='Musikk'", "text='Music'"),
    ("text='Initiativ'", "text='Initiative'"),
    ("text='Kart'", "text='Map'"),
    ("text='Karakterer'", "text='Characters'"),
    ("text='Galskap'", "text='Madness'"),
    ("text='Våpen'", "text='Weapons'"),

    # ── _init() / status ──────────────────────────────────────────────
    ("Cast: {'Ja' if CAST_AVAILABLE else 'Nei'}\")",
     "Cast: {'Yes' if CAST_AVAILABLE else 'No'}\")"),

    # ── _weap_do_load ─────────────────────────────────────────────────
    ('            """Last våpendata. Prøv ekstern først (brukerens egen),\n'
     '            fall tilbake til bundlet versjon."""',
     '            """Load weapon data. Try external first (user\'s own),\n'
     '            fall back to bundled version."""'),
    ('            # Forsøk 1: ekstern fil i /sdcard/Documents/EldritchPortal/',
     '            # Attempt 1: external file in /sdcard/Documents/EldritchPortal/'),
    ('                        log(f"_weap_do_load: ekstern OK, {n} våpen")',
     '                        log(f"_weap_do_load: external OK, {n} weapons")'),
    ('                    log("_weap_do_load: ekstern finnes men ingen tilgang, bruker bundlet")',
     '                    log("_weap_do_load: external found but no access, using bundled")'),
    ('                    log(f"_weap_do_load: ekstern feil ({e}), bruker bundlet")',
     '                    log(f"_weap_do_load: external error ({e}), using bundled")'),
    ('            # Forsøk 2: bundlet fil (pakket inn i APK)',
     '            # Attempt 2: bundled file (packed into APK)'),
    ('                    log(f"_weap_do_load: bundlet OK, {n} våpen")',
     '                    log(f"_weap_do_load: bundled OK, {n} weapons")'),
    ('            # Ingen kilder fungerte',
     '            # No sources worked'),
    ('            err = (f"Fant ingen weapons.json.\\n"',
     '            err = (f"No weapons.json found.\\n"'),
    ('                   f"Bundlet sti: {BUNDLED_WEAPONS}\\n"',
     '                   f"Bundled path: {BUNDLED_WEAPONS}\\n"'),
    ('                   f"Ekstern sti: {EXTERNAL_WEAPONS}")',
     '                   f"External path: {EXTERNAL_WEAPONS}")'),

    # ── _tab method ───────────────────────────────────────────────────
    ('            # Animer sub-fane-panelet inn/ut samtidig som innholdet bytter',
     '            # Animate the sub-tab panel in/out at the same time as content switches'),
    ('            # Første render: ingen fade-out',
     '            # First render: no fade-out'),
    ('            # Fade ut nåværende, deretter swap inn nytt',
     '            # Fade out current, then swap in new'),

    # ── _update_subtabs ───────────────────────────────────────────────
    ('        def _update_subtabs(self, k):\n'
     '            """Animer sub-fane-rad inn/ut basert på aktiv hovedfane.\n'
     '\n'
     '            - Faner med sub-faner (snd/cmb/tool): panelet utvides\n'
     '              nedover og sub-fanene fades inn.\n'
     '            - Faner uten sub-faner (img/rules/cast): panelet kollapser.\n'
     '\n'
     '            spacing animeres sammen med høyden (0 ↔ dp(4)) slik at\n'
     '            geometrien stemmer i begge tilstander. Uten dette ville den\n'
     '            4dp mellomraden tatt plass i kollapset tilstand og dyttet\n'
     '            hovedfanene ut av panelet.\n'
     '            """',
     '        def _update_subtabs(self, k):\n'
     '            """Animate the sub-tab row in/out based on the active main tab.\n'
     '\n'
     '            - Tabs with sub-tabs (snd/cmb/tool): panel expands\n'
     '              downward and sub-tabs fade in.\n'
     '            - Tabs without sub-tabs (img/rules/cast): panel collapses.\n'
     '\n'
     '            spacing is animated together with height (0 ↔ dp(4)) so that\n'
     '            the geometry is correct in both states. Without this the\n'
     '            4dp gap row would take space in the collapsed state and push\n'
     '            main tabs out of the panel.\n'
     '            """'),
    ('                # Bygg sub-faner først',
     '                # Build sub-tabs first'),
    ('                # Animer åpning + fade-inn (alle bruker samme varighet/easing\n'
     '                # så geometrien holder seg konsistent gjennom animasjonen)',
     '                # Animate opening + fade-in (all use the same duration/easing\n'
     '                # so the geometry stays consistent throughout the animation)'),
    ('                # så de ikke flimrer mens raden krymper.',
     '                # so they do not flicker while the row shrinks.'),

    # ── _build_snd_subtabs ────────────────────────────────────────────
    ('            """Bygg Musikk/Ambient-toggle-knapper inn i sub-fane-raden."""',
     '            """Build Music/Ambient toggle buttons into the sub-tab row."""'),

    # ── _build_cmb_subtabs ────────────────────────────────────────────
    ('            """Bygg Initiativ/Kart-toggle-knapper inn i sub-fane-raden."""',
     '            """Build Initiative/Map toggle buttons into the sub-tab row."""'),

    # ── _build_tool_subtabs ───────────────────────────────────────────
    ('            """Bygg Karakter/Våpen/Scenario/Galskap-faner inn i sub-fane-raden."""',
     '            """Build Characters/Weapons/Scenario/Madness tabs into the sub-tab row."""'),

    # ── Images tab ────────────────────────────────────────────────────
    ("                        mklbl(\"Mappen finnes ikke ennå.\\n\"\n"
     "                              \"Start appen på nytt etter å ha\\n\"\n"
     "                              \"godtatt tillatelser.\",",
     "                        mklbl(\"Folder not found yet.\\n\"\n"
     "                              \"Restart the app after\\n\"\n"
     "                              \"accepting permissions.\","),
    ('                self.img_lbl.text = "Mappe ikke funnet"',
     '                self.img_lbl.text = "Folder not found"'),
    ('                self.img_lbl.text = f"{len(dirs)} mapper, {len(imgs)} bilder"',
     '                self.img_lbl.text = f"{len(dirs)} folders, {len(imgs)} images"'),
    ("                        mklbl(\"Ingen bilder funnet.\\n\\n\"\n"
     "                              \"Legg bilder i:\\n\"\n"
     "                              \"Dokumenter/EldritchPortal/images/\\n\\n\"\n"
     "                              \"Tips: lag undermapper for\\n\"\n"
     "                              \"å organisere etter scenario,\\n\"\n"
     "                              \"f.eks. images/Slow Boat/\\n\\n\"\n"
     "                              \"Støttede formater:\\n\"\n"
     "                              \".png  .jpg  .jpeg  .webp\",",
     "                        mklbl(\"No images found.\\n\\n\"\n"
     "                              \"Place images in:\\n\"\n"
     "                              \"Documents/EldritchPortal/images/\\n\\n\"\n"
     "                              \"Tip: create subfolders to\\n\"\n"
     "                              \"organise by scenario,\\n\"\n"
     "                              \"e.g. images/Slow Boat/\\n\\n\"\n"
     "                              \"Supported formats:\\n\"\n"
     "                              \".png  .jpg  .jpeg  .webp\","),

    # ── Combat tab ────────────────────────────────────────────────────
    ('        def _mk_combat(self):\n'
     '            """Kamp-fane med sub-tabs: Initiativ og Kart.\n'
     '\n'
     '            Sub-fanene bygges nå i det globale tab-panelet av\n'
     '            _build_cmb_subtabs(). Denne metoden returnerer kun\n'
     '            innholds-området.\n'
     '            """',
     '        def _mk_combat(self):\n'
     '            """Combat tab with sub-tabs: Initiative and Map.\n'
     '\n'
     '            Sub-tabs are now built in the global tab panel by\n'
     '            _build_cmb_subtabs(). This method only returns\n'
     '            the content area.\n'
     '            """'),
    ('            # Innholds-område — fungerer som "tool_area" for init-tracker\n'
     '            # og som vert for kart-visningen.',
     '            # Content area — acts as "tool_area" for init-tracker\n'
     '            # and as host for the map view.'),

    ('        def _mk_cmb_map(self):\n'
     '            """Kart-sub-tab: åpne battlemap eller vis info om tom liste."""',
     '        def _mk_cmb_map(self):\n'
     '            """Map sub-tab: open battlemap or show info for empty list."""'),
    ('"for å bruke kartet."',
     '"to use the map."'),
    ('"KLAR FOR KART"', '"READY FOR MAP"'),
    ('"Nåværende tur: {act_name}"', '"Current turn: {act_name}"'),
    ('                    f"Nåværende tur: {act_name}",',
     '                    f"Current turn: {act_name}",'),
    ('"Gå til Initiativ-fanen og trykk \'Fullfør\' "',
     '"Go to the Initiative tab and press \'Finish\' "'),
    ('p.add_widget(mkbtn("Åpne kart (fullskjerm)",',
     'p.add_widget(mkbtn("Open map (full screen)",'),
    ('"Kartet åpnes som overlay i full skjermbredde. "',
     '"The map opens as an overlay at full screen width. "'),
    ('"n_fiende = sum(1 for e in self._init_list"', None),  # skip this
    ('                    f"{n_fiende} fiende(r)"',
     '                    f"{n_fiende} enemy/enemies"'),

    # ── Sound tab ─────────────────────────────────────────────────────
    ('        def _mk_sound(self):\n'
     '            """Lyd-fane med toggle mellom Musikk og Ambient.\n'
     '\n'
     '            Sub-fanene bygges nå i det globale tab-panelet av\n'
     '            _build_snd_subtabs(). Denne metoden returnerer kun\n'
     '            innholds-området.\n'
     '            """',
     '        def _mk_sound(self):\n'
     '            """Sound tab with toggle between Music and Ambient.\n'
     '\n'
     '            Sub-tabs are now built in the global tab panel by\n'
     '            _build_snd_subtabs(). This method only returns\n'
     '            the content area.\n'
     '            """'),

    # music folder not found
    ("                        mklbl(\"Musikkmappen finnes ikke ennå.\\n\"\n"
     "                              \"Start appen på nytt etter å ha\\n\"\n"
     "                              \"godtatt tillatelser.\\n\"\n"
     "                              \"Støttede formater:\\n\"",
     "                        mklbl(\"Music folder not found yet.\\n\"\n"
     "                              \"Restart the app after\\n\"\n"
     "                              \"accepting permissions.\\n\"\n"
     "                              \"Supported formats:\\n\""),

    # ambient section
    ('p.add_widget(mklbl("Egen ambient – sømløs loop", color=GDIM,',
     'p.add_widget(mklbl("Custom ambient – seamless loop", color=GDIM,'),
    ('"Støtter .mp3, .ogg, .wav og .flac via Android-filvelgeren."',
     '"Supports .mp3, .ogg, .wav and .flac via the Android file picker."'),
    ('                self.amb_lbl.text = "Egen ambient-opplasting støttes på Android"',
     '                self.amb_lbl.text = "Custom ambient upload supported on Android"'),
    ('            self.amb_lbl.text = "Åpner filvelger for ambientlyd..."',
     '            self.amb_lbl.text = "Opening file picker for ambient sound..."'),
    ('            self.amb_lbl.text = "Trykk for å starte sømløs loop"',
     '            self.amb_lbl.text = "Tap to start seamless loop"'),

    # folder tree
    ('            # Overlay-container (usynlig til innhold åpnes)',
     '            # Overlay container (invisible until content opens)'),
    ('            """Bygg mappetreet med åpne/lukkede mapper."""',
     '            """Build the folder tree with open/closed folders."""'),
    ('            """Åpne/lukke en mappe."""',
     '            """Open/close a folder."""'),
    ('            # Legg overlay over hele content-området',
     '            # Place overlay over the entire content area'),

    # ── Tools / Characters tab ────────────────────────────────────────
    ('        # ---------- KARAKTERER / VERKTØY ----------',
     '        # ---------- CHARACTERS / TOOLS ----------'),
    ('            """Verktøy-fane med sub-tabs: Karakterer, Våpen, Scenario, Galskap.\n'
     '            Sub-fanene bygges nå i det globale tab-panelet av\n'
     '            _build_tool_subtabs(). Denne metoden returnerer kun\n'
     '            handlings-raden + innholdsområdet.',
     '            """Tools tab with sub-tabs: Characters, Weapons, Scenario, Madness.\n'
     '            Sub-tabs are now built in the global tab panel by\n'
     '            _build_tool_subtabs(). This method only returns\n'
     '            the action row + content area.'),
    ('            # Når vi er i Verktøy-fanen skal init-tracker (hvis den kalles)',
     '            # When in the Tools tab the init-tracker (if called)'),
    ('            """Bytt mellom karakterer, våpen, scenario og galskap."""',
     '            """Switch between characters, weapons, scenario and madness."""'),

    # Madness roller
    ('            # Resultat-område (fylles av _roll_madness)',
     '            # Result area (filled by _roll_madness)'),
    ('"Trykk på en knapp for å trille…"',
     '"Press a button to roll…"'),
    ('            """Trill 1d10 på riktig tabell og vis resultatet."""',
     '            """Roll 1d10 on the correct table and display the result."""'),
    ('            again = mkbtn(f"Trill {label} på nytt",',
     '            again = mkbtn(f"Roll {label} again",'),

    # Characters list
    ('                g.add_widget(mklbl("Ingen karakterer ennå.\\nTrykk \'+ Ny\' for å lage en.",',
     '                g.add_widget(mklbl("No characters yet.\\nPress \'+ New\' to create one.",'),
    ('            # Litt ekstra plass under så tastaturet kan skroll opp',
     '            # Extra space below so keyboard can scroll up'),

    # Character file picker
    ('            """Åpne Android filvelger for karakterimport."""',
     '            """Open Android file picker for character import."""'),
    ('                    "Filvelger er kun tilgjengelig på Android."',
     '                    "File picker is only available on Android."'),
    ('                "Åpner filvelger..."',
     '                "Opening file picker..."'),
    ('            """Callback når filvelgeren er ferdig."""',
     '            """Callback when the file picker is done."""'),
    ('"Fila må inneholde enten en liste [...] eller et "',
     '"The file must contain either a list [...] or an "'),
    ('"Fila inneholdt ingen gyldige karakteroppføringer "',
     '"The file contained no valid character entries "'),
    ('            """Normaliser en rå karakter-dict til appens interne format."""',
     '            """Normalise a raw character dict to the app\'s internal format."""'),
    ('            """Vis forhåndsvisning-overlay før import."""',
     '            """Show preview overlay before import."""'),
    ('                f"\\n\\n({skipped} oppføring"',
     '                f"\\n\\n({skipped} entry"'),
    ('"Slå sammen"',
     '"Merge"'),
    ('            """Utfør import — erstatt eksisterende eller slå sammen."""',
     '            """Perform import — replace existing or merge."""'),

    # Initiative tracker
    ('"DEX avgjør rekkefølgen. +50 hvis skyter med håndvåpen."',
     '"DEX determines the order. +50 if shooting with a handgun."'),
    ('            bottom.add_widget(mkbtn("Fullfør", self._init_finish,',
     '            bottom.add_widget(mkbtn("Finish", self._init_finish,'),
    ('"Legg til karakterer under \'Verktøy > Karakterer\' først."',
     '"Add characters under \'Tools > Characters\' first."'),

    # NPC/enemy names — leave game-data names as-is except "Fiende"
    ('"n_fiende"', '"n_enemy"'),  # variable name comment if any
    # Log entry
    ('            # --- Udøde ---', '            # --- Undead ---'),
    ('            """Gå fra setup til aktiv: sorter etter effektiv DEX."""',
     '            """Transition from setup to active: sort by effective DEX."""'),
    ('            # Sorter høyest først (CoC-regel: høy DEX går først)',
     '            # Sort highest first (CoC rule: high DEX goes first)'),
    ('            # Tiebreak: høyere base DEX, så alfabetisk navn',
     '            # Tiebreak: higher base DEX, then alphabetical name'),
    ('            """Aktiv fase: vis sortert rekkefølge."""',
     '            """Active phase: show sorted order."""'),
    ('"Trykk på aktiv (øverst) for å avslutte turen."',
     '"Press the active (top) entry to end the turn."'),
    ('            """Trykk på øverste kort = dens tur er ferdig."""',
     '            """Press the top card = that turn is done."""'),
    ('            """Tøm listen og gå tilbake til setup."""',
     '            """Clear the list and return to setup."""'),
    ('            """Gå tilbake til setup - behold listen."""',
     '            """Return to setup — keep the list."""'),

    # Battlemap
    ('            """Åpne battlemap som overlay. Sync tokens fra init-lista."""',
     '            """Open battlemap as overlay. Sync tokens from init list."""'),
    ('"Trykk på en token i \'Å plassere\' for å begynne."',
     '"Press a token in \'To place\' to begin."'),
    ('"Tøm kart", self._bm_clear,',
     '"Clear map", self._bm_clear,'),
    ('            # Legg overlay på FloatLayout-root',
     '            # Place overlay on FloatLayout root'),
    ('            """Farge for en token basert på type og tilstand."""',
     '            """Colour for a token based on type and state."""'),
    ('                base = [0.60, 0.18, 0.20, 1]  # mørk rød',
     '                base = [0.60, 0.18, 0.20, 1]  # dark red'),
    ('            """Hvem har tur akkurat nå (første i init-lista)?"""',
     '            """Who has the turn right now (first in init list)?"""'),
    ('            """Tegn opp hele kartet basert på state."""',
     '            """Render the entire map based on state."""'),
    ("                    f\"trykk på ledig rute for å plassere.\")",
     "                    f\"press an empty cell to place.\")"),
    ("                    f\"Å plassere ({n_unp}): trykk for å velge.\")",
     "                    f\"To place ({n_unp}): press to select.\")"),
    ('"Trykk på en token for å velge og flytte."',
     '"Press a token to select and move."'),
    ('            """Håndter trykk på en rute."""',
     '            """Handle press on a cell."""'),
    ('            # Modus 3: token valgt fra før',
     '            # Mode 3: token already selected'),
    ('                # Trykk på valgt = dropp valg',
     '                # Press on selected = deselect'),
    ('            # Flytt valgt token hit hvis innenfor gjenværende MOV',
     '            # Move selected token here if within remaining MOV'),
    ('            # Utfør flytt — og tell bruk',
     '            # Perform move — and count usage'),
    ('            """Flytt valgt token tilbake til \'Å plassere\'."""',
     '            """Move selected token back to \'To place\'."""'),
    ('            """Tøm kartet — alle tokens tilbake til unplaced."""',
     '            """Clear the map — all tokens back to unplaced."""'),
    ('            """Flytt øverste init-entry til bunn + nullstill brukt MOV.\n'
     '            Autovelg neste deltakers token hvis den er på kartet.\n'
     '            CoC: hver ny runde får alle full bevegelse igjen."""',
     '            """Move top init-entry to bottom + reset used MOV.\n'
     '            Auto-select next participant\'s token if on the map.\n'
     '            CoC: every new round everyone gets full movement again."""'),
    ('            # Nullstill brukt MOV for alle tokens (plasserte + å plassere)',
     '            # Reset used MOV for all tokens (placed + to place)'),
    ('            # Autovelg tokenen som tilhører neste aktive deltaker',
     '            # Auto-select the token belonging to the next active participant'),

    # ── Scenario tab ──────────────────────────────────────────────────
    ('            """Prøv å kopiere scenario.json fra Documents-mappen til',
     '            """Try to copy scenario.json from the Documents folder to'),
    ('"filer\' ennå. Trykk \'Gi tilgang\' for å åpne "',
     '"files\' yet. Press \'Grant access\' to open "'),
    ('"innstillingene og slå det på.")',
     '"settings and turn it on.")'),
    ('                    hint = ("\\n\\nLøsning: trykk \'Gi tilgang\' nedenfor "',
     '                    hint = ("\\n\\nFix: press \'Grant access\' below "'),
    ('"og slå på \'Tillat administrering av "',
     '"and enable \'Allow management of "'),
    ('            # Les inn fra disk hvis vi ikke har data ennå',
     '            # Load from disk if we do not have data yet'),
    ("            for key, txt in [('clues', 'Ledetråder'),",
     "            for key, txt in [('clues', 'Clues'),"),
    ('"Ingen ledetråder i denne scenarioet."',
     '"No clues in this scenario."'),
    ('            """Vis melding når scenario.json ikke finnes."""',
     '            """Show message when scenario.json is not found."""'),
    ('            # PRIMÆR METODE: SAF-filvelger (ingen tillatelser kreves)',
     '            # PRIMARY METHOD: SAF file picker (no permissions required)'),
    ('"Trykk \'Velg fil\' for å åpne Android sin "',
     '"Press \'Select file\' to open Android\'s "'),
    ('"Tilgang til alle filer: PÅ"',
     '"Access to all files: ON"'),
    ('"For å bruke Importer-knappen må du slå "',
     '"To use the Import button you must turn "'),
    ('"på \'Tilgang til alle filer\' for appen. "',
     '"on \'Access to all files\' for the app. "'),
    ('"Gi tilgang (åpner innstillinger)"',
     '"Grant access (opens settings)"'),
    ('"Kun tilgjengelig på Android 11+."',
     '"Only available on Android 11+."'),
    ('"Trykk \'Last inn\' etterpå."',
     '"Press \'Load\' afterwards."'),
    ('"Last inn på nytt"',
     '"Reload"'),
    ('            """Åpne Android-innstillinger for All Files Access."""',
     '            """Open Android settings for All Files Access."""'),
    ('"Kunne ikke åpne innstillinger"',
     '"Could not open settings"'),
    ('"Prøv å gå manuelt til:\\n"',
     '"Try going manually to:\\n"'),
    ('            """Åpne Android filvelger og la brukeren velge scenario.json."""',
     '            """Open Android file picker and let the user select scenario.json."""'),
    ('"Ikke støttet"',
     '"Not supported"'),
    ('"Filvelger er kun tilgjengelig på Android."',
     '"File picker is only available on Android."'),
    ('"Åpner filvelger..."',
     '"Opening file picker..."'),
    ('            # Lukk meldingen etter kort tid så filvelgeren vises ren',
     '            # Close message after a short time so the file picker appears clean'),
    ('            # Prøv å parse JSON-innhold',
     '            # Try to parse JSON content'),
    ('            """Forsøk å importere scenario fra Documents-mappen."""',
     '            """Attempt to import scenario from the Documents folder."""'),
    ('"Mulige årsaker:"',
     '"Possible causes:"'),
    ('"(sjekk på jsonlint.com)\\n"',
     '"(check at jsonlint.com)\\n"'),
    ('            """Last scenario.json på nytt fra disk."""',
     '            """Reload scenario.json from disk."""'),
    ('            # Reset til liste-modus når vi bytter til Sesjoner',
     '            # Reset to list mode when switching to Sessions'),
    ('            # Tekst-område (midten)',
     '            # Text area (centre)'),
    ('            # Info-knapp (høyre)',
     '            # Info button (right)'),
    ('            # Legg på FloatLayout-roten',
     '            # Add to FloatLayout root'),
    ('"Ingen PC-karakterer ennå.\\n"',
     '"No PC characters yet.\\n"'),
    ('"Ingen sesjoner ennå.\\n"\n'
     '                    "Trykk \'+ Ny sesjon\' for å logge første økt."',
     '"No sessions yet.\\n"\n'
     '                    "Press \'+ New session\' to log the first session."'),
    ("                ('clues_found', 'Ledetråder funnet'),",
     "                ('clues_found', 'Clues found'),"),
    ("            _add_field('clues_found', 'Ledetråder funnet', True, 120)",
     "            _add_field('clues_found', 'Clues found', True, 120)"),
    ('            """Spør om bekreftelse før nullstilling av alle flagg."""',
     '            """Ask for confirmation before resetting all flags."""'),
    ('"Alle avkryssinger i ledetråder, tidslinje og "',
     '"All tick-boxes in clues, timeline and "'),

    # ── Weapons tab ───────────────────────────────────────────────────
    ('        # ---------- VÅPEN ----------',
     '        # ---------- WEAPONS ----------'),
    ('            """Hovedvisning for våpentabellen."""',
     '            """Main view for the weapon table."""'),
    ('                    mklbl("Våpen", color=GOLD, size=14, bold=True))',
     '                    mklbl("Weapons", color=GOLD, size=14, bold=True))'),
    ('"Ingen våpendata funnet."',
     '"No weapon data found."'),
    ('            # Action-bar: søk + epoke + favoritt-toggle',
     '            # Action bar: search + era + favourites toggle'),
    ("                hint_text='Søk\u2026',",
     "                hint_text='Search\u2026',"),
    ('            # Hovedområde',
     '            # Main area'),
    ('            # Karakter-velger: vis hvilken karakter våpen legges til',
     '            # Character selector: show which character weapons are added to'),
    ('            # Våpenliste',
     '            # Weapon list'),
    ('            """Les inn weapons.json på nytt."""',
     '            """Reload weapons.json."""'),
    ('            # Rebuild fordi kategori-knapper må re-styles',
     '            # Rebuild because category buttons need re-styling'),
    ('            """Returner filtrert våpenliste."""',
     '            """Return filtered weapon list."""'),
    ('                # Søk',
     '                # Search'),
    ('            """Bygg våpen-rad-listen basert på filter."""',
     '            """Build the weapon row list based on filter."""'),
    ('            """Bygg en kompakt våpen-rad (78dp høy, klikkbar)."""',
     '            """Build a compact weapon row (78dp tall, clickable)."""'),
    ('            # Høyre: legg-til-knapp + favoritt-knapp',
     '            # Right: add button + favourites button'),
    ('            # Hele raden (unntatt fav-knapp og add-knapp) klikkbar = åpne detalj',
     '            # Entire row (except fav-button and add-button) clickable = open detail'),
    ('            """Legg til våpen i valgt karakters våpenfelt og lagre."""',
     '            """Add weapon to the selected character\'s weapon field and save."""'),
    ('            """Vis detalj-overlay for ett våpen."""',
     '            """Show detail overlay for one weapon."""'),
    ('            # Nøkkel-stats i rutenett',
     '            # Key stats in grid'),
    ('            # Legg overlay på FloatLayout-root (samme mønster som rules)',
     '            # Place overlay on FloatLayout root (same pattern as rules)'),
    ('            """Lukk våpen-detalj-overlay."""',
     '            """Close weapon detail overlay."""'),
]

count = 0
for old, new in REPLACEMENTS:
    if new is None:
        continue
    if old in src:
        src = src.replace(old, new)
        count += 1
    # else silently skip (already translated or not present)

# Fix remaining isolated Norwegian tokens that are safe single-word replacements
# Only inside string literals / comments (safe because these are very specific)
token_map = [
    # Comments
    ("# Indeks 0 = trill 1 osv. Bytt gjerne ut tekst med formuleringer",
     "# Index 0 = roll 1 etc. Replace text with formulations"),
    ("# straight from the Pulp Cthulhu book if you wish.",
     "# straight from the Pulp Cthulhu book if you wish."),
    # log messages
    ('log(f"_weap_do_load: {err}")', 'log(f"_weap_do_load: {err}")'),
]
for old, new in token_map:
    if old in src:
        src = src.replace(old, new)
        count += 1

print(f"Applied {count} replacements.")
remaining = [i+1 for i, line in enumerate(src.splitlines())
             if any(c in line for c in 'æøåÆØÅ')]
print(f"Remaining Norwegian lines: {len(remaining)}")
if remaining:
    for ln in remaining[:40]:
        print(f"  {ln}: {src.splitlines()[ln-1].rstrip()}")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Written.")
