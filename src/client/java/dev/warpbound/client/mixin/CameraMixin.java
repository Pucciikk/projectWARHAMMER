package dev.warpbound.client.mixin;

import dev.warpbound.client.entity.DreadnoughtFx;
import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import net.minecraft.client.Camera;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.BlockGetter;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Camera.class)
public abstract class CameraMixin {
    @Shadow
    private float xRot;
    @Shadow
    private float yRot;
    @Shadow
    private Entity entity;

    @Shadow
    protected abstract void setRotation(float yRot, float xRot);

    @Shadow
    protected abstract void move(float zoom, float dy, float dx);

    /** Вид от третьего лица отодвигается: иначе дредноут закрывает весь экран. */
    @ModifyArg(method = "setup", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/Camera;getMaxZoom(F)F"))
    private float warpbound$dreadnoughtZoom(float zoom) {
        return entity != null && entity.getVehicle() instanceof DreadnoughtEntity ? zoom * 1.6f : zoom;
    }

    /** Тряска от шагов. */
    @Inject(method = "setup", at = @At("TAIL"))
    private void warpbound$shake(BlockGetter level, Entity entity, boolean detached, boolean reverse,
                                 float partialTick, CallbackInfo ci) {
        float[] o = DreadnoughtFx.cameraOffset(entity.tickCount + partialTick);
        if (o != null) {
            this.setRotation(this.yRot + o[0], this.xRot + o[1]);
            this.move(0f, o[2], 0f);
        }
    }
}
