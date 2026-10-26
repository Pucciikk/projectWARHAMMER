package dev.warpbound.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.boarding.BoardingPodEntity;
import dev.warpbound.entity.cult.CultistEntity;
import dev.warpbound.entity.cult.PossessedPriestEntity;
import dev.warpbound.entity.daemon.BloodletterEntity;
import dev.warpbound.entity.daemon.HorrorEntity;
import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import dev.warpbound.entity.projectile.WarpBoltEntity;
import dev.warpbound.entity.ritual.WarpRiftEntity;
import dev.warpbound.entity.transport.DropCapsuleEntity;
import dev.warpbound.entity.transport.ShuttleEntity;
import dev.warpbound.entity.servitor.ServitorEntity;
import dev.warpbound.faction.Faction;
import dev.warpbound.operator.TechPriestEntity;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;

public final class WarpboundEntities {
    // Габарит общей туши: о неё спотыкаются игроки и блоки; попадания ловят части
    public static final EntityType<DreadnoughtEntity> DREADNOUGHT = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, Warpbound.id("dreadnought"),
            EntityType.Builder.of(DreadnoughtEntity::new, MobCategory.MISC)
                    .sized(4.2f, 4.9f)     // 3.2 x 3.75 модели, умноженные на DreadnoughtEntity.SCALE
                    .eyeHeight(4.3f)
                    .clientTrackingRange(10)
                    .build("dreadnought"));

    public static final Item DREADNOUGHT_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("dreadnought_spawn_egg"),
            new SpawnEggItem(DREADNOUGHT, 0x1f3f8f, 0xc9a227, new Item.Properties()));

    public static final EntityType<TechPriestEntity> TECH_PRIEST = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, Warpbound.id("tech_priest"),
            EntityType.Builder.<TechPriestEntity>of((type, level) -> new TechPriestEntity(type, level, Faction.IMPERIUM), MobCategory.MISC)
                    .sized(0.8f, 2.3f)        // капюшон с лампой — 2.3 блока
                    .clientTrackingRange(10)
                    .build("tech_priest"));

    public static final EntityType<TechPriestEntity> DARK_TECH_PRIEST = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, Warpbound.id("dark_tech_priest"),
            EntityType.Builder.<TechPriestEntity>of((type, level) -> new TechPriestEntity(type, level, Faction.CHAOS), MobCategory.MISC)
                    .sized(1.8f, 3.0f)        // магос Тёмных Механикус — 2×3 блока, как железный голем
                    .clientTrackingRange(10)
                    .build("dark_tech_priest"));

    public static final Item TECH_PRIEST_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("tech_priest_spawn_egg"),
            new SpawnEggItem(TECH_PRIEST, 0x8b1a1a, 0xb8b0a0, new Item.Properties()));

    public static final Item DARK_TECH_PRIEST_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("dark_tech_priest_spawn_egg"),
            new SpawnEggItem(DARK_TECH_PRIEST, 0x1a1420, 0x6a2a8a, new Item.Properties()));

    // ---- Сезон 1: заглушки моделей М3–М9 (GeckoLib), рост — по каталогу docs/content/catalog.md

    public static final EntityType<ServitorEntity> SERVITOR = register("servitor",
            EntityType.Builder.of(ServitorEntity::new, MobCategory.MISC).sized(0.7f, 1.9f).clientTrackingRange(10));

    public static final EntityType<BloodletterEntity> BLOODLETTER = register("bloodletter",
            EntityType.Builder.of(BloodletterEntity::new, MobCategory.MONSTER).sized(0.8f, 2.4f).clientTrackingRange(10));

    public static final EntityType<HorrorEntity> PINK_HORROR = register("pink_horror",
            EntityType.Builder.of(HorrorEntity::new, MobCategory.MONSTER).sized(0.9f, 1.6f).clientTrackingRange(10));

    public static final EntityType<HorrorEntity> BLUE_HORROR = register("blue_horror",
            EntityType.Builder.of(HorrorEntity::new, MobCategory.MONSTER).sized(0.55f, 1.0f).clientTrackingRange(10));

    public static final EntityType<CultistEntity> CULTIST = register("cultist",
            EntityType.Builder.of(CultistEntity::new, MobCategory.MONSTER).sized(0.6f, 1.8f).clientTrackingRange(10));

    public static final EntityType<PossessedPriestEntity> POSSESSED_PRIEST = register("possessed_priest",
            EntityType.Builder.of(PossessedPriestEntity::new, MobCategory.MONSTER).sized(0.7f, 1.9f)
                    .fireImmune().clientTrackingRange(12));

    public static final EntityType<BoardingPodEntity> BOARDING_POD = register("boarding_pod",
            EntityType.Builder.of(BoardingPodEntity::new, MobCategory.MISC).sized(1.9f, 3.6f).fireImmune().clientTrackingRange(12));

    public static final EntityType<WarpBoltEntity> WARP_BOLT = register("warp_bolt",
            EntityType.Builder.<WarpBoltEntity>of(WarpBoltEntity::new, MobCategory.MISC).sized(0.3f, 0.3f)
                    .clientTrackingRange(6).updateInterval(2));

    // челнок считает траекторию сам на клиенте — пакеты позиции почти не нужны, а видно его издалека
    public static final EntityType<ShuttleEntity> SHUTTLE = register("shuttle",
            EntityType.Builder.of(ShuttleEntity::new, MobCategory.MISC).sized(8f, 7f).fireImmune()
                    .clientTrackingRange(16).updateInterval(20));

    public static final EntityType<DropCapsuleEntity> DROP_CAPSULE = register("drop_capsule",
            EntityType.Builder.of(DropCapsuleEntity::new, MobCategory.MISC).sized(1.8f, 2.9f).fireImmune()
                    .clientTrackingRange(12).updateInterval(20));

    public static final EntityType<WarpRiftEntity> WARP_RIFT = register("warp_rift",
            EntityType.Builder.of(WarpRiftEntity::new, MobCategory.MISC).sized(6f, 4f).fireImmune()
                    .clientTrackingRange(10).updateInterval(20));

    public static final Item SERVITOR_SPAWN_EGG = egg("servitor", SERVITOR, 0xb8aca4, 0x55585e);
    public static final Item BLOODLETTER_SPAWN_EGG = egg("bloodletter", BLOODLETTER, 0xa81e1a, 0x2a1414);
    public static final Item PINK_HORROR_SPAWN_EGG = egg("pink_horror", PINK_HORROR, 0xe86ebe, 0x5a1e6e);
    public static final Item BLUE_HORROR_SPAWN_EGG = egg("blue_horror", BLUE_HORROR, 0x4678dc, 0x1e285a);
    public static final Item CULTIST_SPAWN_EGG = egg("cultist", CULTIST, 0x5c4a38, 0x8a2a24);
    public static final Item POSSESSED_PRIEST_SPAWN_EGG = egg("possessed_priest", POSSESSED_PRIEST, 0x461216, 0xff3cc8);

    private static <T extends Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
        return Registry.register(BuiltInRegistries.ENTITY_TYPE, Warpbound.id(name), builder.build(name));
    }

    private static Item egg(String name, EntityType<? extends Mob> type, int base, int spots) {
        return Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name + "_spawn_egg"),
                new SpawnEggItem(type, base, spots, new Item.Properties()));
    }

    private WarpboundEntities() {
    }

    public static void register() {
        FabricDefaultAttributeRegistry.register(DREADNOUGHT, DreadnoughtEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(TECH_PRIEST, TechPriestEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(DARK_TECH_PRIEST, TechPriestEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SERVITOR, ServitorEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(BLOODLETTER, BloodletterEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(PINK_HORROR, HorrorEntity.createPinkAttributes());
        FabricDefaultAttributeRegistry.register(BLUE_HORROR, HorrorEntity.createBlueAttributes());
        FabricDefaultAttributeRegistry.register(CULTIST, CultistEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(POSSESSED_PRIEST, PossessedPriestEntity.createAttributes());
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.SPAWN_EGGS)
                .register(entries -> entries.accept(DREADNOUGHT_SPAWN_EGG));
    }
}
