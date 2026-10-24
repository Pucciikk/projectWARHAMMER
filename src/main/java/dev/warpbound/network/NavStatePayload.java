package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.List;

/** Сервер → клиент: пункты назначения для навигационного стола (id и ключ перевода имени) и где корабль сейчас. */
public record NavStatePayload(List<String> ids, List<String> names, String current) implements CustomPacketPayload {
    public static final Type<NavStatePayload> TYPE = new Type<>(Warpbound.id("nav_state"));
    public static final StreamCodec<ByteBuf, NavStatePayload> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list(64)), NavStatePayload::ids,
            ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list(64)), NavStatePayload::names,
            ByteBufCodecs.STRING_UTF8, NavStatePayload::current,
            NavStatePayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
