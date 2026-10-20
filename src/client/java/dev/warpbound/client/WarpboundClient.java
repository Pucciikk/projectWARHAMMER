package dev.warpbound.client;

import dev.warpbound.network.ChaosSyncPayload;
import dev.warpbound.network.ShipStatePayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

public class WarpboundClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        // Обработчики пакетов в 1.20.5+ вызываются в потоке клиента, синхронизация не нужна
        ClientPlayNetworking.registerGlobalReceiver(ChaosSyncPayload.TYPE,
                (payload, context) -> ClientChaosState.set(payload.data()));
        ClientPlayNetworking.registerGlobalReceiver(ShipStatePayload.TYPE,
                (payload, context) -> ClientShipState.update(payload));
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            ClientChaosState.reset();
            ClientShipState.reset();
        });

        WarpSkyRenderer.register();
        WarpHud.register();
    }
}
