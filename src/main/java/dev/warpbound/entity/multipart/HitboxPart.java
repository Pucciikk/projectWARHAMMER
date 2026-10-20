package dev.warpbound.entity.multipart;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerEntity;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * Один хитбокс многосоставной сущности. Свой ID у части есть (его шлёт клиент при ударе),
 * но в мир она не добавляется и не сохраняется: позицию каждый тик ставит хозяин.
 */
public class HitboxPart extends Entity {
    public final Entity host;
    public final Spec spec;
    private final EntityDimensions size;

    /**
     * Где часть сидит относительно хозяина, в блоках.
     * torsoFrame: крутится вместе с корпусом (а не с ногами).
     * armor: множитель входящего урона; больше 1 — уязвимое место.
     */
    public record Spec(String name, boolean torsoFrame, float right, float up, float forward,
                       float width, float height, float armor) {
    }

    public <T extends Entity & MultipartHost> HitboxPart(T host, Spec spec) {
        super(host.getType(), host.level());
        this.host = host;
        this.spec = spec;
        this.size = EntityDimensions.scalable(spec.width(), spec.height());
        this.refreshDimensions();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    @Nullable
    @Override
    public ItemStack getPickResult() {
        return host.getPickResult();
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (this.isInvulnerableTo(source)) {
            return false;
        }
        return ((MultipartHost) host).hurtFromPart(this, source, amount * spec.armor());
    }

    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        return host.interact(player, hand);
    }

    @Override
    public boolean is(Entity entity) {
        return this == entity || host == entity;
    }

    @Override
    public Packet<ClientGamePacketListener> getAddEntityPacket(ServerEntity entity) {
        throw new UnsupportedOperationException("Часть хитбокса не спавнится отдельно");
    }

    @Override
    public EntityDimensions getDimensions(Pose pose) {
        return size;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }
}
