package dev.warpbound.industry.machine;

import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidConstants;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.item.ItemVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.minecraft.server.level.ServerLevel;
import team.reborn.energy.api.EnergyStorage;
import team.reborn.energy.api.EnergyStorageUtil;

import java.util.ArrayList;
import java.util.List;

/** Отдача машины через выходные порты: раз в {@link Conduits#PERIOD} тиков, по списку приёмников, который пересчитывается только при изменении сети. */
final class PortPump {
    private static final long ITEMS_PER_PUSH = 8;
    private static final long FLUID_PER_PUSH = FluidConstants.BUCKET * 2;

    private record Route(MachineSpec.Kind kind, List<Conduits.Target> targets) {
    }

    private List<Route> routes = List.of();
    private long generation = -1;

    void run(ServerLevel level, MultiblockCoreBlockEntity core, MachineSpec spec, PortedMachine machine, long energyBudget) {
        if ((level.getGameTime() + core.getBlockPos().asLong()) % Conduits.PERIOD != 0) return;
        long now = Conduits.generation(level);
        if (now != generation) {
            generation = now;
            List<Route> fresh = new ArrayList<>();
            for (ChainMachines.WorldPort p : ChainMachines.worldPorts(core, spec)) {
                if (p.output()) fresh.add(new Route(p.kind(), Conduits.targets(level, p.pos(), p.side(), p.kind())));
            }
            routes = fresh;
        }
        for (Route r : routes) {
            switch (r.kind()) {
                case ITEM -> {
                    Storage<ItemVariant> from = machine.itemStorage(true);
                    if (from != null) Conduits.push(level, from, r.targets(), MachineSpec.Kind.ITEM, ITEMS_PER_PUSH);
                }
                case FLUID -> {
                    Storage<FluidVariant> from = machine.fluidStorage(true);
                    if (from != null) Conduits.push(level, from, r.targets(), MachineSpec.Kind.FLUID, FLUID_PER_PUSH);
                }
                case ENERGY -> pushEnergy(level, machine.energyStorage(), r.targets(), energyBudget);
            }
        }
    }

    /** Поровну каждому: при нехватке все потребители замедляются одинаково и не гаснут. Остаток отдаём второму проходу. */
    private static void pushEnergy(ServerLevel level, EnergyStorage from, List<Conduits.Target> targets, long budget) {
        if (from == null || targets.isEmpty()) return;
        long left = budget;
        for (int pass = 0; pass < 2 && left > 0; pass++) {
            long share = Math.max(1, left / targets.size());
            for (Conduits.Target t : targets) {
                EnergyStorage to = EnergyStorage.SIDED.find(level, t.pos(), t.side());
                if (to == null || to == from) continue;
                left -= EnergyStorageUtil.move(from, to, Math.min(share, left), null);
                if (left <= 0) break;
            }
        }
    }
}
