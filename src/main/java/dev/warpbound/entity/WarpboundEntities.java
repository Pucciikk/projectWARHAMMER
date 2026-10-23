package dev.warpbound.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import dev.warpbound.faction.Faction;
import dev.warpbound.operator.TechPriestEntity;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EntityType;
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
                    .sized(0.6f, 1.95f)
                    .clientTrackingRange(10)
                    .build("tech_priest"));

    public static final EntityType<TechPriestEntity> DARK_TECH_PRIEST = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, Warpbound.id("dark_tech_priest"),
            EntityType.Builder.<TechPriestEntity>of((type, level) -> new TechPriestEntity(type, level, Faction.CHAOS), MobCategory.MISC)
                    .sized(0.6f, 1.95f)
                    .clientTrackingRange(10)
                    .build("dark_tech_priest"));

    public static final Item TECH_PRIEST_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("tech_priest_spawn_egg"),
            new SpawnEggItem(TECH_PRIEST, 0x8b1a1a, 0xb8b0a0, new Item.Properties()));

    public static final Item DARK_TECH_PRIEST_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("dark_tech_priest_spawn_egg"),
            new SpawnEggItem(DARK_TECH_PRIEST, 0x1a1420, 0x6a2a8a, new Item.Properties()));

    private WarpboundEntities() {
    }

    public static void register() {
        FabricDefaultAttributeRegistry.register(DREADNOUGHT, DreadnoughtEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(TECH_PRIEST, TechPriestEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(DARK_TECH_PRIEST, TechPriestEntity.createAttributes());
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.SPAWN_EGGS)
                .register(entries -> entries.accept(DREADNOUGHT_SPAWN_EGG));
    }
}
