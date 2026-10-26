package dev.warpbound.core;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.EnumMap;
import java.util.Map;

/**
 * Декор, повёрнутый по сторонам света: когитаторная стойка (лицом к игроку), настенный люмен (на стене, светом от неё).
 * Форма задаётся для «лицом на север» и поворачивается сама.
 */
public class FacingDecorBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<FacingDecorBlock> CODEC = simpleCodec(p -> new FacingDecorBlock(p, false, Shapes.block()));

    /** Вешается на стену: смотрит от стены, без опоры отваливается. */
    private final boolean wall;
    private final Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);

    public FacingDecorBlock(Properties properties, boolean wall, VoxelShape north) {
        super(properties);
        this.wall = wall;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
        for (Direction d : Direction.Plane.HORIZONTAL) shapes.put(d, rotate(north, d));
    }

    /** Повернуть форму, заданную для севера, к стороне d (по часовой, как модель в blockstate). */
    private static VoxelShape rotate(VoxelShape north, Direction d) {
        VoxelShape[] out = {Shapes.empty()};
        north.forAllBoxes((x0, y0, z0, x1, y1, z1) -> {
            double[] a = turn(x0, z0, d), b = turn(x1, z1, d);
            out[0] = Shapes.or(out[0], Shapes.box(Math.min(a[0], b[0]), y0, Math.min(a[1], b[1]),
                    Math.max(a[0], b[0]), y1, Math.max(a[1], b[1])));
        });
        return out[0];
    }

    private static double[] turn(double x, double z, Direction d) {
        return switch (d) {
            case EAST -> new double[]{1 - z, x};
            case SOUTH -> new double[]{1 - x, 1 - z};
            case WEST -> new double[]{z, 1 - x};
            default -> new double[]{x, z};
        };
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
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        if (!wall) return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
        Direction face = context.getClickedFace();
        if (face.getAxis().isVertical()) face = context.getHorizontalDirection().getOpposite();
        BlockState state = defaultBlockState().setValue(FACING, face);
        return canSurvive(state, context.getLevel(), context.getClickedPos()) ? state : null;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        if (!wall) return true;
        Direction back = state.getValue(FACING).getOpposite();
        return level.getBlockState(pos.relative(back)).isFaceSturdy(level, pos.relative(back), state.getValue(FACING));
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction dir, BlockState neighbor, net.minecraft.world.level.LevelAccessor level,
                                     BlockPos pos, BlockPos neighborPos) {
        if (wall && dir == state.getValue(FACING).getOpposite() && !canSurvive(state, level, pos)) {
            return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, dir, neighbor, level, pos, neighborPos);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes.get(state.getValue(FACING));
    }
}
