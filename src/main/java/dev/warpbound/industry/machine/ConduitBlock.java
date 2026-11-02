package dev.warpbound.industry.machine;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.PipeBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/** Труба, кабель или пневмопровод: соединяются только со своими и с портами машин. Без сущности блока и без тика. */
public class ConduitBlock extends PipeBlock {
    private final MachineSpec.Kind kind;
    private final MapCodec<ConduitBlock> codec;

    public ConduitBlock(MachineSpec.Kind kind, Properties properties) {
        super(0.1875f, properties);
        this.kind = kind;
        this.codec = simpleCodec(p -> new ConduitBlock(kind, p));
        BlockState state = stateDefinition.any();
        for (Direction d : Direction.values()) state = state.setValue(PROPERTY_BY_DIRECTION.get(d), false);
        registerDefaultState(state);
    }

    public MachineSpec.Kind kind() {
        return kind;
    }

    @Override
    protected MapCodec<? extends PipeBlock> codec() {
        return codec;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(NORTH, EAST, SOUTH, WEST, UP, DOWN);
    }

    /** Состояние со всеми соединениями: и для новой трубы, и когда порт появился или пропал. */
    public BlockState connections(Level level, BlockPos pos) {
        BlockState state = defaultBlockState();
        for (Direction d : Direction.values()) {
            state = state.setValue(PROPERTY_BY_DIRECTION.get(d), connects(level, pos, d));
        }
        return state;
    }

    private boolean connects(Level level, BlockPos pos, Direction d) {
        BlockPos next = pos.relative(d);
        if (level.getBlockState(next).getBlock() instanceof ConduitBlock c) return c.kind == kind;
        // на клиенте описаний машин нет: соединения приходят с сервера
        return !level.isClientSide && Conduits.hasStorage(level, next, d.getOpposite(), kind);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return connections(context.getLevel(), context.getClickedPos());
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor, LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (!(level instanceof Level real) || real.isClientSide) return state;
        return state.setValue(PROPERTY_BY_DIRECTION.get(direction), connects(real, pos, direction));
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
        super.onPlace(state, level, pos, old, moved);
        if (!level.isClientSide) Conduits.invalidate(level);
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        super.onRemove(state, level, pos, newState, moved);
        if (!level.isClientSide) Conduits.invalidate(level);
    }

    @Override
    protected boolean isPathfindable(BlockState state, net.minecraft.world.level.pathfinder.PathComputationType type) {
        return false;
    }

    @Override
    protected float getShadeBrightness(BlockState state, BlockGetter level, BlockPos pos) {
        return 1f;
    }
}
