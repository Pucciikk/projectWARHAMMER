package dev.warpbound.faction;

/**
 * Стороны конфликта. Ксеносы добавятся сюда позже вместе с JSON-матрицей отношений.
 */
public enum Faction {
    IMPERIUM,
    CHAOS;

    public boolean hostileTo(Faction other) {
        return this != other;
    }
}
