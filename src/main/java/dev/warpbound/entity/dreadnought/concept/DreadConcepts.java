package dev.warpbound.entity.dreadnought.concept;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Дредноут-саркофаг. Модель и движения пишет tools/models/blender/dread/castraferrum.py. Вызвать: /summon warpbound:dread_castraferrum, сесть — ПКМ. */
public final class DreadConcepts {
    /** model — имя модели; muzzle — дуло (вправо, вверх, вперёд) от центра у земли, в блоках. */
    public record Variant(String model, float width, float height, Vec3 muzzle, boolean hasFist, float meleeReach, int fireInterval) {
    }

    public static final Variant CASTRAFERRUM = new Variant("dread_castraferrum", 2.3f, 3.5f, new Vec3(1.37, 2.47, 1.45), true, 4.2f, 7);
    public static final List<EntityType<DreadConceptEntity>> TYPES = new ArrayList<>();
    public static final EntityType<DreadConceptEntity> DREAD_CASTRAFERRUM = type(CASTRAFERRUM);

    private DreadConcepts() {
    }

    private static EntityType<DreadConceptEntity> type(Variant v) {
        EntityType<DreadConceptEntity> t = Registry.register(BuiltInRegistries.ENTITY_TYPE, Warpbound.id(v.model()),
                EntityType.Builder.<DreadConceptEntity>of((type, level) -> new DreadConceptEntity(type, level, v), MobCategory.CREATURE)
                        .sized(v.width(), v.height()).clientTrackingRange(10).build(v.model()));
        TYPES.add(t);
        return t;
    }

    public static void register() {
        for (EntityType<DreadConceptEntity> t : TYPES) FabricDefaultAttributeRegistry.register(t, DreadConceptEntity.attributes());
    }

    /** Кнопки пилота. После WarpboundNetwork.registerPayloads: тип пакета должен быть уже известен. */
    public static void registerNetwork() {
        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(dev.warpbound.network.DreadControlPayload.TYPE, (payload, context) -> {
            var player = context.player();
            context.server().execute(() -> {
                if (!(player.getVehicle() instanceof DreadConceptEntity dread)) return;
                if (payload.action() == dev.warpbound.network.DreadControlPayload.FIRE) dread.pilotFire(player);
                else if (payload.action() == dev.warpbound.network.DreadControlPayload.CLAW) dread.pilotClaw(player);
                else if (payload.action() == dev.warpbound.network.DreadControlPayload.SHOVE) dread.pilotShove(player);
            });
        });
    }
}
