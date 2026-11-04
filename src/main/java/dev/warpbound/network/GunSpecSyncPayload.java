package dev.warpbound.network;

import com.mojang.serialization.Codec;
import dev.warpbound.Warpbound;
import dev.warpbound.gun.GunSpec;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

import java.util.Map;

/** Числа оружия для клиента: при входе и после /reload. */
public record GunSpecSyncPayload(Map<ResourceLocation, GunSpec> specs) implements CustomPacketPayload {
    public static final Type<GunSpecSyncPayload> TYPE = new Type<>(Warpbound.id("gun_spec_sync"));
    public static final StreamCodec<RegistryFriendlyByteBuf, GunSpecSyncPayload> STREAM_CODEC = ByteBufCodecs.fromCodecWithRegistries(Codec.unboundedMap(ResourceLocation.CODEC, GunSpec.CODEC))
            .map(GunSpecSyncPayload::new, GunSpecSyncPayload::specs);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
