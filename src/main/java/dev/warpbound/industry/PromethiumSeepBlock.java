package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Прометиевый выход: небольшая синяя лужа у трещины над залежью. Побулькивает, ничего не даёт сам.
 */
public class PromethiumSeepBlock extends Block {
    public static final MapCodec<PromethiumSeepBlock> CODEC = simpleCodec(PromethiumSeepBlock::new);
    private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 1, 16);

    public PromethiumSeepBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor, LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        return direction == Direction.DOWN && !canSurvive(state, level, pos) ? Blocks.AIR.defaultBlockState() : state;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        double x = pos.getX() + 0.2 + random.nextDouble() * 0.6, z = pos.getZ() + 0.2 + random.nextDouble() * 0.6;
        if (random.nextInt(8) == 0) {
            level.addParticle(ParticleTypes.SMOKE, x, pos.getY() + 0.1, z, 0, 0.02, 0);
        }
        if (random.nextInt(30) == 0) {
            level.playLocalSound(x, pos.getY(), z, SoundEvents.LAVA_POP, SoundSource.BLOCKS, 0.4f, 0.6f + random.nextFloat() * 0.3f, false);
        }
    }
}
