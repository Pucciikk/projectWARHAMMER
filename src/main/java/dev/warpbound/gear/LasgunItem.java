package dev.warpbound.gear;

import dev.warpbound.core.WarpboundItems;
import dev.warpbound.network.LasBeamPayload;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerPlayer;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.animatable.client.GeoRenderProvider;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.function.Consumer;

/**
 * Лазган: луч мгновенно бьёт по линии взгляда; клиенты рисуют тонкий жёлтый луч (LasBeamPayload). Рука не машет,
 * смена заряда не дёргает оружие. Заряд — прочность предмета (выстрелов в лазпакете). Модель — GeckoLib (lasgun_3d).
 * Пустой лазган (или Shift + ПКМ) берёт лазпакет из инвентаря и отдаёт разряженный — его можно подзарядить в костре
 * (аварийная зарядка из лора). Временная система до общего каркаса оружия с параметрами в JSON.
 */
public class LasgunItem extends Item implements GeoItem {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private static final double RANGE = 48;
    private static final float DAMAGE = 6f;
    private static final int COOLDOWN = 6;

    public LasgunItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack gun = player.getItemInHand(hand);
        boolean empty = gun.getDamageValue() >= gun.getMaxDamage() - 1;
        if (player.isShiftKeyDown() || empty) {
            if (gun.getDamageValue() > 0 && reload(level, player, gun)) {
                player.getCooldowns().addCooldown(this, 30);
                return InteractionResultHolder.consume(gun);
            }
            if (empty) {
                level.playSound(null, player.blockPosition(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.6f, 1.6f);
                if (!level.isClientSide) {
                    player.displayClientMessage(Component.translatable("item.warpbound.lasgun.empty").withStyle(ChatFormatting.RED), true);
                }
                return InteractionResultHolder.fail(gun);
            }
        }
        player.getCooldowns().addCooldown(this, COOLDOWN);
        if (level instanceof ServerLevel sl) {
            fire(sl, player);
            gun.setDamageValue(gun.getDamageValue() + 1);
        }
        return InteractionResultHolder.consume(gun);
    }

    private static void fire(ServerLevel level, Player player) {
        Vec3 eye = player.getEyePosition();
        Vec3 look = player.getLookAngle();
        Vec3 far = eye.add(look.scale(RANGE));
        BlockHitResult block = level.clip(new ClipContext(eye, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
        Vec3 end = block.getType() == HitResult.Type.MISS ? far : block.getLocation();
        EntityHitResult hit = ProjectileUtil.getEntityHitResult(level, player, eye, end,
                new AABB(eye, end).inflate(1), e -> e instanceof LivingEntity && e.isAlive() && !e.isSpectator(), 0.3f);
        if (hit != null) {
            end = hit.getLocation();
            Entity target = hit.getEntity();
            target.hurt(level.damageSources().playerAttack(player), DAMAGE);
            target.igniteForSeconds(0.5f);
        }
        // луч рисуют клиенты: от ствола в руках стрелка до точки попадания
        LasBeamPayload beam = new LasBeamPayload(player.getId(), end.x, end.y, end.z);
        for (ServerPlayer viewer : PlayerLookup.tracking(player)) ServerPlayNetworking.send(viewer, beam);
        if (player instanceof ServerPlayer self) ServerPlayNetworking.send(self, beam);
        level.sendParticles(net.minecraft.core.particles.ParticleTypes.SMALL_FLAME, end.x, end.y, end.z, 3, 0.04, 0.04, 0.04, 0.01);
        level.playSound(null, player.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.PLAYERS, 0.5f, 1.9f);
    }

    private static boolean reload(Level level, Player player, ItemStack gun) {
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(WarpboundItems.LAS_BATTERY)) {
                if (!level.isClientSide) {
                    s.shrink(1);
                    gun.setDamageValue(0);
                    ItemStack spent = new ItemStack(WarpboundItems.LAS_BATTERY_DEPLETED);
                    if (!inv.add(spent)) player.drop(spent, false);
                }
                level.playSound(null, player.blockPosition(), SoundEvents.IRON_TRAPDOOR_CLOSE, SoundSource.PLAYERS, 0.7f, 1.4f);
                return true;
            }
        }
        return false;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        int left = stack.getMaxDamage() - 1 - stack.getDamageValue();
        tooltip.add(Component.translatable("item.warpbound.lasgun.charge", Math.max(0, left)).withStyle(ChatFormatting.GOLD));
        tooltip.add(Component.translatable("item.warpbound.lasgun.tooltip").withStyle(ChatFormatting.GRAY));
    }

    @Override
    public boolean isValidRepairItem(ItemStack stack, ItemStack repair) {
        return false;
    }

    /** Смена заряда (прочности) не перезапускает анимацию «поднять предмет». */
    @Override
    public boolean allowComponentsUpdateAnimation(Player player, InteractionHand hand, ItemStack oldStack, ItemStack newStack) {
        return false;
    }

    @Override
    public void createGeoRenderer(Consumer<GeoRenderProvider> consumer) {
        GeoGear.RENDER.accept(this, consumer);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
