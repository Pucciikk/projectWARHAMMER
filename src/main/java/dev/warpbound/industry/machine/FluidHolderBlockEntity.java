package dev.warpbound.industry.machine;

import net.fabricmc.fabric.api.transfer.v1.fluid.FluidConstants;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.FilteringStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.SingleVariantStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import java.util.List;

/**
 * Бак: принимает с боков и сверху, отдаёт вниз (по трубе снизу или напрямую в машину). Одна жидкость.
 * Горелка: принимает всё и сжигает 1 ведро в секунду; пока горит, на клиенте огонь.
 */
public class FluidHolderBlockEntity extends BlockEntity {
    private static final long TANK = FluidConstants.BUCKET * 64;
    private static final long FLARE = FluidConstants.BUCKET * 4;
    private static final long BURN_PER_TICK = FluidConstants.BUCKET / 20;
    private static final long PUSH = FluidConstants.BUCKET * 2;

    private final SingleVariantStorage<FluidVariant> store = new SingleVariantStorage<>() {
        @Override
        protected FluidVariant getBlankVariant() {
            return FluidVariant.blank();
        }

        @Override
        protected long getCapacity(FluidVariant variant) {
            return isFlare() ? FLARE : TANK;
        }

        @Override
        protected void onFinalCommit() {
            setChanged();
        }
    };
    private final Storage<FluidVariant> inPort = FilteringStorage.insertOnlyOf(store);
    private final Storage<FluidVariant> outPort = FilteringStorage.extractOnlyOf(store);
    private List<Conduits.Target> targets = List.of();
    private long generation = -1;
    private boolean burning;

    public FluidHolderBlockEntity(BlockPos pos, BlockState state) {
        super(FluidHolders.TYPE, pos, state);
    }

    private boolean isFlare() {
        return getBlockState().getBlock() instanceof FluidHolderBlock b && b.flare();
    }

    public boolean burning() {
        return burning;
    }

    public Storage<FluidVariant> port(Direction side) {
        if (isFlare()) return inPort;
        return side == Direction.DOWN ? outPort : inPort;
    }

    public long droplets() {
        return store.getAmount();
    }

    public MutableComponent describe() {
        if (store.isResourceBlank()) return Component.translatable("gui.warpbound.machine.empty");
        var key = BuiltInRegistries.FLUID.getKey(store.getResource().getFluid());
        Component name = key.getNamespace().equals("minecraft") ? Component.translatable("block.minecraft." + key.getPath())
                : Component.translatable("fluid.warpbound." + key.getPath());
        return Component.empty().append(name).append(" ").append(Component.translatable("gui.warpbound.machine.mb", store.getAmount() / (FluidConstants.BUCKET / 1000)));
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, FluidHolderBlockEntity be) {
        if (!(level instanceof ServerLevel server)) return;
        if (be.isFlare()) {
            boolean now = be.store.getAmount() > 0;
            if (now) {
                be.store.amount = Math.max(0, be.store.amount - BURN_PER_TICK);
                if (be.store.amount == 0) be.store.variant = FluidVariant.blank();
                be.setChanged();
            }
            if (now != be.burning) {
                be.burning = now;
                level.sendBlockUpdated(pos, state, state, 3);
            }
            return;
        }
        if ((level.getGameTime() + pos.asLong()) % Conduits.PERIOD != 0 || be.store.isResourceBlank()) return;
        long gen = Conduits.generation(level);
        if (gen != be.generation) {
            be.generation = gen;
            be.targets = Conduits.targets(server, pos, Direction.DOWN, MachineSpec.Kind.FLUID);
        }
        Conduits.push(server, be.outPort, be.targets, MachineSpec.Kind.FLUID, PUSH);
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        SingleVariantStorage.writeNbt(store, FluidVariant.CODEC, tag, registries);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        SingleVariantStorage.readNbt(store, FluidVariant.CODEC, FluidVariant::blank, tag, registries);
        burning = tag.getBoolean("burning");
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        tag.putBoolean("burning", burning);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
