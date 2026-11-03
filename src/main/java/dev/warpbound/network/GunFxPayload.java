package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Другой игрок выстрелил: вспышка у его оружия. kind — номер GunItem.Kind. */
public record GunFxPayload(int shooter, int kind) implements CustomPacketPayload {
    public static final Type<GunFxPayload> TYPE = new Type<>(Warpbound.id("gun_fx"));
    public static final StreamCodec<FriendlyByteBuf, GunFxPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeVarInt(p.shooter);
                buf.writeVarInt(p.kind);
            },
            buf -> new GunFxPayload(buf.readVarInt(), buf.readVarInt()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
