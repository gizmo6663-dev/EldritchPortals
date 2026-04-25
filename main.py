import os
import sys
import json
import threading
import socket
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from kivy.clock import Clock

LOG = "/sdcard/Documents/EldritchPortals/crash.log"
LOG_HISTORY_LIMIT = 3
MAX_NAME_LENGTH = 18
MAX_OCCUPATION_LENGTH = 15
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def _first_last_name(name):
    """Return only the first and last word of a name (e.g. 'John Michael Doe' → 'John Doe').
    Single-word names are returned unchanged."""
    parts = name.split()
    if len(parts) <= 2:
        return name
    return f"{parts[0]} {parts[-1]}"

# Rotate crash logs on startup so each launch gets a fresh log while
# keeping a small history for debugging.
try:
    for i in range(LOG_HISTORY_LIMIT, 0, -1):
        src = LOG if i == 1 else f"{LOG}.{i - 1}"
        dst = f"{LOG}.{i}"
        if os.path.exists(src):
            try:
                if os.path.exists(dst):
                    os.remove(dst)
            except Exception:
                pass
            os.replace(src, dst)
except Exception:
    pass

def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")

log("=== APP START (v0.3.3 – Abyssal Purple) ===")

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
    from kivy.uix.filechooser import FileChooserListView
    from kivy.core.window import Window
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

    BASE_DIR  = "/sdcard/Documents/EldritchPortals"
    IMG_DIR   = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    # Character file: primary storage in user_data_dir (app-private,
    # always writable). External path used only for migration at
    # first launch — avoids Android 13+ scoped storage problem.
    EXTERNAL_CHAR_FILE = os.path.join(BASE_DIR, "characters.json")
    # CHAR_FILE is set in build() when user_data_dir is available.
    CHAR_FILE = EXTERNAL_CHAR_FILE  # temporary; overridden in build()
    # Scenario file: primary storage in user_data_dir (app-private,
    # always writable). External import path is tried on
    # "Import" — avoids Android 13+ scoped storage problem.
    EXTERNAL_SCENARIO = os.path.join(BASE_DIR, "scenario.json")
    # SCENARIO_FILE is set in build() when user_data_dir is available.

    # Weapon data is BUNDLED with the app (packed into APK).
    # This avoids Android 13+ scoped storage permission problems.
    try:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    BUNDLED_WEAPONS = os.path.join(_BUNDLE_DIR, "weapons.json")
    BUNDLED_CHARS   = os.path.join(_BUNDLE_DIR, "characters.json")
    # Also try an external version — if it exists AND is readable,
    # use it (allows the user to override with their own file if possible).
    EXTERNAL_WEAPONS = os.path.join(BASE_DIR, "weapons.json")
    # Favourites are stored in user_data_dir (app-private, always writable).
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
    # Shadow: a dark RoundedRectangle offset 2dp down.
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
    # Complete CoC 7e + Pulp Cthulhu keeper reference.
    RULES = [
      ("Basic Rules", "", [
        ("Skill Rolls", [
          "Roll d100 (percentile) against the skill value.",
          "Equal to or under = success.",
          "",
          "Success levels:",
          "  Critical: result = 01",
          "  Extreme: result ≤ skill / 5",
          "  Hard: result ≤ skill / 2",
          "  Regular: result ≤ skill",
          "  Failure: result > skill",
          "",
          "Automatic success: 01 always succeeds.",
          "Fumble (based on MAX SKILL, not base skill):",
          "  Requirement ≥ 50: only 100 is fumble",
          "  Requirement < 50: 96–100 is fumble",
          "  Example: skill 60, Hard difficulty (requires 30)",
          "    -> fumble on 96–100",
        ]),
        ("Difficulty Levels", [
          "Keeper sets difficulty level:",
          "  Regular: skill value (standard)",
          "  Hard: half skill value",
          "  Extreme: one fifth of skill value",
          "",
          "Against living opponents:",
          "  Opponent's skill < 50: Regular",
          "  Opponent's skill ≥ 50: Hard",
          "  Opponent's skill ≥ 90: Extreme",
        ]),
        ("Bonus & Penalty", [
          "Bonus die: roll 2 ten-sided dice,",
          "  use the LOWEST.",
          "Penalty die: roll 2 ten-sided dice,",
          "  use the HIGHEST.",
          "",
          "Maximum 2 bonus OR 2 penalty.",
          "Bonus and penalty cancel 1:1.",
          "",
          "Granted by Keeper based on circumstances:",
          "  Advantage: bonus die (good light, time, tools)",
          "  Disadvantage: penalty die (stress, poor visibility)",
        ]),
        ("Pushed Rolls", [
          "Player can push ONE failed roll.",
          "Must describe WHAT they do differently.",
          "Keeper must approve the push.",
          "",
          "Failed push = SERIOUS consequence",
          "(worse than normal failure).",
          "",
          "CANNOT be pushed:",
          "  SAN checks",
          "  Luck checks",
          "  Combat rolls",
          "  Already pushed rolls",
        ]),
        ("Opposed Rolls", [
          "Both parties roll their skills.",
          "Highest success level wins.",
          "Tied level: highest skill value wins.",
          "No success: status quo.",
          "",
          "Common opposed rolls:",
          "  Sneak vs Listen",
          "  Fast Talk vs Psychology",
          "  Charm vs POW",
          "  STR vs STR (break, hold)",
          "  DEX vs DEX (grab, evade)",
          "  Disguise vs Spot Hidden",
        ]),
        ("Luck", [
          "Luck value: 3d6 x 5 (at creation).",
          "Luck check: d100 ≤ Luck.",
          "",
          "Spending Luck:",
          "  After a skill roll: subtract Luck points",
          "  1:1 to lower the result.",
          "  Example: roll 55, skill 50 -> spend 5 Luck.",
          "",
          "Luck does NOT regenerate in standard CoC.",
          "Pulp: regenerate 2d10 Luck per session.",
          "",
          "Group Luck: lowest Luck in the group",
          "  is used for random events.",
        ]),
        ("Experience & Development", [
          "After scenario: mark used skills.",
          "Roll d100 for each marked skill:",
          "  Result > skill = +1d10 to skill.",
          "  Result ≤ skill = no improvement.",
          "",
          "Skill max: 99 (except Cthulhu Mythos: 99).",
          "Aging effects can lower stats.",
        ]),
      ]),
      ("Combat", "", [
        ("Combat Flow", [
          "1. All act in DEX order",
          "   (highest first).",
          "",
          "2. Each participant gets 1 action:",
          "   - Attack (melee or ranged)",
          "   - Flee (withdraw)",
          "   - Maneuver (trip, disarm, etc.)",
          "   - Cast spell",
          "   - Use item / First Aid",
          "   - Other (talk, search, etc.)",
          "",
          "3. Defender chooses reaction:",
          "   - Dodge (evade)",
          "   - Fight Back (counterattack, melee only)",
          "   - Nothing (takes full damage)",
          "",
          "4. Repeat until combat ends.",
        ]),
        ("Melee", [
          "Attacker: roll Fighting skill.",
          "Defender chooses:",
          "",
          "DODGE (opposed vs Dodge skill):",
          "  Attacker wins -> full damage",
          "  Defender wins -> avoids the attack",
          "  Both fail -> nothing happens",
          "",
          "FIGHT BACK (opposed vs Fighting):",
          "  Attacker wins -> full damage",
          "  Defender wins -> defender deals damage",
          "  Both fail -> nothing happens",
          "",
          "Dodge: 1 free per round,",
          "  extra dodge costs action next round.",
          "",
          "OUTNUMBERED:",
          "  When defender has already dodged",
          "  or fought back this round:",
          "  -> all subsequent attacks get",
          "     +1 bonus die.",
          "  Exception: creatures with multiple attacks/round",
          "  can dodge/fight back that many times.",
          "  Does NOT apply to firearms.",
        ]),
        ("Firearms", [
          "Roll Firearms skill. NO opposed roll.",
          "Defender can ONLY dodge at point-blank range.",
          "Otherwise: only cover/move out.",
          "",
          "Range modifiers:",
          "  Point-blank (≤ 1/5 range): +1 bonus",
          "  Medium range (base range): normal",
          "  Long (up to 2x base): +1 penalty",
          "  Extreme (up to 4x base): +2 penalty",
          "",
          "Other modifiers:",
          "  Moving target: +1 penalty die",
          "  Large target: +1 bonus die",
          "  Narrow target: +1 penalty die",
          "  Aim (uses action): +1 bonus",
          "",
          "Impale: Extreme success with",
          "  impaling weapon",
          "  = max weapon damage + extra roll.",
        ]),
        ("Maneuvers", [
          "Fighting maneuvers (instead of damage):",
          "  Trip/knockdown: target falls",
          "  Disarm: target loses weapon",
          "  Hold/grapple: target is restrained",
          "  Throw: push/throw opponent",
          "",
          "Requires: win opposed Fighting check.",
          "Build difference can give bonus/penalty:",
          "  Attacker Build ≥ target + 2: +1 bonus die",
          "  Attacker Build ≤ target - 2: +1 penalty die",
        ]),
        ("Damage Bonus (DB)", [
          "DB based on STR + SIZ:",
          "  2–64:    -2",
          "  65–84:   -1",
          "  85–124:  0",
          "  125–164: +1d4",
          "  165–204: +1d6",
          "  205–284: +2d6",
          "  285–364: +3d6",
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
          "DAMAGE LEVELS:",
          "  Minor wound: loss < half max HP",
          "  Major wound: loss ≥ half max HP",
          "",
          "MAJOR WOUND consequences:",
          "  CON check or faint",
          "  First Aid/Medicine within 1 round",
          "  Must be stabilised or dies",
          "",
          "DYING (0 HP):",
          "  CON check per round",
          "  Fail = death",
          "  Success = holds out 1 more round",
          "",
          "HEALING:",
          "  First Aid: +1 HP (1 attempt/wound)",
          "  Medicine: +1d3 HP (after First Aid)",
          "  Natural: 1 HP/week (minor)",
          "  Major wound: 1d3 HP/week with care",
        ]),
        ("Automatic Weapons", [
          "Burst: 3 bullets, +1 bonus die to damage.",
          "Full auto: choose number of targets,",
          "  distribute bullets, roll for each target.",
          "  1 bonus die per 10 bullets on the target.",
          "",
          "Suppressive fire:",
          "  Covers an area, everyone in the area",
          "  must Dodge or take 1 hit.",
          "  Uses half the magazine.",
        ]),
      ]),
      ("Sanity", "", [
        ("SAN Check", [
          "Roll d100 ≤ current SAN.",
          "",
          "Format: 'X/Y'",
          "  Success: loss = X",
          "  Failure: loss = Y",
          "  Example: '1/1d6' = success loses 1,",
          "    failure loses 1d6 SAN.",
          "",
          "Max SAN = 99 – Cthulhu Mythos skill.",
          "",
          "SAN fumble: automatically maximum SAN loss.",
        ]),
        ("Temporary Insanity", [
          "TRIGGER: 5+ SAN lost in ONE roll.",
          "",
          "Keeper calls for INT check:",
          "  INT success = investigator realizes",
          "    the truth -> TEMPORARILY INSANE",
          "  INT failure = suppressed memory,",
          "    investigator remains sane",
          "",
          "Temporary insanity lasts 1d10 hours.",
          "Begins with a Bout of Madness.",
          "Followed by Underlying Insanity.",
        ]),
        ("Bout of Madness", [
          "Occurs during temporary insanity.",
          "Keeper chooses Real-Time or Summary.",
          "",
          "REAL-TIME (lasts 1d10 rounds):",
          "  1: Amnesia (remembers nothing)",
          "  2: Psychosomatic (blind/deaf/paralysed)",
          "  3: Violence (attack nearest person)",
          "  4: Paranoia (everyone is an enemy)",
          "  5: Physical (nausea/fainting)",
          "  6: Flight (run in panic)",
          "  7: Hallucinations",
          "  8: Echo (repeat actions meaninglessly)",
          "  9: Phobia (new or existing)",
          "  10: Catatonia (completely stiff)",
        ]),
        ("Summary (1d10 hours)", [
          "After real-time bout, lasting effect:",
          "  1: Amnesia for the whole event",
          "  2: Obsessions / rituals",
          "  3: Hallucinations (persistent)",
          "  4: Irrational hatred/fear",
          "  5: Phobia (specific, new or reinforced)",
          "  6: Mania (compulsive behavior)",
          "  7: Paranoia (trusts no one)",
          "  8: Dissociation (detached, unreal)",
          "  9: Eating disorder / insomnia",
          "  10: Mythos obsession (studies forbidden knowledge)",
        ]),
        ("Phobias (selection)", [
          "Acrophobia – fear of heights",
          "Agoraphobia – open spaces",
          "Arachnophobia – spiders",
          "Claustrophobia – confined spaces",
          "Demophobia – crowds",
          "Hemophobia – blood",
          "Hydrophobia – water",
          "Mysophobia – germs/dirt",
          "Necrophobia – the dead/corpses",
          "Nyctophobia – darkness",
          "Pyrophobia – fire",
          "Thalassophobia – the sea/deep water",
          "Xenophobia – strangers/unknown",
          "Zoophobia – animals",
        ]),
        ("Manias (selection)", [
          "Dipsomania – craving for alcohol",
          "Kleptomania – compulsion to steal",
          "Megalomania – delusions of grandeur",
          "Mythomania – compulsive liar",
          "Necromania – obsession with death",
          "Pyromania – arson",
          "Thanatomania – death wish",
          "Xenomania – obsession with foreigners/strangers",
        ]),
        ("Indefinite Insanity", [
          "Triggered when investigator has lost",
          "  1/5 of current SAN in total.",
          "",
          "Effect: long-term madness.",
          "Player loses control of character.",
          "Keeper decides behavior.",
          "Lasts months/years.",
          "",
          "Treatment:",
          "  Institutionalization",
          "  Psychoanalysis over time",
          "  +1d3 SAN per month (max)",
          "  Failed treatment: -1d6 SAN",
        ]),
        ("SAN Recovery", [
          "Psychoanalysis: +1d3 SAN (1/month)",
          "  Failed: -1d6 SAN!",
          "Self-help: improve skill = +1d3 SAN",
          "Complete scenario: Keeper reward",
          "",
          "Max SAN = 99 – Cthulhu Mythos skill.",
          "Permanent SAN loss cannot be restored",
          "  beyond this limit.",
        ]),
      ]),
      ("Chase", "", [
        ("Setup", [
          "1. Type: on foot or vehicle.",
          "2. Number of locations: 5–10 (Keeper chooses).",
          "3. Participants:",
          "   Foot: MOV based on DEX, STR, SIZ.",
          "   Vehicle: speed rating.",
          "4. Speed Roll (CON check):",
          "   Extreme success: +1 MOV for the chase",
          "   Success: no change",
          "   Failure: -1 MOV for the chase",
          "   (vehicle: Drive Auto instead)",
          "5. Compare MOV: higher MOV escapes",
          "   immediately. Otherwise -> full chase.",
          "6. Set starting positions on the track.",
          "7. Place barriers/hazards at locations.",
          "",
          "MOV (Movement Rate):",
          "  If DEX & STR both > SIZ: MOV 9",
          "  If either DEX or STR > SIZ: MOV 8",
          "  If both ≤ SIZ: MOV 7",
          "  Age 40–49: MOV -1",
          "  Age 50–59: MOV -2 (etc.)",
        ]),
        ("Movement & Actions", [
          "Rounds in DEX order (highest first).",
          "",
          "Each round participant can:",
          "  - Move (MOV locations)",
          "  - Perform 1 action:",
          "    Speed: CON check for +1 location",
          "    Attack: Fighting/Firearms",
          "    Barrier: skill check to pass",
          "    Obstacle: create barrier for pursuer",
          "",
          "Hazard handling costs action AND",
          "  movement that round.",
        ]),
        ("Barriers", [
          "Keeper places barriers at locations.",
          "Skill check to pass:",
          "",
          "  Jump over fence: Jump / Climb",
          "  Narrow passage: DEX / Dodge",
          "  Crowd: STR / Charm / Intimidate",
          "  Mud/slippery: DEX / Luck",
          "  Locked door: Locksmith / STR",
          "  Busy street: Drive Auto / DEX",
          "",
          "Failure: lose 1 location movement.",
          "Fumble: fall, damage, stuck, etc.",
        ]),
        ("Victory & Capture", [
          "ESCAPE succeeds when:",
          "  Distance between = number of locations + 1",
          "  (pursuer cannot see the target).",
          "",
          "CAUGHT when:",
          "  Pursuer is at the SAME location.",
          "  Combat or interaction can begin.",
          "",
          "EXHAUSTION:",
          "  CON check per round after round 5.",
          "  Failure: MOV reduced by 1.",
          "  MOV 0: cannot move.",
        ]),
      ]),
      ("Magic & Tomes", "", [
        ("Spell Casting", [
          "Costs vary per spell:",
          "  Magic Points (MP): most common",
          "  SAN: almost always",
          "  HP: some powerful spells",
          "  POW: permanent sacrifice (rare)",
          "",
          "Casting time: 1 round to several hours.",
          "Some require components/rituals.",
          "",
          "MP regenerates: 1 per 2 hours rest.",
          "MP = 0: unconscious for 1d8 hours.",
          "POW sacrifice: permanent, does NOT recover.",
        ]),
        ("Mythos Tomes", [
          "Reading a Mythos tome:",
          "  Initial reading: weeks to months",
          "  Full study: months to years",
          "",
          "Reward: +Cthulhu Mythos skill.",
          "Cost: SAN loss (varies per tome).",
          "Can also learn spells from the tome.",
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
          "Heroes are TOUGHER than standard CoC.",
          "",
          "HP: (CON + SIZ) / 5 (rounded down)",
          "  Standard CoC: (CON+SIZ) / 10",
          "  Effectively DOUBLE HP.",
          "  Optional low-level: (CON+SIZ)/10",
          "",
          "Luck: 2d6+6 x 5 (higher than standard)",
          "  Standard CoC: 3d6 x 5",
          "  Regenerate 2d10 Luck per session.",
          "",
          "First Aid: +1d4 HP (standard: +1 HP)",
          "  Extreme success: automatically 4 HP.",
          "Medicine: +1d4 HP (standard: +1d3)",
          "",
          "Pulp Talents: 2 (standard).",
          "  Low-level pulp: 1 talent",
          "  High-level pulp: 3 talents",
          "",
          "Combat rolls CANNOT be pushed (as standard).",
          "Spending Luck: can also be used to:",
          "  - Avoid dying (5 Luck = stabilise)",
          "  - Reduce damage (after roll)",
        ]),
        ("Archetypes", [
          "Choose 1 archetype at creation.",
          "Grants bonuses and Pulp Talents.",
          "",
          "  Adventurer: versatile explorer",
          "  Beefcake: physically strong, extra HP",
          "  Bon Vivant: charming, socially adept",
          "  Cold Blooded: ruthless, precise",
          "  Dreamer: creative, Mythos-sensitive",
          "  Egghead: intellectual, knowledgeable",
          "  Explorer: explorer, survivalist",
          "  Femme/Homme Fatale: seductive",
          "  Grease Monkey: mechanic, inventive",
          "  Hard Boiled: tough, resilient",
          "  Harlequin: entertainer, distracting",
          "  Hunter: hunter, nature-savvy",
          "  Mystic: spiritual, clairvoyant",
          "  Outsider: solitary, self-taught",
          "  Reckless: daredevil, risk-taker",
          "  Sidekick: loyal, supportive",
          "  Swashbuckler: acrobatic fighter",
          "  Thrill Seeker: adrenaline junkie",
          "  Two-Fisted: brawling specialist",
        ]),
        ("Pulp Talents (selection)", [
          "PHYSICAL:",
          "  Brawler: +1d6 melee damage",
          "  Iron Jaw: ignore 1 K.O. per session",
          "  Quick Healer: double healing",
          "  Tough Guy: +1d6 extra HP",
          "",
          "MENTAL:",
          "  Arcane Insight: +2 Cthulhu Mythos",
          "  Gadget: craft improvised item",
          "  Photographic Memory: remember everything",
          "  Psychic Power: sixth sense",
          "",
          "SOCIAL:",
          "  Smooth Talker: re-roll 1 social check",
          "  Master of Disguise: +1 bonus Disguise",
          "  Lucky: +1d10 extra Luck regen",
          "",
          "COMBAT:",
          "  Rapid Fire: extra shot without penalty",
          "  Outmaneuver: +1 bonus die on maneuvers",
          "  Fleet Footed: +1 MOV in chase",
        ]),
      ]),
      ("Tables", "", [
        ("Melee Weapon Table", [
          "Weapon: damage / attacks",
          "",
          "  Unarmed (fist): 1d3+DB / 1",
          "  Head butt: 1d4+DB / 1",
          "  Kick: 1d4+DB / 1",
          "  Grapple: special / 1",
          "  Knife (small): 1d4+DB / 1",
          "  Knife (large): 1d6+DB / 1",
          "  Club/mace: 1d8+DB / 1",
          "  Sword/saber: 1d8+DB / 1",
          "  Axe (large): 1d8+2+DB / 1",
          "  Spear: 1d8+1+DB / 1",
          "  Chainsaw: 2d8 / 1",
        ]),
        ("Ranged Weapon Table", [
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
          "  See a gruesome murder: 1/1d4+1",
          "  See a massacre: 1d3/1d6+1",
          "  Discover a horror: 0/1d3",
          "",
          "  Discover Mythos evidence: 0/1d2",
          "  Read Mythos tome: 1/1d4",
          "  See Mythos ritual: 1/1d6",
          "  Be subjected to spell: 1/1d6",
        ]),
        ("Aging Effects", [
          "Age affects stats at character creation:",
          "",
          "  15–19: -5 SIZ/STR, -5 EDU,",
          "    Luck: roll twice, use best",
          "  20–39: EDU improvement: +1",
          "  40–49: EDU +2, -5 free STR/CON/DEX,",
          "    APP -5, MOV -1",
          "  50–59: EDU +3, -10 free STR/CON/DEX,",
          "    APP -10, MOV -2",
          "  60–69: EDU +4, -20 free STR/CON/DEX,",
          "    APP -15, MOV -3",
          "  70–79: EDU +4, -40 free STR/CON/DEX,",
          "    APP -20, MOV -4",
          "  80–89: EDU +4, -80 free STR/CON/DEX,",
          "    APP -25, MOV -5",
        ]),
        ("Credit Rating", [
          "Credit Rating = wealth/social status:",
          "",
          "  0: poor, homeless",
          "  1–9: poor, necessities only",
          "  10–49: average",
          "  50–89: wealthy",
          "  90–98: rich",
          "  99: enormously rich",
          "",
          "Spending level (per day):",
          "  CR 0: $0.50",
          "  CR 1–9: $2",
          "  CR 10–49: $10",
          "  CR 50–89: $50",
          "  CR 90–98: $250",
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
                Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO,
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.ACCESS_WIFI_STATE,
                Permission.CHANGE_WIFI_MULTICAST_STATE
            ])
        except:
            pass

    def has_all_files_access():
        """Check if the app has MANAGE_EXTERNAL_STORAGE (Android 11+).
        Returns True if yes, False if no, None if not Android or not relevant."""
        if platform != 'android':
            return None
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            Build = autoclass('android.os.Build$VERSION')
            # Only relevant on Android 11 (API 30) and later
            if Build.SDK_INT < 30:
                return None
            return bool(Environment.isExternalStorageManager())
        except Exception as e:
            log(f"has_all_files_access check failed: {e}")
            return None

    def request_all_files_access():
        """Open Android settings where the user can grant the app
        'All files access'. Requires Android 11+ and that the app
        declares MANAGE_EXTERNAL_STORAGE in the manifest."""
        if platform != 'android':
            return False
        try:
            from jnius import autoclass
            PythonActivity = autoclass(
                'org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            activity = PythonActivity.mActivity
            package = activity.getPackageName()
            try:
                intent = Intent(
                    Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                intent.setData(Uri.parse(f"package:{package}"))
                activity.startActivity(intent)
            except Exception:
                # Fallback: general "All files access" screen
                intent = Intent(
                    Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                activity.startActivity(intent)
            return True
        except Exception as e:
            log(f"request_all_files_access failed: {e}")
            return False

    def load_json(p, d=None):
        """Safely load JSON from *p*.

        Handles missing files, empty files, and malformed JSON without
        crashing – all failures are logged and the caller-supplied
        default *d* is returned instead.  When *d* is ``None`` (the
        default) an empty list is returned as the fallback value.
        """
        default = d if d is not None else []
        if not os.path.exists(p):
            return default
        try:
            with open(p, 'r', encoding='utf-8') as f:
                text = f.read()
            if not text.strip():
                log(f"load_json: empty file – {p}")
                return default
            return json.loads(text)
        except json.JSONDecodeError as e:
            log(f"load_json: {type(e).__name__} in {p}: {e}")
            return default
        except Exception as e:
            log(f"load_json: error reading {p}: {type(e).__name__}: {e}")
            return default

    def save_json(p, d):
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"save_json failed ({p}): {type(e).__name__}: {e}")

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
            # Bind text_size to label width so it adapts to rotation
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
        and the user can choose from anywhere (Documents, Downloads, Google Drive, etc.).
        """
        REQUEST_CODE = 7331

        def __init__(self):
            self.callback = None
            self._activity = None
            self._bound = False

        def _ensure_bound(self):
            """Attach Android activity-result listener."""
            if self._bound or platform != 'android':
                return
            try:
                from jnius import autoclass
                PythonActivity = autoclass(
                    'org.kivy.android.PythonActivity')
                self._activity = PythonActivity.mActivity
                # Register callback for activity result
                from android import activity as android_activity
                android_activity.bind(
                    on_activity_result=self._on_result)
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
                self._activity.startActivityForResult(
                    intent, self.REQUEST_CODE)
            except Exception as e:
                log(f"FilePicker pick error: {e}")
                callback(False, f"Could not open file picker: {e}")

        def _on_result(self, request_code, result_code, intent):
            """Receive result from file picker."""
            if request_code != self.REQUEST_CODE:
                return
            cb = self.callback
            self.callback = None
            if cb is None:
                return
            # RESULT_OK = -1, RESULT_CANCELED = 0
            if result_code != -1 or intent is None:
                Clock.schedule_once(
                    lambda dt: cb(False, "Aborted"), 0)
                return
            try:
                from jnius import autoclass
                uri = intent.getData()
                if uri is None:
                    Clock.schedule_once(
                        lambda dt: cb(False, "No file selected"), 0)
                    return
                # Open input stream via content resolver
                resolver = self._activity.getContentResolver()
                stream = resolver.openInputStream(uri)
                # Read content (byte-wise via InputStreamReader)
                BufferedReader = autoclass(
                    'java.io.BufferedReader')
                InputStreamReader = autoclass(
                    'java.io.InputStreamReader')
                reader = BufferedReader(
                    InputStreamReader(stream, 'UTF-8'))
                sb = []
                line = reader.readLine()
                while line is not None:
                    sb.append(line)
                    line = reader.readLine()
                    if line is not None:
                        sb.append('\n')
                reader.close()
                stream.close()
                text = ''.join(sb)
                Clock.schedule_once(
                    lambda dt: cb(True, text), 0)
            except Exception as e:
                log(f"FilePicker read error: {e}")
                err = f"Reading failed: {type(e).__name__}: {e}"
                Clock.schedule_once(
                    lambda dt: cb(False, err), 0)

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
            self.chars = load_json(CHAR_FILE, [])
            self.edit_idx = None

            # Weapons: favorites file goes in app-private storage (always writable)
            self.WEAPONS_FAV_FILE = os.path.join(
                self.user_data_dir, "weapons_favorites.json")
            # Scenario: also app-private (avoids scoped storage errors
            # when reading .json in /sdcard/Documents/ on Android 13+)
            self.SCENARIO_FILE = os.path.join(
                self.user_data_dir, "scenario.json")
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
            self._weap_char_target = -1

            # FloatLayout as root – allows us to overlay splash on top
            wrapper = FloatLayout()

            main = BoxLayout(orientation='vertical', spacing=0,
                             size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            main.add_widget(Widget(size_hint_y=None, height=dp(30)))

            # TABS
            tabs = RBox(size_hint_y=None, height=dp(52), spacing=dp(4),
                        padding=[dp(8), 0], bg_color=BTN)
            self._tabs = {}
            for key, txt in [('img','Images'),('snd','Sound'),('cmb','Combat'),('tool','Tools'),('rules','Rules'),('cast','Cast')]:
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

            # MINI-PLAYER
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
            self.splash.add_widget(Widget())  # fill top
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
            self.splash.add_widget(Widget())  # fill bottom
            wrapper.add_widget(self.splash)

            self._tab('img')
            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            # Fade out splash after 2.5 seconds
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
            """Load weapon data. Try external first (user's own),
            fall back to bundled version."""
            # Attempt 1: external file in /sdcard/Documents/EldritchPortals/
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
                    log("_weap_do_load: external exists but no access, using bundled")
                except Exception as e:
                    log(f"_weap_do_load: external error ({e}), using bundled")
            # Attempt 2: bundled file (packed into APK)
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
            # Black background behind preview image
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
            self.ac_btn = mkbtn(f"AC:{'ON' if self.auto_cast else 'OFF'}", self._toggle_ac, accent=True, small=True, size_hint_x=0.25)
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
                              "permissions have been granted.",
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
                              "Documents/EldritchPortals/images/\n\n"
                              "Tip: create subfolders\n"
                              "to organize by scenario,\n"
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

        # ---------- COMBAT (Initiative + Map sub-tabs) ----------
        def _mk_combat(self):
            """Combat tab with sub-tabs: Initiative and Map."""
            self._init_tracker_init()
            if not hasattr(self, '_cmb_sub'):
                self._cmb_sub = 'init'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab bar
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

            # Content area — serves as "tool_area" for init tracker
            # and as container for map view.
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
            # Point init tracker's target to cmb_area
            self._init_target_area = self._cmb_area
            if self._cmb_sub == 'init':
                self._mk_init_tracker()
            else:
                self._mk_cmb_map()

        def _mk_cmb_map(self):
            """Map sub-tab: open battlemap or show info about empty list."""
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

            # Info about the list
            n_pc = sum(1 for e in self._init_list
                       if e.get('type') == 'PC')
            n_npc = sum(1 for e in self._init_list
                        if e.get('type') == 'NPC')
            n_enemy = sum(1 for e in self._init_list
                          if e.get('type') == 'Enemy')
            n_s = sum(1 for e in self._init_list
                      if e.get('type') == 'S')

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
                summary.append(f"{n_npc} NPC(s)")
            if n_enemy:
                summary.append(f"{n_enemy} enemy(s)")
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
                    "Go to the Initiative tab and press 'Complete' "
                    "to start round order.",
                    color=DIM, size=10, wrap=True))
            p.add_widget(info_box)

            # Open button
            p.add_widget(mkbtn("Open map (fullscreen)",
                               self._bm_open, accent=True,
                               size_hint_y=None, height=dp(56)))

            p.add_widget(mklbl(
                "The map opens as an overlay in full screen width. "
                "Use 'Close' to return here.",
                color=DIM, size=10, wrap=True, h=40))

            p.add_widget(Widget())
            self._cmb_area.add_widget(p)

        # ---------- SOUND (combined Music + Ambient) ----------
        def _mk_sound(self):
            """Sound tab with toggle between Music and Ambient."""
            if not hasattr(self, '_sound_sub'):
                self._sound_sub = 'mus'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab bar
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

            # Content area
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

        # ---------- MUSIC ----------
        def _mk_mus(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            self.trk_lbl = Label(text="Select a track", font_size=sp(14), color=DIM,
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
                              "permissions have been granted.",
                              color=DIM, size=11, wrap=True))
                    return
                fl = sorted([f for f in os.listdir(MUSIC_DIR)
                             if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.trk_lbl.text = f"{len(fl)} tracks"
                if not fl:
                    self.trk_grid.add_widget(
                        mklbl("No music files found.\n\n"
                              "Place audio files in:\n"
                              "Documents/EldritchPortals/music/\n\n"
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
            p.add_widget(mkbtn("Stop ambient", self._sa, danger=True,
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
            """Collapsible folder view with overlay for content."""
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

            # Overlay container (invisible until content is opened)
            self._rules_main = p
            self._rules_build_tree()
            return p

        def _rules_build_tree(self):
            """Build the folder tree with open/closed folders."""
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
            """Show rule content as overlay."""
            cat_name, icon, subs = RULES[cat_idx]
            sub_name, content = subs[sub_idx]

            # Remove existing overlay if any
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

            # Lay overlay over the entire content area
            # Use FloatLayout wrapper (root)
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
            """Close rule content overlay."""
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
                p.add_widget(mklbl("Casting unavailable\npychromecast missing", color=DIM, size=13))
                return p
            self.cast_lbl = mklbl("Not connected", color=DIM, size=13, h=30)
            p.add_widget(self.cast_lbl)
            p.add_widget(mkbtn("Search for devices", self._scan, accent=True,
                               size_hint_y=None, height=dp(46)))
            self.cast_sp = Spinner(text="Select device...", values=[],
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
            if not n or n == "Select device...":
                return
            self.cast.connect(n, cb=lambda ok: setattr(
                self.cast_lbl, 'text', "Connected!" if ok else "Failed"))

        def _dc(self):
            self.cast.disconnect()
            self.cast_lbl.text = "Disconnected"

        # ---------- CHARACTERS / TOOLS ----------
        def _mk_tool(self):
            """Tools tab with sub-tabs: Characters, Weapons, Scenario."""
            self._scen_init()
            # Migrate away from old 'init' sub-tab if left over
            if not hasattr(self, '_tool_sub') or self._tool_sub == 'init':
                self._tool_sub = 'chars'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab bar
            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))
            self._sub_btn_chars = RToggle(
                text='Characters', group='tool_sub',
                state='down' if self._tool_sub == 'chars' else 'normal',
                bg_color=BTNH if self._tool_sub == 'chars' else BTN,
                color=GOLD if self._tool_sub == 'chars' else DIM,
                font_size=sp(11), bold=True)
            self._sub_btn_chars.bind(on_release=lambda b: self._tool_switch('chars'))
            sub_bar.add_widget(self._sub_btn_chars)

            self._sub_btn_weap = RToggle(
                text='Weapons', group='tool_sub',
                state='down' if self._tool_sub == 'weap' else 'normal',
                bg_color=BTNH if self._tool_sub == 'weap' else BTN,
                color=GOLD if self._tool_sub == 'weap' else DIM,
                font_size=sp(11), bold=True)
            self._sub_btn_weap.bind(on_release=lambda b: self._tool_switch('weap'))
            sub_bar.add_widget(self._sub_btn_weap)

            self._sub_btn_scen = RToggle(
                text='Scenario', group='tool_sub',
                state='down' if self._tool_sub == 'scen' else 'normal',
                bg_color=BTNH if self._tool_sub == 'scen' else BTN,
                color=GOLD if self._tool_sub == 'scen' else DIM,
                font_size=sp(11), bold=True)
            self._sub_btn_scen.bind(on_release=lambda b: self._tool_switch('scen'))
            sub_bar.add_widget(self._sub_btn_scen)

            p.add_widget(sub_bar)

            # Action bar
            self._tool_action_bar = BoxLayout(
                size_hint_y=None, height=dp(42),
                spacing=dp(6), padding=[dp(6), 0])
            p.add_widget(self._tool_action_bar)

            self.tool_area = BoxLayout()
            p.add_widget(self.tool_area)

            # When in the Tools tab the init tracker (if called)
            # uses this tool_area — but since init sub-tab is removed,
            # this shouldn't happen. Set target to None for safety.
            self._init_target_area = None

            self._tool_render_sub()
            return p

        def _tool_switch(self, which):
            """Switch between characters, weapons and scenario."""
            self._tool_sub = which
            for key, btn in (('chars', self._sub_btn_chars),
                             ('weap',  self._sub_btn_weap),
                             ('scen',  self._sub_btn_scen)):
                active = (key == which)
                btn.state    = 'down'   if active else 'normal'
                btn.bg_color = BTNH     if active else BTN
                btn.color    = GOLD     if active else DIM
            self._tool_render_sub()

        def _tool_render_sub(self):
            """Render the appropriate sub-view."""
            self._tool_action_bar.clear_widgets()
            if self._tool_sub == 'chars':
                self._tool_action_bar.add_widget(
                    mkbtn("+ New", self._new_char, accent=True,
                          size_hint_x=0.28))
                self._tool_action_bar.add_widget(
                    mkbtn("Import", self._chars_do_pick_file,
                          small=True, size_hint_x=0.28))
                self._tool_action_bar.add_widget(
                    mkbtn("Refresh", self._show_list,
                          small=True, size_hint_x=0.22))
                self._tool_action_bar.add_widget(
                    mklbl("Characters", color=GOLD, size=14, bold=True))
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
                g.add_widget(mklbl("No characters yet.\nPress '+ New' to create one.",
                                   color=DIM, size=12, h=50))
            else:
                for i, ch in enumerate(self.chars):
                    nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
                    c = GRN if tp == 'PC' else (GOLD if tp == 'NPC' else RED)
                    txt = f"[{tp}]  {_first_last_name(nm)}"
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

        def _view_char(self, idx, back_fn=None):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            _back = back_fn if back_fn is not None else self._show_list
            top.add_widget(mkbtn("Back", _back, small=True, size_hint_x=0.3))
            if back_fn is None:
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
            # Characteristics with individual frames
            stats_list = [(lbl, ch[key]) for key, lbl in CHAR_STATS if ch.get(key)]
            if stats_list:
                g.add_widget(mksep(4))
                g.add_widget(mklbl("CHARACTERISTICS", color=GOLD, size=13, bold=True, h=24))
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
            self.chars.append({"name": "New character", "type": "PC", "skills": {}})
            save_json(CHAR_FILE, self.chars)
            self._edit_char(len(self.chars) - 1)

        def _edit_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            self.edit_idx = idx
            self._weap_char_target = idx
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
                    w = Spinner(text=ch.get(key, 'PC'), values=['PC', 'NPC', 'Enemy'],
                                background_color=BTN, color=GOLD, font_size=sp(11), size_hint_x=0.7)
                else:
                    w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                  background_color=BTN, foreground_color=TXT,
                                  size_hint_x=0.7, padding=[dp(6), dp(4)])
                self._ei[key] = w
                row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("CHARACTERISTICS", color=GOLD, size=12, bold=True, h=24))
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
            g.add_widget(mklbl("NOTES / EQUIPMENT", color=GOLD, size=12, bold=True, h=24))
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
            save_json(CHAR_FILE, self.chars)
            self._edit_char(idx)

        def _save_edit(self):
            if self.edit_idx is None or self.edit_idx >= len(self.chars):
                return
            ch = self.chars[self.edit_idx]
            for key, w in self._ei.items():
                ch[key] = w.text if isinstance(w, (TextInput, Spinner)) else ''
            save_json(CHAR_FILE, self.chars)
            self._show_list()

        def _del_char(self, idx):
            if 0 <= idx < len(self.chars):
                self.chars.pop(idx)
                save_json(CHAR_FILE, self.chars)
                self._show_list()

        # ---------- CHARACTER IMPORT ----------

        def _chars_do_pick_file(self):
            """Open Android file picker for character import."""
            if platform != 'android':
                self._chars_show_message(
                    "Not supported",
                    "File picker is only available on Android.",
                    is_error=True)
                return
            self._chars_show_message(
                "Opening file picker...",
                "Select a .json file with characters. You can browse to "
                "Documents, Downloads, Drive, or anywhere you have the file.",
                is_error=False)
            Clock.schedule_once(
                lambda dt: self._chars_close_overlay(), 0.8)
            Clock.schedule_once(
                lambda dt: self.file_picker.pick(
                    self._chars_on_file_picked,
                    mime_type='*/*'),
                1.0)

        def _chars_on_file_picked(self, ok, text_or_err):
            """Callback when the file picker is done."""
            if not ok:
                if text_or_err != "Aborted":
                    self._chars_show_message(
                        "Could not read file",
                        text_or_err, is_error=True)
                return
            try:
                data = json.loads(text_or_err)
            except json.JSONDecodeError as e:
                self._chars_show_message(
                    "Invalid JSON",
                    f"The file is not valid JSON:\n{e}",
                    is_error=True)
                return
            # Support both bare array and wrapped { "characters": [...] }
            if isinstance(data, list):
                raw_chars = data
            elif isinstance(data, dict) and isinstance(
                    data.get('characters'), list):
                raw_chars = data['characters']
            else:
                self._chars_show_message(
                    "Wrong format",
                    "The file must contain either a list [...] or an "
                    "object with a \"characters\" array "
                    "{ \"characters\": [...] }.",
                    is_error=True)
                return
            # Normalize entries; skip those without a name
            normalized = []
            skipped = 0
            for entry in raw_chars:
                if not isinstance(entry, dict):
                    skipped += 1
                    continue
                if not str(entry.get('name', '')).strip():
                    skipped += 1
                    continue
                normalized.append(self._chars_normalize_entry(entry))
            if not normalized:
                self._chars_show_message(
                    "No characters found",
                    "The file contained no valid character entries "
                    "with a name.",
                    is_error=True)
                return
            self._chars_show_import_preview(normalized, skipped)

        def _chars_normalize_entry(self, entry):
            """Normalize a raw character dict to the app's internal format."""
            all_str_fields = (
                [k for k, _ in CHAR_INFO]
                + [k for k, _ in CHAR_STATS]
                + [k for k, _ in CHAR_DERIVED]
                + [k for k, _ in CHAR_TEXT]
            )
            result = {}
            for field in all_str_fields:
                val = entry.get(field, '')
                result[field] = str(val) if val != '' else ''
            # Normalize type to one of 'PC', 'NPC', 'Enemy'
            raw_type = result.get('type', '').strip()
            if raw_type.lower() == 'pc':
                result['type'] = 'PC'
            elif raw_type.lower() == 'npc':
                result['type'] = 'NPC'
            elif raw_type.lower() in ('fiende', 'enemy', 'fiend', 'foe',
                                      'villain', 'monster', 'creature'):
                result['type'] = 'Enemy'
            else:
                result['type'] = raw_type if raw_type in ('PC', 'NPC', 'Enemy') else 'PC'
            # skills must be a dict
            sk = entry.get('skills', {})
            if not isinstance(sk, dict):
                sk = {}
            result['skills'] = sk
            # Preserve scenario-package extra fields
            for key in ('initiative', 'token'):
                if key in entry:
                    result[key] = entry[key]
            return result

        def _chars_show_import_preview(self, chars, skipped):
            """Show preview overlay before import."""
            count = len(chars)
            preview_names = [ch.get('name', '?') for ch in chars[:5]]
            names_text = "\n".join(f"• {n}" for n in preview_names)
            if count > 5:
                names_text += f"\n… and {count - 5} more"
            skip_text = (
                f"\n\n({skipped} entry"
                f"{'s' if skipped != 1 else ''} without name were "
                "skipped)"
            ) if skipped else ""

            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.9, 0.65),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.add_widget(mklbl(
                "Import characters",
                color=GOLD, size=14, bold=True, h=28))
            overlay.add_widget(mklbl(
                f"{count} character"
                f"{'s' if count != 1 else ''} found:"
                f"{skip_text}",
                color=TXT, size=11, wrap=True))

            scroll = ScrollView()
            names_lbl = mklbl(names_text, color=DIM, size=11, wrap=True)
            scroll.add_widget(names_lbl)
            overlay.add_widget(scroll)

            overlay.add_widget(mklbl(
                "How do you want to import?",
                color=GOLD, size=12, bold=True, h=22))

            btns = BoxLayout(
                size_hint_y=None, height=dp(44), spacing=dp(6))
            btns.add_widget(mkbtn(
                "Cancel", self._chars_close_overlay,
                small=True, size_hint_x=0.3))
            btns.add_widget(mkbtn(
                "Merge",
                lambda: self._chars_do_import(chars, replace=False),
                accent=True, size_hint_x=0.35))
            btns.add_widget(mkbtn(
                "Replace",
                lambda: self._chars_do_import(chars, replace=True),
                danger=True, size_hint_x=0.35))
            overlay.add_widget(btns)

            root = self.tool_area
            while root.parent and not isinstance(
                    root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCci, Rectangle as GRci
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCci(rgba=[0, 0, 0, 0.6])
                dr = GRci(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))

            self._chars_overlay = overlay
            self._chars_dim = dim
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _chars_do_import(self, chars, replace):
            """Perform import — replace existing or merge."""
            self._chars_close_overlay()
            if replace:
                self.chars = list(chars)
            else:
                self.chars = self.chars + list(chars)
            save_json(CHAR_FILE, self.chars)
            self._show_list()
            count = len(chars)
            mode = "Replaced with" if replace else "Added"
            self._chars_show_message(
                "Import successful",
                f"{mode} {count} character"
                f"{'s' if count != 1 else ''}.",
                is_error=False)

        def _chars_show_message(self, title, msg, is_error=False):
            """Show a message as overlay in the characters tab."""
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
                "OK", self._chars_close_overlay,
                accent=True, size_hint_y=None, height=dp(44)))

            root = self.tool_area
            while root.parent and not isinstance(
                    root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCcm, Rectangle as GRcm
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCcm(rgba=[0, 0, 0, 0.6])
                dr = GRcm(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t:
                     self._chars_close_overlay() or True)

            self._chars_dim = dim
            self._chars_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _chars_close_overlay(self):
            """Close character import overlay."""
            ov = getattr(self, '_chars_overlay', None)
            dm = getattr(self, '_chars_dim', None)
            if ov and ov.parent:
                ov.parent.remove_widget(ov)
            if dm and dm.parent:
                dm.parent.remove_widget(dm)
            self._chars_overlay = None
            self._chars_dim = None

        # ---------- INITIATIVE TRACKER (CoC / Pulp Cthulhu) ----------
        def _init_tracker_init(self):
            """Initialize state for initiative tracker."""
            if not hasattr(self, '_init_phase'):
                self._init_phase = 'setup'
                self._init_list = []
            # target_area overridden by Combat tab to self._cmb_area
            if not hasattr(self, '_init_target_area'):
                self._init_target_area = None

        def _init_area(self):
            """Return current container for initiative UI."""
            tgt = getattr(self, '_init_target_area', None)
            if tgt is not None:
                return tgt
            return self.tool_area

        def _mk_init_tracker(self):
            """Build initiative tracker UI."""
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
            top.add_widget(mkbtn("Empty", self._init_clear_list,
                                 danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)

            p.add_widget(mklbl(
                "DEX determines order. +50 if shooting with a handgun.",
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

                    # Type-chip (PC/NPC/S = creature)
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
            bottom.add_widget(mkbtn("Complete", self._init_finish,
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
            """Update +50 firearms toggle."""
            idx = inst._init_idx
            if 0 <= idx < len(self._init_list):
                on = (value == 'down')
                self._init_list[idx]['firearms'] = on
                inst.text = 'X' if on else ''
                inst.color = GOLD if on else DIM
                inst.bg_color = BTNH if on else INPUT

        def _init_show_char_picker(self):
            """Show Investigator picker."""
            already_in = {e.get('name', '') for e in self._init_list}
            pcs = [ch for ch in self.chars
                   if ch.get('type', 'PC') == 'PC'
                   and ch.get('name', '') not in already_in]
            npcs = [ch for ch in self.chars
                    if ch.get('type', 'PC') == 'NPC'
                    and ch.get('name', '') not in already_in]
            enemies = [ch for ch in self.chars
                       if ch.get('type', 'PC') == 'Enemy'
                       and ch.get('name', '') not in already_in]

            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Back", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Select character", color=GOLD, size=13,
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

            if enemies:
                g.add_widget(mklbl("ENEMIES",
                                   color=RED, size=11, bold=True, h=22))
                for ch in enemies:
                    g.add_widget(self._init_make_char_btn(ch))

            if not pcs and not npcs and not enemies:
                g.add_widget(mklbl(
                    "No characters available.\n"
                    "Add characters under 'Tools > Characters' first.",
                    color=DIM, size=11, h=60))

            scroll.add_widget(g)
            p.add_widget(scroll)
            area.add_widget(p)

        def _init_make_char_btn(self, ch):
            """Create button for a character in picker list."""
            nm = ch.get('name', '?')
            tp = ch.get('type', 'PC')
            txt = f"[{tp}]  {_first_last_name(nm)}"
            b = mkbtn(txt, lambda c=ch: self._init_add_character(c),
                      small=True)
            b.halign = 'left'
            b.size_hint_y = None
            b.height = dp(42)
            return b

        def _init_add_character(self, ch):
            """Add character to initiative list."""
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

        # Common enemies and creatures in Call of Cthulhu / Pulp Cthulhu.
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
            # --- Normal Animals ---
            ("Dog (guard)", 60, 8),
            ("Wolf", 75, 11),
            ("Bear", 50, 19),
            ("Puma", 85, 12),
            ("Snake (venomous)", 85, 4),
            ("Rat (large)", 60, 2),
            ("Rat-fungus", 90, 35),
            ("Crocodile", 50, 14),
            ("Shark", 80, 18),
            # --- Undead ---
            ("Zombie", 45, 12),
            ("Ghoul", 65, 13),
            ("Mummy", 50, 18),
            ("Vampire", 80, 15),
            ("Skeleton", 55, 10),
            ("Spectre", 70, 0),
            # --- Minor Mythos creatures ---
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
            ("Winged One (from Yuggoth)", 55, 14),
            ("Y'm-bhi (activated ghoul)", 55, 14),
            # --- Independent beings ---
            ("Elder Thing", 45, 28),
            ("Great Race of Yith", 25, 25),
            ("Yithian (in human host)", 50, 13),
            # --- Pulp-specific gangsters / pulp enemies ---
            ("Gangster (minion)", 55, 12),
            ("Gangster (boss)", 60, 14),
            ("Nazi officer", 65, 13),
            ("Nazi soldier", 60, 12),
            ("SS occultist", 65, 13),
            ("Pulp villain (mastermind)", 75, 15),
            ("Femme fatale", 75, 11),
            ("Private investigator (Pulp)", 70, 13),
        ]

        def _init_show_enemy_picker(self):
            """Show list of CoC enemies and creatures + custom."""
            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Back", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Select creature", color=GOLD, size=13,
                                 bold=True))
            p.add_widget(top)

            # Custom creature
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
            area.add_widget(p)

        def _init_add_enemy(self, name, dex, hp):
            """Add enemy from list. Increment if duplicate."""
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
            """Add custom creature."""
            name = self._init_custom_name.text.strip()
            if not name:
                return
            try:
                dex = int(self._init_custom_dex.text or '0')
            except ValueError:
                dex = 0
            self._init_add_enemy(name, dex, '')

        def _init_remove_entry(self, idx):
            """Remove participant from list."""
            if 0 <= idx < len(self._init_list):
                self._init_list.pop(idx)
                self._mk_init_tracker()

        def _init_clear_list(self):
            """Clear the whole list."""
            self._init_list = []
            self._init_phase = 'setup'
            self._mk_init_tracker()

        def _init_finish(self):
            """Transition from setup to active: sort by effective DEX."""
            # Effective DEX = DEX + 50 if firearms
            for entry in self._init_list:
                base = entry.get('dex', 0)
                entry['effective'] = base + (50 if entry.get('firearms') else 0)
            # Sort highest first (CoC rule: high DEX goes first)
            # Tiebreak: higher base DEX, then alphabetical name
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
            top.add_widget(mkbtn("New round", self._init_new_encounter,
                                 danger=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Edit", self._init_back_to_setup,
                                 small=True, size_hint_x=0.25))
            top.add_widget(mkbtn("Map", self._bm_open,
                                 accent=True, small=True, size_hint_x=0.25))
            top.add_widget(mklbl("Turn", color=GOLD, size=12, bold=True))
            p.add_widget(top)

            p.add_widget(mklbl(
                "Tap the active (topmost) to end their turn.",
                color=DIM, size=10, h=18))

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(4),
                           size_hint_y=None)
