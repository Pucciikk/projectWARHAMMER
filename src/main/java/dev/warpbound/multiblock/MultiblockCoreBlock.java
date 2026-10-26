package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/**
 * Ядро мультиблока. Ставится лицом к игроку: «перед» машины — там, где стоял игрок.
 * Сборка и разбор — Омниссианским ключом ({@link OmnissianKeyItem}).
 */
public abstract class MultiblockCoreBlock extends BaseEntityBlock {
    public static final net.minecraft.world.level.block.state.properties.DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    protected MultiblockCoreBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(MultiblockHost.FORMED, false));
    }

    protected abstract BlockEntityType<? extends MultiblockCoreBlockEntity> coreType();

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, MultiblockHost.FORMED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    /** Прятать модель ядра, когда машина собрана (цельную машину рисует рендер ядра). */
    protected boolean hidesWhenFormed() {
        return false;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return hidesWhenFormed() && state.getValue(MultiblockHost.FORMED) ? RenderShape.ENTITYBLOCK_ANIMATED : RenderShape.MODEL;
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof MultiblockHost core) {
            core.multiblock().onCoreRemoved();
        }
        super.onRemove(state, level, pos, newState, moved);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide ? null : createTickerHelper(type, coreType(), MultiblockCoreBlockEntity::serverTick);
    }
}
