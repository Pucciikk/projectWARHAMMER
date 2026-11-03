package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Игрок нажал на спуск или перезарядку. aiming влияет на разброс. */
public record GunActionPayload(int action, boolean aiming) implements CustomPacketPayload {
    public static final int FIRE = 0, RELOAD = 1;
    public static final Type<GunActionPayload> TYPE = new Type<>(Warpbound.id("gun_action"));
    public static final StreamCodec<FriendlyByteBuf, GunActionPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeVarInt(p.action);
                buf.writeBoolean(p.aiming);
            },
            buf -> new GunActionPayload(buf.readVarInt(), buf.readBoolean()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
