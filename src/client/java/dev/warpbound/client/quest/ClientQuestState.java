package dev.warpbound.client.quest;

import dev.warpbound.player.PlayerProgress;
import dev.warpbound.quest.QuestChapter;
import dev.warpbound.quest.QuestDef;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Что клиент знает о квестах: данные с сервера и свой прогресс. */
public final class ClientQuestState {
    private static Map<ResourceLocation, QuestChapter> chapters = Map.of();
    private static Map<ResourceLocation, QuestDef> quests = Map.of();
    private static PlayerProgress progress = PlayerProgress.EMPTY;
    /** Первая синхронизация после входа не должна сыпать уведомлениями о старых квестах. */
    private static boolean received;

    private ClientQuestState() {
    }

    public static void setData(Map<ResourceLocation, QuestChapter> c, Map<ResourceLocation, QuestDef> q) {
        chapters = c;
        quests = q;
    }

    public static void setProgress(PlayerProgress updated) {
        if (received) {
            for (ResourceLocation id : updated.completed()) {
                if (progress.done(id)) continue;
                QuestDef quest = quests.get(id);
                if (quest != null) Minecraft.getInstance().getToasts().addToast(new QuestToast(quest));
            }
        }
        progress = updated;
        received = true;
    }

    public static void reset() {
        chapters = Map.of();
        quests = Map.of();
        progress = PlayerProgress.EMPTY;
        received = false;
    }

    public static PlayerProgress progress() {
        return progress;
    }

    public static Map<ResourceLocation, QuestDef> quests() {
        return quests;
    }

    public static Optional<QuestChapter> chapter(ResourceLocation id) {
        return Optional.ofNullable(chapters.get(id));
    }

    /** Видимые главы по порядку. Глава с requires_flag появляется только после флага. */
    public static List<Map.Entry<ResourceLocation, QuestChapter>> visibleChapters() {
        return chapters.entrySet().stream()
                .filter(e -> e.getValue().requiresFlag().map(progress::has).orElse(true))
                .sorted(Comparator.comparingInt((Map.Entry<ResourceLocation, QuestChapter> e) -> e.getValue().order())
                        .thenComparing(Map.Entry::getKey))
                .toList();
    }

    public static boolean available(QuestDef quest) {
        return quest.parents().stream().allMatch(progress::done);
    }

    public static ResourceLocation iconTexture(ResourceLocation icon) {
        return ResourceLocation.fromNamespaceAndPath(icon.getNamespace(), "textures/gui/quest/icon/" + icon.getPath() + ".png");
    }
}
