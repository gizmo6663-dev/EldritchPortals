import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from kivy.clock import Clock

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
log("=== APP START (v0.3.2 – Abyssal Purple) ===")

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.label import Label
    from kivy.uix.image import Image
    from kivy.uix.slider import Slider
    from kivy.uix.spinner import Spinner
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.core.window import Window
    from kivy.uix.filechooser import FileChooserListView
    from kivy.graphics import Color as GColor, Rectangle as GRect
    from kivy.utils import platform
    from kivy.metrics import dp, sp
    from kivy.animation import Animation
    from kivy.properties import ListProperty, NumericProperty
    from kivy.lang import Builder
    log("Kivy imported OK")

    CAST_AVAILABLE = False
    try:
        import pychromecast
        CAST_AVAILABLE = True
    except ImportError:
        pass
    USE_JNIUS = False
    MediaPlayer = None
    if platform == 'android':
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            USE_JNIUS = True
            log("Using Android MediaPlayer")
        except:
            pass

    BASE_DIR  = "/sdcard/Documents/EldritchPortal"
    IMG_DIR   = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    CHAR_FILE = os.path.join(BASE_DIR, "characters.json")

    # Weapon data is BUNDLED with the app (packed into the APK).
    # This avoids Android 13+ scoped storage permission issues.
    try:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    BUNDLED_WEAPONS = os.path.join(_BUNDLE_DIR, "weapons.json")
    BUNDLED_CHARS   = os.path.join(_BUNDLE_DIR, "characters.json")
    # Also try an external version — if it exists AND is readable,
    # use it (lets the user override it with their own file if possible).
    EXTERNAL_WEAPONS = os.path.join(BASE_DIR, "weapons.json")
    EXTERNAL_SCENARIO = os.path.join(BASE_DIR, "scenario.json")
    # Favorites are stored in user_data_dir (app-private, always writable).
    # WEAPONS_FAV_FILE is set in build() when user_data_dir is available.

    def ensure_dirs():
        """Create folders AFTER permissions have been granted."""
        for d in [IMG_DIR, MUSIC_DIR]:
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                log(f"makedirs {d}: {e}")
        log(f"Dirs OK: {os.path.exists(IMG_DIR)}, {os.path.exists(MUSIC_DIR)}")

    # === COLORS – ABYSSAL PURPLE ===
    BG   = [0.05, 0.03, 0.07, 1]      # deep purple-black background
    BG2  = [0.10, 0.05, 0.12, 1]      # panel
    INPUT= [0.07, 0.03, 0.09, 1]      # text input background
    BTN  = [0.22, 0.10, 0.16, 1]      # button (burgundy)
    BTNH = [0.38, 0.15, 0.22, 1]      # active tab
    SHAD = [0.02, 0.01, 0.03, 0.6]    # shadow
    GOLD = [0.95, 0.78, 0.22, 1]      # golden accent
    GDIM = [0.58, 0.45, 0.20, 1]      # muted gold
    TXT  = [0.90, 0.85, 0.80, 1]      # light text
    DIM  = [0.52, 0.38, 0.45, 1]      # muted text (purple tone)
    RED  = [0.75, 0.20, 0.22, 1]      # danger/stop
    GRN  = [0.25, 0.58, 0.32, 1]      # OK/PC
    BLUE = [0.30, 0.40, 0.65, 1]      # info
    BLK  = [0.0, 0.0, 0.0, 1]         # black (preview background)
    IMG_EXT   = ('.png','.jpg','.jpeg','.webp')
    HTTP_PORT = 8089

    # ============================================================
    # KV RULES – shadow + rounded corners
    # Shadow: a dark RoundedRectangle offset 2dp downward.
    # Main body: RoundedRectangle with bg_color on top.
    # ============================================================
    Builder.load_string('''
<RBtn>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    bold: True
    canvas.before:
        Color:
            rgba: self.shadow_color
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.width, self.height
            radius: [self.radius]
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<RToggle>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    bold: True
    canvas.before:
        Color:
            rgba: self.shadow_color
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.width, self.height
            radius: [self.radius]
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<RBox>:
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<FramedBox>:
    canvas.before:
        Color:
            rgba: self.frame_color
        Line:
            rectangle: (self.x, self.y, self.width, self.height)
            width: 1.5
''')

    class RBtn(Button):
        bg_color = ListProperty(BTN)
        shadow_color = ListProperty(SHAD)
        radius = NumericProperty(dp(14))

    class RToggle(ToggleButton):
        bg_color = ListProperty(BTN)
        shadow_color = ListProperty(SHAD)
        radius = NumericProperty(dp(14))

    class RBox(BoxLayout):
        bg_color = ListProperty(BG2)
        radius = NumericProperty(dp(20))

    class FramedBox(BoxLayout):
        frame_color = ListProperty(GOLD)

    # === SOUND SOURCES ===
    AMBIENT_SOUNDS = [
        {"name":"--- Nature ---"},
        {"name":"Rain and Thunder","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Ocean Waves","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"Night Rain","url":"https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name":"Wind and Storm","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name":"Night Sounds","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name":"Sea Storm","url":"https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name":"Light Rain","url":"https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name":"Thunderstorm","url":"https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name":"Rough Sea","url":"https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
        {"name":"--- Horror ---"},
        {"name":"Creepy Atmosphere","url":"https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
        {"name":"Unsettling Drone","url":"https://archive.org/download/scary-sound-effects-8/Evil%20Demon%20Drone%20Movie%20Halloween%20Sounds.mp3"},
        {"name":"Dark Suspense","url":"https://archive.org/download/scary-sound-effects-8/Dramatic%20Suspense%20Sound%20Effects.mp3"},
        {"name":"Horror Sounds","url":"https://archive.org/download/creepy-music-sounds/Horror%20Sound%20Effects.mp3"},
    ]

    # === CHARACTER FIELDS ===
    CHAR_INFO = [
        ("name","Name"), ("type","Type"), ("occ","Occupation"), ("archetype","Archetype"),
        ("age","Age"), ("residence","Residence"), ("birthplace","Birthplace"),
    ]
    CHAR_STATS = [
        ("str","STR"), ("con","CON"), ("siz","SIZ"), ("dex","DEX"),
        ("int","INT"), ("pow","POW"), ("app","APP"), ("edu","EDU"),
    ]
    CHAR_DERIVED = [
        ("hp","HP"), ("mp","MP"), ("san","SAN"), ("luck","Luck"),
        ("db","DB"), ("build","Build"), ("move","Move"), ("dodge","Dodge"),
    ]
    CHAR_TEXT = [
        ("weapons","Weapons"), ("talents","Pulp Talents"),
        ("backstory","Backstory"), ("notes","Notes"),
    ]
    SKILLS = [
        ("Accounting","05"), ("Appraise","05"), ("Archaeology","01"),
        ("Art/Craft:","05"), ("Art/Craft 2:","05"),
        ("Charm","15"), ("Climb","20"), ("Computer Use","00"),
        ("Credit Rating","00"), ("Cthulhu Mythos","00"),
        ("Demolitions","01"), ("Disguise","05"), ("Diving","01"),
        ("Dodge","DEX/2"), ("Drive Auto","20"),
        ("Elec. Repair","10"), ("Fast Talk","05"),
        ("Fighting (Brawl)","25"), ("Fighting:",""),
        ("Firearms (Handgun)","20"), ("Firearms (Rifle)","25"), ("Firearms:",""),
        ("First Aid","30"), ("History","05"),
        ("Intimidate","15"), ("Jump","20"),
        ("Language (Other):","01"), ("Language (Other) 2:","01"),
        ("Language (Own)","EDU"),
        ("Law","05"), ("Library Use","20"), ("Listen","20"),
        ("Locksmith","01"), ("Mech. Repair","10"), ("Medicine","01"),
        ("Natural World","10"), ("Navigate","10"), ("Occult","05"),
        ("Persuade","10"), ("Pilot:","01"),
        ("Psychoanalysis","01"), ("Psychology","10"),
        ("Read Lips","01"), ("Ride","05"),
        ("Science:","01"), ("Science 2:","01"),
        ("Sleight of Hand","10"), ("Spot Hidden","25"),
        ("Stealth","20"), ("Survival","10"),
        ("Swim","20"), ("Throw","20"), ("Track","10"),
    ]

    # === RULES & REFERENCE ===
    # Complete CoC 7e + Pulp Cthulhu Keeper reference.
    RULES = [
      ("Basic Rules", "", [
        ("Skill Rolls", [
          "Roll d100 (percentile) against the skill value.",
          "Equal to or under = success.",
          "",
          "Success Levels:",
          "  Critical: result = 01",
          "  Extreme: result <= skill / 5",
          "  Hard: result <= skill / 2",
          "  Regular: result <= skill",
          "  Failure: result > skill",
          "",
          "Automatic success: 01 is always a success.",
          "Fumble (based on the REQUIRED target, not base skill):",
          "  Required target >= 50: only 100 is a fumble",
          "  Required target < 50: 96-100 is a fumble",
          "  Example: skill 60, Hard difficulty (target 30)",
          "    -> fumble on 96-100",
        ]),
        ("Difficulty", [
          "The Keeper sets the difficulty:",
          "  Regular: full skill value (standard)",
          "  Hard: half skill value",
          "  Extreme: one-fifth of skill value",
          "",
          "Against living opponents:",
          "  Opponent skill < 50: Regular",
          "  Opponent skill >= 50: Hard",
          "  Opponent skill >= 90: Extreme",
        ]),
        ("Bonus & Penalty", [
          "Bonus die: roll 2 tens dice,",
          "  use the LOWEST.",
          "Penalty die: roll 2 tens dice,",
          "  use the HIGHEST.",
          "",
          "Maximum 2 bonus OR 2 penalty dice.",
          "Bonus and penalty cancel out 1:1.",
          "",
          "Assigned by the Keeper based on circumstances:",
          "  Advantage: bonus (good light, time, tools)",
          "  Disadvantage: penalty (stress, poor visibility)",
        ]),
        ("Pushed Rolls", [
          "A player may push ONE failed roll.",
          "They must describe WHAT they do differently.",
          "The Keeper must approve the push.",
          "",
          "Failed push = SEVERE consequence",
          "(worse than a normal failure).",
          "",
          "CANNOT be pushed:",
          "  SAN checks",
          "  Luck checks",
          "  Combat rolls",
          "  Already pushed rolls",
        ]),
        ("Opposed Rolls", [
          "Both sides roll their skills.",
          "The highest success level wins.",
          "Same level: the higher skill value wins.",
          "No success: status quo.",
          "",
          "Common opposed rolls:",
          "  Sneak vs Listen",
          "  Fast Talk vs Psychology",
          "  Charm vs POW",
          "  STR vs STR (break free, hold)",
          "  DEX vs DEX (grab, evade)",
          "  Disguise vs Spot Hidden",
        ]),
        ("Luck", [
          "Luck value: 3d6 x 5 (at character creation).",
          "Luck check: d100 <= Luck.",
          "",
          "Spending Luck:",
          "  After a skill roll: spend Luck points",
          "  1:1 to lower the result.",
          "  Example: roll 55, skill 50 -> spend 5 Luck.",
          "",
          "Luck does NOT recover in standard CoC.",
          "Pulp: recover 2d10 Luck per session.",
          "",
          "Group Luck: the lowest Luck in the group",
          "  is used for random events.",
        ]),
        ("Experience & Development", [
          "After a scenario: mark used skills.",
          "Roll d100 for each marked skill:",
          "  Result > skill = +1d10 to the skill.",
          "  Result <= skill = no increase.",
          "",
          "Skill maximum: 99 (including Cthulhu Mythos).",
          "Age effects may reduce attributes.",
        ]),
      ]),
      ("Combat", "", [
        ("Combat Flow", [
          "1. Everyone acts in DEX order",
          "   (highest first).",
          "",
          "2. Each participant gets 1 action:",
          "   - Attack (melee or ranged)",
          "   - Flee (withdraw from combat)",
          "   - Maneuver (trip, disarm, etc.)",
          "   - Cast a spell",
          "   - Use an item / First Aid",
          "   - Other (talk, search, etc.)",
          "",
          "3. The defender chooses a reaction:",
          "   - Dodge (avoid the attack)",
          "   - Fight Back (counterattack, melee only)",
          "   - Nothing (take full damage)",
          "",
          "4. Repeat until combat ends.",
        ]),
        ("Melee", [
          "Attacker: roll Fighting skill.",
          "Defender chooses:",
          "",
          "DODGE (opposed vs Dodge skill):",
          "  Attacker wins -> full damage",
          "  Defender wins -> attack avoided",
          "  Both fail -> nothing happens",
          "",
          "FIGHT BACK (opposed vs Fighting):",
          "  Attacker wins -> full damage",
          "  Defender wins -> defender deals damage",
          "  Both fail -> nothing happens",
          "",
          "Dodge: 1 free per round,",
          "  extra dodges cost the next round's action.",
          "",
          "OUTNUMBERED:",
          "  When the defender has already dodged",
          "  or fought back this round:",
          "  -> all following attacks gain",
          "     +1 bonus die.",
          "  Exception: creatures with multiple attacks/round",
          "  may dodge/fight back that many times.",
          "  Does NOT apply to firearms.",
        ]),
        ("Firearms", [
          "Roll Firearms skill. NO opposed roll.",
          "The defender may ONLY dodge at point-blank range.",
          "Otherwise: just take cover or move away.",
          "",
          "Range modifiers:",
          "  Point-blank (<= 1/5 range): +1 bonus",
          "  Base range: normal",
          "  Long (up to 2x base): +1 penalty",
          "  Extreme (up to 4x base): +2 penalty",
          "",
          "Other modifiers:",
          "  Moving target: +1 penalty",
          "  Large target: +1 bonus",
          "  Narrow target: +1 penalty",
          "  Aiming (uses action): +1 bonus",
          "",
          "Impale: Extreme success with",
          "  impaling weapons",
          "  = maximum weapon damage + one extra roll.",
        ]),
        ("Maneuvers", [
          "Fighting maneuver (instead of damage):",
          "  Trip/knockdown: target falls",
          "  Disarm: target loses weapon",
          "  Hold/grapple: target is restrained",
          "  Throw: shove/throw the opponent",
          "",
          "Requires: win an opposed Fighting check.",
          "Build difference can grant bonus/penalty:",
          "  Attacker Build >= target + 2: +1 bonus",
          "  Attacker Build <= target - 2: +1 penalty",
        ]),
        ("Damage Bonus (DB)", [
          "DB based on STR + SIZ:",
          "  2-64:    -2",
          "  65-84:   -1",
          "  85-124:  0",
          "  125-164: +1d4",
          "  165-204: +1d6",
          "  205-284: +2d6",
          "  285-364: +3d6",
          "",
          "Build value:",
          "  DB -2: Build -2",
          "  DB -1: Build -1",
          "  DB 0:  Build 0",
          "  DB +1d4: Build 1",
          "  DB +1d6: Build 2",
          "  DB +2d6: Build 3",
        ]),
        ("Damage & Healing", [
          "WOUND LEVELS:",
          "  Minor wound: loss < half max HP",
          "  Major wound: loss >= half max HP",
          "",
          "MAJOR WOUND consequences:",
          "  CON check or fall unconscious",
          "  First Aid/Medicine within 1 round",
          "  Must be stabilized or die",
          "",
          "DYING (0 HP):",
          "  CON check each round",
          "  Failure = death",
          "  Success = hangs on for 1 more round",
          "",
          "HEALING:",
          "  First Aid: +1 HP (1 attempt per wound)",
          "  Medicine: +1d3 HP (after First Aid)",
          "  Natural: 1 HP/week (minor)",
          "  Major wound: 1d3 HP/week with care",
        ]),
        ("Automatic Weapons", [
          "Burst: 3 bullets, +1 bonus die to damage.",
          "Full auto: choose the number of targets,",
          "  distribute bullets, roll for each target.",
          "  1 bonus die per 10 bullets at the target.",
          "",
          "Suppressive fire:",
          "  Covers an area; everyone inside",
          "  must Dodge or take 1 hit.",
          "  Uses half the magazine.",
        ]),
      ]),
      ("Sanity", "", [
        ("SAN Check", [
          "Roll d100 <= current SAN.",
          "",
          "Format: 'X/Y'",
          "  Success: loss = X",
          "  Failure: loss = Y",
          "  Example: '1/1d6' = lose 1 on success,",
          "    lose 1d6 SAN on failure.",
          "",
          "Maximum SAN = 99 - Cthulhu Mythos skill.",
          "",
          "SAN fumble: automatic maximum SAN loss.",
        ]),
        ("Temporary Insanity", [
          "TRIGGER: 5+ SAN lost in ONE roll.",
          "",
          "The Keeper calls for an INT check:",
          "  INT success = investigator realizes",
          "    the truth -> TEMPORARILY INSANE",
          "  INT failure = memory repressed,",
          "    investigator keeps it together for now",
          "",
          "Temporary insanity lasts 1d10 hours.",
          "It begins with a Bout of Madness.",
          "It is followed by Underlying Insanity.",
        ]),
        ("Bout of Madness", [
          "Occurs during temporary insanity.",
          "The Keeper chooses Real-Time or Summary.",
          "",
          "REAL-TIME (lasting 1d10 rounds):",
          "  1: Amnesia (remembers nothing)",
          "  2: Psychosomatic (blind/deaf/paralyzed)",
          "  3: Violence (attack the nearest target)",
          "  4: Paranoia (everyone is an enemy)",
          "  5: Physical collapse (nausea/fainting)",
          "  6: Flight (run in panic)",
          "  7: Hallucinations",
          "  8: Echo (repeat actions meaninglessly)",
          "  9: Phobia (new or existing)",
          "  10: Catatonia (freezes completely)",
        ]),
        ("Summary (1d10 hours)", [
          "After the real-time bout, lasting effect:",
          "  1: Amnesia for the whole event",
          "  2: Obsessions / rituals",
          "  3: Hallucinations (persistent)",
          "  4: Irrational hatred/fear",
          "  5: Phobia (specific, new, or intensified)",
          "  6: Mania (compulsive behavior)",
          "  7: Paranoia (trusts no one)",
          "  8: Dissociation (distant, unreal)",
          "  9: Eating disorder / insomnia",
          "  10: Mythos obsession (studies the forbidden)",
        ]),
        ("Phobias (sample)", [
          "Acrophobia - fear of heights",
          "Agoraphobia - open spaces",
          "Arachnophobia - spiders",
          "Claustrophobia - confined spaces",
          "Demophobia - crowds",
          "Hemophobia - blood",
          "Hydrophobia - water",
          "Mysophobia - germs/filth",
          "Necrophobia - the dead/corpses",
          "Nyctophobia - darkness",
          "Pyrophobia - fire",
          "Thalassophobia - the sea/deep water",
          "Xenophobia - strangers/the unknown",
          "Zoophobia - animals",
        ]),
        ("Manias (sample)", [
          "Dipsomania - craving for alcohol",
          "Kleptomania - urge to steal",
          "Megalomania - grandiose delusions",
          "Mythomania - compulsive lying",
          "Necromania - obsession with death",
          "Pyromania - fire-setting",
          "Thanatomania - death wish",
          "Xenomania - obsession with strangers",
        ]),
        ("Indefinite Insanity", [
          "Triggered when the investigator has lost",
          "  1/5 of current SAN in total.",
          "",
          "Effect: long-term madness.",
          "  The player loses control of the character.",
          "  The Keeper decides the behavior.",
          "  Lasts months/years.",
          "",
          "Treatment:",
          "  Institutionalization",
          "  Psychoanalysis over time",
          "  +1d3 SAN per month (maximum)",
          "  Failed treatment: -1d6 SAN",
        ]),
        ("SAN Recovery", [
          "Psychoanalysis: +1d3 SAN (1/month)",
          "  Failed: -1d6 SAN!",
          "Self-help: improve a skill = +1d3 SAN",
          "Completing a scenario: Keeper reward",
          "",
          "Maximum SAN = 99 - Cthulhu Mythos skill.",
          "Permanent SAN loss cannot be recovered",
          "  beyond this limit.",
        ]),
      ]),
      ("Chase", "", [
        ("Setup", [
          "1. Type: on foot or vehicle.",
          "2. Number of locations: 5-10 (Keeper chooses).",
          "3. Participants:",
          "   On foot: MOV based on DEX, STR, SIZ.",
          "   Car: speed rating.",
          "4. Speed Roll (CON check):",
          "   Extreme success: +1 MOV for the chase",
          "   Success: no change",
          "   Failure: -1 MOV for the chase",
          "   (vehicles use Drive Auto instead)",
          "5. Compare MOV: higher MOV escapes",
          "   immediately. Otherwise -> full chase.",
          "6. Set starting positions on the track.",
          "7. Place barriers/hazards on locations.",
          "",
          "MOV (Movement Rate):",
          "  If DEX & STR are both > SIZ: MOV 9",
          "  If either DEX or STR > SIZ: MOV 8",
          "  If both are <= SIZ: MOV 7",
          "  Age 40-49: MOV -1",
          "  Age 50-59: MOV -2 (etc.)",
        ]),
        ("Movement & Actions", [
          "Rounds are resolved in DEX order (highest first).",
          "",
          "Each round a participant may:",
          "  - Move (MOV locations)",
          "  - Perform 1 action:",
          "    Speed: CON check for +1 location",
          "    Attack: Fighting/Firearms",
          "    Barrier: skill check to pass",
          "    Obstacle: create a barrier for the pursuer",
          "",
          "A hazard action costs the action AND",
          "  the movement for that round.",
        ]),
        ("Barriers", [
          "The Keeper places barriers on locations.",
          "Skill checks to pass:",
          "",
          "  Jump a fence: Jump / Climb",
          "  Narrow passage: DEX / Dodge",
          "  Crowd: STR / Charm / Intimidate",
          "  Mud/slippery ground: DEX / Luck",
          "  Locked door: Locksmith / STR",
          "  Busy street: Drive Auto / DEX",
          "",
          "Failure: lose 1 location of movement.",
          "Fumble: fall, take damage, get stuck, etc.",
        ]),
        ("Victory & Defeat", [
          "ESCAPE succeeds when:",
          "  Distance between them = number of locations + 1",
          "  (the pursuer cannot see the target).",
          "",
          "CAUGHT when:",
          "  The pursuer is on the SAME location.",
          "  Combat or interaction may begin.",
          "",
          "EXHAUSTION:",
          "  CON check each round after round 5.",
          "  Failure: MOV is reduced by 1.",
          "  MOV 0: cannot move.",
        ]),
      ]),
      ("Magic & Tomes", "", [
        ("Spells", [
          "Costs vary by spell:",
          "  Magic Points (MP): most common",
          "  SAN: almost always",
          "  HP: some powerful spells",
          "  POW: permanent sacrifice (rare)",
          "",
          "Casting time: 1 round to several hours.",
          "Some require components/rituals.",
          "",
          "MP recovers: 1 per 2 hours of rest.",
          "MP = 0: unconscious for 1d8 hours.",
          "POW sacrifice: permanent, does NOT recover.",
        ]),
        ("Mythos Tomes", [
          "Reading a Mythos tome:",
          "  Initial reading: weeks to months",
          "  Full study: months to years",
          "",
          "Reward: +Cthulhu Mythos skill.",
          "Cost: SAN loss (varies by tome).",
          "May also teach spells from the tome.",
          "",
          "EXAMPLES (CM gain / SAN loss):",
          "  Necronomicon (Latin): +15 / -2d10",
          "  Necronomicon (original): +22 / -3d10",
          "  De Vermis Mysteriis: +10 / -1d8",
          "  Book of Eibon: +11 / -2d4",
          "  Cultes des Goules: +9 / -1d8",
          "  Pnakotic Manuscripts: +7 / -1d6",
          "  Unaussprechlichen Kulten: +9 / -2d4",
          "  Revelations of Glaaki: +7 / -1d4",
          "  Book of Dzyan: +5 / -1d4",
        ]),
        ("Mythos Creatures (SAN)", [
          "Creature: success / failure SAN loss",
          "",
          "  Byakhee: 1/1d6",
          "  Dark Young: 0/1d8",
          "  Deep One: 0/1d6",
          "  Elder Thing: 1/1d6",
          "  Flying Polyp: 1d3/1d20",
          "  Ghoul: 0/1d6",
          "  Great Race: 0/1d6",
          "  Hound of Tindalos: 1d3/1d20",
          "  Mi-Go: 0/1d6",
          "  Nightgaunt: 0/1d6",
          "  Shoggoth: 1d6/1d20",
          "  Star Spawn: 1d6/1d20",
          "  Star Vampire: 1/1d8",
          "",
          "  Great Old Ones:",
          "  Cthulhu: 1d10/1d100",
          "  Hastur: 1d10/1d100",
          "  Nyarlathotep: 0/1d10 (varies)",
          "  Yog-Sothoth: 1d10/1d100",
        ]),
      ]),
      ("Pulp Cthulhu", "", [
        ("Pulp Rules", [
          "Heroes are TOUGHER than standard CoC investigators.",
          "",
          "HP: (CON + SIZ) / 5 (rounded down)",
          "  Standard CoC: (CON+SIZ) / 10",
          "  Effectively DOUBLE HP.",
          "  Optional low-level pulp: (CON+SIZ)/10",
          "",
          "Luck: 2d6+6 x 5 (higher than standard)",
          "  Standard CoC: 3d6 x 5",
          "  Recover 2d10 Luck per session.",
          "",
          "First Aid: +1d4 HP (standard: +1 HP)",
          "  Extreme success: automatically 4 HP.",
          "Medicine: +1d4 HP (standard: +1d3)",
          "",
          "Pulp Talents: 2 by default.",
          "  Low-level pulp: 1 talent",
          "  High-level pulp: 3 talents",
          "",
          "Combat rolls still CANNOT be pushed.",
          "Spending Luck can also be used to:",
          "  - Avoid dying (5 Luck = stabilize)",
          "  - Reduce damage (after the roll)",
        ]),
        ("Archetypes", [
          "Choose 1 archetype at character creation.",
          "It grants bonuses and Pulp Talents.",
          "",
          "  Adventurer: versatile explorer",
          "  Beefcake: physically powerful, extra HP",
          "  Bon Vivant: charming, socially skilled",
          "  Cold Blooded: ruthless, precise",
          "  Dreamer: creative, Mythos-sensitive",
          "  Egghead: intellectual, knowledgeable",
          "  Explorer: explorer, survival expert",
          "  Femme/Homme Fatale: seductive",
          "  Grease Monkey: mechanic, inventive",
          "  Hard Boiled: tough, enduring",
          "  Harlequin: entertainer, distracting",
          "  Hunter: hunter, outdoorsy",
          "  Mystic: spiritual, gifted with divination",
          "  Outsider: lonely, self-taught",
          "  Reckless: daredevil, risk-taker",
          "  Sidekick: loyal, supportive",
          "  Swashbuckler: acrobatic fighter",
          "  Thrill Seeker: adrenaline addict",
          "  Two-Fisted: bare-knuckle specialist",
        ]),
        ("Pulp Talents (sample)", [
          "PHYSICAL:",
          "  Brawler: +1d6 melee damage",
          "  Iron Jaw: ignore 1 K.O. per session",
          "  Quick Healer: double healing",
          "  Tough Guy: +1d6 extra HP",
          "",
          "MENTAL:",
          "  Arcane Insight: +2 Cthulhu Mythos",
          "  Gadget: build an improvised device",
          "  Photographic Memory: remember everything",
          "  Psychic Power: sixth sense",
          "",
          "SOCIAL:",
          "  Smooth Talker: re-roll 1 social check",
          "  Master of Disguise: +1 bonus to Disguise",
          "  Lucky: +1d10 extra Luck recovery",
          "",
          "COMBAT:",
          "  Rapid Fire: extra shot without penalty",
          "  Outmaneuver: +1 bonus on maneuvers",
          "  Fleet Footed: +1 MOV in a chase",
        ]),
      ]),
      ("Tables", "", [
        ("Weapon Table - melee", [
          "Weapon: damage / attacks",
          "",
          "  Unarmed (fist): 1d3+DB / 1",
          "  Head butt: 1d4+DB / 1",
          "  Kick: 1d4+DB / 1",
          "  Grapple: special / 1",
          "  Knife (small): 1d4+DB / 1",
          "  Knife (large): 1d6+DB / 1",
          "  Club/baton: 1d8+DB / 1",
          "  Sword/saber: 1d8+DB / 1",
          "  Axe (large): 1d8+2+DB / 1",
          "  Spear: 1d8+1+DB / 1",
          "  Chainsaw: 2d8 / 1",
        ]),
        ("Weapon Table - firearms", [
          "Weapon: damage / range / shots",
          "",
          "  Derringer (.41): 1d8 / 10y / 1",
          "  Revolver (.32): 1d8 / 15y / 6",
          "  Revolver (.45): 1d10+2 / 15y / 6",
          "  Pistol (9mm): 1d10 / 15y / 8",
          "  Pistol (.45 auto): 1d10+2 / 15y / 7",
          "  Rifle (.30): 2d6+4 / 110y / 5",
          "  Rifle (.303): 2d6+4 / 110y / 10",
          "  Shotgun (12g): 4d6/2d6/1d6",
          "    (range: 10/20/50 yards)",
          "  Thompson SMG: 1d10+2 / 20y / 20",
          "  Dynamite: 5d6 / thrown / 1",
          "    (radius 5 yards)",
        ]),
        ("SAN Loss Overview", [
          "EVENT: success / failure",
          "",
          "  See a corpse: 0/1d3",
          "  See a friend die: 0/1d4",
          "  See something inexplicable: 0/1d2",
          "  Witness a gruesome murder: 1/1d4+1",
          "  Witness mass murder: 1d3/1d6+1",
          "  Discover an atrocity: 0/1d3",
          "",
          "  Discover Mythos evidence: 0/1d2",
          "  Read a Mythos tome: 1/1d4",
          "  Witness a Mythos ritual: 1/1d6",
          "  Be subjected to a spell: 1/1d6",
        ]),
        ("Age Effects", [
          "Age affects attributes at character creation:",
          "",
          "  15-19: -5 SIZ/STR, -5 EDU,",
          "    Luck: roll twice, keep the best",
          "  20-39: EDU improvement: +1",
          "  40-49: EDU +2, -5 distributed STR/CON/DEX,",
          "    APP -5, MOV -1",
          "  50-59: EDU +3, -10 distributed STR/CON/DEX,",
          "    APP -10, MOV -2",
          "  60-69: EDU +4, -20 distributed STR/CON/DEX,",
          "    APP -15, MOV -3",
          "  70-79: EDU +4, -40 distributed STR/CON/DEX,",
          "    APP -20, MOV -4",
          "  80-89: EDU +4, -80 distributed STR/CON/DEX,",
          "    APP -25, MOV -5",
        ]),
        ("Credit Rating", [
          "Credit Rating = wealth/social status:",
          "",
          "  0: poor, homeless",
          "  1-9: poor, only necessities",
          "  10-49: average",
          "  50-89: wealthy",
          "  90-98: rich",
          "  99: enormously wealthy",
          "",
          "Spending level (per day):",
          "  CR 0: $0.50",
          "  CR 1-9: $2",
          "  CR 10-49: $10",
          "  CR 50-89: $50",
          "  CR 90-98: $250",
          "  CR 99: $5000",
        ]),
      ]),
    ]


    def request_android_permissions():
        if platform != 'android':
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO,
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.ACCESS_WIFI_STATE,
                Permission.CHANGE_WIFI_MULTICAST_STATE
            ])
        except:
            pass
        # On Android 11+ (API 30+), READ/WRITE_EXTERNAL_STORAGE no longer covers
        # general files such as .json in /sdcard/Documents/.  Request the
        # "All Files Access" permission (MANAGE_EXTERNAL_STORAGE) by sending the
        # user to the system settings page if it hasn't been granted yet.
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            if Build.VERSION.SDK_INT >= 30:
                Environment = autoclass('android.os.Environment')
                if not Environment.isExternalStorageManager():
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    Toast = autoclass('android.widget.Toast')
                    toast = Toast.makeText(
                        PythonActivity.mActivity,
                        "Eldritch Portals needs 'All Files Access' to read/write"
                        " .json files in Documents. Please grant it on the next screen.",
                        Toast.LENGTH_LONG)
                    toast.show()
                    Intent = autoclass('android.content.Intent')
                    Settings = autoclass('android.provider.Settings')
                    Uri = autoclass('android.net.Uri')
                    pkg = PythonActivity.mActivity.getPackageName()
                    uri = Uri.fromParts("package", pkg, None)
                    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                    intent.setData(uri)
                    PythonActivity.mActivity.startActivity(intent)
        except Exception as e:
            log(f"MANAGE_EXTERNAL_STORAGE request failed: {e}")

    def has_all_files_access():
        """Check whether the app has MANAGE_EXTERNAL_STORAGE (Android 11+).
        Returns True if yes, False if no, None if not Android or not relevant."""
        if platform != 'android':
            return None
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            Build = autoclass('android.os.Build$VERSION')
            if Build.SDK_INT < 30:
                return None
            return bool(Environment.isExternalStorageManager())
        except Exception as e:
            log(f"has_all_files_access check failed: {e}")
            return None

    def request_all_files_access():
        """Open Android settings where the user can grant 'All files access'.
        Requires Android 11+ and MANAGE_EXTERNAL_STORAGE in the manifest."""
        if platform != 'android':
            return False
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            activity = PythonActivity.mActivity
            package = activity.getPackageName()
            try:
                intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                intent.setData(Uri.parse(f"package:{package}"))
                activity.startActivity(intent)
            except Exception:
                intent = Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                activity.startActivity(intent)
            return True
        except Exception as e:
            log(f"request_all_files_access failed: {e}")
            return False

    def load_json(p, d=None):
        try:
            with open(p, 'r') as f:
                return json.load(f)
        except:
            return d if d is not None else []

    def save_json(p, d):
        try:
            with open(p, 'w') as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except:
            pass

    # === HELPER FUNCTIONS ===

    def mkbtn(text, cb=None, accent=False, danger=False, small=False, **kw):
        c = GOLD if accent else (RED if danger else TXT)
        b = RBtn(text=text, color=c, bg_color=BTN,
                 font_size=sp(11) if small else sp(13), **kw)
        if cb:
            b.bind(on_release=lambda x: cb())
        return b

    def mklbl(text, color=TXT, size=12, bold=False, h=None, wrap=False):
        kw = {'text': text, 'font_size': sp(size), 'color': color, 'bold': bold}
        if h:
            kw['size_hint_y'] = None
            kw['height'] = dp(h)
        l = Label(**kw)
        if wrap:
            l.halign = 'left'
            l.size_hint_y = None
            # Bind text_size to the label width so it adapts to rotation
            l.bind(width=lambda w, v: setattr(w, 'text_size', (v - dp(8), None)))
            l.bind(texture_size=l.setter('size'))
        return l

    def mksep(h=6):
        return Widget(size_hint_y=None, height=dp(h))

    def mkvol(callback, value=0.7):
        vr = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(10), 0])
        vr.add_widget(Label(text="Vol", color=DIM, size_hint_x=0.08, font_size=sp(10)))
        sl = Slider(min=0, max=1, value=value, size_hint_x=0.92)
        sl.bind(value=lambda s, v: callback(v))
        vr.add_widget(sl)
        return vr

    # === SERVER / CAST / PLAYERS ===
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, f, *a):
            pass

    class MediaServer:
        def __init__(self):
            self._h = None
        def start(self):
            if self._h:
                return
            try:
                h = partial(QuietHandler, directory=BASE_DIR)
                self._h = HTTPServer(('0.0.0.0', HTTP_PORT), h)
                threading.Thread(target=self._h.serve_forever, daemon=True).start()
            except:
                pass
        def stop(self):
            if self._h:
                self._h.shutdown()
                self._h = None
        @staticmethod
        def ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                r = s.getsockname()[0]
                s.close()
                return r
            except:
                return "127.0.0.1"
        def url(self, fp):
            return f"http://{self.ip()}:{HTTP_PORT}/{os.path.relpath(fp, BASE_DIR)}"

    class CastMgr:
        def __init__(self):
            self.devices = {}
            self.cc = None
            self.mc = None
            self._br = None
        def scan(self, cb=None):
            if not CAST_AVAILABLE:
                return
            self.devices = {}
            def _s():
                try:
                    ccs, br = pychromecast.get_chromecasts()
                    self._br = br
                except:
                    ccs = []
                for c in ccs:
                    self.devices[c.cast_info.friendly_name] = c
                if cb:
                    Clock.schedule_once(lambda dt: cb(list(self.devices.keys())), 0)
            threading.Thread(target=_s, daemon=True).start()
        def connect(self, name, cb=None):
            if name not in self.devices:
                return
            def _c():
                try:
                    c = self.devices[name]
                    c.wait()
                    self.cc = c
                    self.mc = c.media_controller
                    ok = True
                except:
                    ok = False
                if cb:
                    Clock.schedule_once(lambda dt: cb(ok), 0)
            threading.Thread(target=_c, daemon=True).start()
        def cast_img(self, url, cb=None):
            if not self.mc:
                return
            def _c():
                try:
                    self.mc.play_media(url, 'image/jpeg')
                    self.mc.block_until_active()
                    ok = True
                except:
                    ok = False
                if cb:
                    Clock.schedule_once(lambda dt: cb(ok), 0)
            threading.Thread(target=_c, daemon=True).start()
        def disconnect(self):
            try:
                if self._br:
                    self._br.stop_discovery()
                if self.cc:
                    self.cc.disconnect()
            except:
                pass
            self.cc = None
            self.mc = None

    class FilePicker:
        """Android Storage Access Framework file picker.

        Opens the system file picker and reads the selected file via URI —
        requires no storage permissions, works on all Android versions,
        and the user can pick from anywhere (Documents, Downloads, Google Drive, etc.).
        """
        REQUEST_CODE = 7331

        def __init__(self):
            self.callback = None
            self._activity = None
            self._bound = False

        def _ensure_bound(self):
            """Bind to Android activity-result listener."""
            if self._bound or platform != 'android':
                return
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                self._activity = PythonActivity.mActivity
                from android import activity as android_activity
                android_activity.bind(on_activity_result=self._on_result)
                self._bound = True
                log("FilePicker bound to Android activity")
            except Exception as e:
                log(f"FilePicker bind error: {e}")

        def pick(self, callback, mime_type='application/json'):
            """Open file picker. callback(ok, text_or_err) is called
            when the user has selected (or cancelled)."""
            if platform != 'android':
                callback(False, "File picker only available on Android")
                return
            self._ensure_bound()
            if not self._activity:
                callback(False, "Could not access Android activity")
                return
            self.callback = callback
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType(mime_type)
                self._activity.startActivityForResult(intent, self.REQUEST_CODE)
            except Exception as e:
                log(f"FilePicker pick error: {e}")
                callback(False, f"Could not open file picker: {e}")

        def _on_result(self, request_code, result_code, intent):
            """Received result from the file picker."""
            if request_code != self.REQUEST_CODE:
                return
            cb = self.callback
            self.callback = None
            if cb is None:
                return
            if result_code != -1 or intent is None:
                Clock.schedule_once(lambda dt: cb(False, "Cancelled"), 0)
                return
            try:
                from jnius import autoclass
                uri = intent.getData()
                if uri is None:
                    Clock.schedule_once(lambda dt: cb(False, "No file selected"), 0)
                    return
                resolver = self._activity.getContentResolver()
                stream = resolver.openInputStream(uri)
                BufferedReader = autoclass('java.io.BufferedReader')
                InputStreamReader = autoclass('java.io.InputStreamReader')
                reader = BufferedReader(InputStreamReader(stream, 'UTF-8'))
                sb = []
                line = reader.readLine()
                while line is not None:
                    sb.append(line)
                    sb.append('\n')
                    line = reader.readLine()
                reader.close()
                stream.close()
                text = ''.join(sb)
                Clock.schedule_once(lambda dt: cb(True, text), 0)
            except Exception as e:
                log(f"FilePicker read error: {e}")
                err = f"Read failed: {type(e).__name__}: {e}"
                Clock.schedule_once(lambda dt: cb(False, err), 0)

    class APlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._v = 0.7
        def play(self, path):
            self.stop()
            try:
                self.mp = MediaPlayer()
                self.mp.setDataSource(path)
                self.mp.setVolume(self._v, self._v)
                self.mp.prepare()
                self.mp.start()
                self.is_playing = True
            except:
                self.mp = None
                self.is_playing = False
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except:
                    pass
                self.mp = None
            self.is_playing = False
        def pause(self):
            if self.mp and self.is_playing:
                try:
                    self.mp.pause()
                    self.is_playing = False
                except:
                    pass
        def resume(self):
            if self.mp and not self.is_playing:
                try:
                    self.mp.start()
                    self.is_playing = True
                except:
                    pass
        def vol(self, v):
            self._v = v
            if self.mp:
                try:
                    self.mp.setVolume(v, v)
                except:
                    pass

    class SPlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._v = 0.5
        def play_url(self, url):
            self.stop()
            if not USE_JNIUS:
                return False
            def _s():
                try:
                    self.mp = MediaPlayer()
                    self.mp.setDataSource(url)
                    self.mp.setVolume(self._v, self._v)
                    self.mp.prepare()
                    self.mp.start()
                    self.is_playing = True
                    log("Stream OK")
                except Exception as e:
                    log(f"Stream err: {e}")
                    if self.mp:
                        try: self.mp.release()
                        except: pass
                        self.mp = None
                    self.is_playing = False
            threading.Thread(target=_s, daemon=True).start()
            return True
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except:
                    pass
                self.mp = None
            self.is_playing = False
        def vol(self, v):
            self._v = v
            if self.mp:
                try:
                    self.mp.setVolume(v, v)
                except:
                    pass

    class FPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader
            self.SL = SoundLoader
            self.snd = None
            self.is_playing = False
            self._v = 0.7
        def play(self, path):
            self.stop()
            self.snd = self.SL.load(path)
            if self.snd:
                self.snd.volume = self._v
                self.snd.play()
                self.is_playing = True
        def stop(self):
            if self.snd:
                try: self.snd.stop()
                except: pass
                self.snd = None
            self.is_playing = False
        def pause(self):
            if self.snd and self.is_playing:
                self.snd.stop()
                self.is_playing = False
        def resume(self):
            if self.snd and not self.is_playing:
                self.snd.play()
                self.is_playing = True
        def vol(self, v):
            self._v = v
            if self.snd:
                self.snd.volume = v

    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("=== BUILD (v0.3.2 Abyssal Purple) ===")
            Window.clearcolor = BG
            self.title = "Eldritch Portals"
            self.tracks = []
            self.ct = -1
            self.sel_img = None
            self.auto_cast = True
            self.cur_folder = IMG_DIR
            self.player = APlayer() if USE_JNIUS else FPlayer()
            self.streamer = SPlayer()
            self.cast = CastMgr()
            self.server = MediaServer()
            self.file_picker = FilePicker()
            # Characters live in app-private storage (always writable on Android)
            self.CHARS_FILE = os.path.join(self.user_data_dir, "characters.json")
            self.SCENARIO_FILE = os.path.join(self.user_data_dir, "scenario.json")
            self.chars = load_json(self.CHARS_FILE, [])
            # On first launch (no saved characters), seed from the bundled characters.json
            if not self.chars and os.path.exists(BUNDLED_CHARS):
                try:
                    with open(BUNDLED_CHARS, 'r', encoding='utf-8') as _f:
                        _data = json.load(_f)
                    if isinstance(_data, list):
                        self.chars = [ch for ch in _data
                                      if isinstance(ch, dict) and 'name' in ch]
                        if self.chars:
                            save_json(self.CHARS_FILE, self.chars)
                            log(f"Seeded {len(self.chars)} characters from bundled file")
                except Exception as _e:
                    log(f"Could not load bundled characters: {_e}")
            self.edit_idx = None
            self._chars_overlay = None
            self._chars_dim = None

            # Weapons: the favorites file lives in app-private storage (always writable)
            self.WEAPONS_FAV_FILE = os.path.join(
                self.user_data_dir, "weapons_favorites.json")
            self.weapons_data = {
                "weapons": [], "categories": {},
                "subcategories": {}, "field_labels": {}
            }
            self.weap_favorites = set(load_json(self.WEAPONS_FAV_FILE, []))
            self._weap_cat = 'all'
            self._weap_era = 'all'
            self._weap_search = ''
            self._weap_fav_only = False
            self._weap_overlay = None
            self._weap_dim = None
            self._weap_last_error = None

            # FloatLayout as root – lets us place the splash on top
            wrapper = FloatLayout()

            main = BoxLayout(orientation='vertical', spacing=0,
                             size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            main.add_widget(Widget(size_hint_y=None, height=dp(30)))

            # TABS
            tabs = RBox(size_hint_y=None, height=dp(52), spacing=dp(4),
                        padding=[dp(8), 0], bg_color=BTN)
            self._tabs = {}
            for key, txt in [('img','Images'),('snd','Sound'),('cmb','Combat'),('tool','Characters'),('rules','Rules'),('cast','Cast')]:
                active = key == 'img'
                b = RToggle(text=txt, group='tabs',
                            state='down' if active else 'normal',
                            bg_color=BTNH if active else BTN,
                            color=GOLD if active else DIM,
                            font_size=sp(11))
                b.bind(state=self._tab_color)
                b.bind(on_release=lambda x, k=key: self._tab(k))
                tabs.add_widget(b)
                self._tabs[key] = b
            main.add_widget(tabs)

            # MAIN CONTENT
            self.content = RBox(bg_color=BG2)
            main.add_widget(self.content)

            # MINI PLAYER
            mp = RBox(size_hint_y=None, height=dp(48), spacing=dp(6),
                      padding=[dp(10), dp(4)], bg_color=BTN)
            mp.add_widget(Widget(size_hint_x=None, width=dp(4)))
            self.mp_lbl = Label(text="No music", font_size=sp(11),
                                color=DIM, size_hint_x=0.45, halign='left')
            self.mp_lbl.bind(size=self.mp_lbl.setter('text_size'))
            mp.add_widget(self.mp_lbl)
            for t, cb in [("<<", self.prev_track), (">>", self.next_track)]:
                mp.add_widget(mkbtn(t, cb, small=True, size_hint_x=None, width=dp(44)))
            self.mp_btn = mkbtn("Play", self.toggle_play, accent=True,
                                small=True, size_hint_x=None, width=dp(60))
            mp.add_widget(self.mp_btn)
            main.add_widget(mp)

            self.status = Label(text="", font_size=sp(10), color=DIM,
                                size_hint_y=None, height=dp(20))
            main.add_widget(self.status)

            wrapper.add_widget(main)

            # === SPLASH SCREEN ===
            self.splash = RBox(bg_color=BG, radius=0,
                               orientation='vertical',
                               size_hint=(1, 1),
                               pos_hint={'x': 0, 'y': 0})
            # Centered content
            self.splash.add_widget(Widget())  # fyll topp
            t1 = Label(text="ELDRITCH", font_size=sp(42), color=GOLD,
                       bold=True, size_hint_y=None, height=dp(60),
                       halign='center')
            t1.bind(size=t1.setter('text_size'))
            self.splash.add_widget(t1)
            t2 = Label(text="PORTAL", font_size=sp(42), color=GDIM,
                       bold=True, size_hint_y=None, height=dp(60),
                       halign='center')
            t2.bind(size=t2.setter('text_size'))
            self.splash.add_widget(t2)
            sub = Label(text="Keeper Companion Tool", font_size=sp(13),
                        color=DIM, size_hint_y=None, height=dp(30),
                        halign='center')
            sub.bind(size=sub.setter('text_size'))
            self.splash.add_widget(sub)
            self.splash.add_widget(Widget())  # fyll bunn
            wrapper.add_widget(self.splash)

            self._tab('img')
            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            # Fade out the splash after 2.5 sec
            Clock.schedule_once(self._dismiss_splash, 2.5)
            return wrapper

        def _dismiss_splash(self, dt):
            if self.splash:
                anim = Animation(opacity=0, duration=0.8)
                def _remove(*a):
                    if self.splash.parent:
                        self.splash.parent.remove_widget(self.splash)
                    self.splash = None
                anim.bind(on_complete=_remove)
                anim.start(self.splash)

        def _tab_color(self, btn, state):
            if state == 'down':
                btn.bg_color = BTNH
                btn.color = GOLD
            else:
                btn.bg_color = BTN
                btn.color = DIM

        def _init(self):
            ensure_dirs()
            self.server.start()
            self._load_imgs()
            self._load_tracks()
            self._weap_do_load()
            self.status.text = f"IP: {MediaServer.ip()}  |  Cast: {'Yes' if CAST_AVAILABLE else 'No'}"

        def _weap_do_load(self):
            """Load weapon data. Try the external file first (the user's own),
            then fall back to the bundled version."""
            # Attempt 1: external file in /sdcard/Documents/EldritchPortal/
            if os.path.exists(EXTERNAL_WEAPONS):
                try:
                    with open(EXTERNAL_WEAPONS, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and 'weapons' in data:
                        n = len(data.get('weapons', []))
                        log(f"_weap_do_load: external OK, {n} weapons")
                        self.weapons_data = data
                        self._weap_last_error = None
                        return
                except PermissionError:
                    log("_weap_do_load: external file exists but is inaccessible, using bundled")
                except Exception as e:
                    log(f"_weap_do_load: external error ({e}), using bundled")
            # Attempt 2: bundled file (packed into the APK)
            if os.path.exists(BUNDLED_WEAPONS):
                try:
                    with open(BUNDLED_WEAPONS, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    n = len(data.get('weapons', []))
                    log(f"_weap_do_load: bundled OK, {n} weapons")
                    self.weapons_data = data
                    self._weap_last_error = None
                    return
                except Exception as e:
                    err = f"Bundled file: {type(e).__name__}: {e}"
                    log(f"_weap_do_load: {err}")
                    self._weap_last_error = err
                    return
            # No sources worked
            err = (f"Could not find weapons.json.\n"
                   f"Bundled path: {BUNDLED_WEAPONS}\n"
                   f"External path: {EXTERNAL_WEAPONS}")
            log(f"_weap_do_load: {err}")
            self._weap_last_error = err

        def _tab(self, k):
            self.content.clear_widgets()
            builders = {
                'img': self._mk_img, 'snd': self._mk_sound,
                'cmb': self._mk_combat, 'tool': self._mk_tool,
                'rules': self._mk_rules, 'cast': self._mk_cast,
            }
            if k in builders:
                self.content.add_widget(builders[k]())

        # ---------- IMAGES ----------
        def _mk_img(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            # Black background behind the preview image
            preview_box = RBox(size_hint_y=0.4, bg_color=BLK, radius=dp(12))
            self.preview = Image(allow_stretch=True, keep_ratio=True,
                                 color=[1, 1, 1, 0] if not self.sel_img else [1, 1, 1, 1])
            if self.sel_img:
                self.preview.source = self.sel_img
            preview_box.add_widget(self.preview)
            p.add_widget(preview_box)
            p.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(18), color=GDIM,
                               bold=True, size_hint_y=None, height=dp(28)))
            self.img_lbl = Label(text="", font_size=sp(12), color=DIM,
                                 size_hint_y=None, height=dp(20))
            p.add_widget(self.img_lbl)
            nav = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6), padding=[dp(6), 0])
            self.path_lbl = Label(text="", font_size=sp(10), color=DIM, size_hint_x=0.35)
            nav.add_widget(self.path_lbl)
            nav.add_widget(mkbtn("Up", self.folder_up, small=True, size_hint_x=0.2))
            self.ac_btn = mkbtn("AC:ON", self._toggle_ac, accent=True, small=True, size_hint_x=0.25)
            nav.add_widget(self.ac_btn)
            nav.add_widget(mkbtn("Refresh", self._load_imgs, small=True, size_hint_x=0.2))
            p.add_widget(nav)
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(6), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            p.add_widget(scroll)
            self._load_imgs()
            return p

        def _load_imgs(self):
            if not hasattr(self, 'img_grid'):
                return
            self.img_grid.clear_widgets()
            f = self.cur_folder
            rel = os.path.relpath(f, IMG_DIR) if f != IMG_DIR else ""
            self.path_lbl.text = f"/{rel}" if rel else "/"
            try:
                if not os.path.exists(f):
                    self.img_lbl.text = "Folder not found"
                    self.img_grid.add_widget(
                        mklbl("The folder does not exist yet.\n"
                              "Restart the app after\n"
                              "granting permissions.",
                              color=DIM, size=11, wrap=True))
                    return
                items = sorted(os.listdir(f))
                dirs = [d for d in items if os.path.isdir(os.path.join(f, d)) and not d.startswith('.')]
                imgs = [x for x in items if x.lower().endswith(IMG_EXT)]
                self.img_lbl.text = f"{len(dirs)} folders, {len(imgs)} images"
                if not dirs and not imgs:
                    self.img_grid.add_widget(
                        mklbl("No images found.\n\n"
                              "Place images in:\n"
                              "Documents/EldritchPortal/images/\n\n"
                              "Tip: create subfolders to\n"
                              "organize by scenario,\n"
                              "e.g. images/Slow Boat/\n\n"
                              "Supported formats:\n"
                              ".png  .jpg  .jpeg  .webp",
                              color=DIM, size=11, wrap=True))
                    return
                for d in dirs:
                    self.img_grid.add_widget(
                        mkbtn(f"[{d}]", lambda dn=d: self._enter(dn),
                              accent=True, small=True, size_hint_y=None, height=dp(70)))
                for fn in imgs:
                    path = os.path.join(f, fn)
                    img = Image(source=path, allow_stretch=True, keep_ratio=True,
                                size_hint_y=None, height=dp(100), mipmap=True)
                    img._path = path
                    img.bind(on_touch_down=self._img_touch)
                    self.img_grid.add_widget(img)
            except Exception as e:
                log(f"load_imgs: {e}")

        def _img_touch(self, w, touch):
            if w.collide_point(*touch.pos):
                self._sel_img(w._path)
                return True
            return False

        def _enter(self, name):
            self.cur_folder = os.path.join(self.cur_folder, name)
            self._load_imgs()

        def folder_up(self):
            if self.cur_folder != IMG_DIR:
                self.cur_folder = os.path.dirname(self.cur_folder)
                self._load_imgs()

        def _sel_img(self, path):
            self.sel_img = path
            self.img_lbl.text = os.path.basename(path)
            self.img_lbl.color = GOLD
            Animation.cancel_all(self.preview, 'opacity')
            fade_out = Animation(opacity=0, duration=0.3)
            def _swap(*a):
                self.preview.source = path
                Animation(opacity=1, duration=0.4).start(self.preview)
                if self.auto_cast and self.cast.mc:
                    self.img_lbl.text = "Casting..."
                    self.cast.cast_img(self.server.url(path),
                                       cb=lambda ok: setattr(self.img_lbl, 'text',
                                                             "Cast!" if ok else "Failed"))
            fade_out.bind(on_complete=_swap)
            self.preview.color = [1, 1, 1, 1]
            fade_out.start(self.preview)

        def _toggle_ac(self):
            self.auto_cast = not self.auto_cast
            self.ac_btn.text = f"AC:{'ON' if self.auto_cast else 'OFF'}"

        # ---------- MUSIC ----------
        def _mk_mus(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            self.trk_lbl = Label(text="Choose a track", font_size=sp(14), color=DIM,
                                 size_hint_y=None, height=dp(34), bold=True)
            p.add_widget(self.trk_lbl)
            ctrl = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            ctrl.add_widget(mkbtn("<<", self.prev_track, small=True))
            ctrl.add_widget(mkbtn("Play", self.toggle_play, accent=True))
            ctrl.add_widget(mkbtn(">>", self.next_track, small=True))
            ctrl.add_widget(mkbtn("Stop", self.stop_music, danger=True, small=True))
            p.add_widget(ctrl)
            p.add_widget(mkvol(self.player.vol, 0.7))
            scroll = ScrollView()
            self.trk_grid = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            self.trk_grid.bind(minimum_height=self.trk_grid.setter('height'))
            scroll.add_widget(self.trk_grid)
            p.add_widget(scroll)
            self._load_tracks()
            return p

        def _load_tracks(self):
            if not hasattr(self, 'trk_grid'):
                return
            self.trk_grid.clear_widgets()
            self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR):
                    self.trk_lbl.text = "Folder not found"
                    self.trk_grid.add_widget(
                        mklbl("The music folder does not exist yet.\n"
                              "Restart the app after\n"
                              "granting permissions.",
                              color=DIM, size=11, wrap=True))
                    return
                fl = sorted([f for f in os.listdir(MUSIC_DIR)
                             if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.trk_lbl.text = f"{len(fl)} tracks"
                if not fl:
                    self.trk_grid.add_widget(
                        mklbl("No music files found.\n\n"
                              "Place audio files in:\n"
                              "Documents/EldritchPortal/music/\n\n"
                              "Supported formats:\n"
                              ".mp3  .ogg  .wav  .flac",
                              color=DIM, size=11, wrap=True))
                    return
                for i, fn in enumerate(fl):
                    self.tracks.append(os.path.join(MUSIC_DIR, fn))
                    self.trk_grid.add_widget(
                        mkbtn(fn, lambda idx=i: self.play_track(idx),
                              small=True, size_hint_y=None, height=dp(42)))
            except Exception as e:
                log(f"load_tracks: {e}")

        def play_track(self, idx):
            if idx < 0 or idx >= len(self.tracks):
                return
            self.ct = idx
            self.player.play(self.tracks[idx])
            n = os.path.basename(self.tracks[idx])
            self.trk_lbl.text = f"Playing: {n}"
            self.trk_lbl.color = GOLD
            self.mp_lbl.text = n
            self.mp_btn.text = "Pause"

        def toggle_play(self):
            if not self.player.is_playing and self.ct < 0:
                if self.tracks:
                    self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause()
                self.mp_btn.text = "Play"
            else:
                self.player.resume()
                self.mp_btn.text = "Pause"

        def stop_music(self):
            self.player.stop()
            self.mp_btn.text = "Play"
            self.mp_lbl.text = "Stopped"
            self.trk_lbl.text = "Stopped"

        def next_track(self):
            if self.tracks:
                self.play_track((self.ct + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.ct - 1) % len(self.tracks))

        # ---------- AMBIENT ----------
        def _mk_amb(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                if 'url' not in snd:
                    g.add_widget(mklbl(snd['name'], color=GDIM, size=11, bold=True, h=24))
                else:
                    g.add_widget(
                        mkbtn(snd['name'],
                              lambda u=snd['url'], n=snd['name']: self._pa(u, n),
                              small=True, size_hint_y=None, height=dp(40)))
            scroll.add_widget(g)
            p.add_widget(scroll)
            p.add_widget(mkbtn("Stop Ambient", self._sa, danger=True,
                               size_hint_y=None, height=dp(44)))
            p.add_widget(mkvol(self.streamer.vol, 0.5))
            self.amb_lbl = mklbl("", color=DIM, size=11, h=20)
            p.add_widget(self.amb_lbl)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _pa(self, url, name):
            self._an = name
            self._ac = 0
            self.amb_lbl.text = f"Loading: {name}..."
            if self.streamer.play_url(url):
                Clock.schedule_interval(self._poll, 2)

        def _poll(self, dt):
            self._ac += 1
            if self.streamer.is_playing:
                self.amb_lbl.text = f"Playing: {self._an}"
                self.amb_lbl.color = GRN
                return False
            if self._ac >= 10:
                self.amb_lbl.text = f"Failed: {self._an}"
                self.amb_lbl.color = RED
                return False
            self.amb_lbl.text = f"Loading: {self._an} ({self._ac*2}s)..."
            return True

        def _sa(self):
            self.streamer.stop()
            self.amb_lbl.text = "Stopped"
            self.amb_lbl.color = DIM

        # ---------- RULES ----------
        def _mk_rules(self):
            """Collapsible folder view with an overlay for content."""
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            self._rules_expanded = set()
            self._rules_overlay = None

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(34))
            hdr.add_widget(mklbl("RULES & REFERENCE", color=GOLD, size=15, bold=True))
            p.add_widget(hdr)
            p.add_widget(mksep(2))

            # Folder list
            scroll = ScrollView()
            self._rules_tree = GridLayout(cols=1, spacing=dp(2), padding=dp(4), size_hint_y=None)
            self._rules_tree.bind(minimum_height=self._rules_tree.setter('height'))
            scroll.add_widget(self._rules_tree)
            p.add_widget(scroll)

            # Overlay container (hidden until content is opened)
            self._rules_main = p
            self._rules_build_tree()
            return p

        def _rules_build_tree(self):
            """Build the folder tree with opened/closed folders."""
            self._rules_tree.clear_widgets()
            for i, (cat_name, icon, subs) in enumerate(RULES):
                expanded = i in self._rules_expanded
                arrow = "[-]" if expanded else "[+]"
                # Folder button
                fbtn = RBtn(
                    text=f"  {arrow}  {cat_name}",
                    bg_color=BTNH if expanded else BTN,
                    color=GOLD if expanded else TXT,
                    font_size=sp(13), halign='left',
                    size_hint_y=None, height=dp(44))
                fbtn.bind(on_release=lambda x, idx=i: self._rules_toggle(idx))
                self._rules_tree.add_widget(fbtn)

                if expanded:
                    for j, (sub_name, content) in enumerate(subs):
                        n = len([l for l in content if l])
                        sbtn = RBtn(
                            text=f"       >  {sub_name}",
                            bg_color=BG2, color=TXT,
                            font_size=sp(12), halign='left',
                            size_hint_y=None, height=dp(38))
                        sbtn.bind(on_release=lambda x, ci=i, si=j: self._rules_open(ci, si))
                        self._rules_tree.add_widget(sbtn)

        def _rules_toggle(self, cat_idx):
            """Open/close a folder."""
            if cat_idx in self._rules_expanded:
                self._rules_expanded.discard(cat_idx)
            else:
                self._rules_expanded.add(cat_idx)
            self._rules_build_tree()

        def _rules_open(self, cat_idx, sub_idx):
            """Show rule content as an overlay."""
            cat_name, icon, subs = RULES[cat_idx]
            sub_name, content = subs[sub_idx]

            # Remove any existing overlay
            self._rules_close_overlay()

            # Build overlay
            overlay = RBox(bg_color=BG, radius=dp(16),
                           orientation='vertical', spacing=dp(4),
                           padding=dp(8),
                           size_hint=(0.95, 0.92),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header with close + navigation
            hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            hdr.add_widget(mkbtn("Close", self._rules_close_overlay,
                                 danger=True, small=True, size_hint_x=0.25))
            if sub_idx > 0:
                hdr.add_widget(mkbtn("<<",
                    lambda: (self._rules_close_overlay(), self._rules_open(cat_idx, sub_idx - 1)),
                    small=True, size_hint_x=None, width=dp(36)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(36)))

            hdr.add_widget(mklbl(sub_name, color=GOLD, size=13, bold=True))

            if sub_idx < len(subs) - 1:
                hdr.add_widget(mkbtn(">>",
                    lambda: (self._rules_close_overlay(), self._rules_open(cat_idx, sub_idx + 1)),
                    small=True, size_hint_x=None, width=dp(36)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(36)))
            overlay.add_widget(hdr)

            # Breadcrumb
            overlay.add_widget(mklbl(f"{cat_name}  >  {sub_name}",
                                     color=DIM, size=10, h=18))

            # Separator
            sep = Widget(size_hint_y=None, height=dp(1))
            from kivy.graphics import Color as GColor, Rectangle as GRect
            with sep.canvas:
                GColor(rgba=BTNH)
                r = GRect(pos=sep.pos, size=sep.size)
            sep.bind(pos=lambda w, v: setattr(r, 'pos', w.pos),
                     size=lambda w, v: setattr(r, 'size', w.size))
            overlay.add_widget(sep)
            overlay.add_widget(mksep(4))

            # Content
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(1), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for line in content:
                if line == "":
                    g.add_widget(mksep(10))
                elif line.startswith("  "):
                    g.add_widget(mklbl(line, color=DIM, size=12, h=20))
                else:
                    g.add_widget(mklbl(line, color=TXT, size=13, h=22))

            g.add_widget(mksep(30))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            # Place the overlay over the entire content area
            # Use the FloatLayout wrapper (root)
            root = self._rules_main
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            fl = root.parent if isinstance(root.parent, FloatLayout) else root

            # Dimmed background
            dim = Widget(size_hint=(1, 1))
            from kivy.graphics import Color as GC2, Rectangle as GR2
            with dim.canvas:
                GC2(rgba=[0, 0, 0, 0.6])
                dr = GR2(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t: self._rules_close_overlay() or True)

            self._rules_dim = dim
            self._rules_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _rules_close_overlay(self):
            """Close the rule content overlay."""
            if self._rules_overlay and self._rules_overlay.parent:
                fl = self._rules_overlay.parent
                fl.remove_widget(self._rules_overlay)
                if hasattr(self, '_rules_dim') and self._rules_dim and self._rules_dim.parent:
                    fl.remove_widget(self._rules_dim)
            self._rules_overlay = None
            self._rules_dim = None


        # ---------- CAST ----------
        def _mk_cast(self):
            p = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            if not CAST_AVAILABLE:
                p.add_widget(mklbl("Casting unavailable\npychromecast is missing", color=DIM, size=13))
                return p
            self.cast_lbl = mklbl("Not connected", color=DIM, size=13, h=30)
            p.add_widget(self.cast_lbl)
            p.add_widget(mkbtn("Search for Devices", self._scan, accent=True,
                               size_hint_y=None, height=dp(46)))
            self.cast_sp = Spinner(text="Choose device...", values=[],
                                   size_hint_y=None, height=dp(46),
                                   background_color=BTN, color=TXT)
            p.add_widget(self.cast_sp)
            r = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
            r.add_widget(mkbtn("Connect", self._cn, accent=True))
            r.add_widget(mkbtn("Disconnect", self._dc, danger=True))
            p.add_widget(r)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _scan(self):
            self.cast_lbl.text = "Searching..."
            self.cast.scan(cb=self._od)

        def _od(self, n):
            if n:
                self.cast_sp.values = n
                self.cast_sp.text = n[0]
            self.cast_lbl.text = f"Found {len(n)}" if n else "None"

        def _cn(self):
            n = self.cast_sp.text
            if not n or n == "Choose device...":
                return
            self.cast.connect(n, cb=lambda ok: setattr(
                self.cast_lbl, 'text', "Connected!" if ok else "Failed"))

        def _dc(self):
            self.cast.disconnect()
            self.cast_lbl.text = "Disconnected"

        # ---------- CHARACTERS ----------

        # ---------- SOUND (combined Music + Ambient) ----------
        def _mk_sound(self):
            """Sound tab with Music and Ambient sub-tabs."""
            if not hasattr(self, '_sound_sub'):
                self._sound_sub = 'mus'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))

            b_mus = RToggle(
                text='Music', group='sound_sub',
                state='down' if self._sound_sub == 'mus' else 'normal',
                bg_color=BTNH if self._sound_sub == 'mus' else BTN,
                color=GOLD if self._sound_sub == 'mus' else DIM,
                font_size=sp(12), bold=True)
            b_mus.bind(on_release=lambda b: self._sound_switch('mus'))
            sub_bar.add_widget(b_mus)

            b_amb = RToggle(
                text='Ambient', group='sound_sub',
                state='down' if self._sound_sub == 'amb' else 'normal',
                bg_color=BTNH if self._sound_sub == 'amb' else BTN,
                color=GOLD if self._sound_sub == 'amb' else DIM,
                font_size=sp(12), bold=True)
            b_amb.bind(on_release=lambda b: self._sound_switch('amb'))
            sub_bar.add_widget(b_amb)

            p.add_widget(sub_bar)

            self._sound_area = BoxLayout()
            p.add_widget(self._sound_area)

            self._sound_render()
            return p

        def _sound_switch(self, which):
            self._sound_sub = which
            self._sound_render()

        def _sound_render(self):
            self._sound_area.clear_widgets()
            if self._sound_sub == 'mus':
                self._sound_area.add_widget(self._mk_mus())
            else:
                self._sound_area.add_widget(self._mk_amb())

        # ---------- COMBAT ----------
        def _mk_combat(self):
            """Combat tab with sub-tabs: Initiative and Map."""
            self._init_tracker_init()
            if not hasattr(self, '_cmb_sub'):
                self._cmb_sub = 'init'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))

            b_init = RToggle(
                text='Initiative', group='cmb_sub',
                state='down' if self._cmb_sub == 'init' else 'normal',
                bg_color=BTNH if self._cmb_sub == 'init' else BTN,
                color=GOLD if self._cmb_sub == 'init' else DIM,
                font_size=sp(12), bold=True)
            b_init.bind(on_release=lambda b: self._cmb_switch('init'))
            sub_bar.add_widget(b_init)

            b_map = RToggle(
                text='Map', group='cmb_sub',
                state='down' if self._cmb_sub == 'map' else 'normal',
                bg_color=BTNH if self._cmb_sub == 'map' else BTN,
                color=GOLD if self._cmb_sub == 'map' else DIM,
                font_size=sp(12), bold=True)
            b_map.bind(on_release=lambda b: self._cmb_switch('map'))
            sub_bar.add_widget(b_map)

            p.add_widget(sub_bar)

            self._cmb_area = BoxLayout()
            p.add_widget(self._cmb_area)

            self._cmb_render()
            return p

        def _cmb_switch(self, which):
            self._cmb_sub = which
            self._cmb_render()

        def _cmb_render(self):
            """Show initiative tracker or map view."""
            self._cmb_area.clear_widgets()
            self._init_target_area = self._cmb_area
            if self._cmb_sub == 'init':
                self._mk_init_tracker()
            else:
                self._mk_cmb_map()

        def _mk_cmb_map(self):
            """Map sub-tab: open battlemap or show info if list is empty."""
            p = BoxLayout(orientation='vertical',
                          spacing=dp(10), padding=dp(12))

            if not self._init_list:
                p.add_widget(Widget())
                p.add_widget(mklbl(
                    "Add participants in the Initiative tab\n"
                    "to use the map.",
                    color=DIM, size=13, wrap=True))
                p.add_widget(Widget())
                self._cmb_area.add_widget(p)
                return

            n_pc = sum(1 for e in self._init_list if e.get('type') == 'PC')
            n_npc = sum(1 for e in self._init_list if e.get('type') == 'NPC')
            n_s = sum(1 for e in self._init_list if e.get('type') == 'S')

            info_box = RBox(orientation='vertical', bg_color=BG2,
                            size_hint_y=None, height=dp(110),
                            padding=dp(12), spacing=dp(4),
                            radius=dp(10))
            info_box.add_widget(mklbl(
                "READY FOR MAP", color=GOLD, size=13, bold=True, h=22))
            summary = []
            if n_pc:
                summary.append(f"{n_pc} investigator(s)")
            if n_npc:
                summary.append(f"{n_npc} NPC")
            if n_s:
                summary.append(f"{n_s} creature(s)")
            info_box.add_widget(mklbl(
                "  •  ".join(summary) if summary else "No participants",
                color=TXT, size=12, wrap=True))

            act_name = (self._init_list[0].get('name', '')
                        if self._init_phase == 'active'
                        and self._init_list else '')
            if act_name:
                info_box.add_widget(mklbl(
                    f"Current turn: {act_name}",
                    color=DIM, size=11, wrap=True))
            else:
                info_box.add_widget(mklbl(
                    "Go to the Initiative tab and press 'Finish' "
                    "to start the round order.",
                    color=DIM, size=10, wrap=True))
            p.add_widget(info_box)

            p.add_widget(mkbtn("Open map (fullscreen)",
                               self._bm_open, accent=True,
                               size_hint_y=None, height=dp(56)))

            p.add_widget(mklbl(
                "The map opens as a full-width overlay. "
                "Use 'Close' to return here.",
                color=DIM, size=10, wrap=True, h=40))

            p.add_widget(Widget())
            self._cmb_area.add_widget(p)

        def _mk_tool(self):
            """Character tab with sub-tabs: Characters, Weapons, and Scenario."""
            self._scen_init()
            # 'init' was a sub-tab in older versions; fall back to 'chars'
            if not hasattr(self, '_tool_sub') or self._tool_sub == 'init':
                self._tool_sub = 'chars'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))
            b_chars = RToggle(
                text='Characters', group='tool_sub',
                state='down' if self._tool_sub == 'chars' else 'normal',
                bg_color=BTNH if self._tool_sub == 'chars' else BTN,
                color=GOLD if self._tool_sub == 'chars' else DIM,
                font_size=sp(11), bold=True)
            b_chars.bind(on_release=lambda b: self._tool_switch('chars'))
            sub_bar.add_widget(b_chars)

            b_weap = RToggle(
                text='Weapons', group='tool_sub',
                state='down' if self._tool_sub == 'weap' else 'normal',
                bg_color=BTNH if self._tool_sub == 'weap' else BTN,
                color=GOLD if self._tool_sub == 'weap' else DIM,
                font_size=sp(11), bold=True)
            b_weap.bind(on_release=lambda b: self._tool_switch('weap'))
            sub_bar.add_widget(b_weap)

            b_scen = RToggle(
                text='Scenario', group='tool_sub',
                state='down' if self._tool_sub == 'scen' else 'normal',
                bg_color=BTNH if self._tool_sub == 'scen' else BTN,
                color=GOLD if self._tool_sub == 'scen' else DIM,
                font_size=sp(11), bold=True)
            b_scen.bind(on_release=lambda b: self._tool_switch('scen'))
            sub_bar.add_widget(b_scen)

            p.add_widget(sub_bar)

            self._tool_action_bar = BoxLayout(
                size_hint_y=None, height=dp(42),
                spacing=dp(6), padding=[dp(6), 0])
            p.add_widget(self._tool_action_bar)

            self.tool_area = BoxLayout()
            p.add_widget(self.tool_area)

            self._init_target_area = None

            self._tool_render_sub()
            return p

        def _tool_switch(self, which):
            self._tool_sub = which
            self._tool_render_sub()

        def _tool_render_sub(self):
            """Render the correct sub-view."""
            self._tool_action_bar.clear_widgets()
            if self._tool_sub == 'chars':
                self._tool_action_bar.add_widget(
                    mkbtn("+ New", self._new_char, accent=True,
                          size_hint_x=0.26))
                self._tool_action_bar.add_widget(
                    mkbtn("Import", self._chars_import,
                          small=True, size_hint_x=0.26))
                self._tool_action_bar.add_widget(
                    mkbtn("Export", self._chars_export,
                          small=True, size_hint_x=0.26))
                self._tool_action_bar.add_widget(
                    mklbl("Characters", color=GOLD, size=13, bold=True))
                self._show_list()
            elif self._tool_sub == 'scen':
                self._mk_scenario()
            else:
                self._mk_weapons()

        def _show_list(self):
            self.tool_area.clear_widgets()
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            if not self.chars:
                g.add_widget(mklbl("No characters yet.\nTap '+ New' to create one.",
                                   color=DIM, size=12, h=50))
            else:
                for i, ch in enumerate(self.chars):
                    nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
                    oc = ch.get('occ', '')
                    c = GRN if tp == 'PC' else GOLD
                    txt = f"[{tp}]  {nm}"
                    if oc:
                        txt += f"  -  {oc}"
                    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
                    b = mkbtn(txt, lambda idx=i: self._view_char(idx),
                              small=True, size_hint_x=0.72)
                    b.color = c
                    b.halign = 'left'
                    row.add_widget(b)
                    row.add_widget(mkbtn("Edit", lambda idx=i: self._edit_char(idx),
                                        accent=True, small=True, size_hint_x=0.28))
                    g.add_widget(row)
            scroll.add_widget(g)
            self.tool_area.add_widget(scroll)

        def _view_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Back", self._show_list, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Edit", lambda: self._edit_char(idx),
                                 accent=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Delete", lambda: self._del_char(idx),
                                 danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
            g.add_widget(mklbl(f"[{tp}]  {nm}", color=GOLD, size=18, bold=True, h=34))
            for key, lbl in CHAR_INFO:
                v = ch.get(key, '')
                if v and key not in ('name', 'type'):
                    g.add_widget(mklbl(f"{lbl}:  {v}", color=TXT, size=14, h=26))
            # Attributes with individual frames
            stats_list = [(lbl, ch[key]) for key, lbl in CHAR_STATS if ch.get(key)]
            if stats_list:
                g.add_widget(mksep(4))
                g.add_widget(mklbl("ATTRIBUTES", color=GOLD, size=13, bold=True, h=24))
                stats_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
                for lbl, val in stats_list:
                    framed = FramedBox(orientation='vertical', size_hint_x=1, padding=dp(4), spacing=dp(2))
                    framed.add_widget(Label(text=lbl, font_size=sp(10), color=GOLD, bold=True))
                    framed.add_widget(Label(text=str(val), font_size=sp(14), color=TXT, bold=True))
                    stats_row.add_widget(framed)
                g.add_widget(stats_row)
            # Derived stats with individual frames
            derived_list = [(lbl, ch[key]) for key, lbl in CHAR_DERIVED if ch.get(key)]
            if derived_list:
                g.add_widget(mksep(4))
                g.add_widget(mklbl("HP / MP / SAN / LUCK", color=GOLD, size=13, bold=True, h=24))
                derived_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
                for lbl, val in derived_list:
                    framed = FramedBox(orientation='vertical', size_hint_x=1, padding=dp(4), spacing=dp(2))
                    framed.add_widget(Label(text=lbl, font_size=sp(10), color=GOLD, bold=True))
                    framed.add_widget(Label(text=str(val), font_size=sp(14), color=TXT, bold=True))
                    derived_row.add_widget(framed)
                g.add_widget(derived_row)
            sk = ch.get('skills', {})
            if sk and isinstance(sk, dict):
                g.add_widget(mksep(4))
                g.add_widget(mklbl("SKILLS", color=GOLD, size=13, bold=True, h=24))
                for sn in sorted(sk.keys()):
                    sv = sk[sn]
                    if sv:
                        sk_txt = f"{sn}: {sv}"
                        framed = FramedBox(orientation='horizontal', size_hint_y=None, 
                                         height=dp(34), padding=dp(4), spacing=dp(4))
                        framed.add_widget(mklbl(sk_txt, color=TXT, size=12, wrap=True))
                        g.add_widget(framed)
            for key, lbl in CHAR_TEXT:
                v = ch.get(key, '')
                if v:
                    g.add_widget(mksep(4))
                    g.add_widget(mklbl(lbl.upper(), color=GOLD, size=13, bold=True, h=24))
                    g.add_widget(mklbl(str(v), color=TXT, size=13, wrap=True))
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _new_char(self):
            self.chars.append({"name": "New Character", "type": "PC", "skills": {}})
            save_json(self.CHARS_FILE, self.chars)
            self._edit_char(len(self.chars) - 1)

        def _edit_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            self.edit_idx = idx
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Save", self._save_edit, accent=True, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Cancel", self._show_list, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Skills", lambda: self._edit_skills(idx), small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._ei = {}
            g.add_widget(mklbl("BASIC INFO", color=GOLD, size=12, bold=True, h=24))
            for key, lbl in CHAR_INFO:
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                     size_hint_x=0.3, halign='right'))
                if key == 'type':
                    w = Spinner(text=ch.get(key, 'PC'), values=['PC', 'NPC'],
                                background_color=BTN, color=GOLD, font_size=sp(11), size_hint_x=0.7)
                else:
                    w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                  background_color=BTN, foreground_color=TXT,
                                  size_hint_x=0.7, padding=[dp(6), dp(4)])
                self._ei[key] = w
                row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("ATTRIBUTES", color=GOLD, size=12, bold=True, h=24))
            for i in range(0, len(CHAR_STATS), 2):
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                for j in range(2):
                    if i + j < len(CHAR_STATS):
                        key, lbl = CHAR_STATS[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                             size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(6), dp(4)], input_filter='int')
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("HP / MP / SAN / LUCK", color=GOLD, size=12, bold=True, h=24))
            for i in range(0, len(CHAR_DERIVED), 2):
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                for j in range(2):
                    if i + j < len(CHAR_DERIVED):
                        key, lbl = CHAR_DERIVED[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                             size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(6), dp(4)])
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("NOTES / GEAR", color=GOLD, size=12, bold=True, h=24))
            for key, lbl in CHAR_TEXT:
                g.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                   size_hint_y=None, height=dp(20), halign='left'))
                w = TextInput(text=str(ch.get(key, '')), font_size=sp(11), multiline=True,
                              background_color=BTN, foreground_color=TXT,
                              size_hint_y=None, height=dp(80), padding=[dp(6), dp(4)])
                self._ei[key] = w
                g.add_widget(w)
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _edit_skills(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            sk = ch.get('skills', {})
            if not isinstance(sk, dict):
                sk = {}
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Save skills", lambda: self._save_skills(idx),
                                 accent=True, small=True, size_hint_x=0.5))
            top.add_widget(mkbtn("Back", lambda: self._edit_char(idx),
                                 small=True, size_hint_x=0.5))
            p.add_widget(top)
            p.add_widget(mklbl(f"Skills: {ch.get('name', '?')}", color=GOLD, size=13, bold=True, h=26))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._sk_inputs = {}
            for sname, sdefault in SKILLS:
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
                is_spec = sname.endswith(':')
                if is_spec:
                    row.add_widget(Label(text=sname, font_size=sp(10), color=GDIM,
                                         size_hint_x=0.35, halign='right'))
                    w = TextInput(text=str(sk.get(sname, '')), hint_text="Specify + value",
                                  font_size=sp(11), multiline=False, background_color=BTN,
                                  foreground_color=TXT, size_hint_x=0.65, padding=[dp(6), dp(4)])
                    self._sk_inputs[sname] = w
                else:
                    row.add_widget(Label(text=f"{sname} ({sdefault})", font_size=sp(10),
                                         color=DIM, size_hint_x=0.65, halign='left'))
                    w = TextInput(text=str(sk.get(sname, '')), hint_text=sdefault,
                                  font_size=sp(12), multiline=False, background_color=BTN,
                                  foreground_color=TXT, size_hint_x=0.35,
                                  padding=[dp(6), dp(4)], input_filter='int')
                    self._sk_inputs[sname] = w
                row.add_widget(w)
                g.add_widget(row)
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _save_skills(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            sk = {sn: w.text.strip() for sn, w in self._sk_inputs.items() if w.text.strip()}
            self.chars[idx]['skills'] = sk
            save_json(self.CHARS_FILE, self.chars)
            self._edit_char(idx)

        def _save_edit(self):
            if self.edit_idx is None or self.edit_idx >= len(self.chars):
                return
            ch = self.chars[self.edit_idx]
            for key, w in self._ei.items():
                ch[key] = w.text if isinstance(w, (TextInput, Spinner)) else ''
            save_json(self.CHARS_FILE, self.chars)
            self._show_list()

        def _del_char(self, idx):
            if 0 <= idx < len(self.chars):
                self.chars.pop(idx)
                save_json(self.CHARS_FILE, self.chars)
                self._show_list()

        # ---------- CHARACTER IMPORT / EXPORT ----------

        def _open_char_overlay(self, overlay):
            """Attach overlay + dim to the FloatLayout root (same pattern as weapon detail)."""
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                # Fallback: add directly to tool_area
                self.tool_area.add_widget(overlay)
                self._chars_overlay = overlay
                return
            fl = root.parent

            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GColor(rgba=[0, 0, 0, 0.6])
                dr = GRect(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w_, v: setattr(dr, 'pos', w_.pos),
                     size=lambda w_, v: setattr(dr, 'size', w_.size))

            self._chars_dim = dim
            self._chars_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _chars_close_overlay(self):
            """Close any active character overlay."""
            if self._chars_overlay and self._chars_overlay.parent:
                parent = self._chars_overlay.parent
                parent.remove_widget(self._chars_overlay)
                if self._chars_dim and self._chars_dim.parent:
                    parent.remove_widget(self._chars_dim)
            self._chars_overlay = None
            self._chars_dim = None

        def _chars_show_message(self, msg, success=False):
            """Show a brief status message in an overlay."""
            self._chars_close_overlay()
            color = GRN if success else RED
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.82, None),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.height = dp(180)
            overlay.add_widget(mklbl(msg, color=color, size=13, wrap=True))
            overlay.add_widget(Widget())
            overlay.add_widget(mkbtn("OK", self._chars_close_overlay,
                                     accent=True, size_hint_y=None, height=dp(44)))
            self._open_char_overlay(overlay)

        def _chars_export(self):
            """Export the current character list to the Documents folder as characters.json."""
            if not self.chars:
                self._chars_show_message("No characters to export.")
                return
            try:
                export_path = os.path.join(BASE_DIR, "characters_export.json")
                os.makedirs(BASE_DIR, exist_ok=True)
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.chars, f, indent=2, ensure_ascii=False)
                n = len(self.chars)
                self._chars_show_message(
                    f"Exported {n} character{'s' if n != 1 else ''} to:\n{export_path}",
                    success=True)
            except Exception as e:
                self._chars_show_message(f"Export failed:\n{e}")

        def _chars_import(self):
            """Open a file chooser overlay to import a character bundle."""
            self._chars_close_overlay()
            try:
                os.makedirs(BASE_DIR, exist_ok=True)
            except Exception:
                pass
            start_path = BASE_DIR if os.path.exists(BASE_DIR) else os.path.expanduser("~")
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(4),
                padding=dp(10),
                size_hint=(0.96, 0.92),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            hdr.add_widget(mkbtn("Cancel", self._chars_close_overlay,
                                 danger=True, small=True, size_hint_x=0.3))
            hdr.add_widget(mklbl("Select .json File", color=GOLD, size=14, bold=True))
            overlay.add_widget(hdr)

            fc = FileChooserListView(
                path=start_path,
                filters=['*.json'],
                size_hint_y=1)
            overlay.add_widget(fc)

            sel_btn = mkbtn("Select", lambda: self._chars_import_selected(fc.selection),
                            accent=True, size_hint_y=None)
            sel_btn.height = dp(44)
            overlay.add_widget(sel_btn)
            self._open_char_overlay(overlay)

        def _chars_import_selected(self, selection):
            """Validate the selected .json file and show the import preview."""
            if not selection:
                self._chars_show_message("No file selected.")
                return
            path = selection[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self._chars_show_message(f"Error reading file:\n{e}")
                return
            # Auto-detect format: wrap a single character object in a list
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                self._chars_show_message(
                    "Invalid format: expected a character object or a list of characters.")
                return
            valid = [ch for ch in data if isinstance(ch, dict) and 'name' in ch]
            if not valid:
                self._chars_show_message("No valid characters found in file.")
                return
            self._chars_close_overlay()
            self._chars_show_import_preview(valid)

        def _chars_show_import_preview(self, chars_to_import):
            """Show a preview of characters to import with Merge/Replace options."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(6),
                padding=dp(12),
                size_hint=(0.94, 0.90),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            hdr.add_widget(mkbtn("Cancel", self._chars_close_overlay,
                                 danger=True, small=True, size_hint_x=0.3))
            hdr.add_widget(mklbl("Import Preview", color=GOLD, size=14, bold=True))
            overlay.add_widget(hdr)

            n = len(chars_to_import)
            overlay.add_widget(mklbl(
                f"{n} character{'s' if n != 1 else ''} found:",
                color=TXT, size=13, h=28))

            scroll = ScrollView(size_hint_y=1)
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for ch in chars_to_import[:20]:
                nm = ch.get('name', '?')
                tp = ch.get('type', 'PC')
                oc = ch.get('occ', '')
                txt = f"[{tp}]  {nm}"
                if oc:
                    txt += f"  —  {oc}"
                c = GRN if tp == 'PC' else GOLD
                lbl = mklbl(txt, color=c, size=12, h=28)
                g.add_widget(lbl)
            if n > 20:
                g.add_widget(mklbl(f"... and {n - 20} more", color=DIM, size=11, h=22))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            overlay.add_widget(mksep(4))
            btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            btns.add_widget(mkbtn(
                "Add to existing",
                lambda: self._chars_do_import(chars_to_import, replace=False),
                accent=True, small=True))
            btns.add_widget(mkbtn(
                "Replace all",
                lambda: self._chars_do_import(chars_to_import, replace=True),
                danger=True, small=True))
            overlay.add_widget(btns)
            self._open_char_overlay(overlay)

        def _chars_do_import(self, chars_to_import, replace=False):
            """Apply the import, save, and refresh the character list."""
            if replace:
                self.chars = list(chars_to_import)
            else:
                self.chars.extend(chars_to_import)
            save_json(self.CHARS_FILE, self.chars)
            n = len(chars_to_import)
            verb = "Replaced all with" if replace else "Added"
            self._chars_close_overlay()
            self._chars_show_message(
                f"{verb} {n} character{'s' if n != 1 else ''}.",
                success=True)
            self._show_list()

        # ---------- INITIATIVE TRACKER (CoC / Pulp Cthulhu) ----------
        def _init_tracker_init(self):
            """Initialize state for the initiative tracker."""
            if not hasattr(self, '_init_phase'):
                self._init_phase = 'setup'
                self._init_list = []
            if not hasattr(self, '_init_target_area'):
                self._init_target_area = None

        def _init_area(self):
            """Return the current container for the initiative UI."""
            tgt = getattr(self, '_init_target_area', None)
            if tgt is not None:
                return tgt
            return self.tool_area

        def _mk_init_tracker(self):
            """Build the initiative tracker UI."""
            self._init_tracker_init()
            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            if self._init_phase == 'setup':
                self._init_build_setup(p)
            else:
                self._init_build_active(p)

            area.add_widget(p)

        def _init_build_setup(self, p):
            """Setup phase: choose participants and adjust DEX values."""
            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("+ Investigator", self._init_show_char_picker,
                                 accent=True, small=True, size_hint_x=0.37))
            top.add_widget(mkbtn("+ Creature", self._init_show_enemy_picker,
                                 small=True, size_hint_x=0.33))
            top.add_widget(mkbtn("Clear", self._init_clear_list,
                                 danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)

            p.add_widget(mklbl(
                "DEX determines order. +50 if using a handgun.",
                color=DIM, size=10, h=18))

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            if not self._init_list:
                g.add_widget(mklbl(
                    "No participants. Use the buttons above.",
                    color=DIM, size=12, h=60))
            else:
                # Header
                hdr = BoxLayout(size_hint_y=None, height=dp(22),
                                spacing=dp(4))
                hdr.add_widget(mklbl("Name", color=GDIM, size=9, h=20))
                hdr.add_widget(Label(text="DEX", font_size=sp(9),
                                     color=GDIM, size_hint_x=None,
                                     width=dp(50)))
                hdr.add_widget(Label(text="+50", font_size=sp(9),
                                     color=GDIM, size_hint_x=None,
                                     width=dp(34)))
                hdr.add_widget(Label(text="", size_hint_x=None,
                                     width=dp(36)))
                g.add_widget(hdr)

                self._init_inputs = []
                for i, entry in enumerate(self._init_list):
                    row_box = RBox(orientation='horizontal', bg_color=BG2,
                                   size_hint_y=None, height=dp(44),
                                   padding=dp(6), spacing=dp(4), radius=dp(8))

                    # Type chip (PC/NPC/S = creature)
                    tp = entry.get('type', 'PC')
                    chip_color = GRN if tp == 'PC' else (GOLD if tp == 'NPC' else RED)
                    chip = Label(text=tp, font_size=sp(10), color=chip_color,
                                 bold=True, size_hint_x=None, width=dp(36))
                    row_box.add_widget(chip)

                    # Name + base DEX hint
                    nm = entry.get('name', '?')
                    base_dex = entry.get('base_dex', 0)
                    hint = f"  (base {base_dex})" if base_dex else ""
                    nm_lb = Label(text=f"{nm}{hint}",
                                  font_size=sp(12), color=TXT,
                                  halign='left', valign='middle')
                    nm_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                    row_box.add_widget(nm_lb)

                    # DEX value (editable)
                    dex_val = str(entry.get('dex', entry.get('base_dex', 0)))
                    dex_inp = TextInput(
                        text=dex_val, font_size=sp(13), multiline=False,
                        background_color=INPUT, foreground_color=TXT,
                        cursor_color=GOLD,
                        size_hint_x=None, width=dp(50),
                        padding=[dp(4), dp(6)],
                        input_filter='int')
                    dex_inp._init_idx = i
                    dex_inp.bind(text=self._init_on_dex_change)
                    self._init_inputs.append(dex_inp)
                    row_box.add_widget(dex_inp)

                    # +50 firearms toggle
                    fa_tog = RToggle(
                        text='X' if entry.get('firearms') else '',
                        state='down' if entry.get('firearms') else 'normal',
                        color=GOLD if entry.get('firearms') else DIM,
                        bg_color=BTNH if entry.get('firearms') else INPUT,
                        font_size=sp(11), bold=True,
                        size_hint_x=None, width=dp(34))
                    fa_tog._init_idx = i
                    fa_tog.bind(state=self._init_on_firearms_change)
                    row_box.add_widget(fa_tog)

                    # Remove button
                    del_btn = RBtn(text='X', bg_color=BTN, color=RED,
                                   font_size=sp(11), bold=True,
                                   size_hint_x=None, width=dp(36))
                    del_btn.bind(on_release=lambda b, idx=i:
                                 self._init_remove_entry(idx))
                    row_box.add_widget(del_btn)

                    g.add_widget(row_box)

            scroll.add_widget(g)
            p.add_widget(scroll)

            bottom = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            bottom.add_widget(mkbtn("Map", self._bm_open,
                                    small=True, size_hint_x=0.4))
            bottom.add_widget(mkbtn("Finish", self._init_finish,
                                    accent=True, size_hint_x=0.6))
            p.add_widget(bottom)

        def _init_on_dex_change(self, inst, value):
            """Save DEX value."""
            idx = inst._init_idx
            if 0 <= idx < len(self._init_list):
                try:
                    self._init_list[idx]['dex'] = int(value) if value else 0
                except ValueError:
                    self._init_list[idx]['dex'] = 0

        def _init_on_firearms_change(self, inst, value):
            """Update the +50 firearms toggle."""
            idx = inst._init_idx
            if 0 <= idx < len(self._init_list):
                on = (value == 'down')
                self._init_list[idx]['firearms'] = on
                inst.text = 'X' if on else ''
                inst.color = GOLD if on else DIM
                inst.bg_color = BTNH if on else INPUT

        def _init_show_char_picker(self):
            """Show the investigator picker."""
            already_in = {e.get('name', '') for e in self._init_list}
            pcs = [ch for ch in self.chars
                   if ch.get('type', 'PC') == 'PC'
                   and ch.get('name', '') not in already_in]
            npcs = [ch for ch in self.chars
                    if ch.get('type', 'PC') == 'NPC'
                    and ch.get('name', '') not in already_in]

            self._init_area().clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Back", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Choose character", color=GOLD, size=13,
                                 bold=True))
            p.add_widget(top)

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            if pcs:
                g.add_widget(mklbl("INVESTIGATORS (PC)",
                                   color=GRN, size=11, bold=True, h=22))
                for ch in pcs:
                    g.add_widget(self._init_make_char_btn(ch))

            if npcs:
                g.add_widget(mklbl("NPCS",
                                   color=GOLD, size=11, bold=True, h=22))
                for ch in npcs:
                    g.add_widget(self._init_make_char_btn(ch))

            if not pcs and not npcs:
                g.add_widget(mklbl(
                    "No available characters.\n"
                    "Add characters under the 'Characters' tab first.",
                    color=DIM, size=11, h=60))

            scroll.add_widget(g)
            p.add_widget(scroll)
            self._init_area().add_widget(p)

        def _init_make_char_btn(self, ch):
            """Create a button for a character in the picker list."""
            nm = ch.get('name', '?')
            occ = ch.get('occ', '')
            dex = ch.get('dex', '')
            parts = []
            if occ:
                parts.append(occ)
            if dex:
                parts.append(f"DEX {dex}")
            sub = "  -  ".join(parts)
            txt = f"{nm}   {sub}" if sub else nm
            b = mkbtn(txt, lambda c=ch: self._init_add_character(c),
                      small=True)
            b.halign = 'left'
            b.size_hint_y = None
            b.height = dp(42)
            return b

        def _init_add_character(self, ch):
            """Add a character to the initiative list."""
            try:
                dex = int(ch.get('dex', 0) or 0)
            except (ValueError, TypeError):
                dex = 0
            self._init_list.append({
                'name': ch.get('name', '?'),
                'type': ch.get('type', 'PC'),
                'base_dex': dex,
                'dex': dex,
                'firearms': False,
                'hp': ch.get('hp', ''),
            })
            self._mk_init_tracker()

        # Common enemies and creatures from Call of Cthulhu / Pulp Cthulhu.
        # (name, DEX, HP)
        COMMON_ENEMIES = [
            # --- Humans ---
            ("Cultist", 55, 11),
            ("Cult Leader", 65, 12),
            ("Mercenary", 65, 13),
            ("Bandit", 50, 10),
            ("Police Officer", 55, 12),
            ("Detective", 60, 12),
            ("Soldier", 60, 13),
            ("Officer", 65, 14),
            ("Mad Scientist", 50, 10),
            ("Priestess", 55, 11),
            ("Thief", 70, 10),
            ("Brute", 55, 14),
            ("Mystic", 60, 10),
            ("Necromancer", 55, 11),
            ("Spy", 70, 11),
            # --- Ordinary animals ---
            ("Guard Dog", 60, 8),
            ("Wolf", 75, 11),
            ("Bear", 50, 19),
            ("Puma", 85, 12),
            ("Venomous Snake", 85, 4),
            ("Large Rat", 60, 2),
            ("Rat Swarm", 90, 35),
            ("Crocodile", 50, 14),
            ("Shark", 80, 18),
            # --- Undead ---
            ("Zombie", 45, 12),
            ("Ghoul", 65, 13),
            ("Mummy", 50, 18),
            ("Vampire", 80, 15),
            ("Skeleton", 55, 10),
            ("Ghost (spectre)", 70, 0),
            # --- Lesser Mythos creatures ---
            ("Byakhee", 50, 11),
            ("Chthonian (young)", 20, 42),
            ("Chthonian (adult)", 15, 85),
            ("Deep One", 45, 15),
            ("Deep One Hybrid", 60, 12),
            ("Dark Young (Shub-Niggurath)", 45, 60),
            ("Dimensional Shambler", 45, 25),
            ("Dhole", 30, 120),
            ("Fire Vampire", 45, 12),
            ("Flying Polyp", 70, 55),
            ("Formless Spawn", 60, 30),
            ("Ghast", 75, 18),
            ("Ghoul (Mythos)", 65, 13),
            ("Gnorri", 40, 15),
            ("Hound of Tindalos", 90, 34),
            ("Hunting Horror", 75, 46),
            ("Lloigor", 60, 25),
            ("Mi-Go", 55, 13),
            ("Moon-Beast", 50, 42),
            ("Nightgaunt", 65, 12),
            ("Rat-Thing", 80, 4),
            ("Sand-Dweller", 55, 14),
            ("Servant of Glaaki", 35, 18),
            ("Serpent Person", 65, 12),
            ("Shantak", 45, 40),
            ("Shoggoth", 25, 100),
            ("Shoggoth (lesser)", 25, 65),
            ("Spawn of Cthulhu", 40, 60),
            ("Star Vampire", 75, 36),
            ("Star Spawn of Cthulhu", 30, 135),
            ("Tcho-Tcho", 70, 11),
            ("Wendigo", 60, 65),
            ("Winged One (of Yuggoth)", 55, 14),
            ("Y'm-bhi (awakened ghoul)", 55, 14),
            # --- Independent beings ---
            ("Elder Thing", 45, 28),
            ("Great Race of Yith", 25, 25),
            ("Yithian (in human host)", 50, 13),
            # --- Pulp-specific gangsters / pulp enemies ---
            ("Gangster (goon)", 55, 12),
            ("Gangster (boss)", 60, 14),
            ("Nazi Officer", 65, 13),
            ("Nazi Soldier", 60, 12),
            ("SS Occultist", 65, 13),
            ("Pulp Villain (mastermind)", 75, 15),
            ("Femme fatale", 75, 11),
            ("Private Investigator (Pulp)", 70, 13),
        ]

        def _init_show_enemy_picker(self):
            """Show a list of CoC enemies and creatures + custom entry."""
            self._init_area().clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Back", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Choose creature", color=GOLD, size=13,
                                 bold=True))
            p.add_widget(top)

            # Custom
            cust_box = RBox(orientation='vertical', bg_color=BG2,
                            size_hint_y=None, height=dp(110),
                            padding=dp(10), spacing=dp(6), radius=dp(10))
            cust_box.add_widget(mklbl("Custom creature",
                                      color=GOLD, size=11, bold=True, h=18))

            name_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            name_row.add_widget(Label(text="Name:", font_size=sp(11),
                                      color=DIM, size_hint_x=0.2,
                                      halign='right', valign='middle'))
            self._init_custom_name = TextInput(
                text='', font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, padding=[dp(8), dp(6)],
                size_hint_x=0.8)
            name_row.add_widget(self._init_custom_name)
            cust_box.add_widget(name_row)

            stat_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            stat_row.add_widget(Label(text="DEX:", font_size=sp(11),
                                      color=DIM, size_hint_x=0.2,
                                      halign='right', valign='middle'))
            self._init_custom_dex = TextInput(
                text='50', font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, padding=[dp(8), dp(6)],
                size_hint_x=0.2, input_filter='int')
            stat_row.add_widget(self._init_custom_dex)

            stat_row.add_widget(Widget(size_hint_x=0.1))
            add_btn = mkbtn("Add", self._init_add_custom,
                            accent=True, small=True, size_hint_x=0.5)
            stat_row.add_widget(add_btn)
            cust_box.add_widget(stat_row)

            p.add_widget(cust_box)

            p.add_widget(mklbl("CoC & Pulp Cthulhu creatures",
                               color=GOLD, size=11, bold=True, h=22))

            scroll = ScrollView()
            g = GridLayout(cols=2, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for name, dex, hp in self.COMMON_ENEMIES:
                txt = f"{name} ({dex})"
                b = mkbtn(txt,
                          lambda n=name, d=dex, h=hp:
                              self._init_add_enemy(n, d, h),
                          small=True)
                b.size_hint_y = None
                b.height = dp(42)
                b.halign = 'left'
                b.font_size = sp(10)
                g.add_widget(b)

            scroll.add_widget(g)
            p.add_widget(scroll)
            self._init_area().add_widget(p)

        def _init_add_enemy(self, name, dex, hp):
            """Add an enemy from the list. Increment if duplicate."""
            final_name = name
            existing = [e.get('name', '') for e in self._init_list]
            if final_name in existing:
                n = 2
                while f"{name} {n}" in existing:
                    n += 1
                final_name = f"{name} {n}"

            self._init_list.append({
                'name': final_name,
                'type': 'S',
                'base_dex': dex,
                'dex': dex,
                'firearms': False,
                'hp': str(hp) if hp else '',
            })
            self._mk_init_tracker()

        def _init_add_custom(self):
            """Add a custom creature."""
            name = self._init_custom_name.text.strip()
            if not name:
                return
            try:
                dex = int(self._init_custom_dex.text or '0')
            except ValueError:
                dex = 0
            self._init_add_enemy(name, dex, '')

        def _init_remove_entry(self, idx):
            """Remove a participant from the list."""
            if 0 <= idx < len(self._init_list):
                self._init_list.pop(idx)
                self._mk_init_tracker()

        def _init_clear_list(self):
            """Clear the entire list."""
            self._init_list = []
            self._init_phase = 'setup'
            self._mk_init_tracker()

        def _init_finish(self):
            """Move from setup to active: sort by effective DEX."""
            # Effective DEX = DEX + 50 if firearms
            for entry in self._init_list:
                base = entry.get('dex', 0)
                entry['effective'] = base + (50 if entry.get('firearms') else 0)
            # Sort highest first (CoC rule: highest DEX goes first)
            # Tiebreaker: higher base DEX, then alphabetical name
            self._init_list.sort(
                key=lambda e: (e.get('effective', 0),
                               e.get('base_dex', 0),
                               e.get('name', '')),
                reverse=True)
            self._init_phase = 'active'
            self._mk_init_tracker()

        def _init_build_active(self, p):
            """Active phase: show sorted order."""
            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("New Round", self._init_new_encounter,
                                 danger=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Edit", self._init_back_to_setup,
                                 small=True, size_hint_x=0.25))
            top.add_widget(mkbtn("Map", self._bm_open,
                                 accent=True, small=True, size_hint_x=0.25))
            top.add_widget(mklbl("Turn", color=GOLD, size=12, bold=True))
            p.add_widget(top)

            p.add_widget(mklbl(
                "Tap the active entry (top) to end its turn.",
                color=DIM, size=10, h=18))

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for i, entry in enumerate(self._init_list):
                is_active = (i == 0)

                bg = BTNH if is_active else BG2
                box = RBox(orientation='horizontal',
                           bg_color=bg,
                           size_hint_y=None,
                           height=dp(56) if is_active else dp(46),
                           padding=dp(10), spacing=dp(8), radius=dp(10))

                # Large effective DEX
                eff = entry.get('effective', entry.get('dex', 0))
                eff_lb = Label(
                    text=str(eff),
                    font_size=sp(18) if is_active else sp(15),
                    color=GOLD if is_active else TXT,
                    bold=True,
                    size_hint_x=None, width=dp(46),
                    halign='center', valign='middle')
                eff_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                box.add_widget(eff_lb)

                # Type chip
                tp = entry.get('type', 'PC')
                chip_color = GRN if tp == 'PC' else (GOLD if tp == 'NPC' else RED)
                chip = Label(text=tp, font_size=sp(10), color=chip_color,
                             bold=True,
                             size_hint_x=None, width=dp(30))
                box.add_widget(chip)

                # Name + firearms marker
                nm = entry.get('name', '?')
                if entry.get('firearms'):
                    nm_display = f"{nm}  [+50]"
                else:
                    nm_display = nm
                nm_lb = Label(
                    text=nm_display,
                    font_size=sp(15) if is_active else sp(12),
                    color=TXT,
                    bold=is_active,
                    halign='left', valign='middle')
                nm_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                box.add_widget(nm_lb)

                # HP
                hp = entry.get('hp', '')
                if hp:
                    hp_lb = Label(text=f"HP {hp}", font_size=sp(10),
                                  color=DIM,
                                  size_hint_x=None, width=dp(70),
                                  halign='right', valign='middle')
                    hp_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                    box.add_widget(hp_lb)

                if is_active:
                    box.bind(on_touch_down=lambda w, t, idx=i:
                             self._init_on_card_touch(w, t, idx))

                g.add_widget(box)

            scroll.add_widget(g)
            p.add_widget(scroll)

        def _init_on_card_touch(self, widget, touch, idx):
            """Tapping the top card ends that turn."""
            if not widget.collide_point(*touch.pos):
                return False
            if idx == 0:
                top_entry = self._init_list.pop(0)
                self._init_list.append(top_entry)
                self._mk_init_tracker()
                return True
            return False

        def _init_new_encounter(self):
            """Clear the list and go back to setup."""
            self._init_list = []
            self._init_phase = 'setup'
            self._mk_init_tracker()

        def _init_back_to_setup(self):
            """Go back to setup - keep the list."""
            self._init_phase = 'setup'
            self._mk_init_tracker()


        # ---------- BATTLE MAP ----------
        BM_SIZE = 15  # 15x15 grid

        def _bm_open(self):
            """Open the battle map as an overlay. Sync tokens from the initiative list."""
            if not self._init_list:
                # No participants yet
                return
            self._bm_tokens = {}       # (x, y) -> token dict
            self._bm_unplaced = []     # tokens that are not placed
            self._bm_selected = None   # (x, y) or None
            self._bm_placing = None    # token currently held for placement
            self._bm_overlay = None
            self._bm_dim = None
            self._bm_sync_from_init()
            self._bm_build_overlay()

        def _bm_find_mov(self, name, tp):
            """Find MOV for a character, default 8."""
            if tp in ('PC', 'NPC'):
                for ch in self.chars:
                    if ch.get('name') == name:
                        try:
                            return int(ch.get('move', 8) or 8)
                        except (ValueError, TypeError):
                            return 8
            return 8

        def _bm_sync_from_init(self):
            """Generate the token list from the initiative list."""
            pc_n = 1
            npc_n = 1
            en_n = 1
            for entry in self._init_list:
                tp = entry.get('type', 'PC')
                if tp == 'PC':
                    label = f"P{pc_n}"
                    pc_n += 1
                elif tp == 'NPC':
                    label = f"N{npc_n}"
                    npc_n += 1
                else:
                    label = f"E{en_n}"
                    en_n += 1
                self._bm_unplaced.append({
                    'label': label,
                    'name': entry.get('name', '?'),
                    'type': tp,
                    'mov': self._bm_find_mov(
                        entry.get('name', ''), tp),
                    'used_mov': 0,
                    'hp': entry.get('hp', ''),
                })

        def _bm_build_overlay(self):
            """Build the overlay widget."""
            self._bm_close_overlay()

            overlay = RBox(
                bg_color=BG, radius=dp(12),
                orientation='vertical', spacing=dp(4),
                padding=dp(6),
                size_hint=(0.98, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(40),
                            spacing=dp(4))
            hdr.add_widget(mkbtn("Close", self._bm_close_overlay,
                                 danger=True, small=True,
                                 size_hint_x=0.22))
            self._bm_active_lbl = mklbl(
                "", color=GOLD, size=12, bold=True)
            hdr.add_widget(self._bm_active_lbl)
            hdr.add_widget(mkbtn("Next", self._bm_next_turn,
                                 accent=True, small=True,
                                 size_hint_x=0.25))
            overlay.add_widget(hdr)

            # Unplaced row
            self._bm_unp_label = mklbl(
                "", color=DIM, size=10, h=20)
            overlay.add_widget(self._bm_unp_label)

            self._bm_unp_scroll = ScrollView(
                size_hint_y=None, height=dp(44),
                do_scroll_y=False)
            self._bm_unp_row = BoxLayout(
                size_hint_x=None, spacing=dp(4),
                padding=[dp(2), 0])
            self._bm_unp_row.bind(
                minimum_width=self._bm_unp_row.setter('width'))
            self._bm_unp_scroll.add_widget(self._bm_unp_row)
            overlay.add_widget(self._bm_unp_scroll)

            # The grid itself — wrapped in a ScrollView so
            # it fills the space without requiring a perfect square
            grid_wrap = BoxLayout(padding=dp(2))
            self._bm_grid = GridLayout(
                cols=self.BM_SIZE, rows=self.BM_SIZE,
                spacing=dp(1))
            self._bm_cells = {}
            for y in range(self.BM_SIZE):
                for x in range(self.BM_SIZE):
                    btn = Button(
                        text='',
                        background_normal='',
                        background_down='',
                        background_color=BG2,
                        font_size=sp(9),
                        bold=True,
                        color=[1, 1, 1, 1])
                    btn.bind(on_release=lambda b, _x=x, _y=y:
                             self._bm_tap(_x, _y))
                    self._bm_cells[(x, y)] = btn
                    self._bm_grid.add_widget(btn)
            grid_wrap.add_widget(self._bm_grid)
            overlay.add_widget(grid_wrap)

            # Status and bottom buttons
            self._bm_status = mklbl(
                "Tap a token in 'To Place' to begin.",
                color=DIM, size=10, h=22, wrap=True)
            overlay.add_widget(self._bm_status)

            btm = BoxLayout(size_hint_y=None, height=dp(38),
                            spacing=dp(4))
            btm.add_widget(mkbtn(
                "Back to Pool", self._bm_unplace_selected,
                small=True, size_hint_x=0.5))
            btm.add_widget(mkbtn(
                "Clear Map", self._bm_clear,
                danger=True, small=True, size_hint_x=0.5))
            overlay.add_widget(btm)

            # Add the overlay to the FloatLayout root
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                self.tool_area.add_widget(overlay)
                self._bm_overlay = overlay
                self._bm_render()
                return
            fl = root.parent

            from kivy.graphics import Color as GCbm, Rectangle as GRbm
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCbm(rgba=[0, 0, 0, 0.75])
                dr = GRbm(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            # Note: no "close on dim-tap" — we do not want to risk
            # the user closing the map by accident in the middle of combat.

            self._bm_dim = dim
            self._bm_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

            self._bm_render()

        def _bm_close_overlay(self):
            """Close the battle map overlay."""
            ov = getattr(self, '_bm_overlay', None)
            if ov and ov.parent:
                parent = ov.parent
                parent.remove_widget(ov)
                dim = getattr(self, '_bm_dim', None)
                if dim and dim.parent:
                    parent.remove_widget(dim)
            self._bm_overlay = None
            self._bm_dim = None

        def _bm_token_color(self, tp, is_selected=False,
                            is_active_turn=False):
            """Color for a token based on type and state."""
            if tp == 'PC':
                base = [0.25, 0.58, 0.32, 1]  # GRN
            elif tp == 'NPC':
                base = [0.78, 0.60, 0.18, 1]  # muted gold
            else:
                base = [0.60, 0.18, 0.20, 1]  # dark red
            if is_selected:
                base = [min(1, c * 1.5) for c in base[:3]] + [1]
            elif is_active_turn:
                base = [min(1, c * 1.2) for c in base[:3]] + [1]
            return base

        def _bm_active_name(self):
            """Who has the current turn right now (first in the initiative list)?"""
            if self._init_list:
                return self._init_list[0].get('name', '')
            return ''

        def _bm_render(self):
            """Render the entire map based on state."""
            # Update active label
            act = self._bm_active_name()
            if act:
                self._bm_active_lbl.text = f"Turn: {act}"
            else:
                self._bm_active_lbl.text = ""

            # Rebuild unplaced row
            self._bm_unp_row.clear_widgets()
            placing_label = None
            if self._bm_placing:
                placing_label = self._bm_placing.get('label', '')
            for tok in self._bm_unplaced:
                lbl = tok.get('label', '?')
                is_holding = (lbl == placing_label)
                b = RBtn(
                    text=lbl,
                    bg_color=BTNH if is_holding else (
                        self._bm_token_color(tok.get('type', 'PC'))),
                    color=GOLD if is_holding else [1, 1, 1, 1],
                    font_size=sp(12), bold=True,
                    size_hint_x=None, width=dp(54),
                    size_hint_y=None, height=dp(40))
                b.bind(on_release=lambda x, t=tok:
                       self._bm_hold_for_place(t))
                self._bm_unp_row.add_widget(b)

            n_unp = len(self._bm_unplaced)
            if n_unp == 0 and not self._bm_placing:
                self._bm_unp_label.text = "All placed."
            elif placing_label:
                self._bm_unp_label.text = (
                    f"Holding: {placing_label} — "
                    f"tap an empty cell to place it.")
            else:
                self._bm_unp_label.text = (
                    f"To Place ({n_unp}): tap to select.")

            # Calculate valid move cells if a token is selected
            valid_moves = set()
            sel = self._bm_selected
            if sel is not None:
                tok = self._bm_tokens.get(sel)
                if tok:
                    mov = tok.get('mov', 8)
                    used = tok.get('used_mov', 0)
                    remaining = max(0, mov - used)
                    sx, sy = sel
                    if remaining > 0:
                        for y in range(self.BM_SIZE):
                            for x in range(self.BM_SIZE):
                                if (x, y) == (sx, sy):
                                    continue
                                dist = max(abs(x - sx), abs(y - sy))
                                if dist <= remaining:
                                    valid_moves.add((x, y))

            # Draw each cell
            act_name = act
            for (x, y), btn in self._bm_cells.items():
                tok = self._bm_tokens.get((x, y))
                is_sel = (x, y) == sel
                can_move = (x, y) in valid_moves and tok is None
                can_place = (self._bm_placing is not None
                             and tok is None)
                if tok:
                    btn.text = tok['label']
                    is_active = (tok.get('name') == act_name
                                 and act_name)
                    btn.background_color = self._bm_token_color(
                        tok.get('type', 'PC'),
                        is_selected=is_sel,
                        is_active_turn=is_active)
                    btn.color = [1, 1, 1, 1]
                    btn.font_size = sp(10)
                else:
                    btn.text = ''
                    if can_move:
                        btn.background_color = [0.15, 0.32, 0.18, 1]
                    elif can_place:
                        btn.background_color = [0.25, 0.18, 0.22, 1]
                    else:
                        btn.background_color = BG2

            # Status text
            if self._bm_placing:
                lb = self._bm_placing.get('label', '?')
                nm = self._bm_placing.get('name', '?')
                self._bm_status.text = (
                    f"Placing {lb} ({nm}) — tap an empty cell.")
            elif sel is not None:
                tok = self._bm_tokens.get(sel)
                if tok:
                    lb = tok.get('label', '?')
                    nm = tok.get('name', '?')
                    mv = tok.get('mov', 8)
                    used = tok.get('used_mov', 0)
                    remaining = max(0, mv - used)
                    hp = tok.get('hp', '')
                    hp_s = f" HP {hp}" if hp else ""
                    if remaining <= 0:
                        self._bm_status.text = (
                            f"Selected: {lb} ({nm}) — MOV spent "
                            f"({used}/{mv}). Tap 'Next' for a new round."
                            f"{hp_s}")
                    else:
                        self._bm_status.text = (
                            f"Selected: {lb} ({nm}) — MOV {remaining} left "
                            f"({used}/{mv} used).{hp_s}")
                else:
                    self._bm_status.text = ""
            else:
                self._bm_status.text = (
                    "Tap a token to select and move it.")

        def _bm_hold_for_place(self, tok):
            """Select a token for placement (from the unplaced row)."""
            # Toggle: tap again = release
            if self._bm_placing and \
               self._bm_placing.get('label') == tok.get('label'):
                self._bm_placing = None
            else:
                self._bm_placing = tok
                self._bm_selected = None
            self._bm_render()

        def _bm_tap(self, x, y):
            """Handle a tap on a cell."""
            cell = (x, y)
            tok_here = self._bm_tokens.get(cell)

            # Mode 1: placing a token from the unplaced pool
            if self._bm_placing:
                if tok_here:
                    # Cell occupied — do not move, just show a message
                    self._bm_status.text = (
                        "That cell is occupied. Choose an empty one.")
                    return
                # Place the token here
                self._bm_tokens[cell] = self._bm_placing
                self._bm_unplaced = [
                    t for t in self._bm_unplaced
                    if t.get('label') !=
                    self._bm_placing.get('label')]
                self._bm_placing = None
                self._bm_render()
                return

            # Mode 2: no active selection — select token here
            if self._bm_selected is None:
                if tok_here:
                    self._bm_selected = cell
                    self._bm_render()
                return

            # Mode 3: token was already selected
            sel = self._bm_selected
            if cell == sel:
                # Tap selected token again = clear selection
                self._bm_selected = None
                self._bm_render()
                return

            if tok_here:
                # Switch selection to another token
                self._bm_selected = cell
                self._bm_render()
                return

            # Move the selected token here if within remaining MOV
            sel_tok = self._bm_tokens.get(sel)
            if not sel_tok:
                self._bm_selected = None
                self._bm_render()
                return
            mov = sel_tok.get('mov', 8)
            used = sel_tok.get('used_mov', 0)
            remaining = max(0, mov - used)
            sx, sy = sel
            dist = max(abs(x - sx), abs(y - sy))
            if remaining <= 0:
                self._bm_status.text = (
                    f"MOV spent ({used}/{mov}).")
                return
            if dist > remaining:
                self._bm_status.text = (
                    f"Too far ({dist} > {remaining} left).")
                return
            # Perform the move — and count usage
            sel_tok['used_mov'] = used + dist
            del self._bm_tokens[sel]
            self._bm_tokens[cell] = sel_tok
            self._bm_selected = cell
            self._bm_render()

        def _bm_unplace_selected(self):
            """Move the selected token back to 'To Place'."""
            sel = self._bm_selected
            if sel is None:
                return
            tok = self._bm_tokens.get(sel)
            if not tok:
                return
            self._bm_unplaced.append(tok)
            del self._bm_tokens[sel]
            self._bm_selected = None
            self._bm_render()

        def _bm_clear(self):
            """Clear the map — move all tokens back to the pool."""
            for tok in self._bm_tokens.values():
                self._bm_unplaced.append(tok)
            self._bm_tokens = {}
            self._bm_selected = None
            self._bm_placing = None
            self._bm_render()

        def _bm_next_turn(self):
            """Move the top initiative entry to the bottom + reset used MOV.
            Auto-select the next participant's token if it is on the map.
            CoC: each new round restores full movement for everyone."""
            if self._init_list:
                top = self._init_list.pop(0)
                self._init_list.append(top)
            # Reset used MOV for all tokens (placed + in the pool)
            for tok in self._bm_tokens.values():
                tok['used_mov'] = 0
            for tok in self._bm_unplaced:
                tok['used_mov'] = 0
            # Auto-select the token belonging to the next active participant
            self._bm_selected = None
            self._bm_placing = None
            next_name = self._bm_active_name()
            if next_name:
                for cell, tok in self._bm_tokens.items():
                    if tok.get('name') == next_name:
                        self._bm_selected = cell
                        break
            self._bm_render()


        # ---------- WEAPONS ----------
        def _mk_weapons(self):
            """Main view for the weapon table."""
            data = self.weapons_data
            cats = data.get("categories", {})

            if not data.get("weapons"):
                self._tool_action_bar.add_widget(
                    mklbl("Weapons", color=GOLD, size=14, bold=True))
                self.tool_area.clear_widgets()
                msg_box = BoxLayout(orientation='vertical',
                                    spacing=dp(8), padding=dp(20))
                msg_box.add_widget(mklbl(
                    "No weapon data found.",
                    color=GOLD, size=14, bold=True, h=28))

                # Show the latest error message if we have one
                err = getattr(self, '_weap_last_error', None)
                if err:
                    msg_box.add_widget(mklbl(
                        "Error:", color=RED, size=12, bold=True, h=22))
                    msg_box.add_widget(mklbl(
                        err, color=TXT, size=11, wrap=True))
                else:
                    msg_box.add_widget(mklbl(
                        "Place weapons.json in:\n"
                        "/sdcard/Documents/EldritchPortal/",
                        color=DIM, size=11, wrap=True))

                msg_box.add_widget(mklbl(
                    f"Checked path:\n{WEAPONS_FILE}",
                    color=DIM, size=10, wrap=True))

                msg_box.add_widget(mkbtn(
                    "Reload",
                    self._weap_reload, accent=True,
                    size_hint_y=None, height=dp(42)))
                msg_box.add_widget(Widget())
                self.tool_area.add_widget(msg_box)
                return

            # Action bar: search + era + favorite toggle
            search_inp = TextInput(
                text=self._weap_search,
                hint_text='Search…',
                font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD,
                size_hint_x=0.45,
                padding=[dp(8), dp(8)])
            search_inp.bind(text=self._weap_on_search)
            self._tool_action_bar.add_widget(search_inp)

            era_sp = Spinner(
                text=self._weap_era_label(self._weap_era),
                values=['All Eras', '1920s',
                        'Modern', 'Gaslight'],
                size_hint_x=0.35,
                background_color=BTN, color=TXT,
                font_size=sp(11))
            era_sp.bind(text=self._weap_era_change)
            self._tool_action_bar.add_widget(era_sp)

            fav_tog = RToggle(
                text='*',
                state='down' if self._weap_fav_only else 'normal',
                bg_color=BTNH if self._weap_fav_only else BTN,
                color=GOLD if self._weap_fav_only else DIM,
                font_size=sp(14), bold=True,
                size_hint_x=0.2)
            fav_tog.bind(on_release=self._weap_toggle_fav_filter)
            self._tool_action_bar.add_widget(fav_tog)

            # Main area
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical',
                          spacing=dp(4), padding=[dp(4), dp(4)])

            # Category tabs (horizontal scroll)
            cat_scroll = ScrollView(size_hint_y=None, height=dp(40),
                                    do_scroll_y=False)
            cat_row = BoxLayout(size_hint_x=None, spacing=dp(4),
                                padding=[dp(2), 0])
            cat_row.bind(minimum_width=cat_row.setter('width'))

            cat_items = [('all', 'All')]
            cat_items += [(k, v) for k, v in cats.items()]
            for key, lbl in cat_items:
                active = (key == self._weap_cat)
                b = RBtn(
                    text=lbl,
                    bg_color=BTNH if active else BTN,
                    color=GOLD if active else TXT,
                    font_size=sp(11), bold=active,
                    size_hint_x=None, width=dp(90),
                    size_hint_y=None, height=dp(36))
                b.bind(on_release=lambda x, k=key:
                       self._weap_cat_switch(k))
                cat_row.add_widget(b)

            cat_scroll.add_widget(cat_row)
            p.add_widget(cat_scroll)

            # Weapon list
            scroll = ScrollView()
            self._weap_list_grid = GridLayout(
                cols=1, spacing=dp(4),
                padding=[dp(2), dp(4)],
                size_hint_y=None)
            self._weap_list_grid.bind(
                minimum_height=self._weap_list_grid.setter('height'))
            scroll.add_widget(self._weap_list_grid)
            p.add_widget(scroll)

            self.tool_area.add_widget(p)
            self._weap_render_list()

        def _weap_reload(self):
            """Reload weapons.json."""
            self._weap_do_load()
            self._tool_render_sub()

        def _weap_era_label(self, key):
            return {'all': 'All Eras',
                    '1920s': '1920s',
                    'modern': 'Modern',
                    'gaslight': 'Gaslight'}.get(key, 'All Eras')

        def _weap_era_change(self, inst, val):
            rev = {'All Eras': 'all',
                   '1920s': '1920s',
                   'Modern': 'modern',
                   'Gaslight': 'gaslight'}
            self._weap_era = rev.get(val, 'all')
            self._weap_render_list()

        def _weap_on_search(self, inst, val):
            self._weap_search = val.strip().lower()
            self._weap_render_list()

        def _weap_cat_switch(self, cat):
            self._weap_cat = cat
            # Rebuild because category buttons need to be re-styled
            self._tool_render_sub()

        def _weap_toggle_fav_filter(self, inst):
            self._weap_fav_only = (inst.state == 'down')
            inst.bg_color = BTNH if self._weap_fav_only else BTN
            inst.color = GOLD if self._weap_fav_only else DIM
            self._weap_render_list()

        def _weap_filter(self):
            """Return the filtered weapon list."""
            weapons = self.weapons_data.get("weapons", [])
            out = []
            for w in weapons:
                # Category
                if self._weap_cat != 'all':
                    if w.get('category') != self._weap_cat:
                        continue
                # Era
                if self._weap_era != 'all':
                    eras = w.get('era', [])
                    if 'all' not in eras and self._weap_era not in eras:
                        continue
                # Favorite
                if self._weap_fav_only:
                    if w.get('id') not in self.weap_favorites:
                        continue
                # Search
                if self._weap_search:
                    s = self._weap_search
                    hay = (w.get('name', '') + ' ' +
                           w.get('description', '') + ' ' +
                           ' '.join(w.get('tags', []))).lower()
                    if s not in hay:
                        continue
                out.append(w)
            return out

        def _weap_render_list(self):
            """Build the weapon row list based on the current filter."""
            if not hasattr(self, '_weap_list_grid'):
                return
            self._weap_list_grid.clear_widgets()
            subs = self.weapons_data.get("subcategories", {})
            filtered = self._weap_filter()

            if not filtered:
                self._weap_list_grid.add_widget(mklbl(
                    "No matches for the current filter.",
                    color=DIM, size=12, h=40))
                return

            for w in filtered:
                self._weap_list_grid.add_widget(
                    self._weap_make_row(w, subs))

        def _weap_make_row(self, w, subs):
            """Build a compact weapon row (78dp tall, clickable)."""
            wid = w.get('id', '')
            is_fav = wid in self.weap_favorites

            row = RBox(orientation='horizontal',
                       bg_color=BG2,
                       size_hint_y=None, height=dp(78),
                       padding=[dp(8), dp(6)], spacing=dp(6),
                       radius=dp(10))

            # Left: info
            left = BoxLayout(orientation='vertical', spacing=dp(2))

            # Line 1: name + category chip
            l1 = BoxLayout(size_hint_y=None, height=dp(22),
                           spacing=dp(6))
            name_lb = Label(
                text=w.get('name', '?'),
                font_size=sp(13), color=GOLD, bold=True,
                halign='left', valign='middle')
            name_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            l1.add_widget(name_lb)

            sub_key = w.get('subcategory', '')
            sub_lbl = subs.get(sub_key, sub_key)
            if sub_lbl:
                chip = Label(
                    text=sub_lbl,
                    font_size=sp(9), color=DIM, bold=True,
                    size_hint_x=None, width=dp(80),
                    halign='right', valign='middle')
                chip.bind(size=lambda w_, v: setattr(
                    w_, 'text_size', v))
                l1.add_widget(chip)
            left.add_widget(l1)

            # Line 2: skill
            skill_lb = Label(
                text=w.get('skill', ''),
                font_size=sp(10), color=DIM,
                size_hint_y=None, height=dp(18),
                halign='left', valign='middle')
            skill_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            left.add_widget(skill_lb)

            # Line 3: damage | range | ammo | malfunction
            parts = []
            dmg = w.get('damage', '')
            if dmg:
                parts.append(f"Dmg: {dmg}")
            rng = w.get('range', '')
            if rng and rng != 'touch':
                parts.append(f"R: {rng}")
            ammo = w.get('ammo')
            if ammo:
                parts.append(f"Ammo: {ammo}")
            malf = w.get('malfunction')
            if malf:
                parts.append(f"Malf: {malf}")

            stats_lb = Label(
                text='   '.join(parts),
                font_size=sp(10), color=TXT,
                size_hint_y=None, height=dp(20),
                halign='left', valign='middle')
            stats_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            left.add_widget(stats_lb)

            row.add_widget(left)

            # Right: favorite button
            fav_btn = RBtn(
                text='*' if is_fav else 'o',
                bg_color=BTN,
                color=GOLD if is_fav else DIM,
                font_size=sp(18), bold=True,
                size_hint_x=None, width=dp(44),
                size_hint_y=None, height=dp(44),
                pos_hint={'center_y': 0.5})
            fav_btn.bind(on_release=lambda b, _id=wid:
                         self._weap_toggle_fav(_id))
            row.add_widget(fav_btn)

            # Entire row (except favorite button) is clickable = open details
            def _on_touch(widget, touch, weap=w):
                if not widget.collide_point(*touch.pos):
                    return False
                # Not if the favorite button was hit
                if fav_btn.collide_point(*touch.pos):
                    return False
                self._weap_show_detail(weap)
                return True

            row.bind(on_touch_down=_on_touch)
            return row

        def _weap_toggle_fav(self, wid):
            """Toggle favorite status and save."""
            if wid in self.weap_favorites:
                self.weap_favorites.discard(wid)
            else:
                self.weap_favorites.add(wid)
            save_json(self.WEAPONS_FAV_FILE, list(self.weap_favorites))
            self._weap_render_list()

        def _weap_show_detail(self, w):
            """Show the detail overlay for one weapon."""
            self._weap_close_overlay()
            labels = self.weapons_data.get("field_labels", {})
            subs = self.weapons_data.get("subcategories", {})
            cats = self.weapons_data.get("categories", {})

            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(4),
                padding=dp(10),
                size_hint=(0.94, 0.88),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(42),
                            spacing=dp(6))
            hdr.add_widget(mkbtn("Close", self._weap_close_overlay,
                                 danger=True, small=True,
                                 size_hint_x=0.3))
            hdr.add_widget(mklbl(w.get('name', '?'),
                                 color=GOLD, size=14, bold=True))

            wid = w.get('id', '')
            is_fav = wid in self.weap_favorites
            fav_btn = mkbtn('*' if is_fav else 'o',
                            lambda: (self._weap_toggle_fav(wid),
                                     self._weap_show_detail(w)),
                            accent=is_fav, small=True,
                            size_hint_x=None)
            fav_btn.width = dp(50)
            hdr.add_widget(fav_btn)
            overlay.add_widget(hdr)

            # Breadcrumb
            cat_lbl = cats.get(w.get('category', ''), '')
            sub_lbl = subs.get(w.get('subcategory', ''), '')
            crumb = f"{cat_lbl}  >  {sub_lbl}" if sub_lbl else cat_lbl
            overlay.add_widget(mklbl(crumb, color=DIM, size=10, h=18))

            # Content inside the scroll view
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(3),
                           padding=[dp(4), dp(4)], size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            # Key stats in a grid
            g.add_widget(mksep(4))
            stats_box = GridLayout(cols=2, spacing=dp(4),
                                   size_hint_y=None, height=dp(180))

            def _stat(lbl_text, val):
                if val is None or val == '':
                    return
                framed = FramedBox(orientation='vertical',
                                   padding=dp(4), spacing=dp(2))
                framed.add_widget(Label(
                    text=lbl_text, font_size=sp(10),
                    color=GOLD, bold=True,
                    size_hint_y=None, height=dp(16)))
                framed.add_widget(Label(
                    text=str(val), font_size=sp(12),
                    color=TXT, bold=True))
                stats_box.add_widget(framed)

            _stat(labels.get('skill', 'Skill'),
                  w.get('skill', '—'))
            _stat(labels.get('damage', 'Damage'),
                  w.get('damage', '—'))

            db = w.get('uses_db')
            if db is True:
                db_text = 'Yes'
            elif db == 'half':
                db_text = 'Half'
            else:
                db_text = 'No'
            _stat(labels.get('uses_db', 'Uses DB'), db_text)

            _stat(labels.get('can_impale', 'Can Impale'),
                  'Yes' if w.get('can_impale') else 'No')
            _stat(labels.get('range', 'Range'),
                  w.get('range', '—'))
            _stat(labels.get('attacks', 'Attacks / round'),
                  w.get('attacks', '—'))
            _stat(labels.get('ammo', 'Ammo'),
                  w.get('ammo', '—'))
            _stat(labels.get('malfunction', 'Malfunction'),
                  w.get('malfunction', '—'))

            g.add_widget(stats_box)

            # Era and cost
            g.add_widget(mksep(6))
            meta = []
            eras = w.get('era', [])
            if eras:
                era_map = {'all': 'All', 'gaslight': 'Gaslight',
                           '1920s': '1920s',
                           'modern': 'Modern'}
                era_txt = ', '.join(era_map.get(e, e) for e in eras)
                meta.append(f"Era: {era_txt}")
            cost = w.get('cost_1920s')
            if cost:
                meta.append(f"Cost (1920s): {cost}")
            avail = w.get('availability')
            if avail:
                meta.append(f"Availability: {avail}")
            if meta:
                g.add_widget(mklbl(
                    '   •   '.join(meta),
                    color=DIM, size=11, wrap=True))

            # Description
            desc = w.get('description', '')
            if desc:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    labels.get('description', 'Description'),
                    color=GOLD, size=12, bold=True, h=22))
                g.add_widget(mklbl(desc, color=TXT, size=12, wrap=True))

            # Pulp notes
            pulp = w.get('pulp_notes', '')
            if pulp:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    labels.get('pulp_notes', 'Pulp Notes'),
                    color=GOLD, size=12, bold=True, h=22))
                g.add_widget(mklbl(pulp, color=TXT, size=12, wrap=True))

            # Tags
            tags = w.get('tags', [])
            if tags:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    'Tags:  ' + ', '.join(tags),
                    color=DIM, size=10, wrap=True))

            g.add_widget(mksep(30))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            # Add the overlay to the FloatLayout root (same pattern as rules)
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                # Fallback: add directly to tool_area
                self.tool_area.add_widget(overlay)
                self._weap_overlay = overlay
                return
            fl = root.parent

            from kivy.graphics import Color as GCd, Rectangle as GRd
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCd(rgba=[0, 0, 0, 0.6])
                dr = GRd(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w_, v: setattr(dr, 'pos', w_.pos),
                     size=lambda w_, v: setattr(dr, 'size', w_.size))
            dim.bind(on_touch_down=lambda w_, t:
                     self._weap_close_overlay() or True)

            self._weap_dim = dim
            self._weap_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _weap_close_overlay(self):
            """Close the weapon detail overlay."""
            if self._weap_overlay and self._weap_overlay.parent:
                parent = self._weap_overlay.parent
                parent.remove_widget(self._weap_overlay)
                if self._weap_dim and self._weap_dim.parent:
                    parent.remove_widget(self._weap_dim)
            self._weap_overlay = None
            self._weap_dim = None


        # ---------- SCENARIO ----------
        def _scen_init(self):
            """Initialize scenario state."""
            if not hasattr(self, '_scen_data'):
                self._scen_data = None
                self._scen_view = 'clues'

        def _scen_load(self):
            """Read scenario.json from app-private storage."""
            path = self.SCENARIO_FILE
            if not os.path.exists(path):
                self._scen_data = None
                return None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._scen_data = data
                log(f"Scenario loaded: {data.get('title', '?')}")
                return data
            except Exception as e:
                log(f"Scenario error: {e}")
                self._scen_data = {'_error': str(e)}
                return None

        def _scen_save(self):
            """Save scenario.json to app-private storage."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            try:
                os.makedirs(os.path.dirname(self.SCENARIO_FILE), exist_ok=True)
                with open(self.SCENARIO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._scen_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                log(f"Scenario save failed: {e}")

        def _scen_try_import(self):
            """Try to copy scenario.json from the Documents folder to
            app-private storage. Returns (ok, message)."""
            has_access = has_all_files_access()
            if not os.path.exists(EXTERNAL_SCENARIO):
                hint = ""
                if has_access is False:
                    hint = ("\n\nHint: the app does not have 'All files access' yet. "
                            "Tap 'Grant access' to open settings and enable it.")
                return False, (
                    f"No file found in Documents.\n\n"
                    f"Expected path:\n{EXTERNAL_SCENARIO}{hint}")
            try:
                with open(EXTERNAL_SCENARIO, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    return False, "File is not a JSON object."
                os.makedirs(os.path.dirname(self.SCENARIO_FILE), exist_ok=True)
                with open(self.SCENARIO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"Scenario imported: {data.get('title', '?')}")
                return True, f"Imported: {data.get('title', '(no title)')}"
            except PermissionError:
                hint = ""
                if has_access is False:
                    hint = ("\n\nFix: tap 'Grant access' below and "
                            "enable 'Allow managing all files' for Eldritch Portals.")
                return False, "No access to the Documents folder." + hint
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in file:\n{e}"
            except Exception as e:
                return False, f"Error: {type(e).__name__}: {e}"

        def _mk_scenario(self):
            """Build the scenario sub-tab UI."""
            self._scen_init()
            if self._scen_data is None:
                self._scen_load()

            self._tool_action_bar.add_widget(
                mkbtn("Pick File", self._scen_do_pick_file,
                      accent=True, small=True, size_hint_x=0.3))
            self._tool_action_bar.add_widget(
                mkbtn("Reload", self._scen_reload,
                      small=True, size_hint_x=0.25))
            self._tool_action_bar.add_widget(
                mkbtn("Reset", self._scen_confirm_reset,
                      danger=True, small=True, size_hint_x=0.25))
            title_text = "Scenario"
            if self._scen_data and '_error' not in self._scen_data:
                title_text = self._scen_data.get('title', 'Scenario')
            self._tool_action_bar.add_widget(
                mklbl(title_text, color=GOLD, size=11, bold=True))

            self.tool_area.clear_widgets()

            if self._scen_data is None:
                self._scen_show_empty()
                return

            if '_error' in self._scen_data:
                self._scen_show_error()
                return

            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))

            sel = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            for key, txt in [('clues', 'Clues'),
                             ('timeline', 'Timeline'),
                             ('beats', 'Plot'),
                             ('notes', 'Notes')]:
                active = (key == self._scen_view)
                b = RBtn(
                    text=txt,
                    bg_color=BTNH if active else BTN,
                    color=GOLD if active else TXT,
                    font_size=sp(11), bold=active,
                    size_hint_y=None, height=dp(36))
                b.bind(on_release=lambda x, k=key: self._scen_switch_view(k))
                sel.add_widget(b)
            p.add_widget(sel)

            sys_txt = self._scen_data.get('system', '')
            if sys_txt:
                p.add_widget(mklbl(f"System: {sys_txt}", color=DIM, size=10, h=16))

            content = BoxLayout()
            if self._scen_view == 'clues':
                self._scen_build_list(
                    content,
                    self._scen_data.get('clues', []),
                    'where', 'found',
                    "No clues in this scenario.")
            elif self._scen_view == 'timeline':
                self._scen_build_list(
                    content,
                    self._scen_data.get('timeline', []),
                    'when', 'triggered',
                    "No timeline events.")
            elif self._scen_view == 'beats':
                self._scen_build_list(
                    content,
                    self._scen_data.get('beats', []),
                    None, 'done',
                    "No plot points.")
            else:
                self._scen_build_notes(content)
            p.add_widget(content)

            self.tool_area.add_widget(p)

        def _scen_show_empty(self):
            """Show message when no scenario.json is loaded."""
            scroll = ScrollView()
            box = BoxLayout(orientation='vertical',
                            spacing=dp(8), padding=dp(16),
                            size_hint_y=None)
            box.bind(minimum_height=box.setter('height'))

            box.add_widget(mklbl(
                "No scenario loaded.",
                color=GOLD, size=14, bold=True, h=28))

            box.add_widget(mksep(8))
            box.add_widget(mklbl(
                "EASIEST — Pick File",
                color=GOLD, size=12, bold=True, h=22))
            box.add_widget(mklbl(
                "Tap 'Pick File' to open Android's file picker. "
                "Browse to scenario.json wherever you have it — "
                "Documents, Downloads, Google Drive, SD card. "
                "No extra permissions required.",
                color=TXT, size=11, wrap=True))
            box.add_widget(mkbtn(
                "Pick File",
                self._scen_do_pick_file, accent=True,
                size_hint_y=None, height=dp(52)))

            access = has_all_files_access()
            box.add_widget(mksep(10))
            box.add_widget(mklbl(
                "ALTERNATIVE — Import from Documents",
                color=GOLD, size=12, bold=True, h=22))

            if access is True:
                box.add_widget(mklbl(
                    "All files access: ON",
                    color=GRN, size=11, bold=True, h=20))
                box.add_widget(mklbl(
                    f"Place scenario.json in:\n{EXTERNAL_SCENARIO}\n\n"
                    "Then tap 'Import from Documents' below.",
                    color=TXT, size=11, wrap=True))
                box.add_widget(mkbtn(
                    "Import from Documents",
                    self._scen_do_import,
                    size_hint_y=None, height=dp(44)))
            elif access is False:
                box.add_widget(mklbl(
                    "All files access: OFF",
                    color=RED, size=11, bold=True, h=20))
                box.add_widget(mklbl(
                    "To use the Import button you need to enable "
                    "'All files access' for this app. "
                    "One-time setup — but 'Pick File' above is "
                    "simpler and needs no extra permissions.",
                    color=TXT, size=11, wrap=True))
                box.add_widget(mkbtn(
                    "Grant access (opens settings)",
                    self._scen_request_access,
                    size_hint_y=None, height=dp(44)))
            else:
                box.add_widget(mklbl(
                    "Only available on Android 11+.",
                    color=DIM, size=10, wrap=True))

            box.add_widget(mksep(10))
            box.add_widget(mklbl(
                "MANUAL — Copy here",
                color=GDIM, size=11, bold=True, h=20))
            box.add_widget(mklbl(
                self.SCENARIO_FILE,
                color=GDIM, size=10, wrap=True))
            box.add_widget(mklbl(
                "Then tap 'Reload'.",
                color=DIM, size=10, wrap=True))

            box.add_widget(mksep(8))
            box.add_widget(mkbtn(
                "Reload",
                self._scen_reload,
                size_hint_y=None, height=dp(40)))

            scroll.add_widget(box)
            self.tool_area.add_widget(scroll)

        def _scen_request_access(self):
            """Open Android settings for All Files Access."""
            ok = request_all_files_access()
            if not ok:
                self._scen_show_message(
                    "Could not open settings",
                    "Try navigating manually to:\n"
                    "Settings > Apps > Eldritch Portals > "
                    "Permissions > All files",
                    is_error=True)

        def _scen_do_pick_file(self):
            """Open Android file picker and let the user select scenario.json."""
            if platform != 'android':
                self._scen_show_message(
                    "Not supported",
                    "File picker is only available on Android.",
                    is_error=True)
                return
            self._scen_show_message(
                "Opening file picker...",
                "Select a scenario.json file. You can browse to "
                "Documents, Downloads, Drive, or wherever you have it.",
                is_error=False)
            Clock.schedule_once(
                lambda dt: self._scen_close_overlay(), 0.8)
            Clock.schedule_once(
                lambda dt: self.file_picker.pick(
                    self._scen_on_file_picked,
                    mime_type='*/*'),
                1.0)

        def _scen_on_file_picked(self, ok, text_or_err):
            """Callback when the file picker is done."""
            if not ok:
                if text_or_err != "Cancelled":
                    self._scen_show_message(
                        "Could not read file",
                        text_or_err, is_error=True)
                return
            try:
                data = json.loads(text_or_err)
            except json.JSONDecodeError as e:
                self._scen_show_message(
                    "Invalid JSON",
                    f"The file is not valid JSON:\n{e}",
                    is_error=True)
                return
            if not isinstance(data, dict):
                self._scen_show_message(
                    "Wrong format",
                    "The file does not contain a JSON object "
                    "(needs { ... }).",
                    is_error=True)
                return
            try:
                os.makedirs(os.path.dirname(self.SCENARIO_FILE), exist_ok=True)
                with open(self.SCENARIO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"Scenario picked and saved: {data.get('title', '?')}")
            except Exception as e:
                self._scen_show_message(
                    "Could not save",
                    f"Error saving:\n{e}",
                    is_error=True)
                return
            self._scen_data = None
            self._scen_load()
            self._tool_render_sub()
            self._scen_show_message(
                "Scenario loaded",
                f"Selected: {data.get('title', '(no title)')}",
                is_error=False)

        def _scen_do_import(self):
            """Try to import scenario from the Documents folder."""
            ok, msg = self._scen_try_import()
            if ok:
                self._scen_data = None
                self._scen_load()
                self._tool_render_sub()
                self._scen_show_message("Import successful", msg, is_error=False)
            else:
                self._scen_show_message("Import failed", msg, is_error=True)

        def _scen_show_message(self, title, msg, is_error=False):
            """Show a message as an overlay."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.88, 0.5),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.add_widget(mklbl(
                title,
                color=RED if is_error else GOLD,
                size=14, bold=True, h=28))

            scroll = ScrollView()
            overlay.add_widget(scroll)
            body = mklbl(msg, color=TXT, size=11, wrap=True)
            scroll.add_widget(body)

            overlay.add_widget(mkbtn(
                "OK", self._scen_close_overlay,
                accent=True, size_hint_y=None, height=dp(44)))

            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCm, Rectangle as GRm
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCm(rgba=[0, 0, 0, 0.6])
                dr = GRm(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t: (self._scen_close_overlay(), True)[1])

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_show_error(self):
            """Show error message if scenario.json was invalid."""
            err = self._scen_data.get('_error', 'Unknown error')
            scroll = ScrollView()
            box = BoxLayout(orientation='vertical',
                            spacing=dp(8), padding=dp(16),
                            size_hint_y=None)
            box.bind(minimum_height=box.setter('height'))

            box.add_widget(mklbl(
                "Error reading scenario.json",
                color=RED, size=14, bold=True, h=28))
            box.add_widget(mklbl(str(err), color=TXT, size=11, wrap=True))

            box.add_widget(mksep(8))
            box.add_widget(mklbl(
                "Possible causes:",
                color=GOLD, size=12, bold=True, h=22))
            box.add_widget(mklbl(
                "• File is not valid JSON "
                "(check at jsonlint.com)\n"
                "• Missing write permissions\n"
                "• File is empty or corrupt",
                color=TXT, size=11, wrap=True))

            box.add_widget(mksep(6))
            box.add_widget(mklbl(
                "File path in use:",
                color=GOLD, size=11, bold=True, h=20))
            box.add_widget(mklbl(
                self.SCENARIO_FILE,
                color=GDIM, size=10, wrap=True))

            box.add_widget(mksep(10))
            box.add_widget(mkbtn(
                "Reload",
                self._scen_reload, accent=True,
                size_hint_y=None, height=dp(44)))
            box.add_widget(mkbtn(
                "Import from Documents",
                self._scen_do_import,
                size_hint_y=None, height=dp(40)))

            scroll.add_widget(box)
            self.tool_area.add_widget(scroll)

        def _scen_reload(self):
            """Reload scenario.json from disk."""
            self._scen_data = None
            self._scen_load()
            self._tool_render_sub()

        def _scen_switch_view(self, view):
            self._scen_view = view
            self._tool_render_sub()

        def _scen_build_list(self, container, items,
                             subtitle_key, flag_key, empty_msg):
            """Build a list with checkbox rows."""
            if not items:
                container.add_widget(mklbl(
                    empty_msg, color=DIM, size=11, wrap=True))
                return

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for item in items:
                g.add_widget(self._scen_make_row(item, subtitle_key, flag_key))

            scroll.add_widget(g)
            container.add_widget(scroll)

        def _scen_make_row(self, item, subtitle_key, flag_key):
            """Build a row for a clue/timeline/beat."""
            done = bool(item.get(flag_key, False))
            row = RBox(orientation='horizontal',
                       bg_color=BG2 if not done else BTN,
                       size_hint_y=None, height=dp(64),
                       padding=[dp(8), dp(6)], spacing=dp(6),
                       radius=dp(10))

            tog = RBtn(
                text='[X]' if done else '[ ]',
                bg_color=BTNH if done else INPUT,
                color=GOLD if done else DIM,
                font_size=sp(14), bold=True,
                size_hint_x=None, width=dp(52))
            tog.bind(on_release=lambda b, it=item, fk=flag_key:
                     self._scen_toggle(it, fk))
            row.add_widget(tog)

            mid = BoxLayout(orientation='vertical', spacing=dp(2))
            title_lb = Label(
                text=item.get('title', '?'),
                font_size=sp(12),
                color=DIM if done else GOLD,
                bold=True,
                halign='left', valign='middle')
            title_lb.bind(size=lambda w, v: setattr(w, 'text_size', (v[0], None)))
            mid.add_widget(title_lb)

            if subtitle_key:
                sub_val = item.get(subtitle_key, '')
                if sub_val:
                    sub_lb = Label(
                        text=sub_val,
                        font_size=sp(10),
                        color=DIM,
                        halign='left', valign='middle',
                        size_hint_y=None, height=dp(18))
                    sub_lb.bind(size=lambda w, v: setattr(w, 'text_size', (v[0], None)))
                    mid.add_widget(sub_lb)

            row.add_widget(mid)

            desc = item.get('description', '')
            if desc:
                info_btn = RBtn(
                    text='i', bg_color=BTN, color=TXT,
                    font_size=sp(14), bold=True,
                    size_hint_x=None, width=dp(44))
                info_btn.bind(on_release=lambda b,
                              t=item.get('title', '?'),
                              d=desc:
                              self._scen_show_detail(t, d))
                row.add_widget(info_btn)

            return row

        def _scen_toggle(self, item, flag_key):
            """Toggle flag and save."""
            item[flag_key] = not bool(item.get(flag_key, False))
            self._scen_save()
            self._tool_render_sub()

        def _scen_show_detail(self, title, desc):
            """Show full description as an overlay."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(6),
                padding=dp(12),
                size_hint=(0.9, 0.7),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            hdr.add_widget(mkbtn("Close", self._scen_close_overlay,
                                 danger=True, small=True, size_hint_x=0.3))
            hdr.add_widget(mklbl(title, color=GOLD, size=13, bold=True))
            overlay.add_widget(hdr)

            scroll = ScrollView()
            body = mklbl(desc, color=TXT, size=12, wrap=True)
            scroll.add_widget(body)
            overlay.add_widget(scroll)

            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCs, Rectangle as GRs
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCs(rgba=[0, 0, 0, 0.6])
                dr = GRs(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t: (self._scen_close_overlay(), True)[1])

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_close_overlay(self):
            ov = getattr(self, '_scen_overlay', None)
            dm = getattr(self, '_scen_dim', None)
            if ov and ov.parent:
                ov.parent.remove_widget(ov)
            if dm and dm.parent:
                dm.parent.remove_widget(dm)
            self._scen_overlay = None
            self._scen_dim = None

        def _scen_build_notes(self, container):
            """Build notes view."""
            box = BoxLayout(orientation='vertical', spacing=dp(4))
            notes = self._scen_data.get('notes', '')
            self._scen_notes_input = TextInput(
                text=notes, multiline=True,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, font_size=sp(12),
                padding=[dp(8), dp(8)])
            box.add_widget(self._scen_notes_input)
            box.add_widget(mkbtn(
                "Save notes", self._scen_save_notes,
                accent=True, size_hint_y=None, height=dp(44)))
            container.add_widget(box)

        def _scen_save_notes(self):
            """Save notes text."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            self._scen_data['notes'] = self._scen_notes_input.text
            self._scen_save()

        def _scen_confirm_reset(self):
            """Ask for confirmation before resetting all flags."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.8, 0.4),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.add_widget(mklbl(
                "Reset progress?",
                color=GOLD, size=14, bold=True, h=28))
            overlay.add_widget(mklbl(
                "All checkboxes in clues, timeline and "
                "plot points will be reset. Notes are kept.",
                color=TXT, size=11, wrap=True))
            btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            btns.add_widget(mkbtn(
                "Cancel", self._scen_close_overlay,
                small=True, size_hint_x=0.5))
            btns.add_widget(mkbtn(
                "Reset", self._scen_reset_flags,
                danger=True, size_hint_x=0.5))
            overlay.add_widget(btns)

            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCr, Rectangle as GRr
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCr(rgba=[0, 0, 0, 0.6])
                dr = GRr(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_reset_flags(self):
            """Reset all checkboxes."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            for c in self._scen_data.get('clues', []):
                c['found'] = False
            for t in self._scen_data.get('timeline', []):
                t['triggered'] = False
            for b in self._scen_data.get('beats', []):
                b['done'] = False
            self._scen_save()
            self._scen_close_overlay()
            self._tool_render_sub()


        def on_stop(self):
            self.player.stop()
            self.streamer.stop()
            self.server.stop()
            self.cast.disconnect()
            save_json(self.CHARS_FILE, self.chars)

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())
