package dev.warpbound.network;

import dev.warpbound.Warpbound;
import dev.warpbound.chaos.ChaosData;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: текущие данные Хаоса игрока (для эффектов и HUD). */
public record ChaosSyncPayload(ChaosData data) implements CustomPacketPayload {
    public static final Type<ChaosSyncPayload> TYPE = new Type<>(Warpbound.id("chaos_sync"));
    public static final StreamCodec<RegistryFriendlyByteBuf, ChaosSyncPayload> STREAM_CODEC =
            ByteBufCodecs.fromCodecWithRegistries(ChaosData.CODEC).map(ChaosSyncPayload::new, ChaosSyncPayload::data);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
