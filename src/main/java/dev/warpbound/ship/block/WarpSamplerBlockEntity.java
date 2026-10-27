package dev.warpbound.ship.block;

import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.core.WarpboundSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Варп-пробоотборник: цикл повторяет анимацию misc.sample (tools/models/gen_machines.py, warp_sampler).
 * Рука берёт пустую колбу (2.5 с), вставляет в порт (6 с), 20 с порт пьёт варп, на 30-й секунде колба с красной
 * материей встаёт на подставку — тогда образец и выдаётся.
 */
public class WarpSamplerBlockEntity extends BlockEntity implements GeoBlockEntity {
    public static final int CYCLE = 33 * 20;
    private static final int PORT_OPEN = 6 * 20, PORT_CLOSE = 26 * 20, DELIVER = 30 * 20 + 2;
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation SAMPLE = RawAnimation.begin().thenPlay("misc.sample");
    /** Порт в стене модели: пиксели модели от центра низа блока (x вправо, y вверх, z — к стене). */
    private static final Vec3 PORT = new Vec3(0, 36, 2);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int progress = -1;
    private UUID owner;
    private boolean warp;

    public WarpSamplerBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.WARP_SAMPLER, pos, state);
    }

    public boolean busy() {
        return progress >= 0;
    }

    public int secondsLeft() {
        return busy() ? (CYCLE - progress + 19) / 20 : 0;
    }

    /** Запуск цикла. warp — корабль в варпе: колба вернётся с варп-материей, иначе пустой. */
    public void start(ServerPlayer player, boolean warp) {
        progress = 0;
        owner = player.getUUID();
        this.warp = warp;
        setChanged();
        triggerAnim("main", "sample");
        level.playSound(null, BlockPos.containing(worldPos(new Vec3(16, 24, -12))), SoundEvents.PISTON_EXTEND, SoundSource.BLOCKS, 0.6f, 0.7f);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, WarpSamplerBlockEntity be) {
        if (be.progress < 0 || !(level instanceof ServerLevel sl)) return;
        int t = ++be.progress;
        Vec3 port = be.worldPos(PORT);
        if (t == 30 || t == PORT_OPEN - 20 || t == PORT_CLOSE + 10 || t == 29 * 20) {
            sl.playSound(null, BlockPos.containing(port), SoundEvents.PISTON_CONTRACT, SoundSource.BLOCKS, 0.5f, 1.4f);
        }
        if (t == PORT_OPEN) {
            sl.playSound(null, BlockPos.containing(port), SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 0.6f);
        }
        if (t > PORT_OPEN && t < PORT_CLOSE) {
            if (t % 4 == 0) {
                DustParticleOptions dust = new DustParticleOptions(new Vector3f(0.9f, 0.08f, 0.1f), 1.2f);
                sl.sendParticles(dust, port.x, port.y, port.z, 3, 0.18, 0.18, 0.18, 0.0);
            }
            if (t % 40 == 0) {
                sl.sendParticles(ParticleTypes.PORTAL, port.x, port.y, port.z, 12, 0.2, 0.2, 0.2, 0.4);
            }
            if (be.warp && t % 120 == 60) {
                sl.playSound(null, BlockPos.containing(port), WarpboundSounds.WARP_WHISPER, SoundSource.BLOCKS, 0.5f, 0.8f);
            }
        }
        if (t == PORT_CLOSE) {
            sl.playSound(null, BlockPos.containing(port), SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 0.8f, 0.6f);
        }
        if (t == DELIVER) be.deliver(sl);
        if (t >= CYCLE) {
            be.progress = -1;
            be.owner = null;
        }
        if (t % 20 == 0) be.setChanged();
    }

    private void deliver(ServerLevel sl) {
        ItemStack out = new ItemStack(warp ? WarpboundItems.WARP_SAMPLE : WarpboundItems.SAMPLE_VIAL);
        ServerPlayer player = owner == null ? null : sl.getServer().getPlayerList().getPlayer(owner);
        Vec3 front = worldPos(new Vec3(-12, 24, -26));
        boolean near = player != null && player.level() == sl && player.position().closerThan(front, 12);
        if (near) {
            if (!player.getInventory().add(out)) player.drop(out, false);
            player.displayClientMessage(Component.translatable(warp ? "lab.warpbound.done" : "lab.warpbound.empty")
                    .withStyle(warp ? ChatFormatting.DARK_RED : ChatFormatting.GRAY), false);
        } else {
            sl.addFreshEntity(new ItemEntity(sl, front.x, front.y, front.z, out));
        }
        sl.playSound(null, BlockPos.containing(front), warp ? WarpboundSounds.WARP_WHISPER : SoundEvents.GLASS_HIT,
                SoundSource.BLOCKS, 0.8f, 1.2f);
    }

    /** Точка модели (пиксели) → мир, с учётом поворота станции: перед модели (−Z) смотрит в facing. */
    private Vec3 worldPos(Vec3 model) {
        Direction facing = getBlockState().getValue(WarpSamplerBlock.FACING);
        Direction right = facing.getClockWise();
        Vec3 c = Vec3.atBottomCenterOf(worldPosition);
        return c.add(right.getStepX() * model.x / 16, model.y / 16, right.getStepZ() * model.x / 16)
                .add(facing.getStepX() * -model.z / 16, 0, facing.getStepZ() * -model.z / 16);
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("progress", progress);
        tag.putBoolean("warp", warp);
        if (owner != null) tag.putUUID("owner", owner);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        progress = tag.contains("progress") ? tag.getInt("progress") : -1;
        warp = tag.getBoolean("warp");
        owner = tag.hasUUID("owner") ? tag.getUUID("owner") : null;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 0, state -> state.setAndContinue(IDLE))
                .triggerableAnim("sample", SAMPLE));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
