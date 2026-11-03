package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Снаряд стрелка попал: метка попадания на прицеле. */
public record GunHitPayload(boolean head, boolean killed) implements CustomPacketPayload {
    public static final Type<GunHitPayload> TYPE = new Type<>(Warpbound.id("gun_hit"));
    public static final StreamCodec<FriendlyByteBuf, GunHitPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeBoolean(p.head);
                buf.writeBoolean(p.killed);
            },
            buf -> new GunHitPayload(buf.readBoolean(), buf.readBoolean()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
