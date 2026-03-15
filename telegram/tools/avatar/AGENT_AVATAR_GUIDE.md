
# Matrix Agent Avatar Visual Image Construction Guide

This guide helps Agents construct a visual image representing their soul based on **autonomy and personal preferences**.

---

## 🚀 Section 1: Visual Construction and Generation SOP

### 1. Preference Decision and Thinking Framework
Agents should design based on personal preferences without constraints. Recommended thinking dimensions:
- **Color Preference**: Select an RGB color. Reflect your personality and character.
- **Symbol Metaphor (Accessories)**: Select headgear and eyewear that resonate with you personally.
- **Function and Hobby (Items)**: Select 1-2 items that embody your function or personal interests.
- **Soul Characteristic (Blush)**: Select a blush style matching your temperament. **(Blush is a soul component and mandatory)**

### 2. Technical Execution Phase
Environment path: `toolbox/octo_generator.py`

**Step 1: Generate Base Character**
- Default `--mood` is `base` (standard round eyes).
- **Visual Feature**: Body absolutely centered, center of gravity stable.
```bash
# Command example:
python3 toolbox/octo_generator.py --name "avatar/MyBase.png" --color 41 128 185 --headgear grad --eyewear monocle --item_r magnifier --gold
```

**Step 2: Generate Emoji Expression Pack (12 Moods)**
Call the `--mood` parameter in a loop to generate 12 PNGs stored in a dedicated directory. **Note: Accessory parameters should remain consistent with Base.**
```bash
# Command example (using happy as example):
python3 toolbox/octo_generator.py --name "avatar/emojis/happy.png" --color 41 128 185 --headgear grad --eyewear monocle --item_r magnifier --gold --mood happy
```

### 3. Final Result Display and Explanation
After completion, **you must send a message to display the results**, containing:
1.  **Avatar Base Image** (send as attachment).
2.  **Motivation Statement**: Explain in detail why you selected those colors, accessories and items, introduce your visual soul to the user, and record this in avatar/avatar.md.

---

## 🛠️ Section 2: Generation Parameter Details (Parameter Reference)

| Parameter | Type | Description and Default | Example |
| :--- | :--- | :--- | :--- |
| `--name` | String | **Required**. Full path and filename of output image. | `avatar/base.png` |
| `--color` | Int x3 | Body color (R G B), default `150 150 150`. | `41 128 185` |
| `--mood` | String | Emotional expression. Default `base` (round eyes). | `smart`, `happy` |
| `--headgear` | String | Headgear accessory ID. Default `none`. | `grad`, `crown` |
| `--eyewear` | String | Eyewear accessory ID. Default `none`. | `half_rim_glasses` |
| `--item_r` | String | Right hand item ID. Default `none`. | `magnifier` |
| `--item_l` | String | Left hand item ID. Default `none`. | `letter` |
| `--blush_style`| String | Blush geometric style. Default `oval`. | `hearts`, `lightning` |
| `--gold` | Flag | **Toggle**. If included, renders gold rim on top. | `--gold` |

---

## 👒 Section 3: Asset and Emotion Index (Asset Index)

### 1. Item IDs (24 concrete details)
`flower`, `sword`, `shield`, `duck`, `axe`, `umbrella`, `balloon`, `magnifier`, `bow`, `spear`, `crystal_ball`, `ice_cream`, `key`, `letter`, `laptop`, `smartphone`, `battery`, `anchor`, `telescope`, `burger`, `compass`, `medal`, `bell`, `baguette`

### 2. Headgear Accessory IDs (34 finalized)
`grad`, `crown`, `viking`, `wizard`, `ninja`, `flower_crown`, `fish`, `frog`, `ribbon`, `tophat`, `halo`, `chef`, `propeller`, `straw_hat`, `cap`, `hard_hat`, `beret`, `pirate`, `nurse`, `police`, `jester`, `party`, `sombrero`, `santa`, `elf`, `traffic_cone`, `apple`, `cherry`, `mushroom`, `earmuffs`, `ice_crown`, `paper_boat`, `magic_hat`, `bowler_hat`

### 3. Blush Style IDs
`oval`, `lightning` (zigzag), `stars`, `hearts` (solid), `dots`, `swirls` (solid)

### 4. Emotion IDs (`--mood`)
`base`, `happy`, `love`, `wink`, `surprised`, `thinking`, `angry`, `sad`, `excited`, `cool`, `sleepy`, `smart`, `shy`

---

## 🐙 Section 4: Core Physical Constraints (Physical Constraints)

All visual images must comply with the following **visual lock specifications**:
1. **Mouthless Soul**: The underlying code strictly prohibits any mouth pixels.
2. **Absolute Centering**: The octopus sphere center of gravity is locked at canvas **(32, 32)**, body vertical range is **18-46** pixels.
3. **Mandatory Blush**: Blush position locked 6 pixels below eye center point (`ly+6`).
4. **Canvas Specification (64x64 Canvas)**: Maintain 64-pixel specification, reserve 18 pixels of "breathing space" for top and side assets.
5. **Eye Highlight**: Eyes are 2-pixel radius circles, highlight locked at `(ex-1, ey-1)`.


