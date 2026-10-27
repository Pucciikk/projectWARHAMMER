package dev.warpbound.client.mixin;

import dev.warpbound.gear.LasgunItem;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.world.InteractionHand;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Лазган держат двумя руками на изготовке (как арбалет), а не как кирку. */
@Mixin(PlayerRenderer.class)
public abstract class PlayerArmPoseMixin {
    @Inject(method = "getArmPose", at = @At("HEAD"), cancellable = true)
    private static void warpbound$rifleHold(AbstractClientPlayer player, InteractionHand hand,
                                            CallbackInfoReturnable<HumanoidModel.ArmPose> cir) {
        if (player.getItemInHand(hand).getItem() instanceof LasgunItem) cir.setReturnValue(HumanoidModel.ArmPose.CROSSBOW_HOLD);
    }
}
