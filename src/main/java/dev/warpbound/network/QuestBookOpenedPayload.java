package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: игрок открыл окно квестов (первый квест главы 1). */
public record QuestBookOpenedPayload() implements CustomPacketPayload {
    public static final QuestBookOpenedPayload INSTANCE = new QuestBookOpenedPayload();
    public static final Type<QuestBookOpenedPayload> TYPE = new Type<>(Warpbound.id("quest_book_opened"));
    public static final StreamCodec<ByteBuf, QuestBookOpenedPayload> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
