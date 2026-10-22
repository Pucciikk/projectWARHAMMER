package dev.warpbound.quest;

import dev.warpbound.start.CrashSite;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Сюжетные события главы 1, которые не привязаны к блокам: монолог при первом входе,
 * первая ночь и шёпот третьего дня.
 */
public final class StoryDirector {
    /** Монолог при пробуждении. Слова автора мода. */
    private static final String[] INTRO = {
            "Голова раскалывается...",
            "У меня был Патент Вольного Торговца... но всё сгорело.",
            "А команда?.. Где же команда?.. Никого не осталось.",
            "К какой семье я принадлежу? Как меня зовут...",
            "Даже эмблемы корабля стёр варп-шторм.",
            "Видимо, придётся начать всё с нуля..."
    };
    private static final int INTRO_DELAY = 60;
    private static final int LINE_GAP = 70;
    private static final long DAY = 24000L;
    /** Шёпот приходит на третий день: дни 0 и 1 прошли. */
    private static final long WHISPER_DAY = 2;

    private record Line(long tick, Component text) {
    }

    private static final Map<UUID, Deque<Line>> pending = new HashMap<>();

    private StoryDirector() {
    }

    public static void register() {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayer player = handler.getPlayer();
            if (QuestManager.hasFlag(player, StoryFlags.INTRO_SHOWN)) return;
            QuestManager.setFlag(player, StoryFlags.INTRO_SHOWN);
            CrashSite.wakeUp(player);
            scheduleIntro(player, server.getTickCount());
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> pending.remove(handler.getPlayer().getUUID()));
        ServerTickEvents.END_SERVER_TICK.register(StoryDirector::tick);
    }

    private static void scheduleIntro(ServerPlayer player, long now) {
        Deque<Line> lines = new ArrayDeque<>();
        long t = now + INTRO_DELAY;
        for (String s : INTRO) {
            lines.add(new Line(t, Component.literal(s).withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC)));
            t += LINE_GAP;
        }
        lines.add(new Line(t, Component.literal("Журнал памяти: ")
                .withStyle(ChatFormatting.GOLD)
                .append(Component.keybind("key.warpbound.quests").withStyle(ChatFormatting.YELLOW))
                .append(Component.literal(" или кнопка с аквилой в инвентаре.").withStyle(ChatFormatting.GOLD))));
        pending.put(player.getUUID(), lines);
    }

    private static void tick(MinecraftServer server) {
        long now = server.getTickCount();
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            Deque<Line> lines = pending.get(player.getUUID());
            if (lines != null) {
                while (!lines.isEmpty() && lines.peek().tick <= now) player.sendSystemMessage(lines.poll().text);
                if (lines.isEmpty()) pending.remove(player.getUUID());
            }
            if (now % 20 == 0) checkTime(player);
        }
    }

    private static void checkTime(ServerPlayer player) {
        ServerLevel overworld = player.server.overworld();
        long time = overworld.getDayTime();
        long timeOfDay = time % DAY;

        // Первая ночь: игрок застал темноту (или лёг спать), а потом увидел рассвет
        if (!QuestManager.hasFlag(player, StoryFlags.FIRST_NIGHT)) {
            boolean night = timeOfDay >= 13000 && timeOfDay < 23000;
            if (night || player.isSleeping()) {
                QuestManager.setFlag(player, StoryFlags.SAW_NIGHT);
            } else if (QuestManager.hasFlag(player, StoryFlags.SAW_NIGHT)) {
                QuestManager.setFlag(player, StoryFlags.FIRST_NIGHT);
            }
        }

        if (time / DAY >= WHISPER_DAY && !QuestManager.hasFlag(player, StoryFlags.CHAOS_WHISPER)) {
            QuestManager.setFlag(player, StoryFlags.CHAOS_WHISPER);
            player.displayClientMessage(Component.literal("...Безымянный... я помню тебя, даже если ты себя — нет...")
                    .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), true);
            player.playNotifySound(SoundEvents.AMBIENT_SOUL_SAND_VALLEY_MOOD.value(), SoundSource.AMBIENT, 0.8f, 0.6f);
        }
    }
}
