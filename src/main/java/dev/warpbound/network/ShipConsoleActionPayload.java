package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: команда с пульта мостика. value — режим реактора или доля мощности; target — id мира для курса. */
public record ShipConsoleActionPayload(int action, float value, String target) implements CustomPacketPayload {
    public static final int REFRESH = 0, REACTOR_MODE = 1, GELLER_POWER = 2, FIELD_BOOST = 3, COOLANT_FLUSH = 4, PLOT_COURSE = 5,
            ENGINES = 6, GELLER = 7, SHUTTERS = 8, OPEN_RIFT = 9, LAUNCH = 10;

    public static final Type<ShipConsoleActionPayload> TYPE = new Type<>(Warpbound.id("ship_console_action"));
    public static final StreamCodec<FriendlyByteBuf, ShipConsoleActionPayload> STREAM_CODEC = StreamCodec.ofMember(
            (p, buf) -> {
                buf.writeVarInt(p.action);
                buf.writeFloat(p.value);
                buf.writeUtf(p.target);
            },
            buf -> new ShipConsoleActionPayload(buf.readVarInt(), buf.readFloat(), buf.readUtf()));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
