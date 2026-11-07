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
    /** Аллюр: клип и скорость тела, блоков в секунду, при которой ступни не скользят (её печатает скрипт модели). */
    public record Gait(String clip, float speed) {
    }

    /**
     * gaits — аллюры по возрастанию скорости. moveSpeed — атрибут скорости: у мобов путь за тик растёт как квадрат скорости
     * (44 · s² блоков в секунду), поэтому погоня (×1,9) и прогулка (×1,13) попадают в скорости клипов.
     * height — рост в игре, modelHeight — рост модели в её единицах (модель рисуется с увеличением height / modelHeight).
     * overlay: позу собирает клиент по файлу движений assets/warpbound/motion/<model>.json (смешивание аллюров, удар поверх бега);
     * без него — старые клипы GeckoLib attack.melee и misc.hurt, которые перезаписывают кости целиком (пока у Громового воина).
     */
    public record Variant(String model, float width, float height, float modelHeight, List<Gait> gaits, Gait sneak, double moveSpeed, double maxHealth, double armor, double damage,
                          boolean glow, boolean overlay) {
    }

    /** Скорости игрока: ходьба 4,317, бег 5,612, присед 1,295 (решение автора 7.11.2026), медленный шаг 2,0 — для NPC. */
    public static final Variant ASTARTES_VARIANT = new Variant("astartes", 0.8f, 2.4f, 2.2f,
            List.of(new Gait("move.stroll", 2.0f), new Gait("move.walk", 4.317f), new Gait("move.run", 5.612f)), new Gait("move.sneak", 1.295f),
            0.188, 80, 16, 10, true, true);
    /** Громовой воин (7.11.2026): то же тело и движения, что у Астартес, рост 2,3 блока. */
    public static final Variant THUNDER_WARRIOR_VARIANT = new Variant("thunder_warrior", 0.77f, 2.3f, 2.2f,
            List.of(new Gait("move.stroll", 2.0f), new Gait("move.walk", 4.317f), new Gait("move.run", 5.612f)), new Gait("move.sneak", 1.295f),
            0.188, 70, 12, 12, true, true);

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
