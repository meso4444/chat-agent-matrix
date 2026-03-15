
# Matrix Agent Avatar 視覺形象建構指南

本指南引導 Agents 基於 **自主意志與個人喜好**，建構代表其靈魂的視覺形象。

---

## 🚀 一、 形象建構與生成 SOP

### 1. 喜好決策與思考框架
Agent 應依據個人喜好進行設計，不應受到拘束。建議思考維度：
- **配色偏好 (Color)**：選取一組 RGB。反映你的性格與底色。
- **符號隱喻 (Accessories)**：選取具備個人認同感的頭飾與眼鏡。
- **職能與愛好 (Items)**：選取 1-2 件體現你職能或個人興趣的持物。
- **靈魂特徵 (Blush)**：選取符合氣質的腮紅樣式。**（腮紅為靈魂組件，為強制必備項）**

### 2. 技術執行階段
環境路徑：`toolbox/octo_generator.py`

**Step 1: 生成基礎 Character (Base)**
- 預設 `--mood` 為 `base` (標準圓眼)。
- **視覺特徵**：本體絕對置中，重心穩固。
```bash
# 指令範例：
python3 toolbox/octo_generator.py --name "avatar/MyBase.png" --color 41 128 185 --headgear grad --eyewear monocle --item_r magnifier --gold
```

**Step 2: 生成 Emoji 表情包 (12 Moods)**
循環調用 `--mood` 參數生成 12 款 PNG 並存於專屬目錄。**注意：配件參數應與 Base 保持一致。**
```bash
# 指令範例 (以 happy 為例)：
python3 toolbox/octo_generator.py --name "avatar/emojis/happy.png" --color 41 128 185 --headgear grad --eyewear monocle --item_r magnifier --gold --mood happy
```

### 3. 最終成果展示與說明 (Final Showcase)
完成生成後，**必須向使用者發送訊息展示成果**，內容需包含：
1.  **Avatar Base 圖檔** (作為附件發送)。
2.  **動機自述**：詳細說明為何選取該配色、配件與持物，向使用者介紹你的視覺靈魂，同時把此內容筆記在avatar/avatar.md。

---

## 🛠️ 二、 生成參數詳解 (Parameter Reference)

| 參數 | 類型 | 說明與預設值 | 範例 |
| :--- | :--- | :--- | :--- |
| `--name` | String | **必填**。產出圖檔的完整路徑與檔名。 | `avatar/base.png` |
| `--color` | Int x3 | 本體顏色 (R G B)，預設 `150 150 150`。 | `41 128 185` |
| `--mood` | String | 心情表情。預設 `base` (圓眼)。 | `smart`, `happy` |
| `--headgear` | String | 頭部配件 ID。預設 `none`。 | `grad`, `crown` |
| `--eyewear` | String | 眼部配件 ID。預設 `none`。 | `half_rim_glasses` |
| `--item_r` | String | 右手持物 ID。預設 `none`。 | `magnifier` |
| `--item_l` | String | 左手持物 ID。預設 `none`。 | `letter` |
| `--blush_style`| String | 腮紅幾何樣式。預設 `oval`。 | `hearts`, `lightning` |
| `--gold` | Flag | **開關**。若加入，將在頭頂渲染黃金鑲邊。 | `--gold` |

---

## 👒 三、 資產與情緒索引 (Asset Index)

### 1. 持物 ID (24 款具象細節)
`flower`, `sword`, `shield`, `duck`, `axe`, `umbrella`, `balloon`, `magnifier`, `bow`, `spear`, `crystal_ball`, `ice_cream`, `key`, `letter`, `laptop`, `smartphone`, `battery`, `anchor`, `telescope`, `burger`, `compass`, `medal`, `bell`, `baguette`

### 2. 頭部配件 ID (34 款定稿)
`grad`, `crown`, `viking`, `wizard`, `ninja`, `flower_crown`, `fish`, `frog`, `ribbon`, `tophat`, `halo`, `chef`, `propeller`, `straw_hat`, `cap`, `hard_hat`, `beret`, `pirate`, `nurse`, `police`, `jester`, `party`, `sombrero`, `santa`, `elf`, `traffic_cone`, `apple`, `cherry`, `mushroom`, `earmuffs`, `ice_crown`, `paper_boat`, `magic_hat`, `bowler_hat`

### 3. 腮紅樣式 ID
`oval`, `lightning` (鋸齒), `stars`, `hearts` (實心), `dots`, `swirls` (實心)

### 4. 情緒 ID (`--mood`)
`base`, `happy`, `love`, `wink`, `surprised`, `thinking`, `angry`, `sad`, `excited`, `cool`, `sleepy`, `smart`, `shy`

---

## 🐙 四、 核心物理約束 (Physical Constraints)

所有形象必須符合以下 **死鎖規範 (Visual Lock)**：
1. **無嘴靈魂 (Mouthless)**：底層代碼嚴禁出現任何嘴巴像素。
2. **絕對重心置中 (Absolute Centering)**：章魚球體重心鎖定在畫布 **(32, 32)**，本體垂直區間為 **18-46** 像素。
3. **強制腮紅 (Blush Mandatory)**：腮紅位置鎖定於眼睛中心點下方 6 像素處 (`ly+6`)。
4. **畫布規格 (64x64 Canvas)**：維持 64 像素規格，為頂部與側邊資產保留 18 像素的「呼吸空間」。
5. **眼部高光**：眼睛為半徑 2 像素圓形，高光點鎖定於 `(ex-1, ey-1)`。


