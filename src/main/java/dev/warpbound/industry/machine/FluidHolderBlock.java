package dev.warpbound.industry.machine;

import com.mojang.serialization.MapCodec;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Бак или факельная горелка: один блок, жидкость идёт по трубам. Горелка сжигает всё, что приходит: выход для побочных продуктов. */
public class FluidHolderBlock extends BaseEntityBlock {
    private final boolean flare;
    private final MapCodec<FluidHolderBlock> codec;

    public FluidHolderBlock(boolean flare, Properties properties) {
        super(properties);
        this.flare = flare;
        this.codec = simpleCodec(p -> new FluidHolderBlock(flare, p));
    }

    public boolean flare() {
        return flare;
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return codec;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new FluidHolderBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide ? null : createTickerHelper(type, FluidHolders.TYPE, FluidHolderBlockEntity::serverTick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!flare && !level.isClientSide && level.getBlockEntity(pos) instanceof FluidHolderBlockEntity tank) {
            player.displayClientMessage(tank.describe().withStyle(ChatFormatting.GOLD), true);
        }
        return flare ? InteractionResult.PASS : InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!flare || !(level.getBlockEntity(pos) instanceof FluidHolderBlockEntity b) || !b.burning()) return;
        level.addParticle(ParticleTypes.FLAME, pos.getX() + 0.5, pos.getY() + 1.15, pos.getZ() + 0.5, 0, 0.05, 0);
        if (random.nextInt(3) == 0) level.addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, pos.getX() + 0.5, pos.getY() + 1.3, pos.getZ() + 0.5, 0, 0.06, 0);
        if (random.nextInt(30) == 0) level.playLocalSound(pos, SoundEvents.FIRE_AMBIENT, SoundSource.BLOCKS, 0.6f, 0.8f, false);
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        super.onRemove(state, level, pos, newState, moved);
        if (level instanceof ServerLevel) Conduits.invalidate(level);
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
        super.onPlace(state, level, pos, old, moved);
        if (level instanceof ServerLevel) Conduits.invalidate(level);
    }
}
