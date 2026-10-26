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
        PayloadTypeRegistry.playS2C().register(MultiblockErrorsPayload.TYPE, MultiblockErrorsPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ShipyardStatePayload.TYPE, ShipyardStatePayload.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(QuestBookOpenedPayload.TYPE, QuestBookOpenedPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(NavStatePayload.TYPE, NavStatePayload.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(ShipyardActionPayload.TYPE, ShipyardActionPayload.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(NavJumpPayload.TYPE, NavJumpPayload.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ShipConsolePayload.TYPE, ShipConsolePayload.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(ShipConsoleActionPayload.TYPE, ShipConsoleActionPayload.STREAM_CODEC);
    }
}
