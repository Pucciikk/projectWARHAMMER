package dev.warpbound.mixin;

import dev.warpbound.entity.multipart.HitboxPart;
import dev.warpbound.entity.multipart.MultipartHost;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Клиент шлёт ID части, по которой ударил. ID частей идут сразу за ID хозяина,
 * так что достаточно проверить несколько ID назад.
 */
@Mixin(ServerLevel.class)
public abstract class ServerLevelMultipartMixin {
    private static final int MAX_PARTS = 16;

    @Inject(method = "getEntityOrPart", at = @At("RETURN"), cancellable = true)
    private void warpbound$findHitboxPart(int id, CallbackInfoReturnable<Entity> cir) {
        if (cir.getReturnValue() != null) {
            return;
        }
        ServerLevel self = (ServerLevel) (Object) this;
        for (int back = 1; back <= MAX_PARTS; back++) {
            if (self.getEntity(id - back) instanceof MultipartHost host) {
                for (HitboxPart part : host.getHitboxParts()) {
                    if (part.getId() == id) {
                        cir.setReturnValue(part);
                        return;
                    }
                }
            }
        }
    }
}
