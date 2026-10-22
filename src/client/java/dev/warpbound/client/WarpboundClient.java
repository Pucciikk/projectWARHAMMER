package dev.warpbound.client;

import dev.warpbound.client.entity.DreadnoughtFx;
import dev.warpbound.client.entity.DreadnoughtMesh;
import dev.warpbound.client.entity.DreadnoughtRenderer;
import dev.warpbound.client.entity.TechPriestRenderer;
import dev.warpbound.client.quest.ClientQuestState;
import dev.warpbound.client.quest.QuestKeys;
import dev.warpbound.client.start.SlateScreen;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.network.ChaosSyncPayload;
import dev.warpbound.network.ProgressSyncPayload;
import dev.warpbound.network.QuestDataPayload;
import dev.warpbound.network.ShipStatePayload;
import dev.warpbound.start.DataSlateItem;
import net.minecraft.client.Minecraft;
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
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            ClientChaosState.reset();
            ClientShipState.reset();
            ClientQuestState.reset();
        });

        QuestKeys.register();
        DataSlateItem.openScreen = memory -> Minecraft.getInstance().setScreen(new SlateScreen(memory));

        WarpSkyRenderer.register();
        WarpHud.register();

        EntityModelLayerRegistry.registerModelLayer(DreadnoughtRenderer.LAYER, DreadnoughtMesh::create);
        EntityRendererRegistry.register(WarpboundEntities.DREADNOUGHT, DreadnoughtRenderer::new);
        DreadnoughtFx.register();
        EntityRendererRegistry.register(WarpboundEntities.TECH_PRIEST, ctx -> new TechPriestRenderer(ctx, "tech_priest"));
        EntityRendererRegistry.register(WarpboundEntities.DARK_TECH_PRIEST, ctx -> new TechPriestRenderer(ctx, "dark_tech_priest"));
    }
}
