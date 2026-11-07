package dev.warpbound.player;

import dev.warpbound.Warpbound;
import dev.warpbound.network.GeneFormPayload;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.networking.v1.EntityTrackingEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

/**
 * Форма тела игрока (человек, Громовой воин, Астартес): хранится в данных игрока, переживает смерть,
 * рассылается всем, кто видит игрока, и меняет рост через атрибут scale. Пока переключается командой /wb gene,
 * позже — операцией генной модификации.
 */
public final class GeneForms {
    public static final AttachmentType<GeneForm> FORM = AttachmentRegistry.<GeneForm>builder()
            .persistent(GeneForm.CODEC)
            .copyOnDeath()
            .initializer(() -> GeneForm.HUMAN)
            .buildAndRegister(Warpbound.id("gene_form"));
    private static final ResourceLocation SCALE_ID = Warpbound.id("gene_scale");

    private GeneForms() {
    }

    public static GeneForm get(ServerPlayer player) {
        return player.getAttachedOrCreate(FORM);
    }

    public static void set(ServerPlayer player, GeneForm form) {
        player.setAttached(FORM, form);
        applyScale(player, form);
        broadcast(player);
    }

    private static void applyScale(ServerPlayer player, GeneForm form) {
        AttributeInstance scale = player.getAttribute(Attributes.SCALE);
        if (scale == null) return;
        scale.removeModifier(SCALE_ID);
        if (form.scaleBonus() > 0.001)
            scale.addPermanentModifier(new AttributeModifier(SCALE_ID, form.scaleBonus(), AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
    }

    private static void broadcast(ServerPlayer player) {
        GeneFormPayload payload = new GeneFormPayload(player.getId(), get(player).getSerializedName());
        ServerPlayNetworking.send(player, payload);
        for (ServerPlayer other : PlayerLookup.tracking(player)) if (other != player) ServerPlayNetworking.send(other, payload);
    }

    public static void register() {
        // вход, возрождение (новая сущность, новый номер), появление в поле зрения другого игрока
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            applyScale(handler.player, get(handler.player));
            broadcast(handler.player);
        });
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
            applyScale(newPlayer, get(newPlayer));
            broadcast(newPlayer);
        });
        EntityTrackingEvents.START_TRACKING.register((tracked, viewer) -> {
            if (tracked instanceof ServerPlayer p && get(p) != GeneForm.HUMAN)
                ServerPlayNetworking.send(viewer, new GeneFormPayload(p.getId(), get(p).getSerializedName()));
        });
    }
}
