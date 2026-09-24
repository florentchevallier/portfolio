---
title: GeOlympic Games
kind: Interactive web game
status: Prototype v0.5.6, playable online
kind_de: Interaktives Browserspiel
status_de: Prototyp v0.5.6, online spielbar
year: 2026
order: 1
featured: true
summary: >-
  Guess a city, an island or a sea from nothing but its real terrain. No labels, no names,
  just relief: a browser game that turns a topographic map into a recognition puzzle.
summary_de: >-
  Eine Stadt, Insel oder ein Meer allein am Relief erkennen, ohne Beschriftung und ohne Namen:
  ein Browserspiel, das eine topografische Karte in ein Ratespiel verwandelt.
lead: >-
  Every round shows a circular window onto real, unlabelled relief and asks one question: where is this?
  The project began as a test of whether topography alone can carry a recognition game, the way a flag or a
  street photo does.
tags: [JavaScript, MapLibre GL JS, OpenTopoMap, MapTiler, QGIS, Natural Earth]
cover: cover.jpg
cover_alt: "GeOlympic Games banner: the game's title carved in relief on a green topographic map"
cover_ratio: 1800 / 601
og_cover: true
links:
  - {label: Play the game, label_de: Spielen, url: "https://florentchevallier.github.io/GeOlympic-Games/", primary: true, card: true}
  - {label: Source code, url: "https://github.com/florentchevallier/GeOlympic-Games"}
embed:
  url: "https://florentchevallier.github.io/GeOlympic-Games/"
  title: GeOlympic Games, live prototype
  button: Play here
  open_label: Open full screen
  note: The map tiles come from OpenTopoMap and MapTiler and are only requested once you press play.
  height: 700
facts:
  - {label: Role, value: "Concept, game design, data selection and testing. Code written with an AI assistant."}
  - {label: Status, value: "Prototype v0.5.6, hosted on GitHub Pages"}
  - {label: Content, value: "60 cities, islands and seas in six series"}
  - {label: Built with, value: "MapLibre GL JS, OpenTopoMap relief tiles, MapTiler, Natural Earth, QGIS"}
  - {label: Format, value: "One HTML file, no build step, no backend"}
---

## The idea

Most geography games lean on a crutch: a labelled map, a flag, a street photo. I wanted to know whether the shape of
the land alone is enough. Can you recognise a city from the relief around it, the way you would recognise a face?

I looked at a few concepts before choosing one to prototype: rotating 3D country outlines, dragging a flag onto a map,
and a plain topographic map with every label removed. The flag game already exists elsewhere, so I dropped it, and
I built the unlabelled map first. A few iterations in, it worked. Mountain-locked cities, coastal cities, islands and
open seas each turned out to need their own mechanics, so the game is split into separate series with their own rules.

## How a round works

A session is eight rounds worth 1,000 points. Each round is 100 base points plus 25 for answering within five seconds
(three in the hard-timer mode). A wrong guess does not end the round: the circle zooms out one level and the base score
drops. You answer by multiple choice or by typing the name.

| Series | Places | What you see |
|---|---|---|
| Mountain cities | 13 | Real relief in a circle, with no coastline to lean on |
| Coastal cities | 14 | Relief with shoreline, bays and deltas |
| Islands, whole view | 21 | The island fitted to its outline and rotated at a random angle, one guess |
| Islands, relief | 21 | The zoomed circle applied to islands |
| Seas | 12 | A pannable patch of land relief around the sea, unlimited guesses |
| Seas, hard | 12 | Underwater topography only, with no visible coastline |

Places are chosen for how well their terrain reads, from well-known cases like Hong Kong and Cuba to more
distinctive ones like Sarajevo, Bogotá or Sulawesi. Islands whose shape gives the answer away, such as Australia
or Greenland, are left out on purpose.

## How it is built

The whole game is a single HTML file: no build step, no backend, no framework. It is hosted on GitHub Pages.

- **MapLibre GL JS** draws the map. It switches between two styles depending on the mode: an OpenTopoMap relief raster,
  which is genuinely free of place names, and a custom MapTiler bathymetric style for the hard sea mode.
- **Island outlines** come from Natural Earth (50 m) through `world-atlas` and `topojson-client`. Borneo and New Guinea
  are cut from the physical landmass rather than from a single country's polygon, so the shape is not truncated at a border.
- **Sea boundaries** are twelve polygons I drew by hand in QGIS, five to sixteen vertices each.

<figure>
  <img src="seas.svg" alt="Twelve hand-drawn sea polygons: Molucca, Adriatic, Tyrrhenian, Ligurian, Ionian, Aegean, Banda, Sulu, Celebes, Okhotsk, Baltic and Caribbean" loading="lazy">
  <figcaption>The twelve sea boundaries as drawn in QGIS, each scaled to its own cell.</figcaption>
</figure>

## Decisions worth explaining

### Sharper tiles by rendering twice as large

The map is drawn at twice its visible size and scaled back down with CSS. MapLibre therefore requests tiles one zoom
level finer, and a clean downsample looks sharp where an upscaled tile looks blurry. The extra level is capped at each
source's real maximum so the game never asks for tiles that do not exist. Padding values in the code have to be doubled
as well, because they are measured in that larger pixel space.

### No waiting between rounds

Waiting for tiles would eat into a fast player's speed bonus. While a round is played, the game drives a second,
invisible map to the next location, so the browser cache is already warm when the next round starts.

### A boundary that matches the sea

A map library limits panning to a rectangle, and a sea is not a rectangle. The bounding box of the Adriatic is mostly Italy
and the Balkans. The game therefore checks the player's view against the hand-drawn polygon in real time, and a red
vignette warns for as long as the view sits at or past the edge.

<figure>
  <img src="sea-limits.svg" alt="The Adriatic Sea inside its bounding rectangle, with the land inside the rectangle hatched, next to the nine-vertex polygon drawn by hand" loading="lazy">
  <figcaption>The Adriatic Sea: what a rectangular limit allows, and the polygon the game enforces instead.</figcaption>
</figure>

### One projection per kind of round

Terrain rounds use MapLibre's globe projection, which avoids Mercator's distortion near the poles and matters for Antarctica.
Seas and whole-island rounds use plain Mercator, because the globe's pan-boundary and rotated-fit maths were unreliable.
The code tracks the active projection and only switches when it really changes: switching in the middle of a camera move
produced a broken frame.

### A debug mode for the content

Adding `?debug` to the address steps through every place in every series, with direct access to each zoom level and each
viewpoint. It exists to catch bad viewpoints and badly drawn sea limits without playing full sessions.

## What I learned

**A place has to earn its spot.** Flat, dry cities such as Phoenix show almost nothing on a relief map, so Phoenix
was replaced by Athens. I now choose places for how well their terrain reads, not for how famous they are.

**The data source decides the game.** My first version used a custom MapTiler style, and the look was not what I had in mind.
While testing sources in QGIS I found a relief-only OpenTopoMap tile endpoint with no place names, which was exactly the
look I had in mind.

**Know where your data stops.** SRTM, the elevation model behind most relief tiles, does not cover polar latitudes, so
Antarctica mostly shows ice. The game therefore uses a few hand-picked coastal viewpoints there and never shows the whole continent.

**Playtesting drives the engineering.** The prefetching and the continuous warning at a sea's edge both exist because
playing the game showed what was wrong.

**How I worked.** I built this with an AI coding assistant. I wrote the brief for each iteration, chose the concept, the places
and the data, drew the sea boundaries, tested every build on real maps and decided what stayed. The assistant did most of the typing.

## What comes next

- Load the place data from GeoJSON files instead of keeping it in the HTML, so the list can grow.
- More series, rivers among them.
- Address the known limits: a simplified flag hint for multi-country islands, and no polar relief data for Antarctica.

## Data and credits

Relief tiles by [OpenTopoMap](https://opentopomap.org/) (CC-BY-SA), built on OpenStreetMap and SRTM data. Bathymetric style by
[MapTiler](https://www.maptiler.com/), built on OpenStreetMap data. Island geometry from
[Natural Earth](https://www.naturalearthdata.com/). Mapping library: [MapLibre GL JS](https://maplibre.org/).
