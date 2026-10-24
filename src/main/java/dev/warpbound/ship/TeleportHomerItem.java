package dev.warpbound.ship;

import dev.warpbound.core.TooltipItem;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Телепорт-маяк: на планете ПКМ — подняться на свой корабль, если он на орбите. */
public class TeleportHomerItem extends TooltipItem {
    public TeleportHomerItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide && player instanceof ServerPlayer sp) {
            if (ShipInteriors.isInterior(level)) return InteractionResultHolder.pass(stack);
            ShipNavigation.beamUp(sp);
            player.getCooldowns().addCooldown(this, 60);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
