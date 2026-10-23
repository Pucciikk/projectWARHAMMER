package dev.warpbound.start;

import dev.warpbound.Warpbound;
import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundItems;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.List;

/**
 * Место крушения у спавна: спасательная капсула корабля игрока в борозде, вокруг дым,
 * и три обломка поблизости. Ставится один раз на мир, как бонусный сундук в ванилле.
 */
public final class CrashSite {
    private static final String FILE = "warpbound_crash_site";
    /** Капсула лежит вдоль оси X, нос (x = LENGTH-1) зарылся в землю. */
    private static final int LENGTH = 9;
    private static final double SHELL = 2.3, HOLLOW = 1.35;

    private CrashSite() {
    }

    public static void register() {
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            if (!WarpboundConfig.get().crashSiteEnabled) return;
            ServerLevel level = server.overworld();
            Placed placed = level.getDataStorage().computeIfAbsent(
                    new SavedData.Factory<>(Placed::new, (tag, reg) -> Placed.load(tag), null), FILE);
            if (placed.done) return;
            BlockPos origin = place(level, level.getSharedSpawnPos().offset(6, 0, 3), RandomSource.create(level.getSeed()));
            placed.done = true;
            placed.wake = surface(level, origin.offset(LENGTH / 2, 0, 9));
            placed.setDirty();
            level.setDefaultSpawnPos(placed.wake, 180f);
        });
    }

    /**
     * Первое пробуждение: ставим игрока у капсулы лицом к ней, чтобы сюжет начался с одного взгляда.
     * Иначе случайный спавн может бросить его на крышу капсулы или в лес за деревьями.
     */
    public static void wakeUp(ServerPlayer player) {
        ServerLevel level = player.server.overworld();
        Placed placed = level.getDataStorage().get(new SavedData.Factory<>(Placed::new, (tag, reg) -> Placed.load(tag), null), FILE);
        if (placed == null || placed.wake == null) return;
        BlockPos p = placed.wake;
        player.teleportTo(level, p.getX() + 0.5, p.getY(), p.getZ() + 0.5, 180f, 10f);
    }

    /** Поставить место крушения. Центр — точка на земле у хвоста капсулы. Нужна и для команды. */
    public static BlockPos place(ServerLevel level, BlockPos near, RandomSource random) {
        BlockPos origin = surface(level, near);
        int baseY = origin.getY();
        Warpbound.LOG.info("Место крушения: {}", origin);

        crater(level, origin, random);

        // Снести всё над землёй в объёме капсулы: деревья, траву, снег
        for (int x = -2; x <= LENGTH + 1; x++)
            for (int z = -4; z <= 4; z++)
                for (int y = 0; y <= 6; y++)
                    level.setBlock(origin.offset(x, y, z), Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);

        for (int x = 0; x < LENGTH; x++) {
            // Хвост приподнят, нос ушёл в землю на два блока
            double cy = baseY + 1.6 - x * 2.4 / (LENGTH - 1);
            for (int y = (int) Math.floor(cy - SHELL) - 1; y <= (int) Math.ceil(cy + SHELL); y++) {
                for (int z = -3; z <= 3; z++) {
                    double d = Math.sqrt((y + 0.5 - cy) * (y + 0.5 - cy) + z * z);
                    if (d > SHELL) continue;
                    BlockPos p = new BlockPos(origin.getX() + x, y, origin.getZ() + z);
                    boolean cap = x == 0 || x == LENGTH - 1;
                    boolean hatch = z == 3 - 1 && (x == 3 || x == 4) && y >= Math.floor(cy) - 1 && y <= Math.floor(cy);
                    if (d <= HOLLOW && !cap || hatch) {
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                    } else if (random.nextFloat() < 0.06f && y > baseY) {
                        // Пробоины в обшивке
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                    } else if ((x == 2 || x == 6) && !cap) {
                        // латунные пояса: по ним капсулу узнают издалека
                        level.setBlock(p, WarpboundBlocks.BRASS_TRIM.defaultBlockState(), Block.UPDATE_CLIENTS);
                    } else {
                        boolean scorched = x >= LENGTH - 3 || random.nextFloat() < 0.25f;
                        level.setBlock(p, (scorched ? WarpboundBlocks.SCORCHED_HULL_PLATING : WarpboundBlocks.HULL_PLATING)
                                .defaultBlockState(), Block.UPDATE_CLIENTS);
                    }
                }
            }
        }

        // Хвост: стабилизаторы и сопла двигателя
        double tailY = baseY + 1.6;
        int ty = (int) Math.floor(tailY);
        for (int z : new int[]{-3, 3}) {
            level.setBlock(origin.offset(0, ty - baseY, z), WarpboundBlocks.HULL_PLATING.defaultBlockState(), Block.UPDATE_CLIENTS);
            level.setBlock(origin.offset(-1, ty - baseY, z), WarpboundBlocks.BRASS_TRIM.defaultBlockState(), Block.UPDATE_CLIENTS);
        }
        level.setBlock(origin.offset(0, ty - baseY + 3, 0), WarpboundBlocks.HULL_PLATING.defaultBlockState(), Block.UPDATE_CLIENTS);
        level.setBlock(origin.offset(-1, ty - baseY + 3, 0), WarpboundBlocks.BRASS_TRIM.defaultBlockState(), Block.UPDATE_CLIENTS);
        for (int z = -1; z <= 1; z++) {
            level.setBlock(origin.offset(-1, ty - baseY, z), Blocks.IRON_BARS.defaultBlockState(), Block.UPDATE_ALL);
        }
        // Иллюминатор сверху
        level.setBlock(new BlockPos(origin.getX() + 4, (int) Math.ceil(baseY + 1.6 - 4 * 2.4 / (LENGTH - 1) + SHELL) - 1,
                origin.getZ()), Blocks.LIGHT_BLUE_STAINED_GLASS.defaultBlockState(), Block.UPDATE_CLIENTS);

        // Внутри: маяк у хвоста и сундук с уцелевшим
        BlockPos beacon = floorInside(level, origin.offset(1, 0, 0));
        level.setBlock(beacon, WarpboundBlocks.VOX_BEACON.defaultBlockState()
                .setValue(VoxBeaconBlock.FACING, Direction.EAST), Block.UPDATE_ALL);
        BlockPos chest = floorInside(level, origin.offset(5, 0, 0));
        level.setBlock(chest, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.SOUTH), Block.UPDATE_ALL);
        level.setBlock(floorInside(level, origin.offset(3, 0, -1)), Blocks.LANTERN.defaultBlockState(), Block.UPDATE_ALL);
        fill(level, chest, List.of(
                new ItemStack(WarpboundItems.DATA_SLATE_STORM),
                new ItemStack(Items.BREAD, 4),
                new ItemStack(Items.TORCH, 8)));

        // Нос дымит столбом, его видно издалека
        signalFire(level, origin.offset(LENGTH + 1, 0, 0));
        smoulder(level, origin.offset(LENGTH, 0, 3));
        smoulder(level, origin.offset(-2, 0, -3));

        debris(level, origin, 25, 15, random, List.of(new ItemStack(WarpboundItems.DATA_SLATE_NAVIGATOR), new ItemStack(Items.IRON_NUGGET, 6)));
        debris(level, origin, 150, 17, random, List.of(new ItemStack(WarpboundItems.DATA_SLATE_SHIP), new ItemStack(Items.RAW_COPPER, 3)));
        debris(level, origin, 265, 14, random, List.of(new ItemStack(WarpboundItems.VOX_MODULE), new ItemStack(Items.REDSTONE, 2)));
        return origin;
    }

    /** Выжженная воронка и борозда за хвостом. */
    private static void crater(ServerLevel level, BlockPos origin, RandomSource random) {
        BlockState[] scorch = {Blocks.COARSE_DIRT.defaultBlockState(), Blocks.GRAVEL.defaultBlockState(),
                Blocks.BLACKSTONE.defaultBlockState(), Blocks.TUFF.defaultBlockState(), Blocks.COARSE_DIRT.defaultBlockState()};
        for (int x = -10; x <= LENGTH + 5; x++) {
            for (int z = -7; z <= 7; z++) {
                double cx = x - (LENGTH / 2.0), r = Math.sqrt(cx * cx / 1.8 + z * z);
                boolean furrow = x < 0 && Math.abs(z) <= 2;
                if (r > 7 + random.nextFloat() * 1.5 && !furrow) continue;
                BlockPos ground = surface(level, origin.offset(x, 0, z));
                clearColumn(level, ground);
                BlockPos top = ground.below();
                if (!level.getBlockState(top).isSolid()) continue;
                level.setBlock(top, scorch[random.nextInt(scorch.length)], Block.UPDATE_CLIENTS);
            }
        }
    }

    private static void debris(ServerLevel level, BlockPos origin, double angleDeg, int distance,
                               RandomSource random, List<ItemStack> loot) {
        double a = Math.toRadians(angleDeg);
        BlockPos center = surface(level, origin.offset((int) Math.round(Math.cos(a) * distance) + LENGTH / 2,
                0, (int) Math.round(Math.sin(a) * distance)));
        for (int i = 0; i < 6; i++) {
            BlockPos p = surface(level, center.offset(random.nextInt(5) - 2, 0, random.nextInt(5) - 2));
            level.setBlock(p, (random.nextBoolean() ? WarpboundBlocks.SCORCHED_HULL_PLATING : WarpboundBlocks.HULL_PLATING)
                    .defaultBlockState(), Block.UPDATE_CLIENTS);
        }
        BlockPos barrel = surface(level, center.offset(1, 0, 1));
        level.setBlock(barrel, Blocks.BARREL.defaultBlockState().setValue(BarrelBlock.FACING, Direction.UP), Block.UPDATE_ALL);
        fill(level, barrel, loot);
        signalFire(level, center.offset(-1, 0, -1));
    }

    /** Костёр на стоге сена даёт высокий сигнальный дым. */
    private static void signalFire(ServerLevel level, BlockPos near) {
        BlockPos p = surface(level, near);
        level.setBlock(p, Blocks.HAY_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
        level.setBlock(p.above(), Blocks.CAMPFIRE.defaultBlockState().setValue(CampfireBlock.SIGNAL_FIRE, true), Block.UPDATE_ALL);
    }

    private static void smoulder(ServerLevel level, BlockPos near) {
        BlockPos p = surface(level, near);
        level.setBlock(p, Blocks.CAMPFIRE.defaultBlockState(), Block.UPDATE_ALL);
    }

    private static void fill(ServerLevel level, BlockPos pos, List<ItemStack> items) {
        if (level.getBlockEntity(pos) instanceof Container container) {
            for (int i = 0; i < items.size(); i++) container.setItem(i * 3 + 1, items.get(i).copy());
        }
    }

    /** Первая свободная клетка над настоящей землёй: стволы, листва и трава не считаются. */
    private static BlockPos surface(ServerLevel level, BlockPos pos) {
        BlockPos p = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, pos);
        while (p.getY() > level.getMinBuildHeight() && notGround(level.getBlockState(p.below()))) p = p.below();
        return p;
    }

    private static boolean notGround(BlockState state) {
        return state.isAir() || state.is(BlockTags.LOGS) || state.is(BlockTags.LEAVES) || state.canBeReplaced()
                || !state.getFluidState().isEmpty() && !state.isSolid();
    }

    /** Убрать деревья и траву над землёй в колонке: на месте падения капсулы ничего не растёт. */
    private static void clearColumn(ServerLevel level, BlockPos ground) {
        int top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, ground).getY();
        for (int y = ground.getY(); y <= top + 1; y++) {
            BlockPos p = new BlockPos(ground.getX(), y, ground.getZ());
            BlockState state = level.getBlockState(p);
            if (state.is(BlockTags.LOGS) || state.is(BlockTags.LEAVES) || state.canBeReplaced() && state.getFluidState().isEmpty()) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
            }
        }
    }

    /** Пол внутри капсулы: первая не-воздушная клетка снизу вверх по колонке x, z = 0. */
    private static BlockPos floorInside(ServerLevel level, BlockPos column) {
        BlockPos p = new BlockPos(column.getX(), column.getY() - 4, column.getZ());
        for (int i = 0; i < 10; i++, p = p.above()) {
            if (level.getBlockState(p).isSolid() && level.getBlockState(p.above()).isAir()) return p.above();
        }
        return column;
    }

    private static class Placed extends SavedData {
        boolean done;
        BlockPos wake;

        static Placed load(CompoundTag tag) {
            Placed p = new Placed();
            p.done = tag.getBoolean("done");
            if (tag.contains("wake")) p.wake = BlockPos.of(tag.getLong("wake"));
            return p;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            tag.putBoolean("done", done);
            if (wake != null) tag.putLong("wake", wake.asLong());
            return tag;
        }
    }
}
