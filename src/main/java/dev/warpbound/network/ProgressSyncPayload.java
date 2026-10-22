package dev.warpbound.network;

import dev.warpbound.Warpbound;
import dev.warpbound.player.PlayerProgress;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: выполненные квесты и флаги игрока. */
public record ProgressSyncPayload(PlayerProgress progress) implements CustomPacketPayload {
    public static final Type<ProgressSyncPayload> TYPE = new Type<>(Warpbound.id("progress_sync"));
    public static final StreamCodec<RegistryFriendlyByteBuf, ProgressSyncPayload> STREAM_CODEC =
            ByteBufCodecs.fromCodecWithRegistries(PlayerProgress.CODEC).map(ProgressSyncPayload::new, ProgressSyncPayload::progress);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
