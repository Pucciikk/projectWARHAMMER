package dev.warpbound.client;

import dev.warpbound.client.autotest.Autotest;
import dev.warpbound.client.entity.DreadnoughtFx;
import dev.warpbound.client.entity.DreadnoughtMesh;
import dev.warpbound.client.entity.DreadnoughtRenderer;
import dev.warpbound.client.entity.geo.WarpGeoRenderer;
import dev.warpbound.client.entity.ShuttleSounds;
import dev.warpbound.client.particle.WarpFlameParticle;
import dev.warpbound.client.particle.WarpRuneParticle;
import dev.warpbound.core.WarpboundParticles;
import net.fabricmc.fabric.api.client.particle.v1.ParticleFactoryRegistry;
import dev.warpbound.entity.cult.CultistEntity;
import dev.warpbound.entity.transport.ShuttleEntity;
import dev.warpbound.entity.cult.PossessedPriestEntity;
import net.minecraft.client.renderer.entity.NoopRenderer;
import java.util.List;
import java.util.Set;
import dev.warpbound.client.industry.SalvageForgeScreen;
import dev.warpbound.client.multiblock.FixtureRenderer;
import dev.warpbound.client.multiblock.MachineRenderer;
import dev.warpbound.client.multiblock.MultiblockHighlight;
import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import dev.warpbound.client.quest.ClientQuestState;
import dev.warpbound.client.ship.ConsoleScreen;
import dev.warpbound.client.ship.ShipEngineSound;
import dev.warpbound.client.ship.NavScreen;
import dev.warpbound.network.ShipConsolePayload;
import dev.warpbound.client.shipyard.ShipyardScreen;
import dev.warpbound.client.quest.QuestKeys;
import dev.warpbound.client.start.SlateScreen;
import dev.warpbound.core.WarpboundBlocks;
import dev.warpbound.core.WarpboundBuildingBlocks;
import dev.warpbound.core.WarpboundMenus;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.network.ChaosSyncPayload;
import dev.warpbound.network.MultiblockErrorsPayload;
import dev.warpbound.network.NavStatePayload;
import dev.warpbound.network.ShipyardStatePayload;
import dev.warpbound.network.ProgressSyncPayload;
import dev.warpbound.network.QuestDataPayload;
import dev.warpbound.network.ShipStatePayload;
import dev.warpbound.start.DataSlateItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.renderer.RenderType;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.EntityModelLayerRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;

public class WarpboundClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        // Обработчики пакетов в 1.20.5+ вызываются в потоке клиента, синхронизация не нужна
        ClientPlayNetworking.registerGlobalReceiver(ChaosSyncPayload.TYPE,
                (payload, context) -> ClientChaosState.set(payload.data()));
        ClientPlayNetworking.registerGlobalReceiver(ShipStatePayload.TYPE,
                (payload, context) -> ClientShipState.update(payload));
        ClientPlayNetworking.registerGlobalReceiver(QuestDataPayload.TYPE,
                (payload, context) -> ClientQuestState.setData(payload.chapters(), payload.quests()));
        ClientPlayNetworking.registerGlobalReceiver(ProgressSyncPayload.TYPE,
                (payload, context) -> ClientQuestState.setProgress(payload.progress()));
        ClientPlayNetworking.registerGlobalReceiver(MultiblockErrorsPayload.TYPE,
                (payload, context) -> MultiblockHighlight.show(payload));
        ClientPlayNetworking.registerGlobalReceiver(ShipyardStatePayload.TYPE,
                (payload, context) -> ShipyardScreen.receive(payload));
        ClientPlayNetworking.registerGlobalReceiver(NavStatePayload.TYPE,
                (payload, context) -> Minecraft.getInstance().setScreen(new NavScreen(payload)));
        ClientPlayNetworking.registerGlobalReceiver(ShipConsolePayload.TYPE,
                (payload, context) -> ConsoleScreen.receive(payload));
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            ClientChaosState.reset();
            ClientShipState.reset();
            ClientQuestState.reset();
        });

        Autotest.register();
        QuestKeys.register();
        DataSlateItem.openScreen = memory -> Minecraft.getInstance().setScreen(new SlateScreen(memory));

        WarpSkyRenderer.register();
        WarpHud.register();
        MultiblockHighlight.register();
        MenuScreens.register(WarpboundMenus.SALVAGE_FORGE, SalvageForgeScreen::new);
        BlockRenderLayerMap.INSTANCE.putBlock(WarpboundBlocks.MANUAL_PRESS, RenderType.cutout());
        WarpboundBuildingBlocks.CUTOUT.forEach(b -> BlockRenderLayerMap.INSTANCE.putBlock(b, RenderType.cutout()));
        WarpboundBuildingBlocks.TRANSLUCENT.forEach(b -> BlockRenderLayerMap.INSTANCE.putBlock(b, RenderType.translucent()));

        EntityModelLayerRegistry.registerModelLayer(DreadnoughtRenderer.LAYER, DreadnoughtMesh::create);
        EntityRendererRegistry.register(WarpboundEntities.DREADNOUGHT, DreadnoughtRenderer::new);
        DreadnoughtFx.register();
        registerGeoRenderers();
        // собранные машины рисуют цельную модель
        BlockEntityRenderers.register(WarpboundBlockEntities.SALVAGE_FORGE, ctx -> new MachineRenderer<>("salvage_forge"));
        BlockEntityRenderers.register(WarpboundBlockEntities.MANUAL_PRESS, ctx -> new MachineRenderer<>("manual_press"));
        BlockEntityRenderers.register(WarpboundBlockEntities.MECHANICUS_FORGE, ctx -> new MachineRenderer<>("mechanicus_forge"));
        BlockEntityRenderers.register(WarpboundBlockEntities.SHIP_FIXTURE, ctx -> new FixtureRenderer());
    }

    /** Модели GeckoLib (М1–М9). Пока заглушки из tools/models/gen_entities.py, потом — модели автора. */
    private static void registerGeoRenderers() {
        EntityRendererRegistry.register(WarpboundEntities.TECH_PRIEST, ctx -> new WarpGeoRenderer<>(ctx, "tech_priest"));
        EntityRendererRegistry.register(WarpboundEntities.DARK_TECH_PRIEST,
                ctx -> new WarpGeoRenderer<>(ctx, "dark_tech_priest").shadow(1.0f));
        EntityRendererRegistry.register(WarpboundEntities.SERVITOR, ctx -> new WarpGeoRenderer<>(ctx, "servitor"));
        EntityRendererRegistry.register(WarpboundEntities.BLOODLETTER, ctx -> new WarpGeoRenderer<>(ctx, "bloodletter").shadow(0.6f));
        EntityRendererRegistry.register(WarpboundEntities.PINK_HORROR, ctx -> new WarpGeoRenderer<>(ctx, "pink_horror").shadow(0.6f));
        // синий ужас — та же модель, мельче (1.0 блока против 1.6)
        EntityRendererRegistry.register(WarpboundEntities.BLUE_HORROR, ctx -> new WarpGeoRenderer<>(ctx, "pink_horror")
                .texture(e -> "blue_horror").scale((e, pt) -> 0.62).shadow(0.35f));
        EntityRendererRegistry.register(WarpboundEntities.CULTIST, ctx -> new WarpGeoRenderer<CultistEntity>(ctx, "cultist")
                .texture(e -> switch (e.variant()) {
                    case KNIFE -> "cultist";
                    case AUTOGUN -> "cultist_1";
                    case STUBBER -> "cultist_2";
                })
                .bones(List.of("knife", "autogun", "stubber"), e -> switch (e.variant()) {
                    case KNIFE -> Set.of("autogun", "stubber");
                    case AUTOGUN -> Set.of("knife", "stubber");
                    case STUBBER -> Set.of("knife", "autogun");
                }));
        List<String> daemonBones = List.of("daemon_horns", "daemon_jaw", "daemon_spine", "daemon_claw_right", "daemon_claw_left");
        EntityRendererRegistry.register(WarpboundEntities.POSSESSED_PRIEST, ctx -> new WarpGeoRenderer<PossessedPriestEntity>(ctx, "possessed_priest")
                .texture(e -> e.isDaemon() ? "possessed_priest_daemon" : "possessed_priest")
                .bones(daemonBones, e -> e.isDaemon() ? Set.of() : Set.copyOf(daemonBones))
                .scale((e, pt) -> {
                    if (!e.isDaemon()) return 1.0;
                    float left = Math.max(0, e.transformTicks() - pt) / PossessedPriestEntity.TRANSFORM_TICKS;
                    return 1 + (PossessedPriestEntity.DAEMON_SCALE - 1) * (1 - left);
                })
                .shadow(0.7f));
        EntityRendererRegistry.register(WarpboundEntities.BOARDING_POD, ctx -> new WarpGeoRenderer<>(ctx, "boarding_pod", null).shadow(1.4f));
        EntityRendererRegistry.register(WarpboundEntities.WARP_BOLT, NoopRenderer::new);
        // челнок без головы; капсула под брюхом видна, пока он её не сбросил
        EntityRendererRegistry.register(WarpboundEntities.SHUTTLE, ctx -> new WarpGeoRenderer<ShuttleEntity>(ctx, "shuttle", null)
                .bones(List.of("capsule"), e -> e.hasCargo() ? Set.of() : Set.of("capsule")).vehicle().shadow(3.5f));
        EntityRendererRegistry.register(WarpboundEntities.DROP_CAPSULE, ctx -> new WarpGeoRenderer<>(ctx, "drop_capsule", null).vehicle().shadow(0.9f));
        EntityRendererRegistry.register(WarpboundEntities.WARP_RIFT, ctx -> new WarpGeoRenderer<>(ctx, "warp_rift", null).vehicle().shadow(0f));
        ShuttleSounds.register();
        ShipEngineSound.register();
        ParticleFactoryRegistry.getInstance().register(WarpboundParticles.WARP_FLAME, WarpFlameParticle.Provider::new);
        ParticleFactoryRegistry.getInstance().register(WarpboundParticles.WARP_RUNE, WarpRuneParticle.Provider::new);
    }
}
