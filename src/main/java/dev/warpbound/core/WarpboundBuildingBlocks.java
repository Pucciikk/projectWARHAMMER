package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.ship.block.BoardingHatchBlock;
import dev.warpbound.ship.block.BulkheadDoorBlock;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.ColorRGBA;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.phys.shapes.Shapes;

import java.util.List;

/**
 * Набор блоков: корабельная отделка, руды, камень и грунт Кинериса.
 * СГЕНЕРИРОВАНО tools/blocks/gen_block_set.py — руками не править, менять спецификацию в скрипте.
 * Блоки, которые уже были в WarpboundBlocks (обшивка, латунь, балка), здесь не регистрируются.
 */
public final class WarpboundBuildingBlocks {
    public static final Block HULL_SCRAP = block("hull_scrap", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(2.5f, 6f).sound(SoundType.COPPER).requiresCorrectToolForDrops()));
    public static final Block PLASTEEL_PANEL = block("plasteel_panel", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block RIVETED_PLASTEEL_PANEL = block("riveted_plasteel_panel", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block HAZARD_PANEL = block("hazard_panel", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block PLASTEEL_VENT = block("plasteel_vent", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block DECK_GRATING = block("deck_grating", new TransparentBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()));
    public static final Block HULL_PLATING_STAIRS = block("hull_plating_stairs", new StairBlock(WarpboundBlocks.HULL_PLATING.defaultBlockState(), BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block HULL_PLATING_SLAB = block("hull_plating_slab", new SlabBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block PLASTEEL_PANEL_STAIRS = block("plasteel_panel_stairs", new StairBlock(PLASTEEL_PANEL.defaultBlockState(), BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block PLASTEEL_PANEL_SLAB = block("plasteel_panel_slab", new SlabBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block COGITATOR_BANK = block("cogitator_bank", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().lightLevel(s -> 6), false, Shapes.block()));
    public static final Block VOX_GRILLE = block("vox_grille", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops(), false, Shapes.block()));
    public static final Block LUMEN_WALL = block("lumen_wall", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion().lightLevel(s -> 14), true, Block.box(4, 3, 9, 12, 13, 16)));
    public static final Block LUMEN_CEILING = block("lumen_ceiling", new DecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion().lightLevel(s -> 15), Block.box(4, 2, 4, 12, 16, 12)));
    public static final Block RADIATION_SIGN = block("radiation_sign", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion(), true, Block.box(1, 1, 15, 15, 15, 16)));
    public static final Block EMERGENCY_LUMEN = block("emergency_lumen", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion().lightLevel(s -> 10), true, Block.box(4, 3, 9, 12, 13, 16)));
    public static final Block PURITY_SEAL = block("purity_seal", new FacingDecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion(), true, Block.box(4, 0, 14, 12, 15, 16)));
    public static final Block COOLANT_PIPE = block("coolant_pipe", new RotatedPillarBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block GELLER_CONDUIT = block("geller_conduit", new RotatedPillarBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().lightLevel(s -> 9)));
    public static final Block BULKHEAD_DOOR = block("bulkhead_door", new BulkheadDoorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()));
    public static final Block BOARDING_HATCH = block("boarding_hatch", new BoardingHatchBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()));
    public static final Block LEAD_ORE = block("lead_ore", new DropExperienceBlock(UniformInt.of(0, 2), BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3f, 3f).sound(SoundType.STONE).requiresCorrectToolForDrops()));
    public static final Block DEEPSLATE_LEAD_ORE = block("deepslate_lead_ore", new DropExperienceBlock(UniformInt.of(0, 2), BlockBehaviour.Properties.of().mapColor(MapColor.DEEPSLATE).strength(4.5f, 3f).sound(SoundType.DEEPSLATE).requiresCorrectToolForDrops()));
    public static final Block LEAD_BLOCK = block("lead_block", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block RADIUM_ORE = block("radium_ore", new GlowingOreBlock(UniformInt.of(2, 5), 0x7CFF6A, BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3f, 3f).sound(SoundType.STONE).requiresCorrectToolForDrops().lightLevel(s -> 7)));
    public static final Block ADAMANTIUM_ORE = block("adamantium_ore", new DropExperienceBlock(UniformInt.of(4, 8), BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(8f, 1200f).sound(SoundType.ANCIENT_DEBRIS).requiresCorrectToolForDrops()));
    public static final Block WARPSTONE_ORE = block("warpstone_ore", new GlowingOreBlock(UniformInt.of(3, 7), 0xB45CFF, BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3f, 3f).sound(SoundType.STONE).requiresCorrectToolForDrops().lightLevel(s -> 5)));
    public static final Block PSYCRYSTAL_CLUSTER = block("psycrystal_cluster", new DecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE).strength(1.5f).sound(SoundType.AMETHYST_CLUSTER).noOcclusion().lightLevel(s -> 6).noCollission(), Block.box(3, 0, 3, 13, 12, 13)));
    public static final Block ASH_BLOCK = block("ash_block", new ColoredFallingBlock(new ColorRGBA(0xFF807C78), BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_GRAY).strength(0.5f).sound(SoundType.SAND)));
    public static final Block ASH_STONE = block("ash_stone", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE).requiresCorrectToolForDrops()));
    public static final Block ASH_STONE_BRICKS = block("ash_stone_bricks", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE).requiresCorrectToolForDrops()));
    public static final Block ASH_STONE_BRICK_STAIRS = block("ash_stone_brick_stairs", new StairBlock(ASH_STONE_BRICKS.defaultBlockState(), BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE).requiresCorrectToolForDrops()));
    public static final Block ASH_STONE_BRICK_SLAB = block("ash_stone_brick_slab", new SlabBlock(BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE).requiresCorrectToolForDrops()));
    public static final Block ASH_STONE_BRICK_WALL = block("ash_stone_brick_wall", new WallBlock(BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE).requiresCorrectToolForDrops().forceSolidOn()));
    public static final Block ASH_CLAY = block("ash_clay", new Block(BlockBehaviour.Properties.of().mapColor(MapColor.CLAY).strength(0.6f).sound(SoundType.GRAVEL)));
    public static final Block VITRIFIED_GLASS = block("vitrified_glass", new TransparentBlock(BlockBehaviour.Properties.of().mapColor(MapColor.NONE).strength(0.6f).sound(SoundType.GLASS).noOcclusion().isValidSpawn((s, l, p, e) -> false).isRedstoneConductor((s, l, p) -> false).isSuffocating((s, l, p) -> false).isViewBlocking((s, l, p) -> false)));
    public static final Block AMBER_VITRIFIED_GLASS = block("amber_vitrified_glass", new TransparentBlock(BlockBehaviour.Properties.of().mapColor(MapColor.NONE).strength(0.6f).sound(SoundType.GLASS).noOcclusion().isValidSpawn((s, l, p, e) -> false).isRedstoneConductor((s, l, p) -> false).isSuffocating((s, l, p) -> false).isViewBlocking((s, l, p) -> false)));
    public static final Block SMOKE_VITRIFIED_GLASS = block("smoke_vitrified_glass", new TransparentBlock(BlockBehaviour.Properties.of().mapColor(MapColor.NONE).strength(0.6f).sound(SoundType.GLASS).noOcclusion().isValidSpawn((s, l, p, e) -> false).isRedstoneConductor((s, l, p) -> false).isSuffocating((s, l, p) -> false).isViewBlocking((s, l, p) -> false)));
    public static final Block CHARRED_LOG = block("charred_log", new RotatedPillarBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2f).sound(SoundType.WOOD)));
    public static final Block BONE_PILE = block("bone_pile", new DecorBlock(BlockBehaviour.Properties.of().mapColor(MapColor.SAND).strength(0.3f).sound(SoundType.BONE_BLOCK).noOcclusion().noCollission(), Block.box(0, 0, 0, 16, 2, 16)));

    public static final Item RAW_LEAD = item("raw_lead");
    public static final Item LEAD_INGOT = item("lead_ingot");
    public static final Item RAW_RADIUM = item("raw_radium");
    public static final Item RAW_ADAMANTIUM = item("raw_adamantium");
    public static final Item WARPSTONE_SHARD = item("warpstone_shard");
    public static final Item PSYCRYSTAL = item("psycrystal");

    /** Все блоки набора — для вкладки творческого режима. */
    public static final List<Block> ALL = List.of(HULL_SCRAP, PLASTEEL_PANEL, RIVETED_PLASTEEL_PANEL, HAZARD_PANEL, PLASTEEL_VENT, DECK_GRATING, HULL_PLATING_STAIRS, HULL_PLATING_SLAB, PLASTEEL_PANEL_STAIRS, PLASTEEL_PANEL_SLAB, COGITATOR_BANK, VOX_GRILLE, LUMEN_WALL, LUMEN_CEILING, RADIATION_SIGN, EMERGENCY_LUMEN, PURITY_SEAL, COOLANT_PIPE, GELLER_CONDUIT, BULKHEAD_DOOR, BOARDING_HATCH, LEAD_ORE, DEEPSLATE_LEAD_ORE, LEAD_BLOCK, RADIUM_ORE, ADAMANTIUM_ORE, WARPSTONE_ORE, PSYCRYSTAL_CLUSTER, ASH_BLOCK, ASH_STONE, ASH_STONE_BRICKS, ASH_STONE_BRICK_STAIRS, ASH_STONE_BRICK_SLAB, ASH_STONE_BRICK_WALL, ASH_CLAY, VITRIFIED_GLASS, AMBER_VITRIFIED_GLASS, SMOKE_VITRIFIED_GLASS, CHARRED_LOG, BONE_PILE);
    public static final List<Item> ITEMS = List.of(RAW_LEAD, LEAD_INGOT, RAW_RADIUM, RAW_ADAMANTIUM, WARPSTONE_SHARD, PSYCRYSTAL);
    /** Блоки с прозрачными пикселями (cutout) и полупрозрачные (стекло) — для слоёв рендера на клиенте. */
    public static final List<Block> CUTOUT = List.of(DECK_GRATING, LUMEN_WALL, LUMEN_CEILING, RADIATION_SIGN, EMERGENCY_LUMEN, PURITY_SEAL, PSYCRYSTAL_CLUSTER, BONE_PILE);
    public static final List<Block> TRANSLUCENT = List.of(VITRIFIED_GLASS, AMBER_VITRIFIED_GLASS, SMOKE_VITRIFIED_GLASS);

    private WarpboundBuildingBlocks() {
    }

    private static Block block(String name, Block block) {
        Registry.register(BuiltInRegistries.BLOCK, Warpbound.id(name), block);
        Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new BlockItem(block, new Item.Properties()));
        return block;
    }

    private static Item item(String name) {
        return Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new Item(new Item.Properties()));
    }

    /** Вызывается из Warpbound.onInitialize, чтобы класс загрузился до заморозки реестров. */
    public static void register() {
    }
}
