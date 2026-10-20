package dev.warpbound.chaos;

import dev.warpbound.config.WarpboundConfig;
import dev.warpbound.network.ChaosSyncPayload;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;

/**
 * Все изменения порчи идут только через этот класс: он следит за скверной,
 * ступенями и синхронизацией с клиентом.
 */
public final class ChaosLogic {
    private ChaosLogic() {
    }

    public static ChaosData get(ServerPlayer player) {
        return player.getAttachedOrCreate(ChaosAttachments.CHAOS);
    }

    public static void set(ServerPlayer player, ChaosData data) {
        player.setAttached(ChaosAttachments.CHAOS, data);
        sync(player);
    }

    /** Добавить (или снять, если delta < 0) порчу. Ниже скверны порча не опускается. */
    public static void addCorruption(ServerPlayer player, float delta) {
        ChaosData old = get(player);
        float taint = old.taint();
        float value = Mth.clamp(old.corruption() + delta, taint, 100f);

        // При пересечении порога ступени вверх часть порчи оседает в скверну
        CorruptionStage before = old.stage();
        CorruptionStage after = CorruptionStage.of(value);
        if (after.ordinal() > before.ordinal()) {
            float floor = after.threshold - WarpboundConfig.get().taintBelowThreshold;
            taint = Math.max(taint, Math.max(0f, floor));
            onStageReached(player, after);
        }

        ChaosData updated = old.withCorruption(value, taint);
        if (after == CorruptionStage.ASCENSION && "none".equals(old.ascension())) {
            updated = updated.withAscension("offered");
        }
        set(player, updated);
    }

    public static void setCorruption(ServerPlayer player, float value) {
        ChaosData old = get(player);
        float clamped = Mth.clamp(value, old.taint(), 100f);
        addCorruption(player, clamped - old.corruption());
    }

    private static void onStageReached(ServerPlayer player, CorruptionStage stage) {
        Component message = switch (stage) {
            case WHISPER -> Component.literal("Ты слышишь шёпот на краю сознания...");
            case MARKED -> Component.literal("Боги Хаоса заметили тебя.");
            case POSSESSED -> Component.literal("Что-то смотрит твоими глазами.");
            case BRINK -> Component.literal("Ты на краю. Ещё шаг, и пути назад не будет.");
            case ASCENSION -> Component.literal("Боги зовут. Ритуал возвышения ждёт тебя.");
            default -> null;
        };
        if (message != null) {
            player.displayClientMessage(message.copy().withStyle(ChatFormatting.DARK_RED, ChatFormatting.ITALIC), false);
        }
    }

    public static void sync(ServerPlayer player) {
        ServerPlayNetworking.send(player, new ChaosSyncPayload(get(player)));
    }

    public static void registerEvents() {
        // Клиент узнаёт свою порчу при входе, после смерти и при смене измерения
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sync(handler.getPlayer()));
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> sync(newPlayer));
        ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD.register((player, origin, destination) -> sync(player));
    }
}
