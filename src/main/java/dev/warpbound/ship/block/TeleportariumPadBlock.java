package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import dev.warpbound.ship.ShipNavigation;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Площадка телепортариума: ПКМ — высадка на мир, над которым висит корабль. */
public class TeleportariumPadBlock extends ShipFixtureBlock {
    public static final MapCodec<TeleportariumPadBlock> CODEC = simpleCodec(TeleportariumPadBlock::new);

    public TeleportariumPadBlock(Properties properties) {
        super(properties, Block.box(0, 0, 0, 16, 16, 16));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && player instanceof ServerPlayer sp) ShipNavigation.beamDown(sp);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(3) == 0) {
            level.addParticle(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + random.nextDouble(), pos.getY() + 1.05,
                    pos.getZ() + random.nextDouble(), 0, 0.03, 0);
        }
    }
}
