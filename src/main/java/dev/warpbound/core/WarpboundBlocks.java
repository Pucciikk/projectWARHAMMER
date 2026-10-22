package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.start.VoxBeaconBlock;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

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
            .mapColor(MapColor.METAL).strength(-1f, 3600000f).sound(SoundType.NETHERITE_BLOCK).noLootTable()
            .lightLevel(state -> state.getValue(VoxBeaconBlock.REPAIRED) ? 9 : 2)));

    private WarpboundBlocks() {
    }

    private static Block register(String name, Block block) {
        Registry.register(BuiltInRegistries.BLOCK, Warpbound.id(name), block);
        Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new BlockItem(block, new Item.Properties()));
        return block;
    }

    public static void register() {
    }
}
