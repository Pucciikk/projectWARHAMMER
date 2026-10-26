package dev.warpbound.client.mixin;

import dev.warpbound.client.ClientShipState;
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
        return entity != null && entity.getVehicle() instanceof DreadnoughtEntity ? zoom * 2.0f : zoom;
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
        // палуба корабля: дрожь на ходу, толчки запуска двигателей и раскрытия разлома
        float a = ClientShipState.shake();
        if (a > 0.01f) {
            float t = (entity.tickCount + partialTick) * 0.05f;
            float yaw = (float) (Math.sin(t * 31.0) * 0.6 + Math.sin(t * 13.7) * 0.4) * a * 0.9f;
            float pitch = (float) (Math.sin(t * 27.3 + 1.0) * 0.6 + Math.sin(t * 9.1) * 0.4) * a * 0.7f;
            this.setRotation(this.yRot + yaw, this.xRot + pitch);
            this.move(0f, (float) Math.sin(t * 41.0) * 0.02f * a, 0f);
        }
    }
}
