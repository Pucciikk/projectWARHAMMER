package dev.warpbound.network;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

public final class WarpboundNetwork {
    private WarpboundNetwork() {
    }

    public static void registerPayloads() {
        PayloadTypeRegistry.playS2C().register(ChaosSyncPayload.TYPE, ChaosSyncPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ShipStatePayload.TYPE, ShipStatePayload.STREAM_CODEC);
    }
}
