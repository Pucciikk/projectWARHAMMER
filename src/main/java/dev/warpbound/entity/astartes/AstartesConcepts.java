package dev.warpbound.entity.astartes;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import java.util.ArrayList;
import java.util.List;

/**
 * Макеты Астартес и Громового воина: отдельные сущности, позже их модель и движения перейдут к игроку.
 * Модели и клипы пишут tools/models/blender/astartes/astartes.py и thunder_warrior.py.
 * Вызвать: /summon warpbound:astartes, /summon warpbound:thunder_warrior. Показать клип на месте: {NoAI:1b,Clip:"move.walk"}.
 */
public final class AstartesConcepts {
    /** walkSpeed и runSpeed — блоков в секунду при нормальной скорости клипа (печатает скрипт модели); по ним ноги синхронны с землёй. glow — есть ли светящиеся линзы или стёкла очков. */
    public record Variant(String model, float width, float height, float walkSpeed, float runSpeed, double maxHealth, double armor, double damage, boolean glow) {
    }

    public static final Variant ASTARTES_VARIANT = new Variant("astartes", 1.0f, 2.2f, 1.434f, 4.554f, 80, 16, 10, true);
    public static final Variant THUNDER_WARRIOR_VARIANT = new Variant("thunder_warrior", 1.1f, 2.1f, 1.188f, 3.592f, 70, 12, 12, true);

    public static final List<EntityType<BipedConceptEntity>> TYPES = new ArrayList<>();
    public static final EntityType<BipedConceptEntity> ASTARTES = type(ASTARTES_VARIANT);
    public static final EntityType<BipedConceptEntity> THUNDER_WARRIOR = type(THUNDER_WARRIOR_VARIANT);

    private AstartesConcepts() {
    }

    private static EntityType<BipedConceptEntity> type(Variant v) {
        EntityType<BipedConceptEntity> t = Registry.register(BuiltInRegistries.ENTITY_TYPE, Warpbound.id(v.model()),
                EntityType.Builder.<BipedConceptEntity>of((type, level) -> new BipedConceptEntity(type, level, v), MobCategory.CREATURE)
                        .sized(v.width(), v.height()).clientTrackingRange(10).build(v.model()));
        TYPES.add(t);
        return t;
    }

    public static void register() {
        FabricDefaultAttributeRegistry.register(ASTARTES, BipedConceptEntity.attributes(ASTARTES_VARIANT));
        FabricDefaultAttributeRegistry.register(THUNDER_WARRIOR, BipedConceptEntity.attributes(THUNDER_WARRIOR_VARIANT));
    }

    public static Variant variantOf(EntityType<?> type) {
        return type == THUNDER_WARRIOR ? THUNDER_WARRIOR_VARIANT : ASTARTES_VARIANT;
    }
}
