package dev.warpbound.gun;

import dev.warpbound.core.WarpboundItems;
import dev.warpbound.core.WarpboundSounds;
import dev.warpbound.network.GunActionPayload;
import dev.warpbound.network.GunFxPayload;
import dev.warpbound.network.GunSpecSyncPayload;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Серверная сторона оружия: проверяет темп и патроны, создаёт снаряд, завершает перезарядку.
 * Клиент показывает выстрел сразу, не дожидаясь ответа, а сервер решает, что произошло на самом деле.
 */
public final class GunServer {
    private static final class State {
        long lastShot = -1000;
        int reloadEnd = -1;
        int reloadSlot;
    }

    /** Косинус допуска между взглядом на сервере и направлением выстрела: около 15°, больше не набегает даже с отдачей и задержкой. */
    private static final double AIM_TOLERANCE = 0.966;
    private static final Map<UUID, State> STATES = new HashMap<>();

    private GunServer() {
    }

    public static void register() {
        // первое обращение регистрирует типы снарядов и читает data/gun: это нужно до заморозки реестров
        GunProjectiles.LAS_BOLT.getClass();
        GunSpec.REGISTRY.getClass();
        ServerPlayNetworking.registerGlobalReceiver(GunActionPayload.TYPE, (payload, context) -> {
            ServerPlayer player = context.player();
            context.server().execute(() -> {
                if (payload.action() == GunActionPayload.FIRE) fire(player, payload.aiming(), new Vec3(payload.x(), payload.y(), payload.z()));
                else if (payload.action() == GunActionPayload.RELOAD) startReload(player);
            });
        });
        // клиенту нужны скорость и разброс, чтобы показать снаряд сразу: сам он датапак не читает
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sender.sendPacket(new GunSpecSyncPayload(GunSpec.REGISTRY.all())));
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.END_DATA_PACK_RELOAD.register((server, resources, ok) -> {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) ServerPlayNetworking.send(p, new GunSpecSyncPayload(GunSpec.REGISTRY.all()));
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> STATES.remove(handler.player.getUUID()));
        ServerTickEvents.END_SERVER_TICK.register(GunServer::tick);
    }

    private static State state(ServerPlayer player) {
        return STATES.computeIfAbsent(player.getUUID(), id -> new State());
    }

    private static void tick(MinecraftServer server) {
        if (STATES.isEmpty()) return;
        int now = server.getTickCount();
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            State s = STATES.get(player.getUUID());
            if (s == null || s.reloadEnd < 0) continue;
            // сменил оружие — перезарядка сорвалась
            if (player.getInventory().selected != s.reloadSlot || !(player.getMainHandItem().getItem() instanceof GunItem)) {
                s.reloadEnd = -1;
                continue;
            }
            if (now >= s.reloadEnd) {
                s.reloadEnd = -1;
                finishReload(player);
            }
        }
    }

    private static void fire(ServerPlayer player, boolean aiming, Vec3 wanted) {
        ItemStack stack = player.getItemInHand(InteractionHand.MAIN_HAND);
        if (!(stack.getItem() instanceof GunItem gun)) return;
        State s = state(player);
        long now = player.serverLevel().getGameTime();
        // допуск в тик: клиент считает темп по своим тикам, пакет может прийти чуть раньше
        if (s.reloadEnd >= 0 || now - s.lastShot < gun.mechanics.interval() - 1) return;
        int ammo = GunItem.ammo(stack);
        if (ammo <= 0) return;
        s.lastShot = now;
        GunItem.setAmmo(stack, ammo - 1);
        GunSpec spec = GunSpec.of(gun);
        spawn(player, gun, spec, aiming, wanted);
        SoundEvent sound = gun.mechanics.kind() == GunItem.Kind.LAS ? WarpboundSounds.GUN_LAS_FIRE : WarpboundSounds.GUN_BOLTER_FIRE;
        // стрелку звук уже сыграл его клиент, остальным — отсюда
        player.serverLevel().playSound(player, player.getX(), player.getEyeY(), player.getZ(), sound, SoundSource.PLAYERS,
                gun.mechanics.kind() == GunItem.Kind.LAS ? 1.2f : 2.2f, 0.96f + player.getRandom().nextFloat() * 0.08f);
        GunFxPayload fx = new GunFxPayload(player.getId(), gun.mechanics.kind().ordinal());
        for (ServerPlayer viewer : PlayerLookup.tracking(player)) {
            if (viewer != player) ServerPlayNetworking.send(viewer, fx);
        }
    }

    /**
     * Снаряд вылетает из дула и летит в точку, которая стоит под прицелом: луч от глаз находит её, снаряд идёт туда.
     * Так видно, что стреляет оружие, а попадает он всё равно куда смотрит игрок.
     */
    public static GunProjectile spawn(ServerPlayer player, GunItem gun, GunSpec spec, boolean aiming, Vec3 wanted) {
        ServerLevel level = player.serverLevel();
        GunProjectile p = gun.mechanics.kind() == GunItem.Kind.LAS ? GunProjectiles.LAS_BOLT.create(level) : GunProjectiles.BOLT_ROUND.create(level);
        p.setOwner(player);
        p.configure(spec);
        Vec3 look = player.getLookAngle();
        Vec3 eye = player.getEyePosition();
        Vec3 worldUp = Math.abs(look.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
        Vec3 right = look.cross(worldUp).normalize();
        Vec3 up = right.cross(look).normalize();
        // направление считает клиент (там же разброс), сервер только не даёт уйти далеко от взгляда
        double wantedLen = wanted.length();
        Vec3 aimDir = wantedLen > 0.5 && wanted.scale(1 / wantedLen).dot(look) > AIM_TOLERANCE ? wanted.scale(1 / wantedLen) : look;

        // куда смотрит прицел: блок, существо или просто даль
        Vec3 far = eye.add(aimDir.scale(spec.speed() * spec.lifeTicks()));
        var block = level.clip(new ClipContext(eye, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
        Vec3 target = block.getType() == HitResult.Type.MISS ? far : block.getLocation();
        var entity = ProjectileUtil.getEntityHitResult(level, player, eye, target, new AABB(eye, target).inflate(1),
                e -> e != player && e.isAlive() && e.isPickable() && !e.isSpectator(), 0.2f);
        if (entity != null) target = entity.getLocation();

        // дуло: сбоку и ниже глаз, при прицеливании ствол на линии взгляда
        Vec3 muzzle = eye.add(look.scale(0.95)).add(right.scale(aiming ? 0.0 : 0.22)).add(up.scale(aiming ? -0.08 : -0.2));
        // ствол упёрся в стену: выстрел не должен пройти сквозь неё
        if (level.clip(new ClipContext(eye, muzzle, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player)).getType() != HitResult.Type.MISS) muzzle = eye;
        Vec3 dir = target.subtract(muzzle);
        dir = dir.lengthSqr() < 0.04 ? aimDir : dir.normalize();
        p.setPos(muzzle.x, muzzle.y, muzzle.z);
        p.setDeltaMovement(dir.scale(spec.muzzleSpeed()));
        p.setYRot((float) (Mth.atan2(dir.x, dir.z) * Mth.RAD_TO_DEG));
        p.setXRot((float) (Mth.atan2(dir.y, dir.horizontalDistance()) * Mth.RAD_TO_DEG));
        p.yRotO = p.getYRot();
        p.xRotO = p.getXRot();
        level.addFreshEntity(p);
        return p;
    }

    private static void startReload(ServerPlayer player) {
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof GunItem gun)) return;
        State s = state(player);
        if (s.reloadEnd >= 0 || GunItem.ammo(stack) >= gun.mechanics.magSize()) return;
        if (!hasAmmo(player, gun)) return;
        s.reloadEnd = player.server.getTickCount() + gun.mechanics.reloadTicks();
        s.reloadSlot = player.getInventory().selected;
    }

    public static boolean hasAmmo(ServerPlayer player, GunItem gun) {
        return player.getAbilities().instabuild || player.getInventory().contains(new ItemStack(gun.ammoItem()));
    }

    private static void finishReload(ServerPlayer player) {
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof GunItem gun)) return;
        Inventory inv = player.getInventory();
        if (!player.getAbilities().instabuild) {
            int slot = -1;
            for (int i = 0; i < inv.getContainerSize(); i++) {
                if (inv.getItem(i).is(gun.ammoItem())) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) return;
            inv.getItem(slot).shrink(1);
            returnLeftover(player, gun, GunItem.ammo(stack));
        }
        GunItem.setAmmo(stack, gun.mechanics.magSize());
    }

    /** Что остаётся от старого магазина: разряженный лазпакет (его можно зарядить в костре) или оставшиеся болты. */
    private static void returnLeftover(ServerPlayer player, GunItem gun, int left) {
        ItemStack back = ItemStack.EMPTY;
        if (gun.mechanics.kind() == GunItem.Kind.LAS) {
            back = new ItemStack(WarpboundItems.LAS_BATTERY_DEPLETED);
        } else if (left > 0) {
            back = new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(GunItem.id("bolt_round")), left);
        }
        if (!back.isEmpty() && !player.getInventory().add(back)) player.drop(back, false);
    }
}
