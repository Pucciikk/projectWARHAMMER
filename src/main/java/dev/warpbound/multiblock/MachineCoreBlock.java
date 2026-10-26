package dev.warpbound.multiblock;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Ядро машины с цельной моделью ({@link MachineCoreBlockEntity}): собранная машина рисуется моделью,
 * несобранная — своим блоком. ПКМ пустой рукой по несобранной машине главы 1 — освящение;
 * по собранной — {@link #useFormed}.
 */
public abstract class MachineCoreBlock extends MultiblockCoreBlock {
    protected MachineCoreBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected boolean hidesWhenFormed() {
        return true;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof MachineCoreBlockEntity core)) return InteractionResult.PASS;
        if (core.isFormed()) return useFormed(state, level, pos, player, core);
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (core.formsWith(ItemStack.EMPTY) && player instanceof ServerPlayer sp) {
            core.tryForm(sp);
        } else {
            player.displayClientMessage(Component.translatable("multiblock.warpbound.needs_key").withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.CONSUME;
    }

    /** ПКМ по собранной машине (или по любой её невидимой части). */
    protected InteractionResult useFormed(BlockState state, Level level, BlockPos pos, Player player, MachineCoreBlockEntity core) {
        return InteractionResult.PASS;
    }
}
