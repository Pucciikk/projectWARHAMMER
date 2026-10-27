package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: выстрел лазгана. Луч рисует клиент — от ствола в руках стрелка до точки попадания. */
public record LasBeamPayload(int shooter, double x, double y, double z) implements CustomPacketPayload {
    public static final Type<LasBeamPayload> TYPE = new Type<>(Warpbound.id("las_beam"));
    public static final StreamCodec<FriendlyByteBuf, LasBeamPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeVarInt(p.shooter);
                buf.writeDouble(p.x);
                buf.writeDouble(p.y);
                buf.writeDouble(p.z);
            },
            buf -> new LasBeamPayload(buf.readVarInt(), buf.readDouble(), buf.readDouble(), buf.readDouble()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
