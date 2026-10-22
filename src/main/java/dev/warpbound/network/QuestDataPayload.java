package dev.warpbound.network;

import com.mojang.serialization.Codec;
import dev.warpbound.Warpbound;
import dev.warpbound.quest.QuestChapter;
import dev.warpbound.quest.QuestDef;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

import java.util.Map;

/** Сервер → клиент: все главы и квесты из датапака (клиент датапаков не видит). */
public record QuestDataPayload(Map<ResourceLocation, QuestChapter> chapters,
                               Map<ResourceLocation, QuestDef> quests) implements CustomPacketPayload {
    public static final Type<QuestDataPayload> TYPE = new Type<>(Warpbound.id("quest_data"));
    public static final StreamCodec<RegistryFriendlyByteBuf, QuestDataPayload> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.fromCodecWithRegistries(Codec.unboundedMap(ResourceLocation.CODEC, QuestChapter.CODEC)),
            QuestDataPayload::chapters,
            ByteBufCodecs.fromCodecWithRegistries(Codec.unboundedMap(ResourceLocation.CODEC, QuestDef.CODEC)),
            QuestDataPayload::quests,
            QuestDataPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
