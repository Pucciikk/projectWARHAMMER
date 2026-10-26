package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.List;

/**
 * Сервер → клиент: всё, что показывает командный пульт мостика.
 * Пульт открыт — клиент раз в секунду просит обновление ({@link ShipConsoleActionPayload#REFRESH}).
 *
 * @param open      открыть экран (первый ответ) или только обновить уже открытый
 * @param ids       пункты назначения (id) и ключи их имён — для вкладки «Навигация»
 * @param location  id мира, у которого стоит корабль; destination — куда идёт ("" — никуда)
 * @param docked    корабль ещё на стапеле: экран показывает постройку и кнопку выхода в космос
 * @param flight    флаги подготовки: 1 — двигатели, 2 — Поле Геллера, 4 — ставни закрыты
 * @param missing   ключ перевода: чего не хватает до открытия разлома ("" — готово)
 */
public record ShipConsolePayload(boolean open, String shipName, int state, float progress, float field, float storm,
                                 int reactorMode, float heat, float power, float gellerPower, float radiation,
                                 int boostCooldown, int flushCooldown, int crew,
                                 String location, String destination, List<String> ids, List<String> names,
                                 boolean docked, int stage, int stages, boolean launching, int flight, String missing)
        implements CustomPacketPayload {
    public static final Type<ShipConsolePayload> TYPE = new Type<>(Warpbound.id("ship_console"));
    public static final StreamCodec<FriendlyByteBuf, ShipConsolePayload> STREAM_CODEC =
            StreamCodec.ofMember(ShipConsolePayload::write, ShipConsolePayload::read);

    private void write(FriendlyByteBuf buf) {
        buf.writeBoolean(open);
        buf.writeUtf(shipName);
        buf.writeVarInt(state);
        buf.writeFloat(progress);
        buf.writeFloat(field);
        buf.writeFloat(storm);
        buf.writeVarInt(reactorMode);
        buf.writeFloat(heat);
        buf.writeFloat(power);
        buf.writeFloat(gellerPower);
        buf.writeFloat(radiation);
        buf.writeVarInt(boostCooldown);
        buf.writeVarInt(flushCooldown);
        buf.writeVarInt(crew);
        buf.writeUtf(location);
        buf.writeUtf(destination);
        buf.writeCollection(ids, FriendlyByteBuf::writeUtf);
        buf.writeCollection(names, FriendlyByteBuf::writeUtf);
        buf.writeBoolean(docked);
        buf.writeVarInt(stage);
        buf.writeVarInt(stages);
        buf.writeBoolean(launching);
        buf.writeVarInt(flight);
        buf.writeUtf(missing);
    }

    private static ShipConsolePayload read(FriendlyByteBuf buf) {
        return new ShipConsolePayload(buf.readBoolean(), buf.readUtf(), buf.readVarInt(), buf.readFloat(), buf.readFloat(),
                buf.readFloat(), buf.readVarInt(), buf.readFloat(), buf.readFloat(), buf.readFloat(), buf.readFloat(),
                buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readUtf(), buf.readUtf(),
                buf.readList(FriendlyByteBuf::readUtf), buf.readList(FriendlyByteBuf::readUtf),
                buf.readBoolean(), buf.readVarInt(), buf.readVarInt(), buf.readBoolean(), buf.readVarInt(), buf.readUtf());
    }

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
