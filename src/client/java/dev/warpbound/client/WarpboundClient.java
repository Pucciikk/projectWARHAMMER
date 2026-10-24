package dev.warpbound.client;

import dev.warpbound.client.autotest.Autotest;
import dev.warpbound.client.entity.DreadnoughtFx;
import dev.warpbound.client.entity.DreadnoughtMesh;
import dev.warpbound.client.entity.DreadnoughtRenderer;
import dev.warpbound.client.entity.TechPriestRenderer;
import dev.warpbound.client.industry.SalvageForgeScreen;
import dev.warpbound.client.multiblock.MultiblockHighlight;
import dev.warpbound.client.quest.ClientQuestState;
import dev.warpbound.client.ship.NavScreen;
import dev.warpbound.client.shipyard.ShipyardScreen;
import dev.warpbound.client.quest.QuestKeys;
import dev.warpbound.client.start.SlateScreen;
import dev.warpbound.core.WarpboundBlocks;
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

        EntityModelLayerRegistry.registerModelLayer(DreadnoughtRenderer.LAYER, DreadnoughtMesh::create);
        EntityRendererRegistry.register(WarpboundEntities.DREADNOUGHT, DreadnoughtRenderer::new);
        DreadnoughtFx.register();
        EntityRendererRegistry.register(WarpboundEntities.TECH_PRIEST, ctx -> new TechPriestRenderer(ctx, "tech_priest"));
        EntityRendererRegistry.register(WarpboundEntities.DARK_TECH_PRIEST, ctx -> new TechPriestRenderer(ctx, "dark_tech_priest"));
    }
}
