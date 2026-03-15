import argparse
import os
from PIL import Image, ImageDraw

def generate_octopus_final(filename, body_rgb=(150, 150, 150), 
                            mood="base", eyewear="none",
                            headgear="none", item_r="none", item_l="none", 
                            blush_style="oval", has_gold=False, size=64, scale=8):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = img.load(); draw = ImageDraw.Draw(img)
    B = (44, 44, 44, 255); GOLD = (255, 215, 0, 255); W = (255, 255, 255, 255)
    E = (0, 0, 0, 255); RED = (255, 90, 90, 255); BLUE = (52, 152, 219, 255)
    PINK = (255, 182, 193, 255); SKY = (135, 206, 235, 255); YELLOW = (255, 235, 59, 255)
    GREEN = (46, 204, 113, 255); BROWN = (121, 85, 72, 255); PURPLE = (155, 89, 182, 255)
    SILVER = (189, 195, 199, 255); TAN = (210, 180, 140, 255); ORANGE = (255, 127, 80, 255)

    # Body Centered at (32, 32), v11.96 logic
    body_color = (*body_rgb, 255)
    for y in range(size):
        for x in range(size):
            dist_sq = (x - 32)**2 + (y - 32)**2
            if dist_sq < 14**2:
                px[x, y] = body_color
                if has_gold and y < 26 and dist_sq > 12**2: px[x, y] = GOLD

    lx, ly = 24, 30; rx, ry = 40, 30
    blush_y = ly + 6; cur_blush_color = (255, 100, 150, 220); cur_blush_style = blush_style
    
    def draw_eye(ex, ey, eye_mood="standard"):
        if eye_mood == "standard": draw.ellipse([ex-2, ey-2, ex+2, ey+2], fill=E); px[ex-1, ey-1] = W
        elif eye_mood == "smile": draw.arc([ex-2, ey-2, ex+2, ey+2], start=200, end=340, fill=E, width=2)
        elif eye_mood == "closed": draw.line([ex-2, ey+1, ex+2, ey+1], fill=E, width=2); draw.point([ex+2, ey], fill=E)
        elif eye_mood == "heart": draw.polygon([(ex, ey+3), (ex-3, ey), (ex-1, ey-3), (ex, ey-1), (ex+1, ey-3), (ex+3, ey)], fill=RED); px[ex+1, ey-1] = W
        elif eye_mood == "star": draw.ellipse([ex-2, ey-2, ex+2, ey+2], fill=E); draw.line([ex-2, ey, ex+2, ey], fill=W); draw.line([ex, ey-2, ex, ey+2], fill=W)
        elif eye_mood == "angry": draw.polygon([(ex-2, ey-2), (ex+2, ey), (ex-2, ey+2)], fill=E)
        elif eye_mood == "smart": draw.rectangle([ex-3, ey-2, ex+3, ey+2], fill=W, outline=GOLD)

    if mood == "base": draw_eye(lx, ly); draw_eye(rx, ry)
    elif mood == "happy": draw_eye(lx, ly, "smile"); draw_eye(rx, ry, "smile")
    elif mood == "love": draw_eye(lx, ly, "heart"); draw_eye(rx, ry, "heart"); cur_blush_style="hearts"; draw.polygon([(32, 12), (30, 10), (31, 8), (32, 9), (33, 8), (34, 10)], fill=RED)
    elif mood == "wink": draw_eye(lx, ly, "closed"); draw_eye(rx, ry, "standard"); px[lx-3, ly-1]=YELLOW; px[lx-4, ly-2]=YELLOW
    elif mood == "surprised": draw.ellipse([lx-3, ly-3, lx+3, ly+3], fill=E); draw.ellipse([rx-3, ry-3, rx+3, ry+3], fill=E); px[lx-1, ly-1]=W; px[rx-1, ry-1]=W
    elif mood == "thinking": draw_eye(lx, ly); draw_eye(rx, ry); px[49,10]=YELLOW; px[50,10]=YELLOW; px[51,11]=YELLOW; px[50,12]=YELLOW; px[50,14]=YELLOW
    elif mood == "angry": draw_eye(lx, ly, "angry"); draw_eye(rx, ry, "angry"); cur_blush_color=(200, 50, 50, 220); px[44,24]=RED; px[46,24]=RED; px[45,23]=RED; px[45,25]=RED
    elif mood == "sad": draw.line([lx-2, ly+1, lx+2, ly+1], fill=E); draw.line([rx-2, ry+1, rx+2, ry+1], fill=E); px[lx-1, ly+3]=BLUE; px[lx-1, ly+4]=BLUE
    elif mood == "excited": draw_eye(lx, ly, "star"); draw_eye(rx, ry, "star"); px[lx-3, ly-3]=GOLD; px[rx+3, ry-3]=GOLD
    elif mood == "cool": draw.rectangle([lx-5, ly-2, rx+5, ry+2], fill=B, outline=SILVER); draw.line([lx-5, ly-1, rx+5, ly-1], fill=W)
    elif mood == "sleepy": draw.line([lx-2, ly, lx+2, ly], fill=E); draw.line([rx-2, ry, rx+2, ry], fill=E); px[48,12]=BLUE; px[50,10]=BLUE; px[52,8]=BLUE
    elif mood == "smart": draw_eye(lx, ly, "smart"); draw_eye(rx, ry, "smart"); draw.line([50, 10, 50, 14], fill=YELLOW); px[50, 16]=YELLOW; px[20, 21]=GOLD
    elif mood == "shy":
        # ABSOLUTELY SYMMETRIC > < (Height 7, Width 4)
        # Left Eye (>)
        draw.line([(22, 27), (26, 30), (22, 33)], fill=E, width=2)
        # Right Eye (<)
        draw.line([(42, 27), (38, 30), (42, 33)], fill=E, width=2)
        cur_blush_color=(255, 100, 150, 255); px[20, 24]=SKY

    for ox in [lx, rx]:
        if cur_blush_style == "oval": draw.ellipse([ox-2, blush_y, ox+2, blush_y+2], fill=cur_blush_color)
        elif cur_blush_style == "lightning":
            px[ox-2, blush_y]=cur_blush_color; px[ox-1, blush_y-1]=cur_blush_color; px[ox, blush_y]=cur_blush_color; px[ox+1, blush_y-1]=cur_blush_color; px[ox+2, blush_y]=cur_blush_color
        elif cur_blush_style == "stars":
            px[ox, blush_y-1]=cur_blush_color; px[ox-1, blush_y]=cur_blush_color; px[ox, blush_y]=cur_blush_color; px[ox+1, blush_y]=cur_blush_color; px[ox, blush_y+1]=cur_blush_color
        elif cur_blush_style == "hearts":
            px[ox-2, blush_y]=RED; px[ox-1, blush_y]=RED; px[ox+1, blush_y]=RED; px[ox+2, blush_y]=RED; px[ox-2, blush_y+1]=RED; px[ox-1, blush_y+1]=RED; px[ox, blush_y+1]=RED; px[ox+1, blush_y+1]=RED; px[ox+2, blush_y+1]=RED; px[ox-1, blush_y+2]=RED; px[ox, blush_y+2]=RED; px[ox+1, blush_y+2]=RED; px[ox, blush_y+3]=RED
        elif cur_blush_style == "dots": px[ox-2, blush_y+1]=cur_blush_color; px[ox, blush_y+1]=cur_blush_color; px[ox+2, blush_y+1]=cur_blush_color
        elif cur_blush_style == "swirls":
            draw.rectangle([ox-1, blush_y, ox+1, blush_y+2], fill=cur_blush_color)

    if eyewear == "monocle": draw.ellipse([rx-4, ry-4, rx+4, ry+4], outline=GOLD, width=1)
    elif eyewear == "monocle_left": draw.ellipse([lx-4, ly-4, lx+4, ly+4], outline=GOLD, width=1)
    elif eyewear == "glasses": draw.rectangle([lx-4, ly-4, lx+4, ly+4], outline=B); draw.rectangle([rx-4, ry-4, rx+4, ry+4], outline=B); draw.line([lx+4, ly, rx-4, ly], fill=B)
    elif eyewear == "round_glasses": draw.ellipse([lx-4, ly-4, lx+4, ly+4], outline=B); draw.ellipse([rx-4, ry-4, rx+4, ry+4], outline=B); draw.line([lx+4, ly, rx-4, ly], fill=B)
    elif eyewear == "half_rim_glasses":
        for ex, ey in [(lx, ly), (rx, ry)]: draw.line([ex-4, ey-3, ex+4, ey-3], fill=B); draw.line([ex-4, ey-3, ex-4, ey+1], fill=B); draw.line([ex+4, ey-3, ex+4, ey+1], fill=B)
        draw.line([lx+4, ly-1, rx-4, ly-1], fill=B)

    if headgear == "grad": draw.polygon([(32,10), (42,15), (32,20), (22,15)], fill=B)
    elif headgear == "crown": draw.polygon([(24,18), (24,12), (28,16), (32,10), (36,16), (40,12), (40,18)], fill=GOLD, outline=B); px[32,14]=RED
    elif headgear == "viking": draw.ellipse([24,12, 40,20], fill=SILVER, outline=B); draw.polygon([(24,16),(18,8),(26,14)], fill=W); draw.polygon([(40,16),(46,8),(38,14)], fill=W)
    elif headgear == "wizard": draw.polygon([(22,18), (32,6), (42,18)], fill=PURPLE, outline=B); draw.rectangle([18, 18, 46, 20], fill=PURPLE, outline=B)
    elif headgear == "ninja": draw.rectangle([24,14, 40,18], fill=B); draw.line([40,16, 46,20], fill=B, width=2)
    elif headgear == "flower_crown":
        draw.ellipse([22, 16, 42, 20], outline=GREEN, width=1)
        for cx, cy in [(26, 17), (32, 15), (38, 17)]: draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=PINK); px[cx, cy] = YELLOW
    elif headgear == "fish":
        f_color = (255, 127, 80, 255); draw.ellipse([22, 12, 42, 20], fill=f_color); draw.polygon([(42, 16), (48, 12), (48, 20)], fill=f_color); draw.polygon([(28, 12), (33, 10), (38, 12)], fill=f_color); px[26, 15] = W; draw.line([30, 16, 38, 16], fill=B, width=1)
    elif headgear == "frog":
        draw.ellipse([24, 14, 40, 20], fill=GREEN); draw.ellipse([25, 10, 31, 16], fill=GREEN); draw.ellipse([33, 10, 39, 16], fill=GREEN); draw.point([28, 12], fill=E); draw.point([36, 12], fill=E); draw.line([30, 17, 34, 17], fill=B, width=1)
    elif headgear == "ribbon": draw.polygon([(26,12), (32,15), (26,18)], fill=RED); draw.polygon([(38,12), (32,15), (38,18)], fill=RED)
    elif headgear == "tophat": draw.rectangle([24, 10, 40, 18], fill=B); draw.rectangle([20, 18, 44, 20], fill=B); draw.line([24, 16, 40, 16], fill=RED)
    elif headgear == "halo": draw.ellipse([24,8, 40,12], outline=GOLD, width=2)
    elif headgear == "chef": draw.rectangle([24,14, 32,18], fill=W, outline=B); draw.ellipse([24,8, 40,16], fill=W, outline=B)
    elif headgear == "propeller": draw.ellipse([26,14, 38,18], fill=RED); draw.line([32,14, 32,10], fill=B); draw.line([24,10, 40,10], fill=SILVER, width=2)
    elif headgear == "straw_hat": draw.ellipse([16,16, 48,20], fill=YELLOW, outline=B); draw.ellipse([24,10, 40,18], fill=YELLOW, outline=B); draw.line([24,16, 40,16], fill=RED)
    elif headgear == "cap": draw.ellipse([26,12, 38,20], fill=BLUE); draw.rectangle([34,16, 44,18], fill=BLUE)
    elif headgear == "hard_hat": draw.ellipse([24,12, 40,20], fill=YELLOW); draw.rectangle([22,18, 42,20], fill=YELLOW)
    elif headgear == "beret": draw.ellipse([22,12, 40,18], fill=RED); draw.line([32,12, 34,10], fill=B)
    elif headgear == "pirate": draw.polygon([(18,16),(32,8),(46,16),(32,20)], fill=B); draw.ellipse([30,12, 34,16], fill=W)
    elif headgear == "nurse": draw.ellipse([26,12, 38,18], fill=W, outline=B); draw.line([32,14, 32,16], fill=RED); draw.line([31,15, 33,15], fill=RED)
    elif headgear == "police": draw.ellipse([26,12, 38,18], fill=BLUE); draw.rectangle([24,18, 40,20], fill=B); draw.ellipse([31,14, 33,16], fill=GOLD)
    elif headgear == "jester": draw.polygon([(24,18),(20,10),(28,18)], fill=RED); draw.polygon([(32,18),(32,8),(36,18)], fill=BLUE); draw.polygon([(40,18),(44,10),(36,18)], fill=RED); draw.ellipse([19,9,21,11], fill=GOLD); draw.ellipse([31,7,33,9], fill=GOLD); draw.ellipse([43,9,45,11], fill=GOLD)
    elif mood == "party": draw.polygon([(26,18),(32,8),(38,18)], fill=YELLOW); draw.ellipse([30,6, 34,10], fill=RED); draw.line([26,18, 38,18], fill=BLUE)
    elif headgear == "sombrero": draw.ellipse([14,16, 50,20], fill=GREEN); draw.polygon([(26,16),(32,6),(38,16)], fill=GREEN); draw.line([28,14, 36,14], fill=RED)
    elif headgear == "santa": draw.polygon([(24,18),(32,6),(40,18)], fill=RED); draw.ellipse([30,4, 34,8], fill=W); draw.rectangle([22,16, 42,20], fill=W)
    elif headgear == "elf": draw.polygon([(26,18),(32,8),(38,18)], fill=GREEN); draw.rectangle([24,16, 40,18], fill=RED); draw.ellipse([31,7, 33,9], fill=GOLD)
    elif headgear == "traffic_cone": draw.polygon([(26,18),(32,6),(38,18)], fill=ORANGE); draw.line([28,14, 36,14], fill=W); draw.line([29,10, 35,10], fill=W)
    elif headgear == "apple": draw.ellipse([26,10, 38,20], fill=RED); draw.line([32,10, 32,8], fill=BROWN); draw.ellipse([32,8, 36,10], fill=GREEN)
    elif headgear == "cherry": draw.ellipse([26,14, 30,18], fill=RED); draw.ellipse([34,14, 38,18], fill=RED); draw.line([24,14, 28,10], fill=GREEN); draw.line([36,14, 32,10], fill=GREEN)
    elif headgear == "mushroom": draw.ellipse([22,10, 42,20], fill=RED); draw.ellipse([26,12, 30,16], fill=W); draw.ellipse([34,14, 38,18], fill=W); draw.rectangle([28,18, 36,22], fill=W)
    elif headgear == "earmuffs": draw.arc([22,12, 42,22], start=180, end=0, fill=RED, width=2); draw.ellipse([20,18, 26,24], fill=PINK); draw.ellipse([38,18, 44,24], fill=PINK)
    elif headgear == "ice_crown": draw.polygon([(24,18),(24,10),(28,14),(32,8),(36,14),(40,10),(40,18)], fill=SKY)
    elif headgear == "paper_boat": draw.polygon([(22,18),(32,8),(42,18)], fill=W); draw.polygon([(28,18),(32,8),(32,18)], fill=SILVER); draw.rectangle([20,18, 44,20], fill=W)
    elif headgear == "magic_hat": draw.polygon([(24,18),(32,6),(40,18)], fill=BROWN); draw.ellipse([20,16, 44,20], fill=BROWN)
    elif headgear == "bowler_hat": draw.ellipse([24, 12, 40, 18], fill=B); draw.rectangle([20, 16, 44, 18], fill=B)

    def draw_fleshy_tentacle(anchor_x, anchor_y, side, stretch, hook_w, hook_h):
        for i in range(11):
            t = i / 10.0; cx = anchor_x + (side * stretch) * t; cy = anchor_y + 4 * t
            draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=body_color)
        mid_x = anchor_x + side * stretch; mid_y = anchor_y + 4
        for i in range(11):
            t = i / 10.0; cx = mid_x + (side * hook_w) * t; cy = mid_y - hook_h * t
            draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=body_color)
    draw_fleshy_tentacle(23, 44, -1, 4, 4, 5); draw_fleshy_tentacle(41, 44, 1, 4, 4, 5)
    draw_fleshy_tentacle(29, 46, -1, 2, 2, 3); draw_fleshy_tentacle(35, 46, 1, 2, 2, 3)

    def draw_handheld(item_type, side):
        cx = 52 if side == 'r' else 12; cy = 38
        if item_type == "flower":
            draw.line([cx, cy+2, cx, cy+8], fill=GREEN); draw.point([cx-1, cy+5], fill=GREEN); draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=RED); px[cx,cy]=YELLOW; px[cx-2, cy-2]=PINK; px[cx+2, cy-2]=PINK
        elif item_type == "sword":
            draw.rectangle([cx-2, cy-8, cx+2, cy+3], fill=SILVER, outline=B); draw.polygon([(cx-2, cy-8), (cx, cy-13), (cx+2, cy-8)], fill=SILVER, outline=B); draw.line([cx, cy-11, cx, cy+2], fill=W); draw.line([cx-5, cy+3, cx+5, cy+3], fill=GOLD, width=2); draw.rectangle([cx-1, cy+4, cx+1, cy+8], fill=BROWN, outline=B); draw.point([cx, cy+9], fill=GOLD)
        elif item_type == "shield":
            draw.polygon([(cx-5, cy-5), (cx+5, cy-5), (cx+5, cy+2), (cx, cy+8), (cx-5, cy+2)], fill=SILVER, outline=B); draw.rectangle([cx-2, cy-5, cx+2, cy+3], fill=BLUE); draw.line([cx, cy-3, cx, cy+1], fill=W)
        elif item_type == "duck":
            draw.ellipse([cx-2, cy-4, cx+2, cy], fill=YELLOW); draw.point([cx-1, cy-2], fill=E); draw.ellipse([cx-5, cy-1, cx+5, cy+5], fill=YELLOW); px[cx+3 if side=='r' else cx-3, cy-2]=ORANGE
        elif item_type == "axe":
            draw.line([cx, cy-6, cx, cy+8], fill=BROWN, width=2); draw.polygon([(cx, cy-6), (cx+6 if side=='r' else cx-6, cy-10), (cx+6 if side=='r' else cx-6, cy-2)], fill=SILVER, outline=B)
        elif item_type == "umbrella":
            draw.chord([cx-7, cy-10, cx+7, cy-2], start=180, end=0, fill=BLUE, outline=B); draw.line([cx, cy-6, cx, cy+6], fill=B, width=1); draw.arc([cx, cy+4, cx+3, cy+7], start=0, end=180, fill=B)
        elif item_type == "balloon":
            draw.ellipse([cx-5, cy-8, cx+5, cy+2], fill=RED); draw.polygon([(cx-1, cy+2), (cx+1, cy+2), (cx, cy+4)], fill=RED); draw.line([cx, cy+4, cx, cy+9], fill=B)
        elif item_type == "magnifier":
            draw.line([cx, cy, cx, cy+6], fill=BROWN, width=2); draw.ellipse([cx-4, cy-8, cx+4, cy], outline=B, width=2); draw.ellipse([cx-3, cy-7, cx+3, cy-1], fill=SKY); px[cx-1, cy-5] = W
        elif item_type == "bow":
            draw.arc([cx-8, cy-8, cx+2, cy+8], start=270, end=90, fill=BROWN, width=2); draw.line([cx-3, cy-8, cx-3, cy+8], fill=W); draw.line([cx-8, cy, cx+3, cy], fill=SILVER); draw.polygon([(cx+3, cy-2), (cx+7, cy), (cx+3, cy), (cx+3, cy+2)], fill=SILVER, outline=B)
        elif item_type == "spear":
            draw.line([cx, cy-12, cx, cy+10], fill=BROWN, width=2); draw.polygon([(cx-3, cy-12), (cx, cy-22), (cx+3, cy-12)], fill=SILVER, outline=B); draw.point([(cx-1, cy-11), (cx+1, cy-11)], fill=RED)
        elif item_type == "crystal_ball":
            draw.polygon([(cx-4, cy+6), (cx+4, cy+6), (cx, cy+2)], fill=GOLD, outline=B); draw.ellipse([cx-4, cy-6, cx+4, cy+2], fill=SKY, outline=W); px[cx-1, cy-4]=W
        elif item_type == "ice_cream":
            draw.polygon([(cx-3, cy+2), (cx+3, cy+2), (cx, cy+8)], fill=BROWN, outline=B); draw.ellipse([cx-3, cy-2, cx+3, cy+3], fill=PINK, outline=B); draw.ellipse([cx-3, cy-6, cx+3, cy-1], fill=W, outline=B); px[cx+1, cy-7]=RED
        elif item_type == "key":
            draw.ellipse([cx-3, cy-3, cx+3, cy+3], outline=GOLD, width=2); draw.line([cx+3 if side=='r' else cx-3, cy, cx+9 if side=='r' else cx-9, cy], fill=GOLD, width=2); draw.line([cx+6 if side=='r' else cx-6, cy, cx+6 if side=='r' else cx-6, cy+3], fill=GOLD); draw.line([cx+8 if side=='r' else cx-8, cy, cx+8 if side=='r' else cx-8, cy+3], fill=GOLD)
        elif item_type == "letter":
            draw.rectangle([cx-5, cy-3, cx+5, cy+3], fill=W, outline=B); draw.line([cx-5, cy-3, cx, cy], fill=B); draw.line([cx+5, cy-3, cx, cy], fill=B); draw.ellipse([cx-1, cy-1, cx+1, cy+1], fill=RED)
        elif item_type == "laptop":
            draw.polygon([(cx-6, cy+4), (cx+6, cy+4), (cx+4, cy+1), (cx-4, cy+1)], fill=SILVER, outline=B); draw.rectangle([cx-4, cy-5, cx+4, cy+1], fill=B, outline=SILVER); draw.rectangle([cx-3, cy-4, cx+3, cy], fill=SKY)
        elif item_type == "smartphone":
            draw.rectangle([cx-3, cy-5, cx+3, cy+5], fill=B, outline=SILVER); draw.rectangle([cx-2, cy-4, cx+2, cy+3], fill=SKY); px[cx, cy+4]=W; px[cx-1, cy-4]=GREEN
        elif item_type == "battery":
            draw.rectangle([cx-3, cy-4, cx+3, cy+6], fill=GREEN, outline=B); draw.rectangle([cx-1, cy-6, cx+1, cy-4], fill=SILVER, outline=B); draw.line([cx-1, cy+1, cx+1, cy+1], fill=W); draw.line([cx, cy, cx, cy+2], fill=W)
        elif item_type == "anchor":
            draw.line([cx, cy-8, cx, cy+8], fill=GOLD, width=2); draw.line([cx-4, cy-6, cx+4, cy-6], fill=GOLD, width=2); draw.arc([cx-6, cy+2, cx+6, cy+10], start=0, end=180, fill=GOLD, width=2)
        elif item_type == "telescope":
            draw.rectangle([cx-3, cy-6, cx+3, cy-2], fill=BROWN, outline=B); draw.rectangle([cx-2, cy-2, cx+2, cy+4], fill=BROWN, outline=B); draw.rectangle([cx-1, cy+4, cx+1, cy+8], fill=BROWN, outline=B); px[cx, cy-5]=SKY
        elif item_type == "burger":
            draw.ellipse([cx-4, cy-4, cx+4, cy-1], fill=ORANGE); draw.rectangle([cx-4, cy-1, cx+4, cy+1], fill=BROWN); draw.line([cx-4, cy-1, cx+4, cy-1], fill=GREEN); draw.ellipse([cx-4, cy+1, cx+4, cy+4], fill=ORANGE)
        elif item_type == "compass":
            draw.ellipse([cx-5, cy-5, cx+5, cy+5], outline=GOLD, width=2); draw.polygon([(cx-2, cy), (cx+2, cy), (cx, cy-4)], fill=RED); draw.polygon([(cx-2, cy), (cx+2, cy), (cx, cy+4)], fill=SILVER)
        elif item_type == "medal":
            draw.line([cx-2, cy-6, cx, cy-2], fill=BLUE, width=2); draw.line([cx+2, cy-6, cx, cy-2], fill=BLUE, width=2); draw.ellipse([cx-3, cy-2, cx+3, cy+4], fill=GOLD, outline=B)
        elif item_type == "bell":
            draw.line([cx, cy-2, cx, cy+2], fill=BROWN, width=2); draw.polygon([(cx-4, cy+8), (cx+4, cy+8), (cx+2, cy+2), (cx-2, cy+2)], fill=GOLD, outline=B); draw.point([cx, cy+9], fill=B)
        elif item_type == "baguette":
            draw.ellipse([cx-2, cy-8, cx+2, cy+8], fill=TAN); draw.line([cx-1, cy-4, cx+1, cy-2], fill=BROWN); draw.line([cx-1, cy+2, cx+1, cy+4], fill=BROWN)

    draw_handheld(item_r, 'r'); draw_handheld(item_l, 'l')
    final_img = img.resize((size * scale, size * scale), Image.NEAREST); final_img.save(filename)
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--name", required=True); parser.add_argument("--color", nargs=3, type=int, default=[150, 150, 150])
    parser.add_argument("--mood", default="base"); parser.add_argument("--eyewear", default="none"); parser.add_argument("--headgear", default="none")
    parser.add_argument("--item_r", default="none"); parser.add_argument("--item_l", default="none"); parser.add_argument("--gold", action="store_true")
    parser.add_argument("--blush_style", default="oval"); args = parser.parse_args()
    generate_octopus_final(args.name, tuple(args.color), args.mood, args.eyewear, args.headgear, args.item_r, args.item_l, args.blush_style, args.gold)
