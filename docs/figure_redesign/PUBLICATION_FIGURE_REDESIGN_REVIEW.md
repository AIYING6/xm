# Publication Figure Redesign Pass

## Scope and integrity boundary

This pass redesigns the visual presentation of the two accepted main-figure prototypes. It does not alter any relation type, method component, event definition, curve input, seed-level value, RMST value, interval, comparison, or scientific interpretation. Python is the persistent rendering backend. Final source is SVG with editable text; PDF and 600-dpi PNG are delivery fallbacks.

## Shared visual system

- **Method identity:** EA-RG = deep blue; MAPPO = muted brick; HAPPO = cool grey-blue; wider single-graph = muted violet. Colour is always redundant with direct labels or line style.
- **Relation identity:** perception = blue dotted line; environment-delivered communication = green dashed line; task-support = orange dash-dot line. Attack window is absent as a relation and remains, where needed, only a node-state condition.
- **Type:** sans-serif with Chinese-capable fallback; SVG text remains text rather than paths.
- **Final width:** 183 mm (double-column); all body labels are at least 5.4 pt at that physical width.
- **Accessibility:** no result depends on red/green discrimination alone; baseline curves also differ in line style and direct labelling.

## Fig. 1 — method overview

### Scientific visualization review

| Review prompt | Decision |
|---|---|
| Exact question | How are task-chain dependencies under relay failure supplied to the EA-RG policy without claiming learned physical communication? |
| Meaningful difference | The scientifically distinctive object is a three-relation task graph, not an additional attack-window relation or a generic neural-network pipeline. |
| First notice | The reader should first see the relay-mediated task setting, then the three distinct relation families and their relation-specific encoding. |
| Prototype limitation | The prototype gives all boxes and labels similar weight; the red failure banner and long in-box prose compete with the relation mechanism. |
| Redesign response | Use an asymmetric a–b–c composition: task setting, before/after three-relation graph, and a visually dominant coordination module. Node failure is a compact event mark rather than a warning banner. |

### Publication graphic design review

| Criterion | Design decision |
|---|---|
| Hierarchy / balance | The lower coordination module receives the largest visual field; the two upper panels establish task and failure context. |
| Typography / prose | Short nouns inside the graphic; explanatory boundaries move to the caption and manuscript. |
| Whitespace / alignment | Shared baseline, fixed corner radius, thin neutral rules, and aligned module centres. |
| Lines / arrows | One quiet arrow grammar, constant arrowhead and line weight; thin neutral panel rules establish the multi-panel composition without decorative shadows. |
| Colour | Three relation colours are restrained and consistent; nodes remain neutral blue/rose role marks. |
| Final-size / accessibility | Direct relation labels plus colour/line-style redundancy; no dense legend inside the graph. |

## Fig. 2 — primary recovery evidence

### Scientific visualization review

| Review prompt | Decision |
|---|---|
| Exact question | Under matched failure exposure in the locked nominal held-out setting, is EA-RG earlier than MAPPO during the active failure interval? |
| Meaningful difference | The P1 separation is the early recovery distribution and its RMST80 contrast, not the long-horizon tail or a claim of universal dominance. |
| First notice | The EA-RG curve should be visually primary; the reader should then see the 0–35-step detail and the paired RMST80 effect with its uncertainty. |
| Prototype limitation | A large shaded region, remote legend, and annotation box make the time horizon more salient than the curves; the informative early drop is not isolated. |
| Redesign response | Use a dominant full KM panel, a data-motivated 0–35-step small multiple, and a compact dot–whisker panel for Full−MAPPO RMST80. The \(\tau=80\) reference is a thin line only. |

### Publication graphic design review

| Criterion | Design decision |
|---|---|
| Hierarchy / balance | The full KM panel is the hero; the detail and forest panels form a vertically aligned evidence column. |
| Typography / legends | Direct curve-end labels reduce legend travel; panel labels and axis titles remain readable at 183 mm width. |
| Whitespace / annotations | No floating text boxes or arrows. A compact in-panel RMST80 label and a zero reference line carry the quantitative comparison. |
| Lines / colour | EA-RG uses the thickest blue line; MAPPO/HAPPO are secondary; wider single-graph is subdued and dashed. |
| Statistics | The forest panel displays the three seed differences and the hierarchical paired-bootstrap 95% interval, with the negative direction labelled “earlier”. |
| Final-size / accessibility | Line style and direct text distinguish methods in grayscale; sparse axes and restrained rules preserve contrast. |

## Evidence contracts

| Figure | Inputs | Transformations | Exclusions |
|---|---|---|---|
| Fig. 1 | Code-traceable facts MF01–MF10 | No numerical transformation; vector schematic only | No fourth relation, runtime adaptation, physical-message control, or unsupported 6DOF implication |
| Fig. 2 | Frozen matched-exposure raw inputs for four contract methods; P1B RMST80 seed differences and CI | Pool 3 seeds for descriptive KM; no episode exclusions beyond pre-specified Early+Nominal matched failure exposure | All other methods are intentionally routed to Supplementary by the existing Fig. 2 contract; no input rows are dropped within the four displayed methods |

## Completion gates

1. Generate publication SVG, PDF and 600-dpi PNG for both figures, plus a contact sheet.
2. Inspect at the 183-mm manuscript width and retain an output-level visual QA record.
3. Run static figure-source validation and an element-level evidence audit.
4. Update the manuscript only after both scientific and graphic reviews pass.

## Post-redesign scientific visualization review — PASS

### Fig. 1

- **Question answerable at a glance:** the task setting produces three observable relation families, which are the inputs to EA-RG coordination after relay failure.
- **First visual read:** the scenario and before/after task graph introduce the three relation styles; the lower coordination module makes relation-specific encoding the visual centre.
- **Evidence integrity:** no attack-window relation, learned physical communication, runtime gate adaptation, or unimplemented flight-system detail is drawn.
- **Cognitive load:** the former equal-weight architecture boxes were replaced by a compact task context and a visually dominant relation-specific encoder.

### Fig. 2

- **Question answerable at a glance:** EA-RG is earlier than MAPPO during the pre-specified active-failure interval under the locked matched-exposure setting.
- **Meaningful separation:** the 0–35-step detail makes the early curve separation legible; the full curve retains the competing long-horizon context without making its tail dominant.
- **Effect magnitude:** the forest panel shows all three seed differences and the locked pooled bootstrap interval, rather than relying on a prose annotation.
- **Evidence integrity:** only the four methods authorized by the Figure 2 contract are plotted; no row is removed within their pre-specified primary populations.

## Post-redesign publication graphic design review — PASS

- **Hierarchy:** Fig. 1 centers relation-specific encoding; Fig. 2 centers the full KM curve and nests detail/effect-size evidence in a right column.
- **Typography and final size:** both figures are 183 mm wide; final text is 5.4 pt or larger, with panel labels, titles and captions clearly tiered.
- **Whitespace and alignment:** panel gutters, shared baselines, corner radii and arrow grammar are consistent; no legend overlaps data.
- **Colour and accessibility:** EA-RG retains the highest blue line weight; baselines are muted and additionally distinguished by style. Relation labels use line samples as well as colour.
- **Exports and editability:** SVG first with editable text; PDF, 600-dpi PNG and TIFF fallbacks are present. The contact sheet and `PUBLICATION_FIGURE_EVIDENCE_AUDIT.md` record the visual and evidence checks.

**Final redesign verdict:** PASS. The original prototype PNG files remain preserved as scientific prototypes; the publication bundle is the manuscript-facing figure source.
