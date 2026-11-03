package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.ManualPressBlock;
import dev.warpbound.ship.block.CommandConsoleBlock;
import dev.warpbound.ship.block.FixturePartBlock;
import dev.warpbound.ship.block.GravLiftBlock;
import dev.warpbound.industry.MechanicusForgeBlock;
import dev.warpbound.industry.ChainMachineBlock;
import dev.warpbound.industry.machine.ConduitBlock;
import dev.warpbound.industry.machine.ConveyorBlock;
import dev.warpbound.industry.machine.FluidHolderBlock;
import dev.warpbound.industry.machine.FluidPipeBlock;
import dev.warpbound.industry.machine.MachineSpec;
import dev.warpbound.industry.PromethiumExtractorBlock;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import dev.warpbound.industry.SalvageForgeBlock;
import dev.warpbound.multiblock.MachinePartBlock;
import dev.warpbound.ship.block.NavTableBlock;
import dev.warpbound.ship.block.ShipFixtureBlock;
import dev.warpbound.ship.block.StarChartBlock;
import dev.warpbound.ship.block.TeleportariumPadBlock;
import dev.warpbound.ship.block.WarpSamplerBlock;
import dev.warpbound.shipyard.ShipyardConsoleBlock;
import dev.warpbound.start.VoxBeaconBlock;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.sounds.SoundEvents;
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
    /** Прометиевый экстрактор 7×13×9: исполинская качалка, собирается из тяжёлого кожуха, рам и привода. */
    public static final Block PROMETHIUM_EXTRACTOR = register("promethium_extractor", new PromethiumExtractorBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLACK).strength(5f, 12f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()
            .lightLevel(state -> state.getValue(BlockStateProperties.LIT) ? 8 : 0)));
    // ---- провода: только к своим и к портам машин ----
    public static final Block FLUID_PIPE = register("fluid_pipe", new FluidPipeBlock(BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1.5f, 6f)
            .sound(SoundType.COPPER).noOcclusion().forceSolidOn()));
    public static final Block ENERGY_CABLE = conduit("energy_cable", MachineSpec.Kind.ENERGY);
    public static final Block ITEM_TUBE = conduit("item_tube", MachineSpec.Kind.ITEM);
    // ---- машины цепочки: точки эффектов в блоках от ядра (x, высота, глубина) ----
    public static final Block ORE_CRUSHER = chainMachine("ore_crusher", new ChainMachineBlock.Effects(
            new double[][]{{-0.54, 4.2, 2.24}, {0.54, 4.2, 2.24}}, new double[][]{{0, 0.6, -0.3}}, SoundEvents.GRINDSTONE_USE, 0.6f));
    public static final Block WASH_VAT = chainMachine("wash_vat", new ChainMachineBlock.Effects(
            new double[][]{{-1.2, 2.3, -0.15}}, new double[0][], SoundEvents.BOAT_PADDLE_WATER, 0.7f));
    public static final Block COKE_OVEN = chainMachine("coke_oven", new ChainMachineBlock.Effects(
            new double[][]{{0.82, 3.7, 1.92}}, new double[][]{{0, 0.5, -0.4}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.8f));
    public static final Block BLAST_FURNACE = chainMachine("blast_furnace", new ChainMachineBlock.Effects(
            new double[][]{{0, 6.2, 1.9}, {1.82, 6.2, 3.45}}, new double[][]{{0, 0.7, -0.3}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.5f));
    public static final Block CONVERTER = chainMachine("converter", new ChainMachineBlock.Effects(
            new double[][]{{0.82, 5.3, 2.1}}, new double[][]{{0, 1.0, -0.2}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.6f));
    public static final Block ROLLING_MILL = chainMachine("rolling_mill", new ChainMachineBlock.Effects(
            new double[][]{{-2.8, 4.1, 1.15}}, new double[0][], SoundEvents.ANVIL_LAND, 0.5f));
    public static final Block ELECTROLYZER = chainMachine("electrolyzer", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.BEACON_AMBIENT, 1.4f));
    public static final Block WATER_INTAKE = chainMachine("water_intake", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.BOAT_PADDLE_WATER, 0.5f));
    public static final Block COAL_GEN = chainMachine("coal_gen", new ChainMachineBlock.Effects(
            new double[][]{{0.9, 4.3, 1.95}}, new double[][]{{0.25, 0.8, -0.3}}, SoundEvents.PISTON_EXTEND, 0.6f));
    public static final Block SCRIPTORIUM = chainMachine("scriptorium", new ChainMachineBlock.Effects(
            new double[][]{{-1.2, 1.9, 1.34}, {1.2, 1.9, 1.34}}, new double[0][], SoundEvents.VILLAGER_WORK_CARTOGRAPHER, 0.8f));
    public static final Block ARMOURY = chainMachine("armoury", new ChainMachineBlock.Effects(
            new double[0][], new double[][]{{0.34, 1.1, 1.8}}, SoundEvents.ANVIL_USE, 1.2f));
    public static final Block BARREL_SHOP = chainMachine("barrel_shop", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.GRINDSTONE_USE, 1.3f));
    public static final Block AMMO_LINE = chainMachine("ammo_line", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.PISTON_EXTEND, 1.1f));
    public static final Block WEAVERY = chainMachine("weavery", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.VILLAGER_WORK_SHEPHERD, 0.9f));
    public static final Block DISTILLER = chainMachine("distiller", new ChainMachineBlock.Effects(
            new double[][]{{1.2, 8.8, 0.8}}, new double[][]{{-0.1, 0.8, -0.1}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.7f));
    public static final Block DESULFURIZER = chainMachine("desulfurizer", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.BREWING_STAND_BREW, 0.7f));
    public static final Block AUTOCLAVE = chainMachine("autoclave", new ChainMachineBlock.Effects(
            new double[][]{{0.75, 3.9, 1.55}}, new double[0][], SoundEvents.FIRE_EXTINGUISH, 0.6f));
    public static final Block FORGE_SMELTER = chainMachine("forge_smelter", new ChainMachineBlock.Effects(
            new double[][]{{0.72, 3.0, 1.98}}, new double[][]{{0, 1.3, 1.1}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.8f));
    public static final Block COGITATORIUM = chainMachine("cogitatorium", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.UI_LOOM_TAKE_RESULT, 1.3f));
    /** Прометиевый выход: битумная лужа над залежью, метка для экстрактора. */
    public static final Block PROMETHIUM_SEEP = register("promethium_seep", new dev.warpbound.industry.PromethiumSeepBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLUE).strength(0.5f).sound(SoundType.MUD).noOcclusion().noCollission().speedFactor(0.4f).jumpFactor(0.5f)
            .replaceable().pushReaction(net.minecraft.world.level.material.PushReaction.DESTROY).noLootTable()));
    /** Прометиевая трещина: то, что игрок ищет на поверхности. Светится слабо, чтобы её было видно и ночью. */
    public static final Block PROMETHIUM_FISSURE = register("promethium_fissure", new dev.warpbound.industry.PromethiumFissureBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLUE).strength(1.5f, 6f).sound(SoundType.STONE).lightLevel(s -> 3)));
    public static final Block CHEM_REACTOR = chainMachine("chem_reactor", new ChainMachineBlock.Effects(
            new double[][]{{-1.05, 3.9, 1.42}, {1.05, 3.9, 1.42}}, new double[0][], SoundEvents.BREWING_STAND_BREW, 0.9f));
    public static final Block POWDER_WORKS = chainMachine("powder_works", new ChainMachineBlock.Effects(
            new double[][]{{-1.65, 4.0, 1.6}}, new double[0][], SoundEvents.PISTON_EXTEND, 0.8f));
    public static final Block CEMENT_MILL = chainMachine("cement_mill", new ChainMachineBlock.Effects(
            new double[][]{{-0.62, 1.2, 0.0}}, new double[0][], SoundEvents.GRINDSTONE_USE, 0.5f));
    public static final Block CRACKER = chainMachine("cracker", new ChainMachineBlock.Effects(
            new double[][]{{1.02, 4.9, 2.02}}, new double[][]{{-0.25, 0.8, 0.15}}, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, 0.7f));
    public static final Block PROMETHIUM_GEN = chainMachine("promethium_gen", new ChainMachineBlock.Effects(
            new double[][]{{0.95, 4.2, 1.2}}, new double[0][], SoundEvents.PISTON_CONTRACT, 1.4f));
    public static final Block HYDROPONICS = chainMachine("hydroponics", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.BUCKET_FILL, 1.5f));
    public static final Block LUMBER = chainMachine("lumber", new ChainMachineBlock.Effects(
            new double[0][], new double[0][], SoundEvents.AXE_STRIP, 0.8f));
    public static final Block DEEP_DRILL = chainMachine("deep_drill", new ChainMachineBlock.Effects(
            new double[][]{{2.22, 3.8, 0.95}}, new double[0][], SoundEvents.GRINDSTONE_USE, 0.4f));
    public static final Block CONVEYOR = register("conveyor", new ConveyorBlock(BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(1.5f, 6f).sound(SoundType.COPPER).noOcclusion()));
    public static final Block FLUID_TANK = register("fluid_tank", new FluidHolderBlock(false, BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(3f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()));
    public static final Block FLARE_STACK = register("flare_stack", new FluidHolderBlock(true, BlockBehaviour.Properties.of()
            .mapColor(MapColor.METAL).strength(3f, 9f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion().lightLevel(s -> 0)));
    public static final java.util.List<Block> CHAIN_MACHINES = java.util.List.of(ORE_CRUSHER, WASH_VAT, COKE_OVEN, BLAST_FURNACE,
            CONVERTER, ROLLING_MILL, ELECTROLYZER, WATER_INTAKE, COAL_GEN, SCRIPTORIUM, ARMOURY, BARREL_SHOP, AMMO_LINE, WEAVERY,
            DISTILLER, DESULFURIZER, AUTOCLAVE, FORGE_SMELTER, COGITATORIUM,
            CHEM_REACTOR, POWDER_WORKS, CEMENT_MILL, CRACKER, PROMETHIUM_GEN, HYDROPONICS, LUMBER, DEEP_DRILL);
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
    /** Варп-двигатель: врата с воронкой у кормы машинного отделения (11×13×5). */
    public static final Block WARP_DRIVE = register("warp_drive", new ShipFixtureBlock(fixture(MapColor.COLOR_PURPLE).lightLevel(s -> 12)).bigModel());
    /** Штандарт с аквилой на стену: полотнище 2×3.5 блока свисает от кронштейна. */
    public static final Block IMPERIAL_STANDARD = register("imperial_standard", new ShipFixtureBlock(fixture(MapColor.COLOR_RED).noCollission()).bigModel());
    /** Штандарт на древке. */
    public static final Block IMPERIAL_STANDARD_POLE = register("imperial_standard_pole", new ShipFixtureBlock(fixture(MapColor.COLOR_RED)).bigModel());
    /** Гравилифт: площадка в полу, ПКМ — на палубу выше или ниже (анклав ↔ мостик). */
    public static final Block GRAV_LIFT = register("grav_lift", new GravLiftBlock(fixture(MapColor.COLOR_CYAN).lightLevel(s -> 8).noOcclusion()));
    /** Варп-пробоотборник анклава: стол со стенкой и портом в варп, механическая рука набирает пробы. */
    public static final Block WARP_SAMPLER = register("warp_sampler", new WarpSamplerBlock(fixture(MapColor.COLOR_RED).lightLevel(s -> 7).noOcclusion()));
    /** Карта Империума на стене мостика: табло 7×4, ПКМ — выбор мира для курса. */
    public static final Block STAR_CHART = register("star_chart", new StarChartBlock(fixture(MapColor.COLOR_BLACK).lightLevel(s -> 9).noOcclusion()));
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

    private static Block conduit(String name, MachineSpec.Kind kind) {
        return register(name, new ConduitBlock(kind, BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1.5f, 6f)
                .sound(SoundType.COPPER).noOcclusion().forceSolidOn()));
    }

    private static Block chainMachine(String name, ChainMachineBlock.Effects effects) {
        return register(name, new ChainMachineBlock(BlockBehaviour.Properties.of()
                .mapColor(MapColor.COLOR_BLACK).strength(5f, 12f).sound(SoundType.NETHERITE_BLOCK).requiresCorrectToolForDrops().noOcclusion()
                .lightLevel(state -> state.getValue(BlockStateProperties.LIT) ? 6 : 0), effects));
    }
}
