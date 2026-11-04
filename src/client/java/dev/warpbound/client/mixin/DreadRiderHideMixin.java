package dev.warpbound.client.mixin;

import dev.warpbound.entity.dreadnought.concept.DreadConceptEntity;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderDispatcher;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Пилот сидит внутри саркофага: снаружи его не видно. */
@Mixin(EntityRenderDispatcher.class)
public abstract class DreadRiderHideMixin {
    @Inject(method = "shouldRender", at = @At("HEAD"), cancellable = true)
    private <E extends Entity> void warpbound$hidePilot(E entity, Frustum frustum, double x, double y, double z, CallbackInfoReturnable<Boolean> cir) {
        if (entity.getVehicle() instanceof DreadConceptEntity) cir.setReturnValue(false);
    }
}
