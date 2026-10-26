package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Гермодверь (люк) корабля: проём из нескольких клеток открывается и закрывается целиком по ПКМ.
 * Открытая — проходима и не видна (створки ушли в переборку), закрытая — сплошная плита.
 * Запертую (LOCKED) рукой не открыть: так пульт задраивает люки перед выходом в космос и в варп.
 */
public class BulkheadDoorBlock extends Block {
    public static final MapCodec<BulkheadDoorBlock> CODEC = simpleCodec(BulkheadDoorBlock::new);
    public static final BooleanProperty OPEN = BooleanProperty.create("open");
    public static final BooleanProperty LOCKED = BooleanProperty.create("locked");
    /** Сколько клеток проёма обходим за раз (дверь 2×3 — 6, шлюз побольше — до 16). */
    private static final int MAX_CELLS = 32;

    public BulkheadDoorBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(OPEN, false).setValue(LOCKED, false));
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(OPEN, LOCKED);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        // открытую дверь можно «нащупать» лучом (чтобы закрыть), но пройти сквозь
        return state.getValue(OPEN) ? Block.box(6, 0, 6, 10, 16, 10) : Shapes.block();
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(OPEN) ? Shapes.empty() : Shapes.block();
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return state.getValue(OPEN) ? RenderShape.INVISIBLE : RenderShape.MODEL;
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state, BlockGetter level, BlockPos pos) {
        return state.getValue(OPEN);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (state.getValue(LOCKED)) {
            player.displayClientMessage(Component.translatable("block.warpbound.bulkhead_door.locked").withStyle(ChatFormatting.RED), true);
            level.playSound(null, pos, SoundEvents.IRON_DOOR_CLOSE, SoundSource.BLOCKS, 0.6f, 0.5f);
            return InteractionResult.CONSUME;
        }
        setAll(level, cells(level, pos), !state.getValue(OPEN), false);
        return InteractionResult.CONSUME;
    }

    /** Все клетки этого проёма: связные соседние гермодвери. */
    public static List<BlockPos> cells(BlockGetter level, BlockPos start) {
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(start.immutable());
        seen.add(start.immutable());
        while (!queue.isEmpty() && seen.size() < MAX_CELLS) {
            BlockPos p = queue.poll();
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                if (!seen.contains(n) && level.getBlockState(n).getBlock() instanceof BulkheadDoorBlock) {
                    seen.add(n);
                    queue.add(n);
                }
            }
        }
        return List.copyOf(seen);
    }

    /** Открыть/закрыть и запереть проём; звук — у первой клетки. */
    public static void setAll(Level level, List<BlockPos> cells, boolean open, boolean locked) {
        for (BlockPos p : cells) {
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof BulkheadDoorBlock) {
                level.setBlock(p, s.setValue(OPEN, open).setValue(LOCKED, locked), Block.UPDATE_ALL);
            }
        }
        if (!cells.isEmpty() && level instanceof ServerLevel server) {
            BlockPos p = cells.get(0);
            server.playSound(null, p, open ? SoundEvents.PISTON_EXTEND : SoundEvents.PISTON_CONTRACT, SoundSource.BLOCKS, 1f, 0.55f);
            server.playSound(null, p, open ? SoundEvents.IRON_DOOR_OPEN : SoundEvents.IRON_DOOR_CLOSE, SoundSource.BLOCKS, 1f, 0.6f);
        }
    }
}
