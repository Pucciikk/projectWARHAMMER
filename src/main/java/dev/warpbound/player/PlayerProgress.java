package dev.warpbound.player;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.ResourceLocation;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Прогресс игрока: выполненные квесты и сюжетные флаги («починил маяк», «слышал шёпот»).
 * Неизменяемая запись, как и ChaosData.
 */
public record PlayerProgress(Set<ResourceLocation> completed, Set<String> flags) {
    public static final PlayerProgress EMPTY = new PlayerProgress(Set.of(), Set.of());

    public static final Codec<PlayerProgress> CODEC = RecordCodecBuilder.create(i -> i.group(
            ResourceLocation.CODEC.listOf().<Set<ResourceLocation>>xmap(Set::copyOf, List::copyOf)
                    .optionalFieldOf("completed", Set.of()).forGetter(PlayerProgress::completed),
            Codec.STRING.listOf().<Set<String>>xmap(Set::copyOf, List::copyOf)
                    .optionalFieldOf("flags", Set.of()).forGetter(PlayerProgress::flags)
    ).apply(i, PlayerProgress::new));

    public boolean done(ResourceLocation quest) {
        return completed.contains(quest);
    }

    public boolean has(String flag) {
        return flags.contains(flag);
    }

    public PlayerProgress withCompleted(ResourceLocation quest) {
        Set<ResourceLocation> set = new HashSet<>(completed);
        set.add(quest);
        return new PlayerProgress(Set.copyOf(set), flags);
    }

    public PlayerProgress withFlag(String flag) {
        Set<String> set = new HashSet<>(flags);
        set.add(flag);
        return new PlayerProgress(completed, Set.copyOf(set));
    }
}
