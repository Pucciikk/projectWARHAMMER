package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.List;

/** Сервер → клиент: где мультиблоку не хватает блоков и где стоят чужие. Клиент подсвечивает их. */
public record MultiblockErrorsPayload(List<BlockPos> missing, List<BlockPos> wrong) implements CustomPacketPayload {
    /** Больше подсветки — только шум и лишний трафик. */
    private static final int LIMIT = 512;

    public static final Type<MultiblockErrorsPayload> TYPE = new Type<>(Warpbound.id("multiblock_errors"));
    public static final StreamCodec<ByteBuf, MultiblockErrorsPayload> STREAM_CODEC = StreamCodec.composite(
            BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list(LIMIT)), MultiblockErrorsPayload::missing,
            BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list(LIMIT)), MultiblockErrorsPayload::wrong,
            MultiblockErrorsPayload::new);

    public MultiblockErrorsPayload {
        missing = missing.subList(0, Math.min(LIMIT, missing.size()));
        wrong = wrong.subList(0, Math.min(LIMIT, wrong.size()));
    }

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
