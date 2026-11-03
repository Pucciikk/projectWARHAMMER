package dev.warpbound.client.mixin;

import dev.warpbound.client.gun.GunMixinHooks;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiGraphics;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** С оружием в руках вместо ванильного прицела — свой, из GunHud. */
@Mixin(Gui.class)
public abstract class GunGuiMixin {
    @Inject(method = "renderCrosshair", at = @At("HEAD"), cancellable = true)
    private void warpbound$crosshair(GuiGraphics graphics, DeltaTracker tracker, CallbackInfo ci) {
        if (GunMixinHooks.hideCrosshair()) ci.cancel();
    }
}
