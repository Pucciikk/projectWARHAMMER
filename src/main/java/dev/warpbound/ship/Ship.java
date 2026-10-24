package dev.warpbound.ship;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;

import java.util.UUID;

/**
 * Корабль — это данные, а не постройка. Интерьер лишь отображает их.
 * В v0 нет корпусов и модулей: только участок, состояние и Поле Геллера.
 */
public class Ship {
    public final int plot;
    public final UUID owner;
    public String name;

    public ShipState state = ShipState.ORBIT;
    public int stateTicks;
    /** Длительность транзита этого перехода в тиках (берётся из конфига или команды). */
    public int transitTicks;

    /** Прочность Поля Геллера 0..1. */
    public float field = 1.0f;
    /** Сила варп-шторма на маршруте 0..1. */
    public float storm = 0.3f;

    /** На орбите какого пункта назначения корабль (ship_destination). */
    public ResourceLocation location = ShipDestination.HOME;
    /** Куда идёт переход; null, пока корабль на орбите. */
    public ResourceLocation destination;
    /** Переход сорван (пало Поле Геллера): выбросит не туда. */
    public boolean aborted;

    /** Раскладка интерьера (ship_layout); null — старый временный корпус v0. */
    public ResourceLocation layout;

    /** Где корабль «стоит» в реальном мире: туда высаживаются игроки. */
    public ResourceLocation dockDimension;
    public double dockX, dockY, dockZ;

    public Ship(int plot, UUID owner, String name) {
        this.plot = plot;
        this.owner = owner;
        this.name = name;
    }

    public CompoundTag save() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("plot", plot);
        tag.putUUID("owner", owner);
        tag.putString("name", name);
        tag.putString("state", state.name());
        tag.putInt("stateTicks", stateTicks);
        tag.putInt("transitTicks", transitTicks);
        tag.putFloat("field", field);
        tag.putFloat("storm", storm);
        if (layout != null) tag.putString("layout", layout.toString());
        tag.putString("location", location.toString());
        if (destination != null) tag.putString("destination", destination.toString());
        if (dockDimension != null) {
            tag.putString("dockDimension", dockDimension.toString());
            tag.putDouble("dockX", dockX);
            tag.putDouble("dockY", dockY);
            tag.putDouble("dockZ", dockZ);
        }
        return tag;
    }

    public static Ship load(CompoundTag tag) {
        Ship ship = new Ship(tag.getInt("plot"), tag.getUUID("owner"), tag.getString("name"));
        try {
            ship.state = ShipState.valueOf(tag.getString("state"));
        } catch (IllegalArgumentException e) {
            ship.state = ShipState.ORBIT;
        }
        ship.stateTicks = tag.getInt("stateTicks");
        ship.transitTicks = tag.getInt("transitTicks");
        ship.field = tag.getFloat("field");
        ship.storm = tag.getFloat("storm");
        if (tag.contains("layout")) ship.layout = ResourceLocation.tryParse(tag.getString("layout"));
        if (tag.contains("location")) ship.location = ResourceLocation.tryParse(tag.getString("location"));
        if (ship.location == null) ship.location = ShipDestination.HOME;
        if (tag.contains("destination")) ship.destination = ResourceLocation.tryParse(tag.getString("destination"));
        if (tag.contains("dockDimension")) {
            ship.dockDimension = ResourceLocation.tryParse(tag.getString("dockDimension"));
            ship.dockX = tag.getDouble("dockX");
            ship.dockY = tag.getDouble("dockY");
            ship.dockZ = tag.getDouble("dockZ");
        }
        return ship;
    }
}
