package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: кнопка на экране верфи. */
public record ShipyardActionPayload(BlockPos pos, int action) implements CustomPacketPayload {
    public static final int REFRESH = 0, DEPOSIT = 1, START_STAGE = 2, LAUNCH = 3;

    public static final Type<ShipyardActionPayload> TYPE = new Type<>(Warpbound.id("shipyard_action"));
    public static final StreamCodec<ByteBuf, ShipyardActionPayload> STREAM_CODEC = StreamCodec.composite(
            BlockPos.STREAM_CODEC, ShipyardActionPayload::pos,
            ByteBufCodecs.VAR_INT, ShipyardActionPayload::action,
            ShipyardActionPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
