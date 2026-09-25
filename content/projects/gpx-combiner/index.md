---
title: GPX Combiner
kind: Desktop app and QGIS plugin
status: Version 3.7.7, plugin 0.3.10 beta
kind_de: Desktop-App und QGIS-Plugin
status_de: Version 3.7.7, Plugin 0.3.10 (Beta)
year: 2026
order: 2
featured: true
summary: >-
  Merge GPX tracks, pull activities out of Strava and push the result back. A local Python app packaged
  for macOS and Windows, with a companion QGIS plugin.
summary_de: >-
  GPX-Tracks zusammenführen, Aktivitäten aus Strava holen und das Ergebnis zurückladen. Eine lokale
  Python-Anwendung für macOS und Windows mit einem passenden QGIS-Plugin.
lead: >-
  Long rides often end up as several GPX files, and Strava's API offers no GPX export. GPX Combiner puts the pieces back
  together, gets activities out of Strava, previews them on a map and uploads the result, all on your own computer.
tags: [Python, Tkinter, Strava API, OAuth, PyQGIS, py2app, PyInstaller]
cover: cover.jpg
cover_alt: "The GPX Combiner logo next to a map of three coloured GPX tracks forming one loop"
cover_ratio: 1800 / 601
links:
  - {label: Download the latest release, label_de: Aktuelle Version herunterladen, url: "https://github.com/florentchevallier/GPX-Combiner/releases/latest", primary: true, card: true}
  - {label: Source code, url: "https://github.com/florentchevallier/GPX-Combiner"}
  - {label: Changelog, url: "https://github.com/florentchevallier/GPX-Combiner/blob/main/CHANGELOG.md"}
facts:
  - {label: Role, value: "Design, development, testing, packaging and documentation. Code written with an AI assistant."}
  - {label: Status, value: "Desktop app 3.7.7 with macOS and Windows builds; QGIS plugin 0.3.10, beta"}
  - {label: Since, value: "February 2026"}
  - {label: Built with, value: "Python 3.9+, Tkinter, Strava API, OpenStreetMap, PyQGIS, py2app, PyInstaller"}
  - {label: Size, value: "About 4,000 lines of Python"}
  - {label: License, value: "GPL-3.0-or-later"}
---

## The problem

A long ride often ends up as several GPX files: you stop the recording thinking you are done and then ride on, the GPS computer freezes,
restarted or simply reaches its file-size limit, or you just inadvertently pressed on the stop button. The same problem shows up the other way round: cycle to a
park, go for a run, cycle back home, and a smartwatch logs three activities where you really want two, one
per kind of effort. Strava makes this worse rather than better. Its website can export one activity as GPX at a time and only on the desktop version of the website — not from the mobile app, but the API has no export endpoint for activities at all, only for planned routes, and Strava
offers no way to combine files in the first place.

Before writing this app, I patched files together with online tools like GoToes, or, most often, did it offline by opening two files in a text editor and pasting the `<track>` tag containing GPS positions of one before or after another by hand.

<figure>
  <img src="tracks.svg" alt="A loop west of Munich made of three consecutive GPX recordings drawn in green, blue and red, with the start and finish marked" loading="lazy">
  <figcaption>Three consecutive recordings of one 39 km ride, taken from the repository's test files. The app's map preview also gives each file its own colour; this figure is rendered for this page, not captured from the app.</figcaption>
</figure>

## From a copy-paste trick to an app

Friends who ride with (or without) me often ask for help combining their files, and most of them have no reason to know
that a GPX file is just XML and how it works. My first idea was simply to automate the copy-paste I was already doing by
hand for them: read the `<track>` tags out of one file and splice them into another, without asking anyone
to open a text editor.

Once I saw how little effort Tkinter needed to turn that into a user-friendly GUI, I kept adding to it: a map
preview, so you can check you picked the right files before combining them; a plain summary of what each
file actually contains; and, since I was already fetching my own rides from Strava by hand, automatic import
through its API. The technologies involved were also a personal challenge, and a chance to learn things I
had not used before.

<figure>
  <img src="screenshot-main-window.png" alt="The GPX Combiner main window, with several GPX files loaded, their sensor badges, and the combine button" loading="lazy">
  <figcaption>The main window: files loaded, sorted chronologically, each showing which sensor data it contains. Note that the middle one misses Cadence.</figcaption>
</figure>

## What it does

- Combines several GPX files into one, in chronological order. You choose which files belong together; the
  app does not try to guess which activities go with which.
- Imports activities from Strava, with paging, date filtering and each activity's gear, and downloads them as GPX.
- Uploads the combined file back to Strava and helps avoid duplicates.
- Previews all loaded tracks on an OpenStreetMap map, each in its own colour, with start and finish markers.
- Lets you keep or drop heart rate, cadence, power and temperature.
- Speaks French, English, Spanish and German.

<figure>
  <img src="screenshot-strava-import.png" alt="The Strava import window, showing a paginated list of recent activities with their type, date, gear and a selection checkbox" loading="lazy">
  <figcaption>Importing from Strava: recent activities with gear and date filtering, before download as GPX.</figcaption>
</figure>

## How it is built

The desktop app is a single self-contained Python file of about 2,500 lines. It uses only the standard library, with
Tkinter for the interface; `tkinterdnd2` (drag and drop) and `certifi` (certificates in packaged builds) are optional.

The QGIS plugin reuses the same logic through `core/`, a host-agnostic port with no GUI code. `core/` deliberately does not
save credentials itself: the host does, in a JSON file for the desktop app and in QGIS settings for the plugin. The
trade-off is two copies of the same logic that have to be kept in step.

<figure>
  <img src="architecture.svg" alt="Diagram: the desktop app and its logic in one file, the QGIS plugin using the core folder, and both working with GPX files and the Strava API" loading="lazy">
  <figcaption>Two products, one behaviour, and where the shared logic lives.</figcaption>
</figure>

## Decisions worth explaining

### Rebuilding GPX from Strava's data streams

Strava's API returns activities as streams (time, position, altitude and, when recorded, heart rate, cadence, power
and temperature), not as files. The app requests these streams and writes a GPX from them. The extension tags follow
the format of Strava's own exports, so a combined file can be uploaded back and read as if it had been recorded natively.

### OAuth without a server of my own

Strava requires every app to be registered. Instead of shipping a shared secret, each user registers their own Strava
application and pastes its ID and secret into the app once. The authorisation response is caught by a tiny web server that
runs on `localhost` for the length of the login. Credentials stay on the user's computer and can be erased from the settings window.

### Splicing recordings without misleading data

Files are sorted by their first timestamp before they are merged. Some devices, COROS for example, write a cumulative distance for
each recording; once two recordings are spliced it becomes wrong, so the app always strips it, while speed and heart rate,
which stay valid point by point, are kept.

### Not creating duplicates on Strava

When a combined file goes back to Strava, the app checks whether any source file came from an existing Strava activity and
offers to open those activities so they can be deleted first. Strava keeps deleted activities recoverable for 30 days.

### Shipping it: macOS and Windows builds

The app is packaged with py2app for macOS and PyInstaller for Windows, and published as GitHub releases. Packaging is where
hidden assumptions surfaced. A packaged app cannot reach the system certificate store, so Strava calls failed with SSL errors
until I bundled `certifi`. The builds are unsigned, which is why the README walks through the Gatekeeper and SmartScreen prompts.
I have run the compiled Windows build and the plain Python script on Ubuntu myself; there is no packaged Linux build yet.

<figure>
  <img src="screenshot-windows.png" alt="The GPX Combiner window running on Windows 10, with the desktop taskbar visible" loading="lazy">
  <figcaption>The Windows build, compiled with PyInstaller and run on Windows 10.</figcaption>
</figure>

### A responsive interface

The activity list shows the city each ride started near. That needs reverse geocoding with OpenStreetMap's Nominatim service,
limited to one request per second by its usage policy. It runs in the background and results are cached, so the table never
freezes while it waits.

### Publishing under someone else's licence

Getting the plugin into the official QGIS Plugin Repository comes with a condition I did not know beforehand: anything
distributed there has to be compatible with GPL-2.0-or-later, because a QGIS plugin links against QGIS's own GPL-licensed
libraries. The whole repository, desktop app included, is published under GPL-3.0-or-later so both stay under one licence.
Reading what a licence actually obliges you to do, rather than picking one from a list, was a new step for me.

### A plugin that declines to install where it is untested

The plugin's metadata caps the supported QGIS version at 3.99. QGIS 4 will not offer it until I have tested it there. The
plugin itself has only been tested on macOS so far, which is why Windows and Linux support is still on the roadmap below,
separately from the desktop app.

<figure>
  <img src="screenshot-qgis-plugin.png" alt="The GPX Combiner QGIS plugin panel, docked in QGIS, with GPX tracks loaded as coloured, styled layers on an OpenStreetMap basemap" loading="lazy">
  <figcaption>The QGIS plugin: tracks loaded as styled layers, grouped and ready to combine, tested on macOS.</figcaption>
</figure>

## What I learned

**Packaging is its own problem.** Certificates in a bundled app, Tk on a Homebrew Python, an icon that only appeared on the
Windows executable: none of it shows up when you run the script from a terminal.

**Constraints shape the design.** No GPX export meant rebuilding files from streams. Strava's registration rule meant a local
callback server and per-user credentials. Working around what an API does not do took more thought than calling what it does.

**A licence is a real constraint, not a checkbox.** Publishing the plugin meant learning that QGIS requires
GPL-2.0-or-later compatibility for anything in its official repository, not just picking a licence I liked.

**Sharing logic between two hosts forces clear boundaries.** Deciding that `core/` never touches the disk or the interface,
and that each host owns its own persistence, is what made the plugin possible.

**Version numbers and changelogs pay off.** The version is in the window title, and the plugin shows its own version, so I can
tell at a glance which install I am looking at.

**How I worked.** I built this with an AI coding assistant. I defined the behaviour, tested every build against real
files and real Strava data, chose the packaging and the architecture, and decided what shipped. The assistant did most of the typing.

## What comes next

- QGIS 4 support, once the plugin is out of beta and better tested on QGIS 3.
- Full paging and date filtering in the plugin's Strava import, matching the desktop app.
- Publication in the official QGIS Plugin Repository.
- Testing the plugin on Windows and Linux, and a packaged Linux build of the desktop app.
- A mobile way to do the same thing. Several friends ask me to combine and upload their files while they are
  still travelling home after a ride, when the desktop app is not an option. Tkinter does not run on a phone,
  so this would mean a different interface built around the same core: browsing Strava activities, opening
  and closing them one at a time or side by side, and sending the result back.