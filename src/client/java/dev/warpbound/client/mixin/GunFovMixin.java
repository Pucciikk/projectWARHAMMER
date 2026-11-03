package dev.warpbound.client.mixin;

import dev.warpbound.client.gun.GunMixinHooks;
import net.minecraft.client.player.AbstractClientPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** При прицеливании угол зрения сужается: это и есть приближение. */
@Mixin(AbstractClientPlayer.class)
public abstract class GunFovMixin {
    @Inject(method = "getFieldOfViewModifier", at = @At("RETURN"), cancellable = true)
    private void warpbound$aimFov(CallbackInfoReturnable<Float> cir) {
        cir.setReturnValue(cir.getReturnValue() * GunMixinHooks.fovScale());
    }
}
