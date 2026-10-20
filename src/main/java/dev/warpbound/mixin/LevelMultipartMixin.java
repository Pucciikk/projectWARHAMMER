package dev.warpbound.mixin;

import dev.warpbound.entity.multipart.HitboxPart;
import dev.warpbound.entity.multipart.MultipartHost;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.entity.LevelEntityGetter;
import net.minecraft.world.phys.AABB;
import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.List;
import java.util.function.Predicate;

/**
 * Ванилла добавляет в поиск сущностей только части Эндер-дракона.
 * Здесь то же самое для всех MultipartHost: удар, стрела и взрыв находят наши хитбоксы.
 */
@Mixin(Level.class)
public abstract class LevelMultipartMixin {
    @Shadow
    protected abstract LevelEntityGetter<Entity> getEntities();

    @Inject(method = "getEntities(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/phys/AABB;Ljava/util/function/Predicate;)Ljava/util/List;",
            at = @At("RETURN"))
    private void warpbound$addHitboxParts(@Nullable Entity except, AABB area, Predicate<? super Entity> predicate,
                                          CallbackInfoReturnable<List<Entity>> cir) {
        List<Entity> result = cir.getReturnValue();
        // Хозяин сам может не пройти predicate (он не isPickable), поэтому ищем его отдельно
        this.getEntities().get(area, entity -> {
            if (entity instanceof MultipartHost host && (except == null || !host.hidesPartsFrom(except))) {
                for (HitboxPart part : host.getHitboxParts()) {
                    if (part.getBoundingBox().intersects(area) && predicate.test(part)) {
                        result.add(part);
                    }
                }
            }
        });
    }
}
