package dev.warpbound.multiblock;

import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Память части машины: какой блок стоял здесь до освящения и чьё это ядро. */
public class MachinePartBlockEntity extends BlockEntity {
    private BlockState original = Blocks.AIR.defaultBlockState();
    private BlockPos core;

    public MachinePartBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.MACHINE_PART, pos, state);
    }

    void bind(BlockState original, BlockPos core) {
        this.original = original;
        this.core = core.immutable();
        setChanged();
        if (level != null) level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
    }

    /** Отвязать перед возвратом блока — чтобы onRemove не разбирал машину второй раз. */
    void release() {
        core = null;
    }

    public boolean bound() {
        return core != null;
    }

    public BlockPos core() {
        return core;
    }

    public BlockState original() {
        return original;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("original", NbtUtils.writeBlockState(original));
        if (core != null) tag.putLong("core", core.asLong());
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("original")) {
            original = NbtUtils.readBlockState(registries.lookupOrThrow(Registries.BLOCK), tag.getCompound("original"));
        }
        core = tag.contains("core") ? BlockPos.of(tag.getLong("core")) : null;
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        // клиенту нужно ядро — чтобы ПКМ по части открывала машину и на клиенте
        CompoundTag tag = new CompoundTag();
        if (core != null) tag.putLong("core", core.asLong());
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
