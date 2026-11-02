package dev.warpbound.industry.machine;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import org.jetbrains.annotations.Nullable;

/**
 * Что видно в окошках трубы: какая жидкость прошла последней, откуда и до какого тика она течёт. Без тика:
 * отметку ставит машина при передаче, а клиенту пакет уходит только при смене жидкости или продлении потока.
 */
public class FluidPipeBlockEntity extends BlockEntity {
    /** Поток виден ещё столько тиков после передачи: передача идёт раз в 10 тиков. */
    private static final int FLOW_TICKS = 30;
    /** Как часто продлевать поток на клиенте: окошко не мигает, а пакетов мало. */
    private static final int RESEND = 20;

    private Fluid fluid = Fluids.EMPTY;
    @Nullable
    private Direction from;
    private long flowUntil;
    private long lastSent = Long.MIN_VALUE / 2;

    public FluidPipeBlockEntity(BlockPos pos, BlockState state) {
        super(FluidHolders.PIPE, pos, state);
    }

    public Fluid fluid() {
        return fluid;
    }

    /** Сторона, с которой жидкость входит в этот кусок трубы. */
    @Nullable
    public Direction from() {
        return from;
    }

    public boolean flowing(long gameTime) {
        return gameTime < flowUntil;
    }

    void mark(Fluid moved, Direction fromSide, long now) {
        boolean changed = moved != fluid || fromSide != from;
        fluid = moved;
        from = fromSide;
        flowUntil = now + FLOW_TICKS;
        setChanged();
        if (changed || now - lastSent >= RESEND) {
            lastSent = now;
            if (level != null) level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 2);
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        write(tag);
    }

    private void write(CompoundTag tag) {
        tag.putString("fluid", BuiltInRegistries.FLUID.getKey(fluid).toString());
        tag.putInt("from", from == null ? -1 : from.get3DDataValue());
        tag.putLong("until", flowUntil);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("fluid")) {
            fluid = BuiltInRegistries.FLUID.get(net.minecraft.resources.ResourceLocation.parse(tag.getString("fluid")));
        }
        int f = tag.getInt("from");
        from = f < 0 ? null : Direction.from3DDataValue(f);
        flowUntil = tag.getLong("until");
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        write(tag);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
