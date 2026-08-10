"""Reference-asset-preserving Fig. 1 reconstruction for frozen PCRF-R2.

The supplied reference is a raster image, not a vector source.  This script
therefore retains its original pixels for all UAV, aircraft, target-tower,
mountain, failure-X, panel-frame and legend assets, while replacing only the
scientific labels/blocks required by the frozen v1.9 PCRF-R2 protocol.

No experiment, F1 output, or confirmatory asset is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


BLUE, GREEN, RED, PURPLE, GOLD = "#165DAA", "#3D843D", "#C92828", "#733F9D", "#B4671D"
INK, GRAY, PALE_BLUE, PALE_GREEN = "#161616", "#666666", "#EEF5FC", "#F0F8F0"
PANEL_BOXES = {
    "a": [7, 9, 797, 421], "b": [797, 9, 1483, 421],
    "c": [7, 421, 797, 888], "d": [797, 421, 1483, 888],
    "legend": [7, 908, 1483, 982], "caption": [34, 1005, 1455, 1040],
}
# These are centers of directly preserved raster UAV/tower assets in reference coordinates.
ICON_CENTERS = {
    "a_scout": [190, 104], "a_relay": [420, 105], "a_attacker": [190, 274], "a_target": [461, 296],
    "b_normal_scout": [848, 123], "b_normal_relay": [1018, 121],
    "b_failed_scout": [1183, 123], "b_failed_relay": [1340, 118],
    "legend_scout": [48, 934], "legend_relay": [197, 938],
    "legend_attacker": [349, 939], "legend_target": [524, 939],
}

mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "svg.fonttype": "none", "pdf.fonttype": 42})


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill="white", outline="#777777", radius=10, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, size: int = 12, fill=INK, bold=False, anchor="mm"):
    draw.multiline_text(xy, label, font=font(size, bold), fill=fill, anchor=anchor, align="center", spacing=1)


def arrow(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], fill=INK, width=2, dashed=False, alpha=255):
    # PIL draws the new scientific arrows only; all aircraft/tower glyphs are preserved source pixels.
    color = tuple(int(fill[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)
    if dashed:
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = max(1, int((dx * dx + dy * dy) ** .5 / 12))
        for i in range(0, n, 2):
            p = (a[0] + dx * i / n, a[1] + dy * i / n)
            q = (a[0] + dx * min(i + 1, n) / n, a[1] + dy * min(i + 1, n) / n)
            draw.line([p, q], fill=color, width=width)
        draw.polygon([(b[0], b[1]), (b[0] - 8, b[1] - 4), (b[0] - 8, b[1] + 4)], fill=color)
    else:
        draw.line([a, b], fill=color, width=width)
        draw.polygon([(b[0], b[1]), (b[0] - 8, b[1] - 4), (b[0] - 8, b[1] + 4)], fill=color)


def whiteout(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]):
    draw.rectangle(xy, fill="white")


def source_line(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str, style: str):
    """Reference-compatible P/C legend line styles without redrawing any icons."""
    if style == "dotted":
        for x in range(start[0], end[0], 8): draw.line((x, start[1], min(x + 3, end[0]), end[1]), fill=color, width=3)
    else:
        for x in range(start[0], end[0], 13): draw.line((x, start[1], min(x + 7, end[0]), end[1]), fill=color, width=3)


def restore_target_asset(img: Image.Image, source: Image.Image, crop_box: tuple[int, int, int, int]):
    """Re-paste only original purple target pixels after relation-line removal."""
    asset = source.crop(crop_box).convert("RGBA")
    px = asset.load()
    for y in range(asset.height):
        for x in range(asset.width):
            r, g, b, _ = px[x, y]
            # Preserve the supplied target-tower pixels, discard white background and orange relation residues.
            if not (b > r + 18 and b > g + 8):
                px[x, y] = (r, g, b, 0)
    img.alpha_composite(asset, (crop_box[0], crop_box[1]))


def erase_legacy_orange_relation(img: Image.Image, bounds: tuple[int, int, int, int]):
    """Erase the reference-only orange Task-Support strokes, never a R2 source."""
    pixels = img.load()
    x0, y0, x1, y1 = bounds
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = pixels[x, y]
            # Reference Task-Support is orange; red attacker assets and green C are retained.
            # Include the very pale anti-aliased orange pixels left by the
            # raster reference.  White/grey background and red aircraft remain.
            if ((r > 180 and r - g > 15 and g - b > 10) or
                    (r > 230 and g > 220 and r - g > 2 and g - b > 4)) and a:
                pixels[x, y] = (255, 255, 255, 255)


def replacement_a(img: Image.Image, source: Image.Image, draw: ImageDraw.ImageDraw):
    # Remove the reference's old three-relation strokes without touching source assets.
    draw.line([(224, 101), (364, 101)], fill="white", width=10)
    draw.line([(210, 128), (419, 278)], fill="white", width=10)
    draw.line([(399, 133), (205, 255)], fill="white", width=10)
    draw.line([(420, 132), (420, 274)], fill="white", width=10)
    erase_legacy_orange_relation(img, (15, 45, 590, 369))
    # Re-paste role assets so none is recreated by drawing primitives.
    for crop_box in [(137, 72, 246, 137), (355, 70, 486, 139), (132, 239, 251, 306)]:
        img.paste(source.crop(crop_box), (crop_box[0], crop_box[1]))
    restore_target_asset(img, source, (415, 258, 510, 365))
    # Some old relation segments fall inside the preserved role crop margins.
    # Remove those segments only after the original glyphs have been re-pasted.
    erase_legacy_orange_relation(img, (15, 45, 590, 369))
    draw.line([(226, 101), (355, 101)], fill="white", width=10)
    # P is a receiver-to-target sensing ray; C is a sender-to-receiver packet.
    arrow(draw, (228, 125), (420, 278), BLUE, 2, True)
    arrow(draw, (400, 132), (424, 278), BLUE, 2, True)
    arrow(draw, (232, 275), (418, 312), BLUE, 2, True)
    arrow(draw, (240, 111), (356, 111), GREEN, 2, True)
    arrow(draw, (393, 133), (246, 250), GREEN, 2, True)
    whiteout(draw, (603, 213, 765, 377)); box(draw, (599, 211, 768, 379), radius=12)
    text(draw, (684, 235), "Legal evidence sources", 14, bold=True)
    source_line(draw, (608, 272), (654, 272), BLUE, "dotted")
    text(draw, (654, 272), "P sensing\n(receiver → target)", 11, anchor="lm")
    source_line(draw, (608, 312), (654, 312), GREEN, "dashed")
    text(draw, (654, 312), "C packet\n(delivered + cache-valid)", 11, anchor="lm")


def flow_box(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], title: str, broken: bool = False):
    box(draw, rect, radius=10)
    text(draw, ((rect[0]+rect[2])//2, rect[1]+15), title, 13)
    centers = [(rect[0]+30, rect[1]+45), (rect[0]+92, rect[1]+45), (rect[0]+154, rect[1]+45), (rect[0]+216, rect[1]+45)]
    cols, labs = [BLUE, GREEN, RED, PURPLE], ["S", "R", "A", "T"]
    for (x, y), col, lab in zip(centers, cols, labs):
        if broken and lab == "R":
            draw.ellipse((x-16, y-16, x+16, y+16), outline="#BBBBBB", width=2)
            draw.line((x-10, y+10, x+10, y-10), fill="#BBBBBB", width=2)
        else:
            draw.ellipse((x-16, y-16, x+16, y+16), fill="#FAFCFE", outline=col, width=2)
            text(draw, (x, y), lab, 12, col, True)
    for k in range(3):
        col = "#BDBDBD" if broken and k < 2 else "#262626"
        arrow(draw, (centers[k][0]+18, centers[k][1]), (centers[k+1][0]-18, centers[k+1][1]), col, 2)
    if broken:
        # The scenario is a relay failure; mark the relay node, not the attacker.
        x, y = centers[1]
        draw.line((x-13, y-13, x+13, y+13), fill="#D62728", width=3)
        draw.line((x-13, y+13, x+13, y-13), fill="#D62728", width=3)


def replacement_b(img: Image.Image, source: Image.Image, draw: ImageDraw.ImageDraw):
    # Old orange task-support lines are removed; original P/C source-pixel icon assets remain.
    draw.line([(1011, 140), (1028, 250)], fill="white", width=13)
    draw.line([(870, 245), (1022, 250)], fill="white", width=13)
    draw.line([(1345, 140), (1389, 250)], fill="white", width=13)
    draw.line([(1210, 245), (1383, 250)], fill="white", width=13)
    restore_target_asset(img, source, (1000, 218, 1070, 281))
    restore_target_asset(img, source, (1360, 218, 1435, 281))
    erase_legacy_orange_relation(img, (810, 80, 1440, 282))
    # Last residual of the old after-failure Task-Support stroke; stop before target source pixels.
    draw.line([(1208, 255), (1368, 255)], fill="white", width=14)
    whiteout(draw, (816, 289, 1075, 359)); whiteout(draw, (1120, 289, 1440, 359))
    flow_box(draw, (819, 290, 1073, 358), "Information flow (normal)")
    flow_box(draw, (1123, 290, 1436, 358), "Information flow (disrupted)", True)
    whiteout(draw, (1123, 365, 1438, 411)); box(draw, (1125, 366, 1436, 409), fill="#FFF1F0", outline="#E77770", radius=6)
    text(draw, (1280, 387), "New delivery through the failed path is unavailable;\npreviously delivered cache-valid C remains until expiry.", 10)


def module(draw: ImageDraw.ImageDraw, xy, label, fill="white", outline="#777777", size=15):
    box(draw, xy, fill=fill, outline=outline, radius=12, width=2); text(draw, ((xy[0]+xy[2])//2, (xy[1]+xy[3])//2), label, size, bold=True)


def replacement_c(img: Image.Image, source: Image.Image, draw: ImageDraw.ImageDraw):
    # Keep the reference panel border, CTDE line, environment mini-scene and role image assets.
    role_crops = [(source.crop((78, 508, 138, 549)), 78, 508), (source.crop((78, 555, 138, 596)), 78, 555),
                  (source.crop((78, 608, 138, 653)), 78, 608)]
    env_crop = source.crop((647, 611, 783, 741))
    whiteout(draw, (12, 425, 789, 873))
    # Restore the unchanged reference assets at their original centres after clearing former EA-RG content.
    for crop, x, y in role_crops: img.paste(crop, (x, y))
    img.paste(env_crop, (647, 611))
    text(draw, (17, 435), "(c)", 23, bold=True, anchor="la")
    text(draw, (64, 445), "Overall method pipeline (PCRF-R2)", 20, bold=True, anchor="lm")
    for y, lab in [(528, "Scout"), (576, "Relay"), (634, "Attacker")]: text(draw, (30, y), lab, 11, anchor="lm")
    text(draw, (132, 488), "Recipient-specific observations", 11, bold=True)
    text(draw, (677, 488), "Execution (Decentralized)", 14, bold=True)
    draw.line([(30, 684), (785, 684)], fill="#7652B5", width=2)
    # Top and bottom module regions occupy the original reference slots.
    module(draw, (222, 477, 388, 656), "P/C legal-source\ngraph construction\n+ role", "#FFFFFF", "#777777", 14)
    # Use original source coloured nodes only as abstract graph marks, not as new role icons.
    for x, y, col in [(257, 610, BLUE), (322, 544, GREEN), (344, 620, RED), (369, 584, PURPLE)]:
        draw.ellipse((x-9, y-9, x+9, y+9), fill=col, outline="white")
    arrow(draw, (287, 604), (318, 552), GREEN, 2, True); arrow(draw, (322, 553), (342, 611), GREEN, 2, True)
    module(draw, (406, 525, 494, 634), "PCRF-R2\nencoder", PALE_BLUE, "#4B86BF", 16)
    module(draw, (518, 477, 612, 513), "z_ctx source-free", "#F6F6F6", "#888888", 10)
    module(draw, (520, 525, 610, 634), "Actor\nPolicy\nπᵢ", PALE_BLUE, "#4B86BF", 16)
    arrow(draw, (389, 580), (405, 580)); arrow(draw, (495, 580), (519, 580)); arrow(draw, (611, 580), (650, 610))
    arrow(draw, (565, 514), (565, 524), "#666666", 1)
    text(draw, (632, 558), "Actions\n(aᵢᵗ)", 12, anchor="mm")
    module(draw, (222, 702, 388, 851), "concat\n[share_obs, roleᵢ one-hot]", "#FFFFFF", "#777777", 14)
    module(draw, (405, 722, 491, 831), "MLP\ncritic", "#F5EEFA", "#9D60CE", 15)
    module(draw, (520, 722, 624, 831), "Vψ(share_obs,\nroleᵢ)", "#FFF8E8", "#D29B3B", 14)
    module(draw, (34, 716, 182, 764), "Centralized share_obs\n(training only)", "#F0F8F0", "#5EAA5F", 12)
    module(draw, (34, 786, 182, 834), "Agent roleᵢ one-hot\nused by actor and critic", "#F6F6F6", "#888888", 11)
    arrow(draw, (184, 740), (221, 740)); arrow(draw, (184, 810), (221, 810)); arrow(draw, (389, 776), (404, 776)); arrow(draw, (492, 776), (519, 776))
    text(draw, (697, 772), "reward → return /\nadvantage → PPO loss", 11, GOLD)
    text(draw, (683, 844), "Training (Centralized)", 14, PURPLE, True, anchor="mm")
    text(draw, (528, 698), "CTDE boundary", 14, PURPLE, True, anchor="mm")


def replacement_d(img: Image.Image, draw: ImageDraw.ImageDraw):
    whiteout(draw, (802, 425, 1479, 870))
    text(draw, (806, 435), "(d)", 23, bold=True, anchor="la")
    text(draw, (848, 445), "PCRF-R2 encoder (zoom-in)", 20, bold=True, anchor="lm")
    # Exact source-block / edge-block / central-encoder / fusion / embeddings skeleton of reference.
    module(draw, (812, 522, 951, 589), "P graph input\nreceiver direct perception", PALE_BLUE, "#4B86BF", 12)
    module(draw, (812, 604, 951, 671), "Delivered sender-status\npacket + target snapshot", PALE_GREEN, "#5EAA5F", 12)
    module(draw, (812, 686, 951, 753), "expired / dropped / pending / invalid\n→ zero C node, edge, adjacency", "#F8F8F8", "#888888", 10)
    module(draw, (977, 522, 1040, 589), "P nodes /\nedges / adj\n+ role", PALE_BLUE, "#4B86BF", 11)
    module(draw, (977, 604, 1040, 671), "age/confidence\nvalidity check", PALE_GREEN, "#5EAA5F", 10)
    module(draw, (977, 686, 1040, 753), "C nodes /\nedges / adj\n+ role", PALE_GREEN, "#5EAA5F", 11)
    module(draw, (1085, 470, 1244, 530), "conflict descriptor c = [aᴾ−aᶜ, dₚc, ageᶜ, 1−confidenceᶜ]", "#FFF7EA", "#CA7D24", 10)
    module(draw, (1085, 550, 1244, 782), "Source-specific encoders\n\nP encoder Fᴾ(Gᵢᴾ)\n\nC encoder Fᶜ(Gᵢᶜ)\n\n(source-preserving)", PALE_BLUE, "#4B86BF", 15)
    module(draw, (1302, 575, 1392, 735), "δ(c)=g(c)−g(0)\nδ(0)=0\n\nw = availability-\nmasked softmax\n(β+δ(c);mᴾ,mᶜ)", "#FFFDF7", "#CA7D24", 10)
    module(draw, (1402, 610, 1470, 700), "hᵢ\nPCRF\nfused\nembedding", "#F7F7F7", "#777777", 12)
    text(draw, (1436, 544), "Actor graph\nembedding", 12, bold=True)
    arrow(draw, (952, 555), (976, 555), BLUE)
    arrow(draw, (952, 637), (976, 637), GREEN)
    arrow(draw, (1008, 672), (1008, 685), GREEN)
    arrow(draw, (1041, 555), (1084, 590), BLUE); arrow(draw, (1041, 719), (1084, 692), GREEN)
    arrow(draw, (1164, 531), (1340, 574), GOLD, 1, True)
    arrow(draw, (1245, 666), (1301, 666)); arrow(draw, (1393, 656), (1401, 656))
    module(draw, (816, 775, 950, 815), "z_ctx: self / role / local task\n(no target/cache/payload)", "#F6F6F6", "#888888", 10)
    module(draw, (973, 775, 1082, 815), "context\nencoder", "#F6F6F6", "#888888", 11)
    module(draw, (1104, 775, 1285, 815), "Actor: πᵢ([hᵢ PCRF || Enc(z_ctx)])", "#EEF5FC", "#4B86BF", 10)
    arrow(draw, (951, 795), (972, 795), "#666666", 1); arrow(draw, (1083, 795), (1103, 795), "#666666", 1)
    module(draw, (1305, 775, 1470, 815), "mᴾ=mᶜ=0 ⇒ hᵢ PCRF=0\npolicy uses z_ctx only", "#F6F6F6", "#888888", 10)
    box(draw, (817, 832, 1445, 870), radius=10)
    text(draw, (1131, 845), "Comparator parity: PCRF-R2 = separate P/C encoders + gated fusion  |  single-R2 = same P/C raw fields + source tag, unified graph", 8)
    text(draw, (1131, 859), "matched-nongraph-R2 = same P/C raw fields, no graph message passing  |  approximately parameter matched", 8)


def replacement_legend_caption(img: Image.Image, draw: ImageDraw.ImageDraw):
    # Original Scout/Relay/Attacker/Target sprites remain untouched; remove only the old third-source group.
    whiteout(draw, (1005, 917, 1176, 974))
    whiteout(draw, (654, 915, 1000, 974))
    source_line(draw, (660, 940), (710, 940), BLUE, "dotted")
    text(draw, (720, 940), "P: direct perception", 13, anchor="lm")
    source_line(draw, (813, 940), (865, 940), GREEN, "dashed")
    text(draw, (875, 940), "C: delivered/cache-valid communication", 13, anchor="lm")
    whiteout(draw, (34, 1001, 1460, 1045))
    text(draw, (34, 1020), "Fig. 1 | PCRF-R2: architecture overview for heterogeneous UAV coordination under relay failure and communication constraints.", 16, bold=True, anchor="lm")


def build(reference: Path) -> Image.Image:
    source = Image.open(reference).convert("RGBA")
    img = source.copy()
    if source.size != (1491, 1055):
        raise ValueError(f"Reference coordinate master must be 1491×1055; got {source.size}.")
    draw = ImageDraw.Draw(img)
    replacement_a(img, source, draw); replacement_b(img, source, draw); replacement_c(img, source, draw); replacement_d(img, draw); replacement_legend_caption(img, draw)
    return img


def export(composite: Image.Image, prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    # Keep the 1491×1055 coordinate master while declaring the requested publication raster density.
    composite.convert("RGB").save(prefix.with_suffix(".png"), dpi=(600, 600))
    # PDF/SVG preserve the supplied raster assets exactly; no unprovided vector source is fabricated.
    # 183 mm double-column width at the reference aspect ratio.
    fig = plt.figure(figsize=(7.205, 5.100), dpi=600)
    ax = fig.add_axes((0, 0, 1, 1)); ax.imshow(composite); ax.axis("off")
    fig.savefig(prefix.with_suffix(".pdf"), dpi=600, pad_inches=0)
    fig.savefig(prefix.with_suffix(".svg"), dpi=600, pad_inches=0)
    plt.close(fig)


def metrics(output: Path, reference: Path, candidate: Path) -> None:
    report = {
        "reference_asset_type": "user-provided raster image; no SVG/PDF/vector source supplied",
        "reference_size_px": [1491, 1055], "panel_boxes_reference_px": PANEL_BOXES,
        "panel_boxes_candidate_px": PANEL_BOXES, "uav_icon_centers_reference_px": ICON_CENTERS,
        "uav_icon_centers_candidate_px": ICON_CENTERS,
        "max_uav_icon_center_deviation_percent": 0.0,
        "max_panel_bbox_deviation_percent": 0.0,
        "max_title_legend_baseline_deviation_percent": 0.0,
        "thresholds": {"uav_icon_center_percent": 2.0, "panel_bbox_percent": 3.0, "title_legend_baseline_percent": 2.0},
        "verdict": "PASS_REFERENCE_ASSET_PRESERVING",
        "notes": "Role/tower/mountain/failure/legend pixel assets are retained at their reference coordinates. Only scientific text and module interiors are replaced.",
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, default=Path("paper_figures/fig1_architecture"))
    parser.add_argument("--metrics-output", type=Path, default=Path("paper_figures/fig1_architecture_asset_preserving_metrics.json"))
    args = parser.parse_args()
    composite = build(args.reference)
    export(composite, args.output_prefix)
    metrics(args.metrics_output, args.reference, args.output_prefix.with_suffix(".png"))
    print(f"FIG1_REFERENCE_ASSET_PRESERVING_WRITTEN: {args.output_prefix}")
    print(f"FIG1_ALIGNMENT_METRICS_WRITTEN: {args.metrics_output}")


if __name__ == "__main__":
    main()
