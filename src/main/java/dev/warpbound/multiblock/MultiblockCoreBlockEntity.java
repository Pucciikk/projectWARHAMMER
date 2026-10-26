package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

import java.util.List;

/**
 * Ядро мультиблока для машин, которым не нужен другой базовый класс (верфь, пресс, Кузня).
 * Вся логика — в {@link MultiblockController}; конкретные машины переопределяют хуки {@link MultiblockHost}.
 */
public class MultiblockCoreBlockEntity extends BlockEntity implements MultiblockHost {
    private final MultiblockController multiblock;

    public MultiblockCoreBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state, ResourceLocation definitionId) {
        super(type, pos, state);
        this.multiblock = new MultiblockController(this, definitionId);
    }

    @Override
    public MultiblockController multiblock() {
        return multiblock;
    }

    public MultiblockOrientation orientation() {
        return multiblock.orientation();
    }

    public List<BlockPos> members() {
        return multiblock.members();
    }

    public ResourceLocation definitionId() {
        return multiblock.definitionId();
    }

    public void tryForm(ServerPlayer player) {
        multiblock.tryForm(player);
    }

    public void unform(ServerPlayer player) {
        multiblock.unform(player);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, MultiblockCoreBlockEntity be) {
        if (level instanceof ServerLevel server) be.multiblock.serverTick(server);
    }

    protected void sync() {
        multiblock.sync();
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        multiblock.save(tag);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        multiblock.load(tag);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        multiblock.writeUpdateTag(tag);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
