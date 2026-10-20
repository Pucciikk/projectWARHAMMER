package dev.warpbound.chaos;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

/**
 * Data Attachment: данные, «прикреплённые» к игроку и сохраняемые вместе с ним.
 * copyOnDeath — порча не исчезает после смерти.
 */
public final class ChaosAttachments {
    public static final AttachmentType<ChaosData> CHAOS = AttachmentRegistry.<ChaosData>builder()
            .persistent(ChaosData.CODEC)
            .copyOnDeath()
            .initializer(() -> ChaosData.EMPTY)
            .buildAndRegister(Warpbound.id("chaos"));

    private ChaosAttachments() {
    }

    /** Вызывается из onInitialize, чтобы класс загрузился и тип зарегистрировался вовремя. */
    public static void register() {
    }
}
