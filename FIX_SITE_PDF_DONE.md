# ORBITAL FRONTIER — fixes from ФИКС_САЙТ.pdf

## Applied

1. **Home screen / pilot hangar**
   - Removed the duplicate `LVL` badge from the hangar header (pilot level remains in the pilot progress panel).
   - Added the four live pilot stats to the lower-left side of the character stage: vitality, damage, speed and luck, including their upgrade levels.
   - Kept five quick actions (Laboratory, Workshop, Station, Ship, Tasks) in one compact row.

2. **Expeditions / planet map**
   - Preserved the agreed vertical solar-system layout.
   - Made planet rows compact and consistent, with planet tile, name, access state and selected state.
   - Kept the separate planet details / mission panel.

3. **Station inventory**
   - Renamed the resource area to `ИНВЕНТАРЬ СТАНЦИИ`.
   - Removed empty zero-count resource cells so the grid shows only stocked resources.
   - Moved accelerator stock into the Station inventory as a simple icon + count tile.
   - Updated references that previously said the removed warehouse was the place for selling items or new recipes.

4. **Warehouse tab**
   - Removed the separate `СКЛАД` entry from the extra menu and removed its page.
   - Station is now the single inventory entry point.

5. **Ship upgrades**
   - Reworked each upgrade to a compact row: icon, title / level, materials under title, short description, credit price and a single `УЛУЧШИТЬ` button.
   - Kept existing upgrade costs, material requirements and level caps.

6. **Visual consistency**
   - Kept Pixelify Sans as the global typeface.
   - Normalized title / section / description / small-label sizes across screens.
   - Kept square pixel borders and card styling.
   - Applied a consistent grey, disabled state to unavailable buttons.

7. **Runtime diagnostics / deployment cache**
   - Fixed a stale map detail action that referenced an `unlocked` variable from a different callback scope.
   - Added production source maps to make any remaining minified stack traces traceable.
   - Set `index.html` to no-store/no-cache while hashed assets remain immutable, reducing the chance of Telegram WebView showing a stale bundle.

## Validation

- JSX syntax parsed successfully for `App.jsx`, `PlanetRun.jsx` and `main.jsx` using the installed TypeScript compiler.
- Static scope/name diagnostics returned no undeclared names or block-scoped use-before-declaration errors in those files.
- Full Vite production build could not be run in this environment: npm dependency installation failed with `Exit handler never called` / network resolution issues. Run `npm.cmd ci` and `npm.cmd run build` locally before publishing.
