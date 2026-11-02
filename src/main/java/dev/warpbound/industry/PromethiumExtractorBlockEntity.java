package dev.warpbound.industry;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.industry.machine.ChainMachines;
import dev.warpbound.industry.machine.Conduits;
import dev.warpbound.industry.machine.MachineSpec;
import dev.warpbound.industry.machine.PortPumps;
import dev.warpbound.industry.machine.PortedMachine;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidConstants;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.item.ItemVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.FilteringStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.SingleVariantStorage;
import net.minecraft.core.registries.BuiltInRegistries;
import team.reborn.energy.api.EnergyStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * Прометиевый экстрактор: качает сырой прометий в свой бак. Богатство залежи зависит от места (своё у каждого чанка).
 * Бак полон — коромысло останавливается. Прометий идёт в трубу из порта или забирается ведром.
 */
public class PromethiumExtractorBlockEntity extends MachineCoreBlockEntity implements PortedMachine {
    /** Ёмкость бака и ход накопления: в вёдрах, 1 ведро = 1000 единиц. */
    public static final int CAPACITY = 16_000, BUCKET = 1_000;
    /** Единиц за тик при богатстве 100%: ведро за 2,5 секунды. Колонна берёт 10 вёдер за 10 секунд, поэтому на одну нужно 3–8 экстракторов по богатству. */
    private static final int RATE = 20;

    private static final long PER_UNIT = FluidConstants.BUCKET / BUCKET;
    private final SingleVariantStorage<FluidVariant> tank = new SingleVariantStorage<>() {
        @Override
        protected FluidVariant getBlankVariant() {
            return FluidVariant.blank();
        }

        @Override
        protected long getCapacity(FluidVariant variant) {
            return CAPACITY * PER_UNIT;
        }

        @Override
        protected void onFinalCommit() {
            setChanged();
        }
    };
    private final Storage<FluidVariant> outPort = FilteringStorage.extractOnlyOf(tank);
    private final PortPumps pump = new PortPumps();
    private int progress;

    public PromethiumExtractorBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.PROMETHIUM_EXTRACTOR, pos, state, Warpbound.id("promethium_extractor"));
    }

    @Override
    public String modelName() {
        return "promethium_extractor";
    }

    @Override
    public boolean isWorking() {
        return getBlockState().getValue(BlockStateProperties.LIT);
    }

    /** Богатство залежи, 30–100%: постоянно для чанка и мира. */
    public int richness(ServerLevel level) {
        ChunkPos c = new ChunkPos(getBlockPos());
        long h = level.getSeed() ^ (c.x * 341873128712L + c.z * 132897987541L);
        return 30 + Mth.abs((int) (h ^ (h >>> 32))) % 71;
    }

    public int stored() {
        return (int) (tank.getAmount() / PER_UNIT);
    }

    private void add(int units) {
        tank.variant = FluidVariant.of(BuiltInRegistries.FLUID.get(Warpbound.id("crude_promethium")));
        tank.amount = Math.min(CAPACITY * PER_UNIT, tank.getAmount() + units * PER_UNIT);
    }

    /** Забрать ведро из бака. */
    public boolean drainBucket() {
        if (stored() < BUCKET) return false;
        tank.amount -= BUCKET * PER_UNIT;
        if (tank.amount == 0) tank.variant = FluidVariant.blank();
        setChanged();
        return true;
    }

    @Override
    public void tickFormed(ServerLevel level) {
        boolean run = stored() < CAPACITY;
        if (run) {
            progress += RATE * richness(level);
            if (progress >= 100) {
                add(progress / 100);
                progress %= 100;
                setChanged();
            }
        }
        setLit(level, run);
        MachineSpec spec = ChainMachines.spec(definitionId());
        if (spec != null) pump.run(level, this, spec, this, 0);
    }

    @Override
    public void onUnformed(ServerLevel level) {
        setLit(level, false);
        Conduits.invalidate(level);
    }

    @Override
    public void onFormed(ServerLevel level) {
        Conduits.invalidate(level);
        PortPumps.refreshNeighbours(level, this);
        sync();
    }

    @Override
    public Storage<ItemVariant> itemStorage(boolean output) {
        return null;
    }

    @Override
    public Storage<FluidVariant> fluidStorage(boolean output) {
        return output ? outPort : null;
    }

    @Override
    public EnergyStorage energyStorage() {
        return null;
    }

    private long[] clientPortCache = new long[0];

    @Override
    public long[] clientPorts() {
        return clientPortCache;
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = super.getUpdateTag(registries);
        MachineSpec spec = ChainMachines.spec(definitionId());
        if (spec != null) tag.putLongArray("ports", PortPumps.pack(spec));
        return tag;
    }

    private void setLit(ServerLevel level, boolean lit) {
        BlockState state = getBlockState();
        if (state.getValue(BlockStateProperties.LIT) != lit) {
            level.setBlock(getBlockPos(), state.setValue(BlockStateProperties.LIT, lit), Block.UPDATE_ALL);
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        SingleVariantStorage.writeNbt(tank, FluidVariant.CODEC, tag, registries);
        tag.putInt("progress", progress);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("stored")) add(tag.getInt("stored"));   // миры до появления бака
        else SingleVariantStorage.readNbt(tank, FluidVariant.CODEC, FluidVariant::blank, tag, registries);
        if (tag.contains("ports")) clientPortCache = tag.getLongArray("ports");
        progress = tag.getInt("progress");
    }
}
