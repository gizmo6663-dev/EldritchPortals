# Eldritch Portals

**Keeper companion tool for Call of Cthulhu and Pulp Cthulhu — fully supported on Android.**

![Platform](https://img.shields.io/badge/platform-Android-green)
![System](https://img.shields.io/badge/system-CoC_7E_%2F_Pulp-purple)
![License](https://img.shields.io/badge/license-MIT-blue)

Eldritch Portals is an all-in-one app for Keepers who want to keep their session tools on a single phone. The app is designed for use **during live sessions** — optimized for fast lookups, atmosphere, and handling skill rolls during ongoing investigations.

**The app is completely free and always will be.** No ads, no in-app purchases, no data collection.

## About the developer and how the app was made

I am not a professional developer. Eldritch Portals was built by a hobbyist who wanted a practical tool for personal sessions, and most of the code was written with AI assistance (Claude). This is not hidden — I mention it because I believe users should know:

- **Advantages:** Development has moved quickly, which has made it possible to add features based on the needs of active campaigns. The code is well commented and structured.
- **Limitations:** I cannot always guarantee how the code behaves in every edge case, and I do not necessarily find bugs quickly on my own. Please report issues through [Issues](https://github.com/gizmo6663-dev/EldritchPortal/issues) — all feedback is appreciated.
- **If you can code:** Pull requests and suggestions are very welcome. The full source code is available here.

## Features

- **Investigator management** — full support for CoC 7E and Pulp Cthulhu character sheets (PCs and NPCs). Stores all 50+ skills, the 8 attributes (STR, CON, SIZ, DEX, INT, POW, APP, EDU), plus HP, MP, Sanity, and Luck. Pulp Talents, weapons, and backstory have dedicated fields.
- **Initiative tracker (DEX-based)** — build turn order according to CoC rules. Tap and choose from 85+ CoC and Pulp Cthulhu creatures (from Cultist to Shoggoth), or add custom entries. Firearms toggle for the +50 DEX bonus when using handguns.
- **Rules tab** — complete CoC 7E + Pulp Cthulhu Keeper reference: skill rolls, success levels, pushed rolls, opposed rolls, Sanity rules, combat, chases, Pulp Luck Spend, character creation, and more.
- **Image gallery** — folder-based gallery for scene art, NPC portraits, maps, and handouts. Cast to Chromecast for TV display.
- **Music player** — play local music with a mini player that follows you between tabs.
- **Ambient playback** — 30+ preselected streaming sources divided into Nature, Horror, Urban, and Mythos categories. Instant atmosphere.
- **Chromecast support** — send images and audio to a TV through a local HTTP server.

## Installation

**Prebuilt APK:** Download the latest build from [Releases](https://github.com/gizmo6663-dev/EldritchPortal/releases). You must allow installation from unknown sources on Android.

**Build it yourself:**
```bash
git clone https://github.com/gizmo6663-dev/EldritchPortal
cd EldritchPortal
# Via GitHub Actions: manually trigger the "Build APK" workflow
```

**Requirements:** Android 5.0+ (API 21 or higher). Tested on Samsung Galaxy S25 Ultra.

## Usage

The first time you open the app, it creates `/sdcard/Documents/EldritchPortal/` with subfolders for images and music. Place files there to make them appear in the app.

**Creating an investigator:**
1. Open the *Character* tab and tap *+ New*
2. Fill in the basic info and the 8 attributes
3. Calculate derived values (HP = (CON+SIZ)/10, MP = POW/5, SAN = POW, Luck is rolled separately)
4. Tap *Skills* and assign values. Cthulhu Mythos starts at 0, Credit Rating depends on occupation.

**Initiative during combat:**
1. Switch to the *Initiative* sub-tab
2. Tap *+ Investigator* to add saved characters (DEX is pulled automatically)
3. Tap *+ Creature* and choose from the list, or enter a custom one
4. Check +50 for anyone firing a handgun, then tap *Finish*
5. The top card is active — tap it to end that turn

## Data storage

All characters and custom files are stored locally on the phone. Nothing is sent to the internet (except Chromecast, which only sends to your own TV).

Data locations:
- `/sdcard/Documents/EldritchPortal/characters.json` — saved investigators and NPCs
- `/sdcard/Documents/EldritchPortal/images/` — custom images and handouts
- `/sdcard/Documents/EldritchPortal/music/` — custom music files

## Technical details

Written in Python with the Kivy framework. Android performance is handled through pyjnius (using Android MediaPlayer directly for streaming). Built with Buildozer through python-for-android.

**Main dependencies:** kivy, pillow, pychromecast, zeroconf, pyjnius

## Contributing

Suggestions and bug reports are welcome through [Issues](https://github.com/gizmo6663-dev/EldritchPortal/issues). If you are missing specific Mythos creatures in the initiative tracker or rules in the rules tab, open an issue.

## License

MIT — see the `LICENSE` file. The app is developed privately and is not affiliated with Chaosium Inc. Call of Cthulhu and Pulp Cthulhu are trademarks owned by Chaosium Inc. The rule references in the app are rewritten Keeper references, not reproductions of the rule text. Creatures and their statistics are based on publicly available CoC 7E/Pulp material.

## Related projects

- **[Campaign Forge](https://github.com/gizmo6663-dev/CampaignForge)** — sister app for Dungeons & Dragons 5E (2024).
