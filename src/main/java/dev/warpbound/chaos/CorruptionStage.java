package dev.warpbound.chaos;

/**
 * Ступени порчи из дизайн-документа. Пороги — нижняя граница ступени.
 */
public enum CorruptionStage {
    PURE(0, "Чистый"),
    WHISPER(20, "Шёпот"),
    MARKED(40, "Метка"),
    POSSESSED(60, "Одержимый"),
    BRINK(80, "На краю"),
    ASCENSION(100, "Выбор");

    public final int threshold;
    public final String displayName;

    CorruptionStage(int threshold, String displayName) {
        this.threshold = threshold;
        this.displayName = displayName;
    }

    public static CorruptionStage of(float corruption) {
        CorruptionStage result = PURE;
        for (CorruptionStage stage : values()) {
            if (corruption >= stage.threshold) result = stage;
        }
        return result;
    }
}
