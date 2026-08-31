# Image prompts

Eleven image slots in the README. Each prompt below is self contained, so copy
one block at a time. After generating, save the file to the path named in the
README comment block, delete that comment block, and uncomment the `<img>` line
inside it.

**Before using any chart image, check every digit against the numbers written in
its prompt.** Image tools scramble numerals routinely, and the most common
failures are a decimal point moving or `0.867` coming back as `0.687`.

Shared palette: background `#FAF9F5`, text and lines `#141413`, orange `#F37338`,
red `#EB001B`, green `#0A8150`, blue `#2F5FB3`.

---

## Image 1 · Hero banner
`docs/images/01-hero.png` · 1200 x 300 (4:1)

```
A single elegant abstract composition representing an endless loop in payment
security: two opposing arcs forming one continuous circle, one arc deep red and
one arc ink black, with small geometric diamond shapes traveling along both arcs
in opposite directions. The circle sits on the right side of the frame with
generous empty space on the left.

Style: modern enterprise finance illustration, flat vector, warm off white
background, ink black linework, deep red and warm orange as the only accent
colors, thin precise strokes, lots of empty space, calm and premium like a
Mastercard annual report.

Do not include: any text, letters, words, numbers, labels, logos, watermarks,
charts, graphs, screenshots, neon, glowing circuits, hooded figures, falling
green code, padlock icons, 3D render, photorealism.
```

---

## Image 2 · The old test was too easy
`docs/images/02-test-too-easy.png` · 16:9

```
A clean minimal grouped bar chart on a warm off white background.

Title in bold black at top left: "We caught our own test being too easy"
Subtitle in grey beneath it: "Score of a single simple rule, compared with our
full detection system"
A short orange underline between the title and subtitle.

Three pairs of vertical bars. In each pair the left bar is deep red and the right
bar is dark green, with a bold value label above each bar:
Group 1 labelled "One simple rule": red bar 1.000, green bar 0.583
Group 2 labelled "Simplest possible model": red bar 1.000, green bar 0.584
Group 3 labelled "Our full system": red bar 1.000, green bar 0.867

Y axis labelled "Accuracy score (F1)" running 0.0 to 1.2.
Legend at top centre: red swatch "Old version (too easy)", green swatch "Rebuilt
version (realistic)".
Small grey italic caption at the bottom: "In the old version, fraud and normal
payments had score ranges that never overlapped."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, rounded bar tops, thin light horizontal gridlines,
no plot border, generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, drop shadows, dark background, watermark, logo.
```

---

## Image 3 · Tested on real payments
`docs/images/03-real-data.png` · 16:9

```
A clean minimal two line chart on a warm off white background.

Title in bold black at top left: "Tested on 284,807 real payments"
Subtitle in grey beneath it: "Public credit card fraud dataset with 492 real
frauds, tested on later data than it was trained on"
A short orange underline between the title and subtitle.

X axis labelled "Alerts reviewed per day" with ticks at 50, 100, 200, 400, 800,
1600, 3200. Y axis labelled "Share" running 0.0 to 1.0.

A dark green line with round markers labelled "Share of fraud caught", passing
through: 0.454, 0.750, 0.778, 0.787, 0.815, 0.833, 0.870. It rises steeply then
flattens.

A blue line with square markers labelled "Share of alerts that are real fraud",
passing through: 0.980, 0.810, 0.420, 0.213, 0.110, 0.056, 0.029. It falls
steadily from top left to bottom right.

The lines cross near the 100 tick. Legend in the top right corner, no box.
A small white callout box with a thin grey border and a short pointer line
touching the green line near the 100 tick, reading: "Catches 75% of fraud, and
81% of alerts are real. About 5 staff per million payments."

Small grey italic caption at the bottom: "Only 0.172% of these payments were
fraud, about 1 in 518."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, thin precise strokes, thin light horizontal
gridlines, no plot border, generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, area fill under lines, dark background,
watermark.
```

---

## Image 4 · Why it matters how rare fraud is
`docs/images/04-rare-fraud.png` · 16:9

```
A clean minimal single line chart on a warm off white background.

Title in bold black at top left: "Why it matters how rare fraud is"
Subtitle in grey beneath it: "How accurate our alerts are, depending on how
common fraud actually is"
A short orange underline between the title and subtitle.

X axis labelled "How common fraud is (%)" running from 0.1 on the left to 35 on
the right. Y axis labelled "Share of alerts that are real fraud" running 0.0 to
1.0.

A single deep red line with small round markers forming a smooth S curve from the
bottom left to the top right, passing through these points: at 0.1 percent the
value is 0.05, at 0.172 percent it is 0.07, at 0.5 percent it is 0.19, at 1
percent it is 0.31, at 5 percent it is 0.70, at 15 percent it is 0.89, at 35
percent it is 0.96.

Two markers are ringed with a thin black circle, each with a small white callout
box with a thin grey border:
Lower left ring at the 0.172 percent point: "0.172% fraud (real world), 7% of
alerts real"
Upper right ring at the 15 percent point: "15% fraud (our test), 89% of alerts
real"

Small grey italic caption at the bottom: "Same model, same settings. Only the
rarity of fraud changes."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, thin precise strokes, thin light horizontal
gridlines, no plot border, generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, area fill, dark background, watermark.
```

---

## Image 5 · The four stage loop
`docs/images/05-loop.png` · 1200 x 400 (3:1)

```
Four simple geometric shapes arranged in a ring: a circle, a triangle, a square
and a hexagon, evenly spaced, connected by thin curved arrows flowing clockwise
in one unbroken cycle. One of the four connecting arrows is drawn in warm orange
and slightly thicker than the other three. The shapes float on a plain background
with soft subtle shadows beneath them.

Style: modern enterprise finance illustration, flat vector, warm off white
background, ink black linework, warm orange accent, thin precise strokes, lots of
empty space, calm and premium.

Do not include: any text, letters, words, numbers, labels, logos, watermarks,
charts, graphs, screenshots, neon, glowing circuits, 3D render, photorealism.
```

Add the four labels yourself afterwards in Figma or Canva: **Find, Recreate,
Catch, Learn**. Image tools cannot spell reliably, so anything generated with
words in it will come out wrong.

---

## Image 6 · The three attacker types
`docs/images/06-attacker-types.png` · 1200 x 500 (12:5)

This is the most valuable conceptual image in the set. The third figure
disappearing into the background is literally the finding the section describes.

```
Three simple humanoid figures in a row, each built from stacked geometric shapes,
getting more refined from left to right. The left figure is crude and angular in
solid deep red, standing out sharply from the background. The middle figure is
smoother and warm orange, partly blending in. The right figure is elegant and
rendered in almost the same tone as the background, so it nearly disappears and
is visible only by a faint outline.

Style: modern enterprise finance illustration, flat vector, warm off white
background, ink black linework, deep red and warm orange accents, thin precise
strokes, lots of empty space, calm and premium.

Do not include: any text, letters, words, numbers, labels, logos, watermarks,
charts, graphs, screenshots, neon, glowing circuits, hooded figures, falling
green code, padlock icons, 3D render, photorealism.
```

---

## Image 7 · How much fraud we catch, by attacker skill
`docs/images/07-attacker-skill.png` · 16:9

```
A clean minimal horizontal bar chart on a warm off white background with exactly
three bars.

Title in bold black at top left: "How much fraud we catch, by attacker skill"
Subtitle in grey beneath it: "The overall number hides who is actually getting
through"
A short orange underline between the title and subtitle.

Three horizontal bars with rounded ends, a bold value label just to the right of
each bar end, and a two line category label to the left of each bar:
Top bar, dark green, reaching 97.9 percent of the axis. Left label "Naive / 45%
of fraud". Right label "97.9%".
Middle bar, warm orange, reaching 87.4 percent. Left label "Intermediate / 35% of
fraud". Right label "87.4%".
Bottom bar, deep red, reaching only 50.3 percent. Left label "Advanced (copies
real behaviour) / 20% of fraud". Right label "50.3%".

X axis labelled "Share of fraud caught" running 0.0 to 1.0.
Small grey italic caption at the bottom: "Skilled attackers score between 0.58
and 0.96, which sits almost entirely inside the normal customer range."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, thin light vertical gridlines, no plot border,
generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, drop shadows, dark background, watermark.
```

---

## Image 8 · Fraud gangs sharing equipment
`docs/images/08-gangs.png` · 16:9

```
An abstract network diagram: about forty small circles connected by thin ink
black lines, spread out and loosely connected across most of the frame. Within
that loose field there are three tight clusters where the circles are packed
close together and heavily interconnected, drawn in deep red so they stand out
clearly from the sparse black structure around them. Clean and mathematical, like
a figure from an academic paper, with plenty of empty space at the edges.

Style: modern enterprise finance illustration, flat vector, warm off white
background, ink black linework, deep red accents, thin precise strokes, calm and
premium.

Do not include: any text, letters, words, numbers, labels, logos, watermarks,
charts, graphs, screenshots, neon, glowing circuits, 3D render, photorealism.
```

---

## Image 9 · The attacker bots really do learn
`docs/images/09-bots-learning.png` · 16:9

```
A clean minimal three line chart on a warm off white background.

Title in bold black at top left: "The attacker bots really do learn"
Subtitle in grey beneath it: "How often attacker bots got past the detector,
round by round"
A short orange underline between the title and subtitle.

X axis labelled "Training round" running 0 to 60. Y axis labelled "Share of
attacks that got through" running 0.1 to 0.9.

Three lines, each drawn twice: a faint thin jagged version behind and a bold
smooth version in front.
Dark green line labelled "Account Takeover": starts near 0.51, rises to about
0.83 by round 60.
Blue line labelled "Card Testing": starts near 0.44, rises to about 0.86 by round
60.
Warm orange line labelled "Synthetic Identity": starts near 0.27, dips, then
rises to about 0.63 by round 30 and stays flat.

All three rise steeply in the first third then flatten into a noisy plateau.
Legend in the lower right with the heading "Attacker bot", no box.
Small grey italic caption at the bottom: "Faint lines are the raw round by round
results. Bold lines are a 7 round average to show the trend."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, thin precise strokes, thin light horizontal
gridlines, no plot border, generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, area fill, dark background, watermark.
```

---

## Image 10 · Fraud patterns change within 48 hours
`docs/images/10-drift.png` · 16:9

```
A clean minimal horizontal bar chart on a warm off white background with exactly
four bars.

Title in bold black at top left: "Fraud patterns change within 48 hours"
Subtitle in grey beneath it: "Detection quality over two days of real data, with
no retraining"
A short orange underline between the title and subtitle.

Four horizontal bars with rounded ends, a bold value label to the right of each
bar and a category label to the left:
Bar 1, dark green, labelled "Hours 34 to 37", value 0.759
Bar 2, dark green, labelled "Hours 37 to 40", value 0.839, the longest bar
Bar 3, dark green, labelled "Hours 40 to 44", value 0.812
Bar 4, deep red, labelled "Hours 44 to 48", value 0.391, dramatically shorter
than the other three so the drop is obvious at a glance

X axis labelled "Detection quality" running 0.0 to 1.0.
A small white callout box with a thin grey border and a short pointer arrow
touching the red bar, reading: "Detection quality halves in the last few hours.
This is why retraining matters."
Small grey italic caption at the bottom: "Measured on real data. A model that is
never updated gets noticeably worse within two days."

Style: flat editorial data visualisation, Swiss design, warm off white
background, ink black text, thin light vertical gridlines, no plot border,
generous white space, premium and uncluttered.

Do not include: neon, glow, 3D, drop shadows, dark background, watermark.
```

---

## Image 11 · Dashboard screenshot
`docs/images/11-dashboard.png` · no prompt, this is a real screenshot

Do not generate this one. Capture it from the running app.

Before capturing, set the app up so nothing reads zero:

1. Open the dashboard and wait until the counters climb off zero
2. Go to **MARL Adversaries** and press **Trigger Evolution Epoch** four or five
   times, so the curves have real shape
3. Go to **Adversarial Arena** and inject a few attacks so the feed is populated

Then capture the Overview screen with the full browser window, no bookmarks bar,
zoom at 100 percent. On macOS use `Cmd + Shift + 4`, then press `Space`, then
click the window.

A screenshot showing zeros suggests the demo does not work, which is worse than
having no screenshot at all.

---

## Practical notes

- Midjourney handles this flat editorial style best. With DALL-E or Ideogram,
  repeat "flat vector illustration" at the very start of the prompt as well,
  since those tools weight the opening words most heavily.
- If a result looks cluttered, append: `extremely minimal, no more than 12
  elements, at least 60 percent empty space`.
- Generate the charts at 16:9 and the hero at 4:1, then crop rather than letting
  the tool add bars at the sides.
- Check every number in a chart against the values in its prompt before using it.
