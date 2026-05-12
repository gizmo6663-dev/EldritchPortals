import difflib

with open('/home/runner/work/EldritchPortals/EldritchPortals/main.py', 'r', encoding='utf-8') as f:
    eng_lines = f.readlines()
with open('/tmp/src_clean.py', 'r', encoding='utf-8') as f:
    nor_lines = f.readlines()

def translate(text):
    replacements = [
        # Paths
        ('"/sdcard/Documents/EldritchPortal"', '"/sdcard/Documents/EldritchPortals"'),
        ('EldritchPortal/crash.log', 'EldritchPortals/crash.log'),
        ("BASE_DIR  = \"/sdcard/Documents/EldritchPortal\"", "BASE_DIR  = \"/sdcard/Documents/EldritchPortals\""),
        # Version strings
        ('v0.4.5 – Necronomicon, glatt puls-glow', 'v0.4.5 – Necronomicon'),
        ('v0.4.5 Necronomicon, glatt puls-glow', 'v0.4.5 Necronomicon'),
        # Comments
        ('midlertidig; overstyres i build()', 'temporary; overridden in build()'),
        ('# Karakter-fil: primær lagring i user_data_dir (app-private,', '# Character file: primary storage in user_data_dir (app-private,'),
        ('# alltid skrivbar). Ekstern sti brukes kun for migrering ved', '# always writable). External path used only for migration at'),
        ('# første oppstart — unngår Android 13+ scoped storage-problem.', '# first launch — avoids Android 13+ scoped storage problem.'),
        ('# CHAR_FILE settes i build() når user_data_dir er tilgjengelig.', '# CHAR_FILE is set in build() when user_data_dir is available.'),
        ('# Scenario-fil:', '# Scenario file:'),
        ('# alltid skrivbar). Ekstern import-sti forsøkes lest ved', '# always writable). External import path is tried on'),
        ('# "Importer" — unngår', '# "Import" — avoids'),
        ('# SCENARIO_FILE settes i build() når user_data_dir er tilgjengelig.', '# SCENARIO_FILE is set in build() when user_data_dir is available.'),
        ('# Våpendata er BUNDLET med appen (pakket inn i APK).', '# Weapon data is BUNDLED with the app (packed into the APK).'),
        ('# Dette unngår Android 13+ scoped storage permission-problemer.', '# This avoids Android 13+ scoped storage permission problems.'),
        ('# Også prøv en ekstern versjon — hvis den finnes OG er lesbar,', '# Also try an external version — if it exists AND is readable,'),
        ('# WEAPONS_FAV_FILE settes i build() når user_data_dir er tilgjengelig.', '# WEAPONS_FAV_FILE is set in build() when user_data_dir is available.'),
        ('# rett fra Pulp Cthulhu-boka hvis du ønsker.', '# straight from the Pulp Cthulhu book if you wish.'),
        ("# (Generell font er Kivy's default Roboto - støtter norske tegn)", "# (General font is Kivy's default Roboto - supports extended characters)"),
        ('# knapp (vinrød)', '# button (burgundy)'),
        ('# mørk amber for ytre ramme', '# dark amber for outer frame'),
        ('# dypt bok-brunt/burgunder', '# deep book-brown/burgundy'),
        ('# panel-burgunder', '# panel burgundy'),
        ('# aktiv tab', '# active tab'),
        ('# skygge', '# shadow'),
        ('# antikk gull', '# antique gold'),
        ('# dempet gull (border)', '# muted gold (border)'),
        ('# lys metallisk highlight', '# light metallic highlight'),
        ('# varm mellomtone for gull', '# warm midtone for gold'),
        ('# pergament-tekst', '# parchment text'),
        ('# dempet tekst', '# muted text'),
        ('# Bakgrunnsbildet fyller hele skjermen på splash.', '# Background image fills the whole screen on splash.'),
        ('# KV REGLER – skygge + avrundede hjørner', '# KV RULES – shadow + rounded corners'),
        ('# Skygge: en mørk RoundedRectangle forskjøvet ned og gjort litt smalere,', '# Shadow: a dark RoundedRectangle shifted down and made slightly narrower,'),
        ('# mens høyden beholdes som en ratio av widgeten for å gi en mykere', '# while height is kept as a ratio of the widget for a softer'),
        ('# "floor shadow" uten å endre selve knapp/panel-bredden.', '# "floor shadow" without changing the button/panel width itself.'),
        ('#     border-linjer (mørk amber + gull) — slankere og roligere.', '#     border lines (dark amber + gold) — slimmer and calmer.'),
        ('#   - RToggle: tynn gullstripe i bunnen som KUN vises når', '#   - RToggle: thin gold stripe at the bottom that ONLY shows when'),
        ('#   - PreviewFrame (galleri-rammer): 2 border-linjer + topp-glød.', '#   - PreviewFrame (gallery frames): 2 border lines + top glow.'),
        ('#     Beholder ornamentert preg, men uten indre glint-støy.', '#     Retains ornate character, but without inner glint noise.'),
        ('# Farge-overlay (burgunder/vinrød)', '# Colour overlay (burgundy/wine red)'),
        ('# Mørk ytre kant (gir dybde)', '# Dark outer edge (gives depth)'),
        ('# Én Rectangle som bruker en blurret avrundet-rektangel-tekstur.', '# One Rectangle using a blurred rounded-rectangle texture.'),
        ('# nøyaktig 0 ved kantene, så det er INGEN synlige klippekanter', '# exactly 0 at the edges, so there are NO visible clipping edges'),
        ('# Mørk ytre kant', '# Dark outer edge'),
        ('# Tab-indikator: smal lysskjær-stripe i bunn — KUN ved aktiv tab', '# Tab indicator: narrow light-glow stripe at bottom — ONLY for active tab'),
        ('# Topp-glød (subtil høylysrefleks i overkant)', '# Top glow (subtle highlight reflection at top edge)'),
        ('# Puls-amplitude (0..1) — drevet av Animation når state=\'down\'.', "# Pulse amplitude (0..1) — driven by Animation when state='down'."),
        ('# KV-en gjør resten: én blurret glow-tekstur fades inn/ut med', '# The KV does the rest: one blurred glow texture fades in/out with'),
        ('# denne verdien for å skape pust-effekten.', '# this value to create the breathing effect.'),
        ('# Mye mykere enn lineær, ingen synlig "klipping"', '# Much softer than linear, no visible "clipping"'),
        ('# Linje 3: skade | rekkevidde | magasin | feiling', '# Line 3: damage | range | magazine | malfunction'),
        ('# target_area overstyres av Kamp-fanen til self._cmb_area', '# target_area overridden by Combat tab to self._cmb_area'),
        ('# Animer lukking. Fjern barn først når animasjonen er ferdig', '# Animate closing. Remove children first when animation is done'),
        ('# Avbryt eventuelle pågående animasjoner', '# Cancel any ongoing animations'),
        # UI strings
        ('"Havbølger"', '"Ocean Waves"'),
        ('"Skummel atmosfære"', '"Eerie Atmosphere"'),
        ('"Mørk spenning"', '"Dark Tension"'),
        ('("age","Alder")', '("age","Age")'),
        ('("residence","Bosted")', '("residence","Residence")'),
        ('("birthplace","Fødested")', '("birthplace","Birthplace")'),
        ('("weapons","Våpen")', '("weapons","Weapons")'),
        ('"Ny runde"', '"New Round"'),
        ('"Brutal slager"', '"Brutal Slugger"'),
        ('"Velg enhet..."', '"Select device..."'),
        ('"Velg et spor"', '"Select a track"'),
        ('"Velg egen lyd"', '"Choose custom sound"'),
        ('"Velg lyd først"', '"Choose sound first"'),
        ('"Velg en lokal lydfil for å loope den sømløst."', '"Select a local audio file to loop it seamlessly."'),
        ('"Lukk"', '"Close"'),
        ('"Lagre"', '"Save"'),
        ('"Avbryt"', '"Cancel"'),
        ('"Lagre skills"', '"Save skills"'),
        ('"ENKLEST — Velg fil"', '"EASIEST — Choose file"'),
        ("entry += f' skade {damage}'", "entry += f' damage {damage}'"),
        ("if rng and rng != 'berøring':", "if rng and rng != 'touch':"),
        ('"Legg til deltakere i Initiativ-fanen"', '"Add participants in the Initiative tab"'),
        ('"for å starte runde-rekkefølge."', '"to start round order."'),
        ("\"Bruk 'Lukk' for å komme tilbake hit.\"", "\"Use 'Close' to return here.\""),
        ("\"Legg til karakterer under 'Characters'.\"", "\"Add characters under 'Characters'.\""),
        # Custom sound
        ('Egen lyd', 'Custom Sound'),
        # Insanity table - RT
        ('"Psykosomatisk handikap"', '"Psychosomatic Disability"'),
        ('Psykosomatisk handikap', 'Psychosomatic Disability'),
        ('Plutselig blind, døv eller lam i 1d10 runder', 'Suddenly blind, deaf, or lame for 1d10 rounds'),
        ('"Vold"', '"Violence"'),
        ('Angriper nærmeste mål — venn eller fiende — i 1d10 runder.', 'Attacks nearest target — friend or foe — for 1d10 rounds.'),
        ('Forveksler en tilstedeværende med en viktig person fra fortiden; oppfører seg deretter i 1d10 runder.', 'Mistakes someone present for an important person from the past; behaves accordingly for 1d10 rounds.'),
        ('"Betydelig person"', '"Significant Person"'),
        ('Betydelig person', 'Significant Person'),
        ('"Besvimelse"', '"Fainting"'),
        ('Besvimelse', 'Fainting'),
        ('Kollapser bevisstløs av sjokket i 1d10 runder.', 'Collapses unconscious from the shock for 1d10 rounds.'),
        ('"Flukt"', '"Flight"'),
        ('Flukt', 'Flight'),
        ('Flykter i blind panikk vekk fra trusselen i 1d10 runder.', 'Flees in blind panic away from the threat for 1d10 rounds.'),
        ('"Fysisk hysteri"', '"Physical Hysteria"'),
        ('Fysisk hysteri', 'Physical Hysteria'),
        ('Gråter, ler eller skriker ukontrollert i 1d10 runder; ute av stand til å handle.', 'Cries, laughs, or screams uncontrollably for 1d10 rounds; unable to act.'),
        ('"Fobi"', '"Phobia"'),
        ('Fobi', 'Phobia'),
        ('"Mani"', '"Mania"'),
        ('Mani', 'Mania'),
        ('"Hukommelsestap"', '"Memory Loss"'),
        ('Hukommelsestap', 'Memory Loss'),
        # SUM insanity
        ('"Stjålne timer"', '"Stolen Hours"'),
        ('Stjålne timer', 'Stolen Hours'),
        ('"Voldelig adferd"', '"Violent Behaviour"'),
        ('Voldelig adferd', 'Violent Behaviour'),
        ('"Innlagt"', '"Committed"'),
        ('Innlagt', 'Committed'),
        ('"Hjemflukt"', '"Flight Home"'),
        ('Hjemflukt', 'Flight Home'),
        ('"Hysteri"', '"Hysteria"'),
        ('Hysteri', 'Hysteria'),
        # Rules data
        ('"Suksessnivåer:"', '"Success levels:"'),
        ('Suksessnivåer:', 'Success levels:'),
        ('"Fumble (basert på KRAV, ikke base skill):"', '"Fumble (based on THRESHOLD, not base skill):"'),
        ('Fumble (basert på KRAV, ikke base skill):', 'Fumble (based on THRESHOLD, not base skill):'),
        ('bruk den HØYESTE.', 'use the HIGHEST.'),
        ('Gis av Keeper basert på omstendigheter:', 'Given by Keeper based on circumstances:'),
        ('  Fordel: bonus (godt lys, tid, verktøy)', '  Advantage: bonus (good light, time, tools)'),
        ('  Ulempe: penalty (stress, dårlig sikt)', '  Disadvantage: penalty (stress, poor visibility)'),
        ('Må beskrive HVA de gjør annerledes.', 'Must describe WHAT they do differently.'),
        ('Keeper må godkjenne pushen.', 'Keeper must approve the push.'),
        ('Høyeste suksessnivå vinner.', 'Highest success level wins.'),
        ('Likt nivå: høyeste skill-verdi vinner.', 'Tied level: highest skill value wins.'),
        ('1. Alle handler i DEX-rekkefølge', '1. All act in DEX order'),
        ('   (høyeste først).', '   (highest first).'),
        ('2. Hver deltaker får 1 handling:', '2. Each participant gets 1 action:'),
        ('   - Manøver (trip, disarm, etc.)', '   - Manoeuvre (trip, disarm, etc.)'),
        ('3. Forsvarer velger reaksjon:', '3. Defender chooses reaction:'),
        ('   - Dodge (unngå)', '   - Dodge (avoid)'),
        ('   - Ingenting (tar full skade)', '   - Nothing (takes full damage)'),
        ('Angriper: rull Fighting-skill.', 'Attacker: roll Fighting skill.'),
        ('Forsvarer velger:', 'Defender chooses:'),
        ('  Angriper vinner -> full skade', '  Attacker wins -> full damage'),
        ('  Forsvarer vinner -> unngår angrepet', '  Defender wins -> avoids the attack'),
        ('  Forsvarer vinner -> forsvarer gjør skade', '  Defender wins -> defender deals damage'),
        ('Dodge: 1 gratis per runde,', 'Dodge: 1 free per round,'),
        ('  ekstra dodge koster handling neste runde.', '  extra dodge costs an action next round.'),
        ('  Når forsvarer allerede har dodget', '  When defender has already dodged'),
        ('  eller fought back denne runden:', '  or fought back this round:'),
        ('  Unntak: vesener med flere angrep/runde', '  Exception: creatures with multiple attacks/round'),
        ('  = maks våpenskade + ekstra kast.', '  = max weapon damage + extra roll.'),
        ('Fighting-manøver (i stedet for skade):', 'Fighting manoeuvre (instead of damage):'),
        ('  Trip/knockdown: mål faller', '  Trip/knockdown: target falls'),
        ('  Hold/grapple: mål er fastholdt', '  Hold/grapple: target is held'),
        ('  Bevegelig mål: +1 penalty', '  Moving target: +1 penalty'),
        ('  Stort mål: +1 bonus', '  Large target: +1 bonus'),
        ('  Smalt mål: +1 penalty', '  Small target: +1 penalty'),
        ('  gjennomborende våpen', '  impaling weapon'),
        ('Oppstår ved midlertidig insanity.', 'Occurs on temporary insanity.'),
        ('REAL-TIME (varig 1d10 runder):', 'REAL-TIME (lasting 1d10 rounds):'),
        ('Casting time: 1 runde til flere timer.', 'Casting time: 1 round to several hours.'),
        ('HP: (CON + SIZ) / 5 (avrundet ned)', 'HP: (CON + SIZ) / 5 (rounded down)'),
        ('  - Redusere skade (etter kast)', '  - Reduce damage (after roll)'),
        ('Velg 1 arketype ved opprettelse.', 'Choose 1 archetype at creation.'),
        ('  Brawler: +1d6 melee-skade', '  Brawler: +1d6 melee damage'),
        ('Våpen: skade / attacks', 'Weapon: damage / attacks'),
        ('Våpen: skade / range / shots', 'Weapon: damage / range / shots'),
        ('  First Aid/Medicine innen 1 runde', '  First Aid/Medicine within 1 round'),
        ('  CON-sjekk per runde', '  CON-check per round'),
        ('  Suksess = holder ut 1 runde til', '  Success = lasts 1 more round'),
        ('  First Aid: +1 HP (1 forsøk/skade)', '  First Aid: +1 HP (1 attempt/wound)'),
        ('Burst: 3 kuler, +1 bonus die til skade.', 'Burst: 3 bullets, +1 bonus die to damage.'),
        ('  Bruker halve magasinet.', '  Uses half the magazine.'),
        ('Hver runde kan deltaker:', 'Each round a participant can:'),
        ('  bevegelse den runden.', '  movement that round.'),
        ('Fumble: fall, skade, fastklemt, etc.', 'Fumble: fall, damage, stuck, etc.'),
        ('  CON-sjekk per runde etter runde 5.', '  CON-check per round after round 5.'),
        ('  1:1 for å senke resultatet.', '  1:1 to lower the result.'),
        ('  Resultat ≤ skill = ingen økning.', '  Result ≤ skill = no increase.'),
        ('DB basert på STR + SIZ:', 'DB based on STR + SIZ:'),
        ('  Angriper Build ≥ mål + 2: +1 bonus', '  Attacker Build ≥ target + 2: +1 bonus'),
        ('  Angriper Build ≤ mål - 2: +1 penalty', '  Attacker Build ≤ target - 2: +1 penalty'),
        # Section headings in rules
        ('Skytevåpen\n', 'Firearms\n'),
        ('Manøvrer\n', 'Manoeuvres\n'),
    ]
    for nor, eng in replacements:
        text = text.replace(nor, eng)
    return text

print("Running SequenceMatcher...")
matcher = difflib.SequenceMatcher(None, eng_lines, nor_lines, autojunk=False)
opcodes = matcher.get_opcodes()
print(f"Got {len(opcodes)} opcodes")

result = []
for tag, i1, i2, j1, j2 in opcodes:
    if tag == 'equal':
        result.extend(eng_lines[i1:i2])
    elif tag == 'insert':
        result.extend(translate(line) for line in nor_lines[j1:j2])
    elif tag == 'replace':
        result.extend(translate(line) for line in nor_lines[j1:j2])
    elif tag == 'delete':
        pass  # skip deleted lines

print(f"Result: {len(result)} lines")

with open('/home/runner/work/EldritchPortals/EldritchPortals/main.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

print("Written successfully.")
