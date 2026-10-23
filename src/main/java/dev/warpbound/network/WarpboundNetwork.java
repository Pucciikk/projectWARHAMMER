package dev.warpbound.network;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

public final class WarpboundNetwork {
    private WarpboundNetwork() {
    }

    public static void registerPayloads() {
        PayloadTypeRegistry.playS2C().register(ChaosSyncPayload.TYPE, ChaosSyncPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ShipStatePayload.TYPE, ShipStatePayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(QuestDataPayload.TYPE, QuestDataPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ProgressSyncPayload.TYPE, ProgressSyncPayload.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(QuestBookOpenedPayload.TYPE, QuestBookOpenedPayload.STREAM_CODEC);
    }
}
