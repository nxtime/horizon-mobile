# Third-party notices

## wgpu-hal

`third_party/wgpu-hal` is [wgpu-hal](https://github.com/gfx-rs/wgpu) 30.0.1 by the gfx-rs
developers, with upstream fixes applied
([gfx-rs/wgpu#10124](https://github.com/gfx-rs/wgpu/pull/10124),
[gfx-rs/wgpu#10714](https://github.com/gfx-rs/wgpu/pull/10714)). It is licensed under MIT or
Apache-2.0; both licenses are in that folder (`LICENSE.MIT`, `LICENSE.APACHE`).

## Create

`crates/horizon-client/src/game/kinetic_machines.rs` ports
[Create](https://github.com/Creators-of-Create/Create) 6.0.10's mechanical drill and crushing
wheels (BlockBreakingKineticBlockEntity, DrillBlockEntity, CrushingWheelBlock and
CrushingWheelControllerBlockEntity) and the recipes Create makes as the game loads
(RuntimeDataGenerator), and `processing.rs`, `basins.rs`, `fans.rs`, `belts.rs`, `saws.rs`,
`funnels.rs`, `chutes.rs`, `bearings.rs` and `arms.rs` beside it its depot, millstone,
mechanical press, basin, mechanical mixer, blaze burner, encased fan, mechanical belt,
mechanical saw, funnels, chute, bearings and mechanical arm (DepotBehaviour,
MillstoneBlockEntity, PressingBehaviour, BasinRecipe, MechanicalMixerBlockEntity,
BlazeBurnerBlockEntity, AirCurrent, FanProcessing, BeltInventory, BeltConnectorItem,
SawBlockEntity, TreeCutter, FunnelBlock, FunnelBlockEntity, BeltFunnelBlock,
BeltFunnelInteractionHandler, ChuteBlockEntity, MechanicalBearingBlockEntity,
WindmillBearingBlockEntity, BearingContraption, BlockMovementChecks, ArmBlockEntity,
ArmInteractionPoint, ArmAngleTarget and their renderers), with `horizon_client::kinetics`'s water wheel
(WaterWheelBlockEntity) and stress (KineticNetwork) and `own_states.rs`'s placement
(DirectionalAxisKineticBlock), by The Create Team, whose code is under the MIT license
(`licenses/create-MIT.txt`). Create's assets are All Rights Reserved; none are in this
repository: a shared port fetches them from Modrinth on the player's device.
## naga

`third_party/naga` is [naga](https://github.com/gfx-rs/wgpu) 30.0.1 by the gfx-rs developers, with
fixes to its GLSL frontend that shader packs need, each applied in the commit that needed it. It is licensed under MIT or Apache-2.0; both licenses
are in that folder (`LICENSE.MIT`, `LICENSE.APACHE`).

## Pixelify Sans

`crates/horizon-theme/fonts/PixelifySans-*.ttf` is [Pixelify Sans](https://github.com/eifetx/Pixelify-Sans)
by The Pixelify Sans Project Authors, licensed under the SIL Open Font License 1.1
(`crates/horizon-theme/fonts/OFL-PixelifySans.txt`).

## Pixelarticons

`crates/horizon-theme/icons/pixel/*.svg` are icons from
[Pixelarticons](https://github.com/halfmage/pixelarticons) by Gerrit Halfmann, under the MIT
license (`crates/horizon-theme/icons/pixel/LICENSE-pixelarticons.txt`). `star.svg` is Horizon's own, drawn on
the same grid.

## OpenJDK for Android (fetched on the phone, not shipped)

To prepare the game files on a phone, Starling downloads OpenJDK 25.0.5 built for Android by
AngelAuraMC ([angelauramc-openjdk-build](https://github.com/AngelAuraMC/angelauramc-openjdk-build),
release `download_jre25`, checked against the SHA-256 in `crates/starling-account/src/java.rs`),
runs it for the preparing and deletes it after. OpenJDK is licensed under the GNU General Public
License version 2 with the Classpath Exception; its sources are at
[openjdk/jdk](https://github.com/openjdk/jdk), the build's scripts and patches in that
repository. Starling's launcher for it (`packaging/android/native/java_launcher.c`) is MIT.

## Bedrock's touch buttons (fetched on the phone, not shipped)

The touch controls wear Minecraft: Bedrock Edition's own buttons, which Starling downloads on the
phone from Mojang's [bedrock-samples](https://github.com/Mojang/bedrock-samples) repository (the
revision and each file's git blob SHA-1 in `crates/horizon-client/assets/bedrock-touch.json`, which
`tools/bedrock_touch_manifest.py` writes) into the player's resources, Mojang's `LICENSE.md` beside
them. They are © Mojang AB, under the Minecraft End User License Agreement the download is subject
to; Starling carries none of them. Where they are missing, Starling's own buttons
(`crates/horizon-client/assets/touch`, drawn by `packaging/touch/make.py`) are MIT.
## AMD FidelityFX SDK (FSR 3.1 frame generation)

`crates/horizon-client-render/src/gfx/frame_gen/optical_flow.wgsl` and `interpolation.wgsl` are
ports to WGSL of the optical flow and frame interpolation shaders of the
[AMD FidelityFX SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) 1.1.4
(`sdk/include/FidelityFX/gpu/{opticalflow,frameinterpolation}`, at commit
[c6efa6bf7f20](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/tree/c6efa6bf7f2027b3ec94f28578bb5965eabb9e55)),
and `optical_flow.rs` follows the SDK's `sdk/src/components/opticalflow/ffx_opticalflow.cpp`
(its passes, their order and their dispatch sizes). Copyright (C) 2024 Advanced Micro Devices,
Inc., under the MIT license, whose text heads each file. AMD and FidelityFX are AMD's
trademarks; Horizon is not affiliated with AMD.

## Mod loader logos

The launcher shows the logo of the mod loader an instance plays with.

- `launcher/assets/logos/quilt.png` is the Quilt mini icon (`brand/128png/quilt_mini_icon_transparent.png`)
  from [QuiltMC/art](https://github.com/QuiltMC/art), by the Quilt Project, dedicated to the public
  domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
- `launcher/assets/logos/neoforge.png` is NeoForged's icon (`art/neoforged_icon_16x16.png`) from
  [neoforged/.github](https://github.com/neoforged/.github/tree/main/art), © the NeoForged team,
  created by Ridanisaurus, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is
  unmodified (the launcher scales it up by whole pixels).
- Fabric's and Forge's icons are not shipped: neither publishes a license for its logo. The launcher
  fetches them from their own sites when an instance needs them
  ([fabric-loader's icon](https://github.com/FabricMC/fabric-loader/blob/master/src/main/resources/assets/fabricloader/icon.png),
  [files.minecraftforge.net's](https://files.minecraftforge.net/)).

Each logo belongs to its project. Showing it says which loader an instance runs; it does not mean
the project endorses Horizon.

## Sign in with Microsoft

The launcher's sign-in buttons follow Microsoft's published branding guidelines for apps that sign in
with Microsoft accounts
([Sign in with Microsoft branding](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-branding-in-apps)).
The four-square Microsoft symbol in `launcher/src/microsoft.rs` reproduces the squares, positions and
colours of Microsoft's official `ms-symbollockup_mssymbol_19.svg` from that page, unmodified. Microsoft
and its logo are trademarks of the Microsoft group of companies; Horizon is not endorsed by Microsoft.
