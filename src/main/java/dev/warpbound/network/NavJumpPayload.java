package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: проложить курс к пункту назначения. */
public record NavJumpPayload(String destination) implements CustomPacketPayload {
    public static final Type<NavJumpPayload> TYPE = new Type<>(Warpbound.id("nav_jump"));
    public static final StreamCodec<ByteBuf, NavJumpPayload> STREAM_CODEC =
            ByteBufCodecs.STRING_UTF8.map(NavJumpPayload::new, NavJumpPayload::destination);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
