package dev.warpbound.faction;

import dev.warpbound.chaos.ChaosData;
import dev.warpbound.chaos.ChaosLogic;
import net.minecraft.server.level.ServerPlayer;

/**
 * Верность игрока нигде не хранится: она вычисляется из порчи.
 * Все NPC спрашивают только этот класс, поэтому правило меняется в одном месте.
 */
public enum Allegiance {
    /** Порча ниже 60: свой для Империума. */
    LOYAL,
    /** Порча 60 и выше: имперские NPC стреляют, но падение ещё не случилось. */
    SUSPECT,
    /** Принял возвышение. */
    FALLEN;

    public static final float SUSPECT_THRESHOLD = 60f;

    public static Allegiance of(ChaosData data) {
        if ("accepted".equals(data.ascension())) return FALLEN;
        return data.corruption() >= SUSPECT_THRESHOLD ? SUSPECT : LOYAL;
    }

    public static Allegiance of(ServerPlayer player) {
        return of(ChaosLogic.get(player));
    }

    /** Какой стороне игрок сейчас ближе: на неё смотрят NPC. */
    public Faction side() {
        return this == LOYAL ? Faction.IMPERIUM : Faction.CHAOS;
    }
}
