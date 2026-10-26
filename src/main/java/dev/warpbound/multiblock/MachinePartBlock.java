package dev.warpbound.multiblock;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Часть собранной машины: невидимый блок на месте блока груды. Помнит исходный блок и своё ядро.
 * Модель машины рисует ядро; ПКМ по части — то же, что ПКМ по ядру (печь, пресс открываются откуда угодно).
 */
public class MachinePartBlock extends BaseEntityBlock {
    public static final MapCodec<MachinePartBlock> CODEC = simpleCodec(MachinePartBlock::new);

    public MachinePartBlock(Properties properties) {
        super(properties);
    }

    /** Спрятать блок груды: на его место — часть машины, исходный блок — в её память. */
    static void replace(ServerLevel level, BlockPos pos, BlockPos core) {
        BlockState original = level.getBlockState(pos);
        if (original.is(WarpboundBlocks.MACHINE_PART)) return;
        level.setBlock(pos, WarpboundBlocks.MACHINE_PART.defaultBlockState(), Block.UPDATE_CLIENTS);
        if (level.getBlockEntity(pos) instanceof MachinePartBlockEntity part) part.bind(original, core);
    }

    /** Вернуть блок груды на место части (только если часть принадлежит этому ядру). */
    static void restore(ServerLevel level, BlockPos pos, BlockPos core) {
        if (!(level.getBlockEntity(pos) instanceof MachinePartBlockEntity part) || !core.equals(part.core())) return;
        BlockState original = part.original();
        part.release();
        level.setBlock(pos, original, Block.UPDATE_ALL);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MachinePartBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state, BlockGetter level, BlockPos pos) {
        return true;
    }

    @Override
    protected float getShadeBrightness(BlockState state, BlockGetter level, BlockPos pos) {
        return 1f;
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hit) {
        BlockPos core = core(level, pos);
        if (core == null) return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        BlockState coreState = level.getBlockState(core);
        return coreState.useItemOn(stack, level, player, hand, hit.withPosition(core));
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        BlockPos core = core(level, pos);
        if (core == null) return InteractionResult.PASS;
        return level.getBlockState(core).useWithoutItem(level, player, hit.withPosition(core));
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof MachinePartBlockEntity part
                && part.bound() && level.getBlockEntity(part.core()) instanceof MultiblockHost host) {
            host.multiblock().onPartRemoved(pos);
        }
        super.onRemove(state, level, pos, newState, moved);
    }

    private static BlockPos core(Level level, BlockPos pos) {
        return level.getBlockEntity(pos) instanceof MachinePartBlockEntity part && part.bound() ? part.core() : null;
    }
}
