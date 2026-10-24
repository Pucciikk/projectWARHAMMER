package dev.warpbound.multiblock;

import dev.warpbound.core.TooltipItem;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

/**
 * Омниссианский ключ — инструмент освящения машин.
 * ПКМ по ядру — собрать машину (или узнать, чего не хватает). Shift+ПКМ по любой её части — разобрать.
 */
public class OmnissianKeyItem extends TooltipItem {
    public OmnissianKeyItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        boolean coreClicked = level.getBlockEntity(pos) instanceof MultiblockCoreBlockEntity;
        BlockPos corePos = coreClicked ? pos : Multiblocks.coreOf(level, pos).orElse(null);
        if (corePos == null) return InteractionResult.PASS;
        if (level.isClientSide) return InteractionResult.SUCCESS;

        if (!(level.getBlockEntity(corePos) instanceof MultiblockCoreBlockEntity core)
                || !(context.getPlayer() instanceof ServerPlayer player)) return InteractionResult.PASS;
        if (player.isShiftKeyDown()) {
            core.unform(player);
        } else if (coreClicked) {
            core.tryForm(player);
        } else {
            return InteractionResult.PASS;
        }
        return InteractionResult.CONSUME;
    }
}
