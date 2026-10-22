package dev.warpbound.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.ResourceLocation;

import java.util.List;

/**
 * Квест из датапака (data/&lt;ns&gt;/quest/*.json). Текст пишется прямо в JSON;
 * {@code {player}} в описании заменяется ником игрока.
 *
 * @param x,y позиция узла на карте главы, в клетках по 32 пикселя
 */
public record QuestDef(ResourceLocation chapter, int x, int y, List<ResourceLocation> parents,
                       List<Criterion> criteria, String title, String description,
                       ResourceLocation icon, List<Reward> rewards) {
    public static final Codec<QuestDef> CODEC = RecordCodecBuilder.create(i -> i.group(
            ResourceLocation.CODEC.fieldOf("chapter").forGetter(QuestDef::chapter),
            Codec.INT.fieldOf("x").forGetter(QuestDef::x),
            Codec.INT.fieldOf("y").forGetter(QuestDef::y),
            ResourceLocation.CODEC.listOf().optionalFieldOf("parents", List.of()).forGetter(QuestDef::parents),
            Criterion.CODEC.listOf().fieldOf("criteria").forGetter(QuestDef::criteria),
            Codec.STRING.fieldOf("title").forGetter(QuestDef::title),
            Codec.STRING.fieldOf("description").forGetter(QuestDef::description),
            ResourceLocation.CODEC.fieldOf("icon").forGetter(QuestDef::icon),
            Reward.CODEC.listOf().optionalFieldOf("rewards", List.of()).forGetter(QuestDef::rewards)
    ).apply(i, QuestDef::new));
}
