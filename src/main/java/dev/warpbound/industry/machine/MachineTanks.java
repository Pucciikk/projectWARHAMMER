package dev.warpbound.industry.machine;

import net.fabricmc.fabric.api.transfer.v1.fluid.FluidConstants;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.CombinedStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.FilteringStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.SingleVariantStorage;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.material.Fluid;

import java.util.ArrayList;
import java.util.List;

/** Баки машины: входные снаружи только наполняются, выходные снаружи только опустошаются. */
public final class MachineTanks {
    public static final long CAPACITY = FluidConstants.BUCKET * 16;
    private static final long PER_MB = FluidConstants.BUCKET / 1000;

    /** Можно ли залить эту жидкость в этот входной бак. */
    public interface Filter {
        boolean accepts(int tank, FluidVariant variant);
    }

    private final class Tank extends SingleVariantStorage<FluidVariant> {
        private final int index;
        private final boolean input;

        Tank(int index, boolean input) {
            this.index = index;
            this.input = input;
        }

        @Override
        protected FluidVariant getBlankVariant() {
            return FluidVariant.blank();
        }

        @Override
        protected long getCapacity(FluidVariant variant) {
            return CAPACITY;
        }

        @Override
        protected boolean canInsert(FluidVariant variant) {
            return !input || filter.accepts(index, variant);
        }

        @Override
        protected void onFinalCommit() {
            changed.run();
        }
    }

    private final Filter filter;
    private final Runnable changed;
    private final List<Tank> in = new ArrayList<>();
    private final List<Tank> out = new ArrayList<>();
    private final Storage<FluidVariant> inPort;
    private final Storage<FluidVariant> outPort;

    public MachineTanks(int inCount, int outCount, Filter filter, Runnable changed) {
        this.filter = filter;
        this.changed = changed;
        List<Storage<FluidVariant>> a = new ArrayList<>(), b = new ArrayList<>();
        for (int i = 0; i < inCount; i++) {
            Tank t = new Tank(i, true);
            in.add(t);
            a.add(FilteringStorage.insertOnlyOf(t));
        }
        for (int i = 0; i < outCount; i++) {
            Tank t = new Tank(i, false);
            out.add(t);
            b.add(FilteringStorage.extractOnlyOf(t));
        }
        inPort = new CombinedStorage<>(a);
        outPort = new CombinedStorage<>(b);
    }

    public Storage<FluidVariant> inPort() {
        return inPort;
    }

    public Storage<FluidVariant> outPort() {
        return outPort;
    }

    public boolean hasIn(Fluid fluid, int mb) {
        long need = mb * PER_MB;
        for (Tank t : in) if (t.getResource().isOf(fluid) && t.getAmount() >= need) return true;
        return false;
    }

    /** Для автотестов и команд: залить напрямую, минуя порт. */
    public void fillIn(Fluid fluid, int mb) {
        for (Tank t : in) {
            if (t.isResourceBlank() || t.getResource().isOf(fluid)) {
                t.variant = FluidVariant.of(fluid);
                t.amount = Math.min(CAPACITY, t.amount + mb * PER_MB);
                return;
            }
        }
    }

    public void clear() {
        for (Tank t : in) {
            t.variant = FluidVariant.blank();
            t.amount = 0;
        }
        for (Tank t : out) {
            t.variant = FluidVariant.blank();
            t.amount = 0;
        }
    }

    public boolean outEmpty() {
        for (Tank t : out) if (!t.isResourceBlank()) return false;
        return true;
    }

    public void drainIn(Fluid fluid, int mb) {
        long need = mb * PER_MB;
        for (Tank t : in) {
            if (t.getResource().isOf(fluid) && t.getAmount() >= need) {
                t.amount -= need;
                if (t.amount == 0) t.variant = FluidVariant.blank();
                changed.run();
                return;
            }
        }
    }

    private Tank outFor(Fluid fluid, long need) {
        for (Tank t : out) if (t.getResource().isOf(fluid) && t.getAmount() + need <= CAPACITY) return t;
        for (Tank t : out) if (t.isResourceBlank()) return t;
        return null;
    }

    public boolean outFits(Fluid fluid, int mb) {
        return outFor(fluid, mb * PER_MB) != null;
    }

    public void fillOut(Fluid fluid, int mb) {
        long add = mb * PER_MB;
        Tank t = outFor(fluid, add);
        if (t == null) return;
        t.variant = FluidVariant.of(fluid);
        t.amount += add;
        changed.run();
    }

    public boolean outFull(int tank) {
        return out.get(tank).getAmount() >= CAPACITY;
    }

    public void fill(int tank, FluidVariant variant, long droplets) {
        Tank t = out.get(tank);
        if (!t.isResourceBlank() && !t.getResource().equals(variant)) return;
        t.variant = variant;
        t.amount = Math.min(CAPACITY, t.amount + droplets);
        changed.run();
    }

    /** Данные для окна: по два числа на бак, миллибакеты и номер жидкости. Сначала входы, потом выходы. */
    public int dataAt(int i) {
        int tank = i / 2;
        Tank t = tank < in.size() ? in.get(tank) : out.get(tank - in.size());
        if (i % 2 == 0) return (int) (t.getAmount() / PER_MB);
        return t.isResourceBlank() ? -1 : BuiltInRegistries.FLUID.getId(t.getResource().getFluid());
    }

    public int dataCount() {
        return (in.size() + out.size()) * 2;
    }

    public void save(CompoundTag tag, HolderLookup.Provider registries) {
        CompoundTag all = new CompoundTag();
        for (int i = 0; i < in.size(); i++) saveOne(all, "in" + i, in.get(i), registries);
        for (int i = 0; i < out.size(); i++) saveOne(all, "out" + i, out.get(i), registries);
        tag.put("tanks", all);
    }

    private static void saveOne(CompoundTag all, String key, Tank t, HolderLookup.Provider registries) {
        CompoundTag c = new CompoundTag();
        SingleVariantStorage.writeNbt(t, FluidVariant.CODEC, c, registries);
        all.put(key, c);
    }

    public void load(CompoundTag tag, HolderLookup.Provider registries) {
        if (!tag.contains("tanks")) return;
        CompoundTag all = tag.getCompound("tanks");
        for (int i = 0; i < in.size(); i++) loadOne(all, "in" + i, in.get(i), registries);
        for (int i = 0; i < out.size(); i++) loadOne(all, "out" + i, out.get(i), registries);
    }

    private static void loadOne(CompoundTag all, String key, Tank t, HolderLookup.Provider registries) {
        if (all.contains(key)) SingleVariantStorage.readNbt(t, FluidVariant.CODEC, FluidVariant::blank, all.getCompound(key), registries);
    }
}
