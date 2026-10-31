# Horizon mods

Two kinds of mod run in Horizon:

| Kind | File | What it is | Where it runs |
|---|---|---|---|
| **Content mod** | `.hmod` | Data and assets: blocks, items, recipes, loot, tags, models, textures, structures. No code. | Read when the game starts |
| **Native mod** | `.hnmod` | A [horizon-mixins](https://github.com/horizon-rust/horizon-mixins) bundle: Rust that changes the game's own source before it is compiled. | In a game the launcher builds for the player ([native-mods.md](native-mods.md)) |

| Part | Where | State |
|---|---|---|
| The contract (WIT) | `crates/horizon-mod-sdk/wit/horizon.wit` | 0.1: log, game-read, chat, hud, storage, command, ui; tick, frame, chat and command hooks |
| SDK for mod authors | `crates/horizon-mod-sdk` | 0.1 |
| Example mods | `crates/horizon-mod-sdk/examples/coords-hud`, `examples/predator-missile` | coordinates, facing and time HUD, `/where`, `/coords`; `/missile`, a guided missile from vanilla commands |
| Horizon's official mods | `mods/official/` | the extras moving to the registry: FPS Counter (`fps-overlay`), Keystrokes, Zoom, Minimap; Far View (`far-view`), distant terrain; and Recipes, a recipe viewer |
| Runtime | `crates/horizon-mods` | wasmtime 50 (Horizon: 48 LTS), component model |
| Authoring tool | `crates/cargo-horizon-mod` | `cargo horizon-mod new [--template code\|content] / build / run / test / check`, and the registry's CI (`registry build / review / list`) |
| In the game | `crates/horizon-client/src/game/mods.rs`, Options > Mods | client mods |
| Launcher mod browser (Modrinth, CurseForge with a key) | [mod-browser.md](mod-browser.md) | resource packs, modpacks |
| Registry index (`index.json`, `.hpack`), signatures | `horizon_mods::index`, [api/mod-index.md](api/mod-index.md) | schema 1; launcher and website next |
| Server mods, registries | this page, [Roadmap](#roadmap) | planned |

## Design goals

1. **Safe to install.** A mod is untrusted code. It runs in a WebAssembly
   sandbox with no file, network, process or clock access, a memory cap and a
   time budget per call. It can only do what its capabilities grant, and the
   player sees those before turning it on.
2. **One file for every platform.** The same `.hmod` runs on Windows, macOS
   and Linux, x86-64 and ARM: authors build once, players never meet "wrong
   build for my OS".
3. **Free when unused.** No mod on: no engine, no thread, no compile, one
   branch per hook. Measured below.
4. **Vanilla stays vanilla.** Mods add; they cannot patch the game's code the
   way Mixins do. What they may change is a list of hooks the game calls at
   fixed points, so the parity harnesses keep testing the same game.
5. **Stable for authors.** The contract is a versioned WIT package; a mod
   built for API 0.1 keeps loading on later 0.1.x games.

## How it works

```
 mod crate (Rust)                         Horizon
 ───────────────                          ───────
 impl Mod for MyMod { ... }               horizon-mods::Mods
 export_mod!(MyMod)                         ├─ Engine (cranelift), made on first mod
        │ cargo horizon-mod build           ├─ one Store per mod: 64 MiB, fuel per call
        ▼                                   ├─ Linker: log, game, chat, hud (WIT imports)
 my_mod.hmod = zip {                        └─ calls the events export: init, tick,
   horizon-mod.toml,                             frame, command, chat
   mod.wasm  (a WebAssembly component)
 }
```

- **WebAssembly components.** Mods compile to `wasm32-unknown-unknown`;
  `cargo horizon-mod build` wraps the module into a
  [component](https://component-model.bytecodealliance.org/) for the
  `horizon:mods/horizon-mod` world. The WIT file is the whole API: host
  functions the mod imports (`log`, `game`, `chat`, `hud`) and the `events`
  interface it exports. No WASI: the component cannot even name a file or a
  socket.
- **Capabilities are imports.** Every imported interface except `log` is a
  capability. The manifest declares them; the game reads the component's
  actual imports and refuses a mod whose code imports one its manifest does not
  declare (`uses capability chat, missing from horizon-mod.toml`). So the list
  the player reads is the truth, not a promise.
- **Hooks on request.** `init` returns a `registration`: the commands the mod
  owns and which of `tick`, `frame` and `chat` it wants. The game calls only
  those. A mod that wants nothing per frame costs nothing per frame.
- **Retained HUD.** A mod sets its panel (corner and coloured lines) when it
  changes; the game draws it every frame with the extras' overlay code. Most
  HUD mods need no frame hook at all.
- **Snapshots, not callbacks into the world.** Once per tick (and before a
  command) the game copies what mods may read (player position, look, health,
  food, dimension, world clock) into a snapshot shared by all mods. Mods never
  hold references into the game, so they cannot stall or corrupt it.

### What a mod can do (API 0.1)

| Interface | Capability | Functions |
|---|---|---|
| `log` | always | `write(level, message)`, in the game log as `[mod <id>]` |
| `game` | `game-read` | `get-player()`: x y z, yaw, pitch, health, food, dimension; `get-clock()`: game time, day time; `raycast(distance)`: the first block along the view (fluids pass), up to 1024 blocks and across the distant terrain, with the point hit and the block's id |
| `chat` | `chat` | `show(text)`: a line only the local player sees, after the mod's name (8 per call) |
| `hud` | `hud` | `set-panel(corner, lines)`, `clear()`: up to 16 lines of 256 characters |
| `storage` | `storage` | `get(key)`, `set(key, value)`, `delete(key)`: a per-mod folder of up to 64 files, 4 MiB total, at most 1 MiB written per call |
| `command` | `command` | `run(line)`: a vanilla command run as the player, with the player's permissions, after the hook returns (8 per call); mods' own commands are not run. `run-quiet(lines)`: up to 256 a call, the same rights, nothing in the chat (single player and Horizon's servers run them 64 a tick and log one line a batch; elsewhere they go as chat commands and their feedback shows) |
| `ui` | `ui` | `open-screen`, `close-screen`, `set-settings`: a screen the mod owns and a page in Options > Mods, of text, button, item and list widgets the game lays out and draws with its own menus' code; `browser.set-items`, `browser.poll`: a recipe viewer's panel of items right of the inventory and container screens (not the creative one), which the game pages and draws with its own slots and search box, and the mod hears its clicks, its searches and the mod's own keys (`input.register-key`) pressed over any item on the screen; `browser.set-recipes`: recipes in the panel's place (crafting grids, cooking, stonecutting, smithing and brewing layouts, their slots cycling through their stacks, a note and an action button each), paged by the game, with clicks on their slots, action buttons, page turns and a back button. **Experimental:** the manifest needs `experimental = ["ui"]` |
| `render` | `render` | `set-hud(shapes)`: up to 1024 fills, four-cornered shapes, GUI sprites, items and text, kept on the HUD (over the hotbar, under chat and screens, hidden with F1) until replaced; `set-corner(corner, w, h, shapes)`: a box the game places in a corner, stacked with its overlays and other panels, as `hud`'s panels are; `text-width(text)`; `frame-stats()`: the game's FPS, min and 1% low; `gui-size()`; `shake(strength, seconds)`: the view turns, the player doesn't, scaled by Distortion Effects; `set-zoom(zoom)`: the field of view divided by up to 10, eased or at once, with slower turning, while playing and not through a spyglass (the strongest of several mods' zooms counts); `set-minimap(minimap)`: a map of the world around the player in a corner, as a map item colours it (the floor underground and under roofs), square or round, turning with the player or north up, with the player's arrow; the game keeps its tiles within its own frame budget (one map at a time, the first loaded mod's); `set-far-terrain(far-terrain)`: the world past the render distance as distant terrain, out to 64 to 1024 chunks, built by the game's own workers (the player's LOD Distance, when on, wins; the first loaded mod's). The game's own HUD renderer draws them: a mod never supplies shader code. **Experimental:** `experimental = ["render"]` |
| `input` | `input` | `claim-items(ids)`: the use button on those items is the mod's (`use-start`, `use-stop` with the ticks held; the game doesn't place, eat or swing); `register-key(name, label, key)`: up to 16 keys (`key.keyboard.r`), heard while playing as `key-down` / `key-up` (the game's own mapping on that key still runs; a screen opening lets held keys up), mouse buttons as `key.mouse.4`. The player rebinds them on the mod's page in Options > Mods, where the game lists them first as Key Binds rows (click, then press a key or mouse button; Esc binds none), even for a mod without `ui`; the choice is kept in `horizon-mods.txt` (`key.<mod>.<name>:key.keyboard.z`) and wins over `register-key`'s default; `claim-wheel(on)`: the wheel's steps become `wheel` events and the hotbar doesn't move (the one input a mod takes from the game; a mod's keys never do); `held()`; `mapping(name)`: a movement or click mapping's key label and whether it is held; `clicks-per-second()`; `poll()` returns the events, at most 256 kept. **Experimental:** `experimental = ["input"]` |
| `recipes` | `recipes` | `items()`: every item in the registry's order, with its name in the player's language and its tags; `all()`: every recipe (crafting, smelting, blasting, smoking, campfire, stonecutting, smithing, brewing), its slots as the stacks that fit each, its results, cooking time and experience, and the recipe book's id for it; `known()`: the book ids the player's recipe book holds; `place(book-id, all)`: the recipe book's click on a recipe, in the open inventory's or crafting table's grid (refused for a recipe the player's book doesn't hold, as vanilla's server refuses it); `give(stack)`: in creative mode, the stack into the player's inventory, as from the creative inventory. The recipes are the world's in single player and on Horizon's servers, vanilla 26.3's on any other server (a client is sent no others), while `known` follows that server's book. The game makes the tables once, when a mod first reads them. **Experimental:** `experimental = ["recipes"]` |

| Hook (export) | When |
|---|---|
| `init() -> result<registration, string>` | once, after loading; an error keeps the mod off and is shown |
| `tick(tick)` | each game tick while in a world (20 per second) |
| `frame(seconds)` | each rendered frame |
| `command(name, args) -> result<option<string>, string>` | `/name args` typed in chat, for a command the mod registered |
| `chat(text)` | each chat line the player receives, as plain text |

Commands: vanilla's command names win. A mod asking for `/give` does not get
it (logged), and two mods cannot share a name (the first one loaded keeps it).
The chat box colours and Tab-completes a mod's commands like vanilla's, for
every player whatever their permission level, and takes any text after the
name (the mod reads it as `args`; API 0.1 has no way to declare argument types).

### Planned interfaces

Each is a new capability, added in a 0.x minor version so older mods keep
loading. Ordered by what the first native ports need:

| Interface | For | Notes |
|---|---|---|
| `keys` | keybinds | registered binds appear in Controls; press/release events |
| `target` | the crosshair's block or entity, with its state and NBT summary | Jade/WTHIT-style tooltips |
| `inventory-read` | the player's inventory, held item, open container | AppleSkin, recipe viewers |
| `recipes` (Starling: done; Horizon's is above) | an item's recipes and uses, the recipe book's filling of a grid | EMI, JEI-style viewers |
| `world-read` | blocks and biomes around the player, within the render distance | minimaps, schematics |
| `render` (world); Starling's `world-draw` (done) | world-space lines, see-through boxes, texts, labels and icons (sprites facing the camera), kept in layers the game draws every frame, beside the HUD shapes `render` has | Light Overlay, waypoints; Litematica's ghost blocks next |
| `registries` | new blocks, items, entities and recipes, mostly data: JSON models, textures, loot and recipes in the `.hmod`'s `assets/` and `data/` | server side; see [Multiplayer](#multiplayer) |
| `server` | world events (entity spawn/death), game rules, world read/write, typed server commands | after [server mods 0.3](#server-mods-api-03-experimental)'s players, chat, blocks and commands |
| `net` | a mod's own client↔server channel (custom payloads) | only between the two halves of the same mod |

There is no file, socket, process or raw-input interface, on purpose.

## Choosing the runtime

| Option | Sandbox | One file for all OSes | Typed API | Cost | Verdict |
|---|---|---|---|---|---|
| **wasmtime + component model** | yes: memory, fuel, no imports but ours | yes | WIT → Rust on both sides | 85 ns per empty hook call; 50 ms to compile a 64 KB mod on load | **chosen** |
| wasmtime, core modules with a hand ABI | yes | yes | no: pointers and lengths by hand | a few ns less per call | not worth the fragile ABI |
| wasmi (interpreter) | yes | yes | no components | no compile time, execution ~10-50x slower than cranelift code | kept in mind for a platform without JIT |
| Lua (mlua) or another script | partial (strip the stdlib, hope) | yes | no | fast to write | not Rust; weak sandbox |
| native `cdylib` plugins | none | no: per OS and arch, unstable Rust ABI | yes | none | unsafe for players |
| an embedded JVM | none per mod | yes | Java | 100+ MB, seconds of startup | see the research |

wasmtime 48 is a long-term-support line (security fixes until August 2028)
and needs Rust 1.95. It reads WebAssembly with the same wasm-tools release
(0.254) as the `wit-component` that packs mods and the SDK's `wit-bindgen`, so
the build carries one copy of them. Only its `runtime`, `cranelift`,
`component-model` and `std` features are on: no WASI, no async, no GC
proposal, no profiling. Its cranelift backend generates native code for x86-64
and ARM64 on Windows, macOS and Linux, which is why one `.hmod` serves them
all.

Starling runs wasmtime 50 instead, with `winch` and `parallel-compilation` on
too: its Winch compiles a mod quickly on a phone (the full cranelift compile
follows in the background), and 50's runs the shared JavaScript engine on ARM
where 36 crashed it. 50 reads WebAssembly with wasm-tools 0.261, so the build
carries that copy beside the 0.254 one packing and the SDK use.

The game links it only with its `mods` feature: every release build turns it
on (`release.yml`), and a build from source needs
`cargo build --release -p horizon-client --features mods` to run code mods.
Without it (the tests and probes) wasmtime and cranelift aren't built, a
quarter of a clean build; content mods still load, and the game logs why the
code mods don't start.

### Performance

Measured on the Mac mini (M4 Pro), release build, `cargo test -p
horizon-mods --features runtime,pack --release --test sandbox -- --ignored --nocapture`:

| | per call |
|---|---|
| tick with no mod loaded | 1.2 ns (one check) |
| empty `tick` hook (call into the sandbox and back, fuel on) | 85.5 ns |
| empty `frame` hook | 87.5 ns |
| coords-hud's `tick` (reads the player and clock, formats 3 lines, compares) | 2.3 µs |
| loading coords-hud (read, compile with cranelift, instantiate, `init`) | 50 ms, once |

In the game, same world and view, `horizon-ctl bench 10` three times each
(4 other sessions shared the machine, so the tails are noisy; the median is
the stable figure):

| | median frame | mean FPS |
|---|---|---|
| no `horizon-mods` folder | 2.62-2.71 ms | 149-163 |
| coords-hud on | 2.72-2.78 ms | 151-254 |

At 20 ticks per second coords-hud costs 46 µs per second of game time: well
under 0.01 ms per frame. The frame-time medians differ by less than the
run-to-run spread.

**Budgets.** Each call gets fuel (about one unit per WebAssembly instruction):
2 billion for `init`, 50 million for `tick`, 10 million for `frame`, 100
million for a command or chat line. A runaway loop ends in a fraction of a
second (the sandbox test's endless `/spin` is cut well within its 5 s limit)
instead of hanging the game. The target budgets a mod should stay under are
tighter: **1 ms per tick and 0.1 ms per frame**. The runtime keeps each mod's
average call time (`Entry::cost`); the Mods page will show it, and a mod over
budget for long will be flagged, then paused.

### Crash isolation

A trap (panic, out-of-bounds access, `unreachable`), running out of fuel or
hitting the 64 MiB memory cap stops **that mod only**. The game says so in
chat (`Mod Test Guest stopped: it took too long (an endless loop?)`), marks it
on the Mods page and carries on; the other mods keep running. Host functions
clip what a mod hands back (chat lines per call, HUD lines and lengths). Tests:
`crates/horizon-mods/tests/sandbox.rs` (an endless loop, a panic and a 1 GiB
allocation, next to a healthy mod; `cargo test -p horizon-mods --features
runtime,pack`).

## Playing with mods

1. Install a mod from the launcher's Mods page ([mod-browser.md](mod-browser.md)), or put its files by hand in the
   game folder (the one holding `options.txt`): a content mod's `.hmod` (or a folder holding `horizon-mod.toml`) in
   `horizon-mods/`. Native mods go in `horizon-native-mods/`, and the launcher builds them
   ([native-mods.md](native-mods.md)).
2. Options > **Mods** lists them with what each may do ("May add blocks, items and mob effects to your worlds") and a
   switch. They start off. The choice is kept in `horizon-mods.txt` (`mod.<id>:true`).
3. A content mod's blocks, items and mob effects load once, when the game starts: restart the game after a switch.
4. A mod that can't load shows why, in red, on its row.

Two turned-on content mods never own the same namespace: the first by file name loads, and the other stays out with
the reason in the log.

Benchmarks (`--benchmark`) never load mods.

## Making a content mod

```sh
cargo install --git https://github.com/horizon-rust/horizon cargo-horizon-mod
cargo horizon-mod new my-mod        # a content mod: manifest, one block with its model, loot and recipe
cd my-mod
cargo horizon-mod run               # build my-mod.hmod, then start the game with it turned on
cargo horizon-mod build             # only build: target/horizon-mod/my_mod.hmod
cargo horizon-mod check target/horizon-mod/my_mod.hmod   # the registry's checks; --json for JSON
```

The crate's `assets/` and `data/` folders go into the `.hmod` too (the mod's own sprites:
`assets/<id>/textures/gui/sprites/<name>.png`, drawn as `<id>:<name>`).

`run` starts `horizon-client` (on `PATH`, or `--game PATH`, or
`HORIZON_CLIENT`) with `--dev-mod target/horizon-mod/<id>.hmod`. A dev mod is
always on, and the game checks its file once a second: rebuild and it restarts
with "Mods reloaded" in chat. Its in-memory state starts over; whatever it
saved with capability `storage` survives the reload.

### The manifest

```toml
id = "my_mod"                # [a-z0-9_]{1,64}: settings key, log name
name = "My mod"
version = "0.1.0"
description = "..."
authors = ["..."]
api = "0.2"                  # content mods
side = "both"
capabilities = ["registries"]
namespaces = []              # optional: more namespaces the mod's files use (below)
```

Unknown keys are refused, so a typo is an error, not a silently ignored permission.

### Content mods (API 0.2)

A content mod has capability `registries` and carries `assets/` and `data/` in the `.hmod`. It adds blocks and items
by declaring them in `data/<id>/horizon/block/*.json` and `data/<id>/horizon/item/*.json`, each copying a vanilla
template ([modpacks.md](modpacks.md#registries-02-data-driven-blocks-items-and-mob-effects)), and mob effects (below):

```json
{ "template": "minecraft:iron_block",
  "properties": { "hardness": 4.0, "light": 3, "sounds": "minecraft:amethyst_block" },
  "item": true }
```

A block copies its template's states. It can also declare state properties of
its own, which its template does not have — how a pipe says which sides it
connects to, or a machine whether it is running. Its states then become its
template's states times the combinations of the ones it declares, in a fixed
order with every declared default first, so ids do not move between loads:

```json
{ "template": "minecraft:stone",
  "state_properties": {
    "facing": { "type": "enum", "values": ["north", "south", "east", "west"] },
    "lit": { "type": "boolean" } },
  "default_state": { "lit": "true" } }
```

A `boolean` is `false` and `true`, as vanilla spells them; an `enum` is a list
of values, and a name or value is lower case letters, digits and underscores.
A declared name may not be one the template already has, and `default_state`
takes one value per declared property too, so a block's default is exactly one
state of its own. Every combination has to fit in the states a world holds
(2^20), so a declaration that would not is refused when the mods load.

An item copies its template's data components, with `max_stack_size` and
`rarity` changed, and any other 26.3 component set or removed in
`components`, written as a data component patch is: `minecraft:<type>` sets
one, `!minecraft:<type>` with `{}` removes it. That is how a modded sword
gets its own damage and durability, or a tool its mining speed:

```json
{ "template": "minecraft:iron_sword",
  "components": {
    "minecraft:max_damage": 900,
    "minecraft:attribute_modifiers": [{ "type": "minecraft:attack_damage",
      "id": "minecraft:base_attack_damage", "amount": 7.0,
      "operation": "add_value", "slot": "mainhand" }],
    "!minecraft:repairable": {} } }
```

A block's item takes the same `components`, over the components of its
template block's item; a block with `"item": false` can't have them. Block files
have no `max_stack_size` or `rarity` keys, so those two go in `components` here
(an integer 1 to 99, and one of `common`, `uncommon`, `rare`, `epic`):

```json
{ "template": "minecraft:iron_block",
  "components": {
    "minecraft:max_stack_size": 16,
    "minecraft:damage_resistant": { "types": "#minecraft:is_fire" } } }
```

A mod's creative inventory tabs are `data/<id>/horizon/creative_tab/*.json`:
a title, the item on the tab's button, and its items in order (items the game
doesn't have are left out):

```json
{ "title": "Ruby", "icon": "ruby:ruby", "items": ["ruby:ruby", "ruby:ruby_block"] }
```

They come after vanilla's tabs, ten to a page as NeoForge pages them; the
buttons above the inventory turn the pages. The title is a lang key or English
text: `"title": "itemGroup.ruby"` uses that key from the mod's lang files, and a
lang file's `itemGroup.<mod id>.<file name>` (`creative_tab/gems.json` →
`itemGroup.ruby.gems`) translates any title. A mod's items join the search tab
under their names.

A component type no vanilla item has is refused, so a misspelt one fails
the load instead of doing nothing. Behaviour the game ties to a vanilla
item's id doesn't come along yet: a copy of the trident doesn't throw
([#3305](https://github.com/horizon-rust/horizon/issues/3305)).

A mod effect is declared in `data/<id>/horizon/mob_effect/<name>.json` with what vanilla's `MobEffect` takes: its
category (`beneficial`, `harmful` or `neutral`) and its RGB colour (0 to `0xFFFFFF`), which its particles take:

```json
{ "category": "harmful", "color": 9154528 }
```

It is the effect `<id>:<name>`: `/effect give @s ruby:glow 30` gives it, saves and mobs keep it, and it reaches LAN and
dedicated server players who run the same mods (its network id follows vanilla's). Its name is the translation
`effect.<id>.<name>` from the mod's `assets/<id>/lang/`, its icon `assets/<id>/textures/mob_effect/<name>.png` (18x18,
as vanilla's; without one it draws as the missing texture). It does nothing on its own yet: no tick behaviour and no
attribute modifiers. A world opened without the mod drops the effect from its players and mobs. Clients join a server
only with the same mods' effects, as with its blocks.

`crafting_remainder` names what the item leaves in the crafting grid when a
recipe uses it, as a milk bucket leaves a bucket (vanilla's
`Item.Properties.craftRemainder`, not a data component): a vanilla item or
one of the mod's own, refused at load otherwise. It holds on the crafting
table, the inventory grid and the crafter, not yet as furnace fuel or in a
brewing stand. What the item leaves once eaten
or drunk is the `minecraft:use_remainder` component instead:

```json
{ "template": "minecraft:mushroom_stew", "crafting_remainder": "minecraft:bowl" }
```

Any mod, without `registries`, may carry its own GUI sprites:
`assets/<id>/textures/gui/sprites/*.png`, the icons of its buttons
(`widgets.add-window-button`'s, a touch button's), named `<id>:<name>`. They
load into the GUI atlas as the game starts, as content does.

The fence: files go in the mod's own namespaces (`assets/<id>/`,
`data/<id>/`, and those its manifest lists), plus additions to vanilla tags
(`data/minecraft/tags/`) and to the convention tags NeoForge and Fabric mods
share (`data/c/tags/`).
Templates and `sounds` name vanilla blocks; unknown keys are refused.

Some Java mods ship their files under other names than their mod id (Towns and Towers, mod id `t_and_t`, under
`kaisyn` and `towns_and_towers`). A content mod lists those in its manifest:

```toml
id = "t_and_t"
api = "0.2"
capabilities = ["registries"]
namespaces = ["kaisyn", "towns_and_towers"]
```

A listed namespace is the mod's as its id is: its `assets/` and `data/` files load, and the game reads its tags,
recipes, names and loot. Blocks, items and mob effects are declared in `data/<id>/horizon/` only. `minecraft`, `c` and
`horizon` cannot be listed. Two mods that are on may not own the same namespace (one's id or listed namespace being
the other's): the game keeps the first in load order and leaves the other's content out, with "mods A and B both use
the namespace N; turn one of them off" in the log. Paths use vanilla's resource characters, at most 65,536 files, 16
MiB each and 512 MiB in all. A mod whose content is refused is left out, with the reason in the log. The game reads
this content into its block and item tables (`horizon_client::mod_content`, [modpacks.md](modpacks.md)). A tag entry
naming an id nobody registers (a block a port left out, another mod's item) is dropped, so the rest of the tag still
loads; vanilla would drop the whole tag.

Tags merge as a data pack's do. Every mod's file for one tag (vanilla's `data/minecraft/tags/`, the convention
`data/c/tags/`, or another mod's) adds its values after vanilla's and the mods' before it, in load order. A file with
`"replace": true` first drops what came before it, vanilla's entries and the earlier mods', and the mods after it
still add theirs, as a higher data pack does. Since the result depends on load order, the game says so in the log:
"mod towns replaces data/minecraft/tags/worldgen/biome/has_structure/village_plains.json: vanilla's entries and those
of adds are left out, ...". Tags are the only `minecraft` files a mod may hold: its other content stays in its own
namespaces.

A mod adds to structure sets, template pools and processor lists that are not its own (vanilla's villages, another
mod's houses) with a set, pool or processor list file in its own namespace holding `horizon:add_to`, a key vanilla data
never has. Its entries are appended to each set, pool or list named, after every mod's own files, by
`horizon:priority` (lower first, 1000 when it has none), then in mod and file order; the file is no set, pool or list
itself. A name nobody defines is skipped.

```json
{ "horizon:add_to": "minecraft:villages",
  "structures": [ { "structure": "mymod:village_beach", "weight": 10 } ] }
```

A pool addition holds `"elements"` as a pool does, a processor list addition `"processors"`. This is what
Lithostitched's `add_structure_set_entries`, `add_template_pool_elements` and `add_processor_list_processors` modifiers
do on NeoForge and Fabric, and `horizon-port-pack carry` writes the last two from those.

A pool element may be one of Lithostitched's: `lithostitched:limited` (`delegate`, `limit`, `min_depth`) places its
`delegate` at most `limit` times in one structure start, and `lithostitched:guaranteed` (`delegate`, `count`,
`min_depth`) is tried before its pool's other elements at each jigsaw that reaches that pool (as target or fallback)
until `count` are placed. Neither goes below a piece shallower than `min_depth` (the start is at depth 0).

A structure (and any of its pool elements, in place of the structure's) may hold
`horizon:enhanced_terrain_adaptation`: MoogsStructureLib's terrain kernel, which carves or buries terrain around the
pieces on top of vanilla's `terrain_adaptation`. `kernel_size` and `kernel_distance` shape the kernel; `top` and
`bottom` (`carve`, `bury` or `none`) act above and below a piece's floor; `bottom_offset`, `padding` (`x`, `top`,
`bottom`, `z`) and MoogsStructureLib's `band` (`bottom`, `top`, `piece_heights`) move the box it measures from. On a
structure, `rigid_junctions` adds rigid pieces' junctions as well and `inflate` grows the start's box by the kernel
radius. `kernel_size` 0 is none.

```json
{ "horizon:enhanced_terrain_adaptation": { "kernel_size": 24, "kernel_distance": 24,
    "top": "carve", "bottom": "none", "rigid_junctions": true, "inflate": true } }
```

## Native mods

Behaviour that needs code (a new key, a HUD, a tool that changes how mining works) is a native mod. It is a bundle of
a `horizon-mixin.toml` and a few `.rs` helpers that hook into named functions of the game. Start from
[horizon-native-mod-template](https://github.com/horizon-rust/horizon-native-mod-template). How the launcher builds
one, what it pins and why it is not sandboxed: [native-mods.md](native-mods.md).

A native mod's config files go in the game's shared `config/` folder, beside `options.txt` (on a dedicated server,
beside `server.properties`), as Fabric and NeoForge mods' do: the mod picks its own file names, such as
`config/<mod id>.json`. It asks for the folder with `Game::native_config_dir()` (hook points API 26), which needs no
game, so it works from any hook, and makes the folder when missing. Settings kept with `native_set_setting` stay where they were, in `horizon-mods/.horizon-mod-data/<id>/`.

## Publish your mod

Horizon's registry lists mods, modpacks (`.hpack`) and resource packs made for Horizon. **A project is reviewed
once, when it is listed; its later releases are checked by machine, not read by a person.** Players find them at
[playhorizon.dev/mods](https://playhorizon.dev/mods) and in the launcher (Mods, then **Horizon** beside Modrinth),
which checks every file before it installs it.

1. Run `cargo horizon-mod check` on the file (above): the registry runs the same checks.
2. Put the source in a public GitHub repository, under a licence that lets players run it. A native mod's `.hnmod` is
   its source.
3. Publish a **GitHub release** in it with the file as an asset (`.hmod`, `.hnmod`, `.hpack`, `.hshader`, or a resource
   pack's `.zip`), and its `.minisig` beside it if you sign. The release notes are the changelog.
4. List the project once: open [playhorizon.dev/mods/submit](https://playhorizon.dev/mods/submit), sign in with GitHub
   and give the repository and the page (name, summary, licence, optionally a minisign public key). It opens a pull
   request in [horizon-rust/horizon-mods](https://github.com/horizon-rust/horizon-mods) adding `mods/<id>.toml`, with
   you as owner. A reviewer reads the repository and its source and merges it.

**Releasing a version is only step 3.** Publish a GitHub release (not a draft or a pre-release); within the hour the
registry reads it, runs the checks a submission runs (the file's own, the signature, the id and the version in the
file's manifest), and lists it. A release that fails is skipped and reported in an issue of the registry, never
published. Nobody opens a pull request and nobody reviews it. The version is the one in the file's manifest (the tag
when the file has none), the date and the changelog are the release's, the SHA-256 is computed by the registry, and
the launcher downloads the asset from your repository and refuses any other bytes. A published file never changes:
publish a new version. `revoked.toml` takes a bad one down.

Once it is published, its page and its card in the launcher show its rating: players signed in with GitHub on its
page give it 1 to 5 stars, one rating per account, which they can change. Its owners can't rate it, and nobody sees
who rated.

Your page can live in your repository too: a `horizon-registry.toml` at its root (on the newest release's tag) with
`name`, `summary`, `description`, `authors` and `license` fills what the registry's entry leaves out; the entry's own
words win. Its owners, key, kind and icon are the registry's, changed by a pull request. Projects listed before this
(`versions` in their entry) keep their hosted versions. The formats: [api/mod-index.md](api/mod-index.md).

### Integrity and signing

- **Integrity.** Every download is checked against the SHA-256 the index lists before the file reaches the game
  folder.
- **Signing.** Authors sign files with an Ed25519 key (minisign format: a `.minisig` beside the file); the index pins
  each project's public key, so an update signed by another key is refused. Unsigned local files stay allowed, with an
  "unsigned" mark.
- **Takedowns.** A file the registry takes down (`revoked.toml`) is refused by the launcher and turned off where
  installed.

## Horizon's official mods

Horizon's own mods are native. They live in
[horizon-rust/horizon-mods](https://github.com/horizon-rust/horizon-mods) under `native/<name>/`:

| Mod | Folder | Replaces |
|---|---|---|
| FPS Counter | `native/fps-overlay` | Extras > FPS counter |
| Keystrokes | `native/keystrokes` | Extras > Keystrokes |
| Zoom | `native/zoom` | Extras > Zoom |
| Minimap | `native/minimap` | Extras > Minimap |
| Recipes | `native/recipes` | The Recipes mod (item panel and recipe pages, on hook points version 2) |
| Coordinates HUD | `native/coords-hud` | A small example mod (position and facing, `/where`, `/coords`) |

The game keeps the parts that must be fast, such as drawing the minimap's map, and a native mod picks the options
([extras.md](extras.md)). Far View is not a mod any more: its distance and detail are Graphics > LOD Distance and Far
Detail ([graphics.md](graphics.md)).
