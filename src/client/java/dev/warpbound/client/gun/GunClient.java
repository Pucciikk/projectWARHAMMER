package dev.warpbound.client.gun;

import com.mojang.blaze3d.platform.InputConstants;
import dev.warpbound.Warpbound;
import dev.warpbound.gun.GunItem;
import dev.warpbound.network.GunActionPayload;
import dev.warpbound.network.GunFxPayload;
import dev.warpbound.network.GunHitPayload;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.event.client.player.ClientPreAttackCallback;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.lwjgl.glfw.GLFW;

/**
 * Состояние оружия на клиенте: что в руках, идёт ли перезарядка, сколько до следующего выстрела.
 * Выстрел показывается сразу, ответа сервера не ждёт: задержка на спуске убивает ощущение от стрельбы.
 */
public final class GunClient {
    private static final ResourceLocation AIM_SLOW = Warpbound.id("gun_aim_slow");
    public static final KeyMapping RELOAD = KeyBindingHelper.registerKeyBinding(new KeyMapping("key.warpbound.reload", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, "key.categories.warpbound"));

    private static GunItem held;
    private static int heldSlot = -1;
    /** Время в тиках игры, когда началось действие; меньше нуля — не идёт. */
    private static double equipAt = -1, reloadAt = -1, fireAt = -1;
    private static int eventCursor;
    private static long nextShot;
    /** Выстрелы, о которых сервер ещё не отчитался: счётчик на экране должен падать сразу. */
    private static int pending, lastSeenAmmo;
    private static boolean aimKey;
    private static boolean wasFiring;
    static float aim, sprint;
    static double hitAt = -100;
    static boolean hitKilled, hitHead;
    /** Разброс прицела от стрельбы, 0..1: прицел расходится и сходится обратно. */
    static float bloom;
    // ---- команды автотеста
    private static int autoShots;
    private static boolean autoAim;

    private GunClient() {
    }

    public static void register() {
        ClientPreAttackCallback.EVENT.register((client, player, clicks) -> player.getMainHandItem().getItem() instanceof GunItem);
        ClientTickEvents.END_CLIENT_TICK.register(GunClient::tick);
        ClientPlayNetworking.registerGlobalReceiver(GunHitPayload.TYPE, (payload, context) -> {
            Minecraft mc = context.client();
            if (mc.level == null) return;
            hitAt = now(mc);
            hitKilled = payload.killed();
            hitHead = payload.head();
            playLocal(GunClips.sound("hit_marker"), payload.killed() ? 0.9f : 0.6f, payload.head() ? 1.4f : 1.0f);
        });
        ClientPlayNetworking.registerGlobalReceiver(GunFxPayload.TYPE, (payload, context) -> {
            Minecraft mc = context.client();
            if (mc.level == null) return;
            Entity shooter = mc.level.getEntity(payload.shooter());
            if (shooter == null) return;
            Vec3 m = GunView.approxMuzzle(shooter, 1f);
            mc.level.addParticle(ParticleTypes.SMOKE, m.x, m.y, m.z, 0, 0.02, 0);
            mc.level.addParticle(ParticleTypes.FLAME, m.x, m.y, m.z, 0, 0, 0);
        });
    }

    static double now(Minecraft mc) {
        return mc.level == null ? 0 : mc.level.getGameTime() + mc.getTimer().getGameTimeDeltaPartialTick(true);
    }

    static GunItem held() {
        return held;
    }

    private static void playLocal(SoundEvent sound, float volume, float pitch) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.level != null) {
            mc.level.playLocalSound(mc.player.getX(), mc.player.getEyeY(), mc.player.getZ(), sound, SoundSource.PLAYERS, volume, pitch, false);
        }
    }

    public static boolean holdingGun() {
        return held != null;
    }

    static int shownAmmo(ItemStack stack) {
        return Math.max(0, GunItem.ammo(stack) - pending);
    }

    static boolean reloading() {
        return reloadAt >= 0;
    }

    static float reloadProgress(Minecraft mc, GunItem gun) {
        return reloadAt < 0 ? 0 : (float) Math.min(1, (now(mc) - reloadAt) / gun.mechanics.reloadTicks());
    }

    private static void tick(Minecraft mc) {
        LocalPlayer player = mc.player;
        if (player == null || mc.level == null) {
            held = null;
            return;
        }
        ItemStack stack = player.getMainHandItem();
        GunItem gun = stack.getItem() instanceof GunItem g ? g : null;
        if (gun != held || player.getInventory().selected != heldSlot) {
            held = gun;
            heldSlot = player.getInventory().selected;
            reloadAt = -1;
            pending = 0;
            lastSeenAmmo = gun != null ? GunItem.ammo(stack) : 0;
            if (gun != null) {
                equipAt = mc.level.getGameTime();
                eventCursor = 0;
                playEvents(GunVisual.of(gun), "equip", 0);
                nextShot = mc.level.getGameTime() + 6;
            }
        }
        updateAim(mc, player, gun);
        if (gun == null) return;
        GunVisual visual = GunVisual.of(gun);
        // счётчик сервера догнал: снимаем столько же предсказанных выстрелов
        int real = GunItem.ammo(stack);
        if (real < lastSeenAmmo) pending = Math.max(0, pending - (lastSeenAmmo - real));
        else if (real > lastSeenAmmo) pending = 0;
        lastSeenAmmo = real;
        bloom = Math.max(0, bloom - 0.08f);
        long time = mc.level.getGameTime();
        // ---- перезарядка идёт по клипу
        if (reloadAt >= 0) {
            double elapsed = time - reloadAt;
            playEvents(visual, "reload", (float) (elapsed / 20));
            if (elapsed >= gun.mechanics.reloadTicks()) reloadAt = -1;
        }
        if (mc.screen == null) {
            while (RELOAD.consumeClick()) startReload(mc, player, gun, stack, visual);
            boolean firing = mc.options.keyAttack.isDown() || autoShots > 0;
            boolean allowed = firing && (gun.mechanics.automatic() || !wasFiring || autoShots > 0);
            if (allowed && reloadAt < 0 && time >= nextShot) shoot(mc, player, gun, stack, visual);
            wasFiring = firing;
        } else {
            wasFiring = false;
        }
    }

    private static void updateAim(Minecraft mc, LocalPlayer player, GunItem gun) {
        boolean want = gun != null && reloadAt < 0 && mc.screen == null && (autoAim || mc.options.keyUse.isDown()) && !player.isSprinting();
        aimKey = want;
        aim += ((want ? 1f : 0f) - aim) * 0.32f;
        boolean run = gun != null && player.isSprinting();
        sprint += ((run ? 1f : 0f) - sprint) * 0.22f;
        var speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            if (want && !speed.hasModifier(AIM_SLOW)) {
                speed.addTransientModifier(new AttributeModifier(AIM_SLOW, -0.35, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
            } else if (!want && speed.hasModifier(AIM_SLOW)) {
                speed.removeModifier(AIM_SLOW);
            }
        }
    }

    private static void shoot(Minecraft mc, LocalPlayer player, GunItem gun, ItemStack stack, GunVisual visual) {
        long time = mc.level.getGameTime();
        if (shownAmmo(stack) <= 0) {
            nextShot = time + 6;
            if (!wasFiring) playLocal(GunClips.sound("gun_dry"), 0.7f, 1f);
            startReload(mc, player, gun, stack, visual);
            return;
        }
        nextShot = time + gun.mechanics.interval();
        if (autoShots > 0) autoShots--;
        pending++;
        player.setSprinting(false);
        ClientPlayNetworking.send(new GunActionPayload(GunActionPayload.FIRE, aimKey));
        fireAt = now(mc);
        bloom = Math.min(1, bloom + (gun.mechanics.kind() == GunItem.Kind.LAS ? 0.22f : 0.38f));
        GunView.onShot(visual, player);
        boolean las = gun.mechanics.kind() == GunItem.Kind.LAS;
        String name = (las ? "las_fire" : "bolter_fire");
        playLocal(GunClips.sound(name), las ? 0.75f : 1.15f, 0.97f + player.getRandom().nextFloat() * 0.06f);
    }

    private static void startReload(Minecraft mc, LocalPlayer player, GunItem gun, ItemStack stack, GunVisual visual) {
        if (reloadAt >= 0 || shownAmmo(stack) >= gun.mechanics.magSize()) return;
        boolean has = player.getAbilities().instabuild || player.getInventory().contains(new ItemStack(gun.ammoItem()));
        if (!has) {
            playLocal(GunClips.sound("gun_dry"), 0.7f, 0.8f);
            return;
        }
        ClientPlayNetworking.send(new GunActionPayload(GunActionPayload.RELOAD, false));
        reloadAt = mc.level.getGameTime();
        eventCursor = 0;
    }

    private static void playEvents(GunVisual visual, String clip, float seconds) {
        var events = GunClips.get(visual.model(), clip).events();
        while (eventCursor < events.size() && events.get(eventCursor).time() <= seconds) {
            playLocal(GunClips.sound(events.get(eventCursor).name()), 0.8f, 1f);
            eventCursor++;
        }
    }

    /** Какой клип показывать в этом кадре и сколько секунд он идёт. */
    static GunClips.Clip activeClip(GunVisual visual, Minecraft mc, float[] secondsOut) {
        double t = now(mc);
        if (reloadAt >= 0) {
            secondsOut[0] = (float) ((t - reloadAt) / 20);
            return GunClips.get(visual.model(), "reload");
        }
        GunClips.Clip equip = GunClips.get(visual.model(), "equip");
        if (equipAt >= 0 && (t - equipAt) / 20 < equip.length()) {
            secondsOut[0] = (float) ((t - equipAt) / 20);
            return equip;
        }
        GunClips.Clip fire = GunClips.get(visual.model(), "fire");
        if (fireAt >= 0 && (t - fireAt) / 20 < fire.length()) {
            secondsOut[0] = (float) ((t - fireAt) / 20);
            return fire;
        }
        secondsOut[0] = 0;
        return GunClips.get(visual.model(), "idle");
    }

    /** Команды сценария автотеста: gun fire 5, gun aim on, gun reload. */
    public static void autotest(String arg) {
        String[] parts = arg.trim().split("\\s+");
        Minecraft mc = Minecraft.getInstance();
        switch (parts[0]) {
            case "fire" -> autoShots = parts.length > 1 ? Integer.parseInt(parts[1]) : 1;
            case "flash" -> GunView.holdFlash = parts.length > 1 && parts[1].equals("on");
            case "aim" -> autoAim = parts.length > 1 && parts[1].equals("on");
            case "reload" -> {
                if (held != null && mc.player != null) startReload(mc, mc.player, held, mc.player.getMainHandItem(), GunVisual.of(held));
            }
            default -> throw new IllegalArgumentException(arg);
        }
    }
}
