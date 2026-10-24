package dev.warpbound.network;

import dev.warpbound.Warpbound;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.List;

/**
 * Сервер → клиент: состояние верфи для экрана постройки.
 * Поставки текущего этапа идут тремя параллельными списками: предмет, сколько нужно, сколько сдано.
 */
public record ShipyardStatePayload(BlockPos pos, String className, List<String> stages, int stage,
                                   List<String> items, List<Integer> counts, List<Integer> deposited,
                                   int buildLeft, int buildTotal, boolean launching) implements CustomPacketPayload {
    public static final Type<ShipyardStatePayload> TYPE = new Type<>(Warpbound.id("shipyard_state"));
    public static final StreamCodec<FriendlyByteBuf, ShipyardStatePayload> STREAM_CODEC =
            StreamCodec.ofMember(ShipyardStatePayload::write, ShipyardStatePayload::read);

    private static final StreamCodec<ByteBuf, List<String>> STRINGS = ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list(64));
    private static final StreamCodec<ByteBuf, List<Integer>> INTS = ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list(64));

    private void write(FriendlyByteBuf buf) {
        buf.writeBlockPos(pos);
        buf.writeUtf(className);
        STRINGS.encode(buf, stages);
        buf.writeVarInt(stage);
        STRINGS.encode(buf, items);
        INTS.encode(buf, counts);
        INTS.encode(buf, deposited);
        buf.writeVarInt(buildLeft);
        buf.writeVarInt(buildTotal);
        buf.writeBoolean(launching);
    }

    private static ShipyardStatePayload read(FriendlyByteBuf buf) {
        return new ShipyardStatePayload(buf.readBlockPos(), buf.readUtf(), STRINGS.decode(buf), buf.readVarInt(),
                STRINGS.decode(buf), INTS.decode(buf), INTS.decode(buf), buf.readVarInt(), buf.readVarInt(), buf.readBoolean());
    }

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
