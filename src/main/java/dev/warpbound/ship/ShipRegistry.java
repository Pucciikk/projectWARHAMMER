package dev.warpbound.ship;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Реестр всех кораблей мира. Хранится в сохранении Overworld (data/warpbound_ships.dat).
 */
public class ShipRegistry extends SavedData {
    private static final String FILE = "warpbound_ships";

    private final Map<Integer, Ship> byPlot = new LinkedHashMap<>();
    private int nextPlot = 1;

    public static ShipRegistry get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(
                new SavedData.Factory<>(ShipRegistry::new, ShipRegistry::load, null), FILE);
    }

    public Ship create(UUID owner, String name) {
        Ship ship = new Ship(nextPlot++, owner, name);
        byPlot.put(ship.plot, ship);
        setDirty();
        return ship;
    }

    public Optional<Ship> byPlot(int plot) {
        return Optional.ofNullable(byPlot.get(plot));
    }

    /** В v0 у игрока один корабль: берём первый, которым он владеет. */
    public Optional<Ship> ownedBy(UUID owner) {
        return byPlot.values().stream().filter(s -> s.owner.equals(owner)).findFirst();
    }

    /** Забыть корабль (отладка: заново построить и вывести в космос). Его участок не переиспользуется. */
    public void remove(Ship ship) {
        byPlot.remove(ship.plot);
        setDirty();
    }

    public Collection<Ship> all() {
        return byPlot.values();
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        ListTag list = new ListTag();
        for (Ship ship : byPlot.values()) list.add(ship.save());
        tag.put("ships", list);
        tag.putInt("nextPlot", nextPlot);
        return tag;
    }

    private static ShipRegistry load(CompoundTag tag, HolderLookup.Provider registries) {
        ShipRegistry registry = new ShipRegistry();
        ListTag list = tag.getList("ships", Tag.TAG_COMPOUND);
        for (int i = 0; i < list.size(); i++) {
            Ship ship = Ship.load(list.getCompound(i));
            registry.byPlot.put(ship.plot, ship);
        }
        registry.nextPlot = Math.max(tag.getInt("nextPlot"), 1);
        return registry;
    }
}
