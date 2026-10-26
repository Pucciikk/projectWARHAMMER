package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.ManualPressBlock;
import dev.warpbound.ship.block.CommandConsoleBlock;
import dev.warpbound.ship.block.FixturePartBlock;
import dev.warpbound.industry.MechanicusForgeBlock;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import dev.warpbound.industry.SalvageForgeBlock;
import dev.warpbound.multiblock.MachinePartBlock;
import dev.warpbound.ship.block.NavTableBlock;
import dev.warpbound.ship.block.ShipFixtureBlock;
import dev.warpbound.ship.block.TeleportariumPadBlock;
import dev.warpbound.shipyard.ShipyardConsoleBlock;
import dev.warpbound.start.VoxBeaconBlock;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.phys.shapes.Shapes;

public final class WarpboundBlocks {
    /** Обшивка корабля: из неё собрана капсула, позже — модули кораблей. */
    public static final Block HULL_PLATING = register("hull_plating", new Block(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_GRAY).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    public static final Block SCORCHED_HULL_PLATING = register("scorched_hull_plating", new Block(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLACK).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    /** Латунный пояс обшивки. */
    public static final Block BRASS_TRIM = register("brass_trim", new Block(BlockBehaviour.Properties.of()
            .mapColor(MapColor.GOLD).strength(4f, 9f).sound(SoundType.COPPER).requiresCorrectToolForDrops()));
    /** Вокс-маяк капсулы. Неразрушим: без него не закончить главу 1. */
    public static final Block VOX_BEACON = register("vox_beacon", new VoxBeaconBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(-1f, 3600000f).sound(SoundType.NETHERITE_BLOCK).noLootTable().noOcclusion()
            .lightLevel(state -> state.getValue(VoxBeaconBlock.REPAIRED) ? 9 : 2)));
    /** Балка стапеля: из неё собирают раму верфи. */
    public static final Block DOCK_GIRDER = register("dock_girder", new Block(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_GRAY).strength(5f, 12f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()));
    /** Горн обломков: переплавка корабельного лома. */
    public static final Block SALVAGE_FORGE = register("salvage_forge", new SalvageForgeBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLACK).strength(3.5f).sound(SoundType.METAL).requiresCorrectToolForDrops().noOcclusion()
            .lightLevel(state -> state.getValue(SalvageForgeBlock.LIT) ? 13 : 0)));
    /** Ручной пресс: шестерни и пластины. */
    public static final Block MANUAL_PRESS = register("manual_press", new ManualPressBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(3.5f).sound(SoundType.METAL).requiresCorrectToolForDrops().noOcclusion()));
    /** Ядро Кузни Механикус (5×5×6): рабочее место техножреца, освящается ключом. */
    public static final Block MECHANICUS_FORGE = register("mechanicus_forge", new MechanicusForgeBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_RED).strength(5f, 12f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()
            .lightLevel(state -> state.getValue(BlockStateProperties.LIT) ? 14 : 4)));
    // ---- оборудование отсеков корабля ----
    /** Навигационный стол мостика: выбор цели и старт перехода. */
    public static final Block NAV_TABLE = register("nav_table", new NavTableBlock(fixture(MapColor.COLOR_BLACK).lightLevel(s -> 6)).bigModel());
    /** Ауспик мостика: на нём появляется туманное предупреждение о варп-событии. */
    public static final Block AUSPEX = register("auspex", new ShipFixtureBlock(fixture(MapColor.COLOR_GREEN).lightLevel(s -> 8)).bigModel());
    /** Узел Поля Геллера: варп-шторм перегружает их, игроки чинят. */
    public static final Block GELLER_NODE = register("geller_node", new ShipFixtureBlock(fixture(MapColor.COLOR_LIGHT_BLUE).lightLevel(s -> 10)).bigModel());
    /** Ядро реактора: сердце машинного отделения. */
    public static final Block REACTOR_CORE = register("reactor_core", new ShipFixtureBlock(fixture(MapColor.COLOR_ORANGE).lightLevel(s -> 15)).bigModel());
    /** Площадка телепортариума: высадка на мир под кораблём. */
    public static final Block TELEPORTARIUM_PAD = register("teleportarium_pad", new TeleportariumPadBlock(fixture(MapColor.COLOR_CYAN).lightLevel(s -> 9)).bigModel());
    /** Пульт верфи — ядро стапеля. */
    public static final Block SHIPYARD_CONSOLE = register("shipyard_console", new ShipyardConsoleBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(5f, 12f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops()
            .noOcclusion().lightLevel(state -> 7)));
    /** Командный пульт мостика: состояние корабля, навигация, Поле Геллера, реактор. */
    public static final Block COMMAND_CONSOLE = register("command_console",
            new CommandConsoleBlock(fixture(MapColor.COLOR_BLACK).lightLevel(s -> 7)).bigModel());
    /** Капитанский трон мостика (М7). Позже — точка возрождения после смерти на Кинерисе. */
    public static final Block COMMAND_THRONE = register("command_throne", new ShipFixtureBlock(fixture(MapColor.COLOR_RED),
            Shapes.or(Block.box(2, 0, 2, 14, 8, 14), Block.box(3, 8, 12, 13, 24, 14))));

    /** Часть крупного корабельного оборудования: невидима, прочна, ПКМ — по оборудованию. Без предмета. */
    public static final Block FIXTURE_PART = Registry.register(BuiltInRegistries.BLOCK, Warpbound.id("fixture_part"),
            new FixturePartBlock(fixture(MapColor.METAL)));

    /** Часть собранной машины: невидима, помнит блок груды (см. MultiblockController). Без предмета. */
    public static final Block MACHINE_PART = Registry.register(BuiltInRegistries.BLOCK, Warpbound.id("machine_part"),
            new MachinePartBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(-1f, 3600000f)
                    .sound(SoundType.NETHERITE_BLOCK).noLootTable().noOcclusion()));

    private WarpboundBlocks() {
    }

    /** Свойства корабельного оборудования: прочное, не выпадает и не ломается игроками в бою (интерьер ломают только события). */
    private static BlockBehaviour.Properties fixture(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).strength(-1f, 3600000f).sound(SoundType.NETHERITE_BLOCK).noLootTable()
                .noOcclusion();
    }

    private static Block register(String name, Block block) {
        Registry.register(BuiltInRegistries.BLOCK, Warpbound.id(name), block);
        Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new BlockItem(block, new Item.Properties()));
        return block;
    }

    public static void register() {
    }
}
