package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Игрок нажал на спуск или перезарядку. x, y, z — куда он выстрелил, уже с разбросом: снаряд на его экране и снаряд на сервере летят одинаково. */
public record GunActionPayload(int action, boolean aiming, float x, float y, float z) implements CustomPacketPayload {
    public static final int FIRE = 0, RELOAD = 1;
    public static final Type<GunActionPayload> TYPE = new Type<>(Warpbound.id("gun_action"));
    public static final StreamCodec<FriendlyByteBuf, GunActionPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeVarInt(p.action);
                buf.writeBoolean(p.aiming);
                buf.writeFloat(p.x);
                buf.writeFloat(p.y);
                buf.writeFloat(p.z);
            },
            buf -> new GunActionPayload(buf.readVarInt(), buf.readBoolean(), buf.readFloat(), buf.readFloat(), buf.readFloat()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
