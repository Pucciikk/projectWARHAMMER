package dev.warpbound.industry.machine;

import net.fabricmc.fabric.api.transfer.v1.item.ItemStorage;
import net.fabricmc.fabric.api.transfer.v1.item.ItemVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.FilteringStorage;
import net.fabricmc.fabric.api.transfer.v1.storage.base.SingleVariantStorage;
import net.fabricmc.fabric.api.transfer.v1.transaction.Transaction;
import dev.warpbound.multiblock.MachinePartBlock;
import dev.warpbound.multiblock.MultiblockCoreBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.Containers;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.List;

/**
 * Лента: приёмный буфер на входе и до четырёх пачек на ленте. Пачка едет от 0 до 1 и отдаётся вперёд; пока вперёд нельзя, стоит и подпирает остальных.
 * Пустая лента в тике сразу выходит, так что простой ничего не стоит.
 */
public class ConveyorBlockEntity extends BlockEntity {
    private static final float SPEED = 0.05f;
    private static final float GAP = 0.25f;
    private static final int BATCH = 8;
    /** Насколько предмет заезжает в люк машины за границу блока: совпадает с глубиной короба в PortRenderer. */
    private static final float INTO_HATCH = 0.42f;

    /** Пачка на ленте. */
    public static final class Batch {
        public final ItemStack stack;
        public float at;

        Batch(ItemStack stack, float at) {
            this.stack = stack;
            this.at = at;
        }
    }

    private final SingleVariantStorage<ItemVariant> inbox = new SingleVariantStorage<>() {
        @Override
        protected ItemVariant getBlankVariant() {
            return ItemVariant.blank();
        }

        @Override
        protected long getCapacity(ItemVariant variant) {
            return Math.min(BATCH, variant.getItem().getDefaultMaxStackSize());
        }

        @Override
        protected void onFinalCommit() {
            setChanged();
        }
    };
    private final Storage<ItemVariant> port = FilteringStorage.insertOnlyOf(inbox);
    private final List<Batch> batches = new ArrayList<>();

    public ConveyorBlockEntity(BlockPos pos, BlockState state) {
        super(FluidHolders.CONVEYOR, pos, state);
    }

    public List<Batch> batches() {
        return batches;
    }

    private boolean machineAt(Direction direction) {
        if (level == null) return false;
        var block = level.getBlockState(worldPosition.relative(direction)).getBlock();
        return block instanceof MachinePartBlock || block instanceof MultiblockCoreBlock;
    }

    /** Докуда едет предмет: у машины дальше границы блока, в её люк. */
    public float endAt() {
        return machineAt(getBlockState().getValue(ConveyorBlock.FACING)) ? 1 + INTO_HATCH : 1;
    }

    /** Откуда появляется предмет: из люка машины, если она стоит сзади. */
    private float startAt() {
        return machineAt(getBlockState().getValue(ConveyorBlock.FACING).getOpposite()) ? -INTO_HATCH : 0;
    }

    /** Принимает сзади, сбоку и сверху; спереди — выход. */
    public Storage<ItemVariant> port(Direction side) {
        return side == getBlockState().getValue(ConveyorBlock.FACING) ? null : port;
    }

    public static void clientTick(Level level, BlockPos pos, BlockState state, ConveyorBlockEntity be) {
        be.advance();
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, ConveyorBlockEntity be) {
        if (be.batches.isEmpty() && be.inbox.isResourceBlank()) return;
        boolean changed = false;
        if (!be.inbox.isResourceBlank() && (be.batches.isEmpty() || be.batches.get(be.batches.size() - 1).at >= be.startAt() + GAP)) {
            be.batches.add(new Batch(be.inbox.getResource().toStack((int) be.inbox.getAmount()), be.startAt()));
            be.inbox.variant = ItemVariant.blank();
            be.inbox.amount = 0;
            changed = true;
        }
        be.advance();
        if (!be.batches.isEmpty() && be.batches.get(0).at >= be.endAt()) changed |= be.deliver(level, pos, state);
        if (changed) {
            be.setChanged();
            level.sendBlockUpdated(pos, state, state, 3);
        } else if (!be.batches.isEmpty()) {
            be.setChanged();
        }
    }

    private void advance() {
        if (batches.isEmpty()) return;
        float limit = endAt();
        for (Batch b : batches) {
            b.at = Math.min(limit, b.at + SPEED);
            limit = b.at - GAP;
        }
    }

    private boolean deliver(Level level, BlockPos pos, BlockState state) {
        Direction facing = state.getValue(ConveyorBlock.FACING);
        Storage<ItemVariant> next = ItemStorage.SIDED.find(level, pos.relative(facing), facing.getOpposite());
        if (next == null) return false;
        Batch first = batches.get(0);
        long moved;
        try (Transaction tx = Transaction.openOuter()) {
            moved = next.insert(ItemVariant.of(first.stack), first.stack.getCount(), tx);
            tx.commit();
        }
        if (moved <= 0) return false;
        first.stack.shrink((int) moved);
        if (first.stack.isEmpty()) batches.remove(0);
        return true;
    }

    /** Лента сломана: всё едущее падает. */
    void dropAll() {
        if (level == null) return;
        for (Batch b : batches) Containers.dropItemStack(level, worldPosition.getX() + 0.5, worldPosition.getY() + 0.5, worldPosition.getZ() + 0.5, b.stack);
        if (!inbox.isResourceBlank()) {
            Containers.dropItemStack(level, worldPosition.getX() + 0.5, worldPosition.getY() + 0.5, worldPosition.getZ() + 0.5,
                    inbox.getResource().toStack((int) inbox.getAmount()));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        write(tag, registries);
        SingleVariantStorage.writeNbt(inbox, ItemVariant.CODEC, tag, registries);
    }

    private void write(CompoundTag tag, HolderLookup.Provider registries) {
        ListTag list = new ListTag();
        for (Batch b : batches) {
            CompoundTag c = new CompoundTag();
            c.put("item", b.stack.save(registries));
            c.putFloat("at", b.at);
            list.add(c);
        }
        tag.put("batches", list);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        batches.clear();
        for (Tag t : tag.getList("batches", Tag.TAG_COMPOUND)) {
            CompoundTag c = (CompoundTag) t;
            ItemStack.parse(registries, c.getCompound("item")).ifPresent(s -> batches.add(new Batch(s, c.getFloat("at"))));
        }
        if (tag.contains("variant")) SingleVariantStorage.readNbt(inbox, ItemVariant.CODEC, ItemVariant::blank, tag, registries);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        write(tag, registries);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
