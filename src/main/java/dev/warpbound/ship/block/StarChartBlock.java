package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import dev.warpbound.ship.ShipNavigation;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Карта Империума на стене мостика: табло 7×4 блока (рисует StarChartRenderer), остальные клетки табло —
 * {@link FixturePartBlock}. Сам блок — нижний средний ряд табло, стоит вплотную к стене, facing — к зрителю.
 * ПКМ — экран карты, на котором выбирается мир для курса.
 */
public class StarChartBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<StarChartBlock> CODEC = simpleCodec(StarChartBlock::new);
    /** Размер табло в блоках: по ширине (с центром на блоке) и вверх от блока. */
    public static final int WIDTH = 7, HEIGHT = 4;

    /** Табло прижато к стене позади (с противоположной от facing стороны клетки). */
    private static final VoxelShape PLATE_N = Block.box(0, 0, 14, 16, 16, 16);
    private static final VoxelShape PLATE_S = Block.box(0, 0, 0, 16, 16, 2);
    private static final VoxelShape PLATE_E = Block.box(0, 0, 0, 2, 16, 16);
    private static final VoxelShape PLATE_W = Block.box(14, 0, 0, 16, 16, 16);

    public StarChartBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return switch (state.getValue(FACING)) {
            case SOUTH -> PLATE_S;
            case EAST -> PLATE_E;
            case WEST -> PLATE_W;
            default -> PLATE_N;
        };
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && player instanceof ServerPlayer sp) ShipNavigation.openChart(sp);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new StarChartBlockEntity(pos, state);
    }
}
