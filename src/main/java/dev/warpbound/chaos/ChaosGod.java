package dev.warpbound.chaos;

public enum ChaosGod {
    KHORNE("Кхорн"),
    NURGLE("Нургл"),
    TZEENTCH("Тзинч"),
    SLAANESH("Слаанеш");

    public final String displayName;

    ChaosGod(String displayName) {
        this.displayName = displayName;
    }
}
