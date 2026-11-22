# Verification scope

The model index records the byte size and SHA-256 of each downloadable STL, STEP, DXF and preview PNG. Binary STL checks cover triangle count, finite coordinates, bounding box and signed volume. A CAD rebuild additionally reloads individual STEP parts as single valid solids, checks welded STL edges and tests interference against the board pin envelopes. S8 measures the local CASE9 change against its S7 upper and lower shells. [Rebuild commands](../docs/build.md)

## Reference solids

The following inventory covers the STEP `PRODUCT` names beginning with `REF_` in the two fit assemblies. Indices are inclusive. Geometry comes from the [S8 generator](../simple/source/generate_simple.py) and [C3 generator](../deluxe/source/generate_enclosure.py).

| Family (after `REF_`) | S8 (42 named solids) | C3 (35 named solids) | Construction |
|---|---|---|---|
| Boards and display | base_PCB, LCD_PCB, LCD_body, touch_glass, visible_screen, core_PCB, core_components, unused_LCD_header | Same eight | Nominal rectangular envelopes and pierced boards |
| Connectors | J1–J6 | J1, J2, J3, J5, J6 | Rounded rectangular clearance envelopes |
| Switches | SW1–SW4 each with _body and _actuator | SW1–SW4, each fused | Body and actuator boxes/cylinders |
| Indicators | LED1, LED2 | LED1, LED2 | S8 LED1 uses cylinders and a dome; C3 uses two cylinders. S8 LED2 is the author’s formed-lead solid described below |
| Display mounting | standoff16_1–4, lid_screw_1–4, bottom_LCD_screw_1–4 | standoff16_1–4 | Bored hexagonal posts and simplified screw heads/shanks |
| Case and retainer | case_lid_screw_1–3, base_nut_1–3 | retainer_M3_head_1–4, retainer_M3_shank_1–4, retainer_M3_nut_1–4 | Cylinders and drilled hexagonal prisms |

S8’s restored `LED2_REFERENCE.step` matches the author-generated R8 `hardware/library/LED2_R6_formed.step`, SHA-256 `46edee2aa790dfde90c98b1c481701c09683fccb0df2d0dbbe00e25ba9958271`. The R8 generator constructs the lens and leads using primitives, sections, lofts and boolean operations. [R8 source and licensing](../THIRD_PARTY.md)

## Frozen inputs and physical fit

The 13 compressed S8 inputs occupy 4,032,600 bytes. The current generator or S7 comparison directly reads four (741,686 bytes compressed). The nine earlier snapshots (3,290,914 bytes) preserve the recorded design history and allow the full input audit to be reproduced. Compressed and restored hashes are in [the frozen input list](../simple/reference/inputs.json).

The screen glass height, core-board stack and ribbon, LED and switch mounting heights, spacer threads, nut fit, plugs and light-pipe performance need physical checks. The glass height is nominal and printed tolerances depend on the printer. CAD clearance and mesh checks alone cannot establish fit.
