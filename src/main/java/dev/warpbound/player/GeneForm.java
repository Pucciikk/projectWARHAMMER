package dev.warpbound.player;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/**
 * Форма тела игрока после генной модификации. model — имя модели GeckoLib (geo, текстура, клипы, наложения),
 * height — рост в игре, блоков: от него атрибут scale (обычный игрок 1,8), а с ним и хитбокс.
 */
public enum GeneForm implements StringRepresentable {
    HUMAN("human", null, 1.8f, 1.8f),
    THUNDER_WARRIOR("thunder_warrior", "thunder_warrior", 2.3f, 2.2f),
    /** 2,4 — самый большой рост, при котором пригнувшись (×0,83) проходишь в двери и тоннели высотой 2 (решение автора 7.11.2026). */
    ASTARTES("astartes", "astartes", 2.4f, 2.2f);

    public static final Codec<GeneForm> CODEC = StringRepresentable.fromEnum(GeneForm::values);

    private final String id;
    private final String model;
    private final float height;
    private final float modelHeight;

    GeneForm(String id, String model, float height, float modelHeight) {
        this.id = id;
        this.model = model;
        this.height = height;
        this.modelHeight = modelHeight;
    }

    /** Рост самой модели в её единицах (geo): модель рисуется с увеличением height / modelHeight. */
    public float modelHeight() {
        return modelHeight;
    }

    @Override
    public String getSerializedName() {
        return id;
    }

    /** null у человека: рисуется обычный игрок. */
    public String model() {
        return model;
    }

    public float height() {
        return height;
    }

    /** Добавка к атрибуту scale (ADD_MULTIPLIED_BASE). */
    public double scaleBonus() {
        return height / 1.8 - 1;
    }

    public static GeneForm byId(String id) {
        for (GeneForm f : values()) if (f.id.equals(id)) return f;
        return HUMAN;
    }
}
