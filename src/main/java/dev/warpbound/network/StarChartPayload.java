package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.ArrayList;
import java.util.List;

/**
 * Сервер → клиент: карта Империума на мостике. Миры корабля (пункты назначения с местом на карте):
 * id, ключ имени, координаты [0..1], есть ли мир на сервере. current — где корабль, destination — куда проложен курс.
 * canJump — корабль на орбите и курс можно менять.
 */
public record StarChartPayload(List<String> ids, List<String> names, List<Float> xs, List<Float> ys, List<Boolean> available,
                               String current, String destination, boolean canJump) implements CustomPacketPayload {
    public static final Type<StarChartPayload> TYPE = new Type<>(Warpbound.id("star_chart"));
    public static final StreamCodec<FriendlyByteBuf, StarChartPayload> STREAM_CODEC =
            StreamCodec.ofMember(StarChartPayload::write, StarChartPayload::read);

    private void write(FriendlyByteBuf buf) {
        buf.writeVarInt(ids.size());
        for (int i = 0; i < ids.size(); i++) {
            buf.writeUtf(ids.get(i));
            buf.writeUtf(names.get(i));
            buf.writeFloat(xs.get(i));
            buf.writeFloat(ys.get(i));
            buf.writeBoolean(available.get(i));
        }
        buf.writeUtf(current);
        buf.writeUtf(destination);
        buf.writeBoolean(canJump);
    }

    private static StarChartPayload read(FriendlyByteBuf buf) {
        int n = Math.min(buf.readVarInt(), 64);
        List<String> ids = new ArrayList<>(), names = new ArrayList<>();
        List<Float> xs = new ArrayList<>(), ys = new ArrayList<>();
        List<Boolean> available = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            ids.add(buf.readUtf());
            names.add(buf.readUtf());
            xs.add(buf.readFloat());
            ys.add(buf.readFloat());
            available.add(buf.readBoolean());
        }
        return new StarChartPayload(ids, names, xs, ys, available, buf.readUtf(), buf.readUtf(), buf.readBoolean());
    }

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
