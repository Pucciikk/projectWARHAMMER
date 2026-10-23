package dev.warpbound.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.ResourceLocation;

import java.util.Optional;

/**
 * Глава окна квестов.
 *
 * @param branch      "common", "imperium" или "chaos" — от ветки зависит оформление вкладки
 * @param order       порядок вкладок
 * @param icon        иконка: textures/gui/quest/icon/&lt;path&gt;.png
 * @param requiresFlag вкладка видна только с этим флагом
 * @param sealed      вкладка видна, но закрыта (намёк на ветку Хаоса); sealedText — что сказать при клике
 */
public record QuestChapter(String title, String branch, int order, ResourceLocation icon,
                           Optional<String> requiresFlag, boolean sealed, String sealedText) {
    public static final Codec<QuestChapter> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.fieldOf("title").forGetter(QuestChapter::title),
            Codec.STRING.optionalFieldOf("branch", "common").forGetter(QuestChapter::branch),
            Codec.INT.optionalFieldOf("order", 0).forGetter(QuestChapter::order),
            ResourceLocation.CODEC.fieldOf("icon").forGetter(QuestChapter::icon),
            Codec.STRING.optionalFieldOf("requires_flag").forGetter(QuestChapter::requiresFlag),
            Codec.BOOL.optionalFieldOf("sealed", false).forGetter(QuestChapter::sealed),
            Codec.STRING.optionalFieldOf("sealed_text", "").forGetter(QuestChapter::sealedText)
    ).apply(i, QuestChapter::new));
}
