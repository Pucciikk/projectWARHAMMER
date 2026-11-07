package dev.warpbound.network;

import dev.warpbound.Warpbound;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: форма тела игрока с номером сущности entityId (свой игрок и все, кто его видит). */
public record GeneFormPayload(int entityId, String form) implements CustomPacketPayload {
    public static final Type<GeneFormPayload> TYPE = new Type<>(Warpbound.id("gene_form"));
    public static final StreamCodec<RegistryFriendlyByteBuf, GeneFormPayload> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, GeneFormPayload::entityId, ByteBufCodecs.STRING_UTF8, GeneFormPayload::form, GeneFormPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
