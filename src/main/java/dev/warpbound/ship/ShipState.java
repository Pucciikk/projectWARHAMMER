package dev.warpbound.ship;

/** Машина состояний корабля: ORBIT → ENTERING → TRANSIT → EXITING → ORBIT. */
public enum ShipState {
    ORBIT("Орбита"),
    ENTERING("Вход в варп"),
    TRANSIT("Транзит"),
    EXITING("Выход из варпа");

    public final String displayName;

    ShipState(String displayName) {
        this.displayName = displayName;
    }

    public static ShipState byId(int id) {
        ShipState[] values = values();
        return id >= 0 && id < values.length ? values[id] : ORBIT;
    }
}
