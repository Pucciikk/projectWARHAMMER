package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Прометиевая трещина: расколотый камень, из которого сочится синий прометий. Метка залежи, её и ищет игрок:
 * на суше видно столбик дыма и синие огоньки, под водой поднимается цепочка пузырей.
 */
public class PromethiumFissureBlock extends Block {
    public static final MapCodec<PromethiumFissureBlock> CODEC = simpleCodec(PromethiumFissureBlock::new);

    public PromethiumFissureBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        double x = pos.getX() + 0.25 + random.nextDouble() * 0.5, y = pos.getY() + 1.02, z = pos.getZ() + 0.25 + random.nextDouble() * 0.5;
        if (level.getFluidState(pos.above()).is(FluidTags.WATER)) {
            for (int i = 0; i < 3; i++) {
                level.addParticle(ParticleTypes.BUBBLE, x, y + random.nextDouble() * 0.5, z, 0, 0.25 + random.nextDouble() * 0.15, 0);
            }
            return;
        }
        if (!level.getBlockState(pos.above()).isAir()) return;
        if (random.nextInt(6) == 0) {
            level.addAlwaysVisibleParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, true, x, y, z, 0, 0.05, 0);
        }
        if (random.nextInt(4) == 0) {
            level.addParticle(ParticleTypes.SOUL_FIRE_FLAME, x, y, z, 0, 0.015 + random.nextDouble() * 0.02, 0);
        }
        if (random.nextInt(40) == 0) {
            level.playLocalSound(x, y, z, SoundEvents.LAVA_POP, SoundSource.BLOCKS, 0.35f, 0.5f + random.nextFloat() * 0.3f, false);
        }
    }
}
