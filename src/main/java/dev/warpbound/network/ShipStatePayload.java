package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Сервер → клиент: состояние корабля, на котором находится игрок.
 * Клиент по нему рисует небо: звёзды на орбите, варп в транзите.
 *
 * @param aboard   игрок на борту какого-либо корабля
 * @param state    порядковый номер {@link dev.warpbound.ship.ShipState}
 * @param progress прогресс текущего состояния 0..1
 * @param field    прочность Поля Геллера 0..1
 * @param storm    сила варп-шторма 0..1
 */
public record ShipStatePayload(boolean aboard, int state, float progress, float field, float storm)
        implements CustomPacketPayload {
    public static final Type<ShipStatePayload> TYPE = new Type<>(Warpbound.id("ship_state"));
    public static final StreamCodec<RegistryFriendlyByteBuf, ShipStatePayload> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.BOOL, ShipStatePayload::aboard,
            ByteBufCodecs.VAR_INT, ShipStatePayload::state,
            ByteBufCodecs.FLOAT, ShipStatePayload::progress,
            ByteBufCodecs.FLOAT, ShipStatePayload::field,
            ByteBufCodecs.FLOAT, ShipStatePayload::storm,
            ShipStatePayload::new);

    public static final ShipStatePayload NOT_ABOARD = new ShipStatePayload(false, 0, 0, 1, 0);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
