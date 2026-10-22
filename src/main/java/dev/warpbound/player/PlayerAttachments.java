package dev.warpbound.player;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

/** Данные игрока помимо Хаоса. Генном и псайкер появятся здесь же отдельными attachment. */
public final class PlayerAttachments {
    public static final AttachmentType<PlayerProgress> PROGRESS = AttachmentRegistry.<PlayerProgress>builder()
            .persistent(PlayerProgress.CODEC)
            .copyOnDeath()
            .initializer(() -> PlayerProgress.EMPTY)
            .buildAndRegister(Warpbound.id("progress"));

    private PlayerAttachments() {
    }

    public static void register() {
    }
}
