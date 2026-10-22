package dev.warpbound.quest;

import dev.warpbound.Warpbound;
import dev.warpbound.core.DataRegistry;
import dev.warpbound.network.ProgressSyncPayload;
import dev.warpbound.network.QuestBookOpenedPayload;
import dev.warpbound.network.QuestDataPayload;
import dev.warpbound.player.PlayerAttachments;
import dev.warpbound.player.PlayerProgress;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.stats.Stats;
import net.minecraft.world.item.ItemStack;

import java.util.Map;

/**
 * Серверная часть квестов: данные из датапака, проверка условий, награды и синхронизация.
 * Сюжетные события (монолог, шёпот, ночь) живут в {@link StoryDirector} и ставят флаги через {@link #setFlag}.
 */
public final class QuestManager {
    public static final DataRegistry<QuestChapter> CHAPTERS = new DataRegistry<>("quest_chapter", QuestChapter.CODEC);
    public static final DataRegistry<QuestDef> QUESTS = new DataRegistry<>("quest", QuestDef.CODEC);

    /** Условия проверяются раз в секунду: этого хватает, а сервер не тратит время зря. */
    private static final int CHECK_INTERVAL = 20;

    private QuestManager() {
    }

    public static void register() {
        QUESTS.onReload(registry -> registry.all().forEach((id, quest) -> {
            for (ResourceLocation parent : quest.parents()) {
                if (registry.get(parent).isEmpty()) Warpbound.LOG.error("quest: {}: нет родителя {}", id, parent);
            }
        }));

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            sendData(handler.getPlayer());
            sync(handler.getPlayer());
        });
        ServerLifecycleEvents.END_DATA_PACK_RELOAD.register((server, resources, success) -> {
            for (ServerPlayer player : server.getPlayerList().getPlayers()) sendData(player);
        });
        ServerTickEvents.END_SERVER_TICK.register(QuestManager::tick);
        ServerPlayNetworking.registerGlobalReceiver(QuestBookOpenedPayload.TYPE,
                (payload, context) -> setFlag(context.player(), StoryFlags.OPENED_QUEST_BOOK));
    }

    public static PlayerProgress get(ServerPlayer player) {
        return player.getAttachedOrCreate(PlayerAttachments.PROGRESS);
    }

    private static void set(ServerPlayer player, PlayerProgress progress) {
        player.setAttached(PlayerAttachments.PROGRESS, progress);
        sync(player);
    }

    /** Для отладки: начать сюжет заново. */
    public static void reset(ServerPlayer player) {
        set(player, PlayerProgress.EMPTY);
    }

    public static boolean hasFlag(ServerPlayer player, String flag) {
        return get(player).has(flag);
    }

    /** Поставить сюжетный флаг и сразу проверить квесты, которые его ждут. */
    public static void setFlag(ServerPlayer player, String flag) {
        PlayerProgress progress = get(player);
        if (progress.has(flag)) return;
        set(player, progress.withFlag(flag));
        evaluate(player);
    }

    private static void tick(MinecraftServer server) {
        if (server.getTickCount() % CHECK_INTERVAL != 0) return;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) evaluate(player);
    }

    /** Выполнить всё, что можно. Цепочка закрывается за один вызов, если условия уже выполнены. */
    public static void evaluate(ServerPlayer player) {
        boolean changed;
        do {
            changed = false;
            PlayerProgress progress = get(player);
            for (Map.Entry<ResourceLocation, QuestDef> entry : QUESTS.all().entrySet()) {
                ResourceLocation id = entry.getKey();
                QuestDef quest = entry.getValue();
                if (progress.done(id) || !available(progress, quest) || !satisfied(player, progress, quest)) continue;
                complete(player, id, quest);
                changed = true;
                break;
            }
        } while (changed);
    }

    public static boolean available(PlayerProgress progress, QuestDef quest) {
        return quest.parents().stream().allMatch(progress::done);
    }

    private static boolean satisfied(ServerPlayer player, PlayerProgress progress, QuestDef quest) {
        for (Criterion c : quest.criteria()) {
            boolean ok = switch (c.type()) {
                case Criterion.ITEM -> player.getInventory().countItem(c.item().orElseThrow()) >= c.count();
                case Criterion.CRAFTED -> player.getStats().getValue(Stats.ITEM_CRAFTED.get(c.item().orElseThrow())) >= c.count();
                case Criterion.FLAG -> progress.has(c.flag().orElseThrow());
                default -> false;
            };
            if (!ok) return false;
        }
        return true;
    }

    private static void complete(ServerPlayer player, ResourceLocation id, QuestDef quest) {
        set(player, get(player).withCompleted(id));
        for (Reward reward : quest.rewards()) {
            ItemStack stack = reward.stack();
            if (!player.getInventory().add(stack)) player.drop(stack, false);
        }
        Warpbound.LOG.debug("{} выполнил квест {}", player.getGameProfile().getName(), id);
    }

    public static void sync(ServerPlayer player) {
        ServerPlayNetworking.send(player, new ProgressSyncPayload(get(player)));
    }

    private static void sendData(ServerPlayer player) {
        ServerPlayNetworking.send(player, new QuestDataPayload(CHAPTERS.all(), QUESTS.all()));
    }
}
