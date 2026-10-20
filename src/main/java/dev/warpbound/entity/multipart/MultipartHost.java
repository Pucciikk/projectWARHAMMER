package dev.warpbound.entity.multipart;

import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;

/**
 * Сущность из нескольких хитбоксов (как Эндер-дракон, но для любых наших существ).
 * Части не живут в мире сами по себе: миксины в Level/ServerLevel подставляют их
 * в поиск сущностей, поэтому по ним можно попасть мечом, стрелой и взрывом.
 */
public interface MultipartHost {
    HitboxPart[] getHitboxParts();

    /** Урон по конкретной части; множитель брони части уже учтён. */
    boolean hurtFromPart(HitboxPart part, DamageSource source, float amount);

    /** Своих частей не видит ни сам хозяин, ни его пилот, иначе пилот бил бы по себе. */
    default boolean hidesPartsFrom(Entity viewer) {
        Entity self = (Entity) this;
        return viewer == self || viewer.getRootVehicle() == self;
    }
}
