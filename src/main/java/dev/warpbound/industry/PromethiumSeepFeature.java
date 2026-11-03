package dev.warpbound.industry;

import com.mojang.serialization.Codec;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundBuildingBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * Выход прометия над полем {@link PromethiumDeposits}: извилистая трещина в грунте, из которой сочится синее, и небольшая лужа рядом.
 * В центральном чанке поля всегда, в остальных изредка и короче. На дне моря только трещина с пузырями.
 * Вне поля не делает ничего, поэтому трещина всегда честно показывает залежь.
 */
public class PromethiumSeepFeature extends Feature<NoneFeatureConfiguration> {
    public PromethiumSeepFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> ctx) {
        WorldGenLevel level = ctx.level();
        RandomSource random = ctx.random();
        ChunkPos chunk = new ChunkPos(ctx.origin());
        long seed = level.getSeed();
        if (!PromethiumDeposits.isDeposit(seed, chunk.x, chunk.z)) return false;
        boolean center = PromethiumDeposits.isFieldCenter(seed, chunk.x, chunk.z);
        if (!center && random.nextInt(3) != 0) return false;
        // трещина идёт от середины чанка, поэтому не выходит за область, куда фиче можно писать
        int x = chunk.getMiddleBlockX(), z = chunk.getMiddleBlockZ();
        int length = center ? 5 + random.nextInt(3) : 2 + random.nextInt(2);
        int dirX = random.nextBoolean() ? 1 : -1, dirZ = random.nextBoolean() ? 1 : -1;
        boolean placed = false;
        for (int i = 0; i < length; i++) {
            placed |= crack(level, random, x, z, i < length / 2 + 1);
            // шагаем по диагонали с отклонениями: прямая линия выглядела бы постройкой
            if (random.nextInt(3) != 0) x += dirX;
            if (random.nextInt(3) != 0) z += dirZ;
        }
        return placed;
    }

    private static boolean crack(WorldGenLevel level, RandomSource random, int x, int z, boolean puddle) {
        BlockPos ground = findGround(level, x, level.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z) - 1, z);
        if (ground == null) return false;
        level.setBlock(ground, WarpboundBlocks.PROMETHIUM_FISSURE.defaultBlockState(), 2);
        // камень под трещиной пропитан битумом: видно, если копнуть
        if (!level.getBlockState(ground.below()).isAir()) level.setBlock(ground.below(), WarpboundBuildingBlocks.BITUMEN_SHALE.defaultBlockState(), 2);
        if (!level.getBlockState(ground.above()).canBeReplaced()) return true;
        if (!level.getFluidState(ground.above()).isEmpty()) return true;
        level.setBlock(ground.above(), Blocks.AIR.defaultBlockState(), 2);
        if (puddle) {
            for (int[] d : new int[][]{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
                if (random.nextInt(5) < 3) continue;
                BlockPos side = findGround(level, x + d[0], ground.getY() + 2, z + d[1]);
                if (side == null || side.getY() != ground.getY()) continue;
                BlockPos top = side.above();
                if (level.getFluidState(top).isEmpty() && level.getBlockState(top).canBeReplaced()) {
                    level.setBlock(side, WarpboundBuildingBlocks.BITUMEN_SHALE.defaultBlockState(), 2);
                    level.setBlock(top, WarpboundBlocks.PROMETHIUM_SEEP.defaultBlockState(), 2);
                }
            }
        }
        return true;
    }

    /** Спускаемся сквозь листву, стволы и траву: высота OCEAN_FLOOR_WG считает деревья твёрдыми, а трещина лежит на земле. */
    private static BlockPos findGround(WorldGenLevel level, int x, int y, int z) {
        for (int i = 0; i < 24; i++, y--) {
            BlockPos p = new BlockPos(x, y, z);
            BlockState s = level.getBlockState(p);
            if (s.is(BlockTags.DIRT) || s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(BlockTags.SAND) || s.is(BlockTags.TERRACOTTA)
                    || s.is(Blocks.GRAVEL) || s.is(WarpboundBuildingBlocks.BITUMEN_SHALE) || s.is(WarpboundBlocks.PROMETHIUM_FISSURE)) return p;
            if (!s.is(BlockTags.LEAVES) && !s.is(BlockTags.LOGS) && !s.canBeReplaced()) return null;
        }
        return null;
    }
}
