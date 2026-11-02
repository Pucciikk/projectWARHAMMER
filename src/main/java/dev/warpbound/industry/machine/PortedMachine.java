package dev.warpbound.industry.machine;

import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.item.ItemVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import org.jetbrains.annotations.Nullable;
import team.reborn.energy.api.EnergyStorage;

/** Машина с разъёмами: что отдаёт наружу через порты. Null — такого вида портов нет. */
public interface PortedMachine {
    /** Входной порт только принимает, выходной только отдаёт. */
    @Nullable
    Storage<ItemVariant> itemStorage(boolean output);

    @Nullable
    Storage<FluidVariant> fluidStorage(boolean output);

    @Nullable
    EnergyStorage energyStorage();

    /** Порты для клиента, упакованные в число: см. {@code ChainMachineBlockEntity#packPort}. */
    long[] clientPorts();
}
