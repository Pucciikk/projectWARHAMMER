package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AbstractFurnaceBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/** Горн обломков: переплавляет корабельный лом в пласталь и латунь. Топливо — как у печи. */
public class SalvageForgeBlock extends AbstractFurnaceBlock {
    public static final MapCodec<SalvageForgeBlock> CODEC = simpleCodec(SalvageForgeBlock::new);

    public SalvageForgeBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends AbstractFurnaceBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SalvageForgeBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return createFurnaceTicker(level, type, WarpboundBlockEntities.SALVAGE_FORGE);
    }

    @Override
    protected void openContainer(Level level, BlockPos pos, Player player) {
        if (level.getBlockEntity(pos) instanceof SalvageForgeBlockEntity forge) player.openMenu(forge);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(LIT)) return;
        double x = pos.getX() + 0.5, y = pos.getY(), z = pos.getZ() + 0.5;
        if (random.nextDouble() < 0.15) {
            level.playLocalSound(x, y, z, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.BLOCKS, 1f, 0.8f, false);
        }
        Direction facing = state.getValue(FACING);
        double side = random.nextDouble() * 0.6 - 0.3;
        double ox = facing.getAxis() == Direction.Axis.X ? facing.getStepX() * 0.52 : side;
        double oz = facing.getAxis() == Direction.Axis.Z ? facing.getStepZ() * 0.52 : side;
        level.addParticle(ParticleTypes.LAVA, x + ox, y + 0.4, z + oz, 0, 0, 0);
        // Искры лома: горн плюётся раскалёнными осколками
        if (random.nextInt(3) == 0) level.addParticle(ParticleTypes.ELECTRIC_SPARK, x + ox, y + 0.6, z + oz,
                facing.getStepX() * 0.08, 0.05, facing.getStepZ() * 0.08);
        level.addParticle(ParticleTypes.LARGE_SMOKE, x, y + 1.1, z, 0, 0.02, 0);
    }
}
