package dev.warpbound.client.gun;

import dev.warpbound.gear.ChainswordItem;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Цепной меч на клиенте: обороты мотора, бег цепи, серия ударов при удержании, звук двигателя. Урон и попадание считает обычная атака. */
public final class ChainswordClient {
    private static final String[] SWINGS = {"swing_a", "swing_b", "swing_c"};
    /** Шагов цепи в секунду: на холостом ходу и на полных оборотах. */
    private static final float IDLE_RATE = 2.5f, FULL_RATE = 15f;
    private static boolean held, wasSwinging;
    private static int heldSlot = -1, swingIndex, smoke;
    private static double equipAt = -1, swingAt = -1;
    private static String swingClip = SWINGS[0];
    private static float rev;
    private static float phase;
    private static long lastNanos;
    private static EngineSound engine;
    private static boolean autoRev;

    private ChainswordClient() {
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(ChainswordClient::tick);
    }

    static float rev() {
        return rev;
    }

    /** Команда автотеста: держать мотор на полных оборотах. */
    public static void autoRev(boolean on) {
        autoRev = on;
    }

    /** Положение цепи от 0 до 1 в пределах одного шага. Считается по настоящему времени, один раз на кадр. */
    static float chainPhase() {
        long now = System.nanoTime();
        float dt = lastNanos == 0 ? 0 : Math.min(0.1f, (now - lastNanos) / 1e9f);
        lastNanos = now;
        phase += dt * Mth.lerp(rev, IDLE_RATE, FULL_RATE);
        phase -= (float) Math.floor(phase);
        return phase;
    }

    private static void tick(Minecraft mc) {
        LocalPlayer player = mc.player;
        if (player == null || mc.level == null) {
            held = false;
            return;
        }
        boolean now = player.getMainHandItem().getItem() instanceof ChainswordItem;
        if (now && (!held || player.getInventory().selected != heldSlot)) {
            equipAt = GunClient.now(mc);
            swingAt = -1;
            mc.level.playLocalSound(player.getX(), player.getEyeY(), player.getZ(), GunClips.sound("chainsword_start"), SoundSource.PLAYERS, 0.8f, 1f, false);
        }
        held = now;
        heldSlot = player.getInventory().selected;
        if (!held) {
            rev = Math.max(0, rev - 0.1f);
            return;
        }
        // ---- новая дуга каждого взмаха: ванильный счётчик взмаха только начал идти
        boolean swinging = player.swinging && player.swingTime <= 1;
        if (swinging && !wasSwinging) {
            swingIndex = (swingIndex + 1) % SWINGS.length;
            swingClip = SWINGS[swingIndex];
            swingAt = GunClient.now(mc);
            mc.level.playLocalSound(player.getX(), player.getEyeY(), player.getZ(), GunClips.sound("chainsword_swing"), SoundSource.PLAYERS, 0.75f, 0.92f + player.getRandom().nextFloat() * 0.16f, false);
        }
        wasSwinging = swinging;
        // ---- удержание ЛКМ: удар за ударом, как только оружие готово. В блок не лезем: это обычная добыча
        boolean attack = mc.screen == null && mc.options.keyAttack.isDown();
        if (attack && player.getAttackStrengthScale(0f) >= 1f && mc.gameMode != null) {
            HitResult hit = mc.hitResult;
            if (hit instanceof EntityHitResult eh) {
                mc.gameMode.attack(player, eh.getEntity());
                player.swing(InteractionHand.MAIN_HAND);
            } else if (hit == null || hit.getType() == HitResult.Type.MISS) {
                player.resetAttackStrengthTicker();
                player.swing(InteractionHand.MAIN_HAND);
            }
        }
        boolean inSwing = swingAt >= 0 && (GunClient.now(mc) - swingAt) / 20 < 0.75;
        float target = attack || inSwing || autoRev ? 1f : 0f;
        rev += (target - rev) * (target > rev ? 0.3f : 0.09f);
        // ---- звук и выхлоп
        if (engine == null || engine.isStopped()) {
            engine = new EngineSound(player);
            mc.getSoundManager().play(engine);
        }
        // выхлоп только со стороны: частица в полуметре от камеры закрывает полэкрана
        if (!mc.options.getCameraType().isFirstPerson() && ++smoke >= (rev > 0.5f ? 2 : 7)) {
            smoke = 0;
            Vec3 look = player.getViewVector(1f);
            Vec3 right = look.cross(new Vec3(0, 1, 0));
            right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
            Vec3 at = player.getEyePosition(1f).add(look.scale(0.55)).add(right.scale(0.34)).add(0, -0.1, 0);
            mc.level.addParticle(ParticleTypes.SMOKE, at.x, at.y, at.z, look.x * 0.02, 0.03, look.z * 0.02);
        }
    }

    /** Какой клип показывать в первом лице и сколько секунд он идёт. */
    static GunClips.Clip activeClip(Minecraft mc, float[] secondsOut) {
        double t = GunClient.now(mc);
        if (swingAt >= 0) {
            GunClips.Clip clip = GunClips.get(ChainswordRenderer.MODEL, swingClip);
            if ((t - swingAt) / 20 < clip.length()) {
                secondsOut[0] = (float) ((t - swingAt) / 20);
                return clip;
            }
        }
        GunClips.Clip equip = GunClips.get(ChainswordRenderer.MODEL, "equip");
        if (equipAt >= 0 && (t - equipAt) / 20 < equip.length()) {
            secondsOut[0] = (float) ((t - equipAt) / 20);
            return equip;
        }
        secondsOut[0] = 0;
        return GunClips.get(ChainswordRenderer.MODEL, "idle");
    }

    /** Мотор: один зацикленный звук, обороты меняют высоту и громкость. Глохнет, когда меч убран. */
    private static final class EngineSound extends AbstractTickableSoundInstance {
        private final LocalPlayer player;

        EngineSound(LocalPlayer player) {
            super(GunClips.sound("chainsword_engine"), SoundSource.PLAYERS, SoundInstance.createUnseededRandom());
            this.player = player;
            looping = true;
            delay = 0;
            volume = 0.2f;
            pitch = 0.75f;
            x = player.getX();
            y = player.getY();
            z = player.getZ();
        }

        @Override
        public void tick() {
            if (player.isRemoved() || !(player.getMainHandItem().getItem() instanceof ChainswordItem)) {
                stop();
                return;
            }
            x = player.getX();
            y = player.getEyeY();
            z = player.getZ();
            volume = 0.3f + 0.7f * rev;
            pitch = 0.9f + 0.45f * rev;
        }
    }
}
