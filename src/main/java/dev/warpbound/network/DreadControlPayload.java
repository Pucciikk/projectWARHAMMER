package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Пилот дредноута нажал на кнопку оружия. Движение идёт обычным управлением транспортом. */
public record DreadControlPayload(int action) implements CustomPacketPayload {
    public static final int FIRE = 0, CLAW = 1, SHOVE = 2;
    public static final Type<DreadControlPayload> TYPE = new Type<>(Warpbound.id("dread_control"));
    public static final StreamCodec<FriendlyByteBuf, DreadControlPayload> STREAM_CODEC = StreamCodec.of(
            (buf, p) -> buf.writeVarInt(p.action), buf -> new DreadControlPayload(buf.readVarInt()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
