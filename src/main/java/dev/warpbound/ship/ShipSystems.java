package dev.warpbound.ship;

import dev.warpbound.core.WarpboundEffects;
import dev.warpbound.core.WarpboundSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;

import java.util.Optional;

/**
 * Системы корабля, которыми командуют с пульта мостика:
 * <ul>
 *   <li>реактор — режим (холостой, штатный, форсаж, заглушен) задаёт мощность и нагрев;</li>
 *   <li>распределение мощности на Поле Геллера — чем больше, тем медленнее Поле проседает в варпе
 *       и быстрее заряжается на орбите, но реактор греется сильнее;</li>
 *   <li>импульс Поля — мгновенно добавляет прочности ценой резкого нагрева;</li>
 *   <li>промывка охладителя — сбивает нагрев, долго перезаряжается;</li>
 *   <li>радиация — копится в реакторном отсеке при нагреве выше 70 % и облучает всех рядом с ядром.</li>
 * </ul>
 * Цифры баланса пока здесь; переедут в конфиг, когда устоятся.
 */
public final class ShipSystems {
    public enum ReactorMode {
        IDLE(0.3f, 0.15f), NORMAL(0.75f, 0.45f), OVERDRIVE(1.0f, 0.82f), SCRAM(0f, 0f);

        /** Мощность (0..1) и нагрев, к которому реактор стремится в этом режиме. */
        public final float power, heat;

        ReactorMode(float power, float heat) {
            this.power = power;
            this.heat = heat;
        }

        public static ReactorMode of(Ship ship) {
            ReactorMode[] v = values();
            return ship.reactorMode >= 0 && ship.reactorMode < v.length ? v[ship.reactorMode] : NORMAL;
        }
    }

    public static final float RAD_THRESHOLD = 0.7f;
    public static final int BOOST_COOLDOWN = 20 * 120, FLUSH_COOLDOWN = 20 * 60;
    private static final float BOOST_FIELD = 0.15f, BOOST_HEAT = 0.22f, FLUSH_HEAT = 0.3f;
    private static final double RAD_RANGE = 7;

    private ShipSystems() {
    }

    /** Сколько мощности реально идёт на Поле: доля распределения × мощность реактора. */
    public static float fieldSupply(Ship ship) {
        return ship.gellerPower * ReactorMode.of(ship).power;
    }

    /** На форсаже переход идёт на треть быстрее. */
    public static int transitStep(Ship ship) {
        if (ship.state == ShipState.TRANSIT && ReactorMode.of(ship) == ReactorMode.OVERDRIVE && ship.stateTicks % 3 == 0) return 2;
        return 1;
    }

    static void tick(MinecraftServer server, Ship ship) {
        ReactorMode mode = ReactorMode.of(ship);
        // нагрев тянется к уровню режима; распределение на Поле добавляет до 15 %
        float target = Math.min(1f, mode.heat + (mode == ReactorMode.SCRAM ? 0 : ship.gellerPower * 0.15f));
        ship.heat += (target - ship.heat) * (target > ship.heat ? 0.0015f : 0.004f);
        ship.heat = Mth.clamp(ship.heat, 0f, 1f);
        if (ship.boostCooldown > 0) ship.boostCooldown--;
        if (ship.flushCooldown > 0) ship.flushCooldown--;

        // радиация растёт от перегрева и медленно выветривается
        if (ship.heat > RAD_THRESHOLD) ship.radiation += (ship.heat - RAD_THRESHOLD) * 0.0025f;
        else ship.radiation -= 0.0008f;
        ship.radiation = Mth.clamp(ship.radiation, 0f, 1f);

        if (ship.radiation > 0.05f && server.getTickCount() % 40 == 0) irradiate(server, ship);
        if (ship.heat > 0.92f && server.getTickCount() % 200 == 0) {
            for (ServerPlayer p : ShipService.crew(server, ship)) {
                p.displayClientMessage(Component.translatable("ship.warpbound.reactor_critical").withStyle(ChatFormatting.RED, ChatFormatting.BOLD), true);
            }
        }
    }

    /** Ядро реактора этого корабля в мире интерьеров (из раскладки). */
    public static Optional<BlockPos> reactorPos(Ship ship) {
        if (ship.reactorRel != null) return Optional.of(ShipInteriors.origin(ship.plot).offset(ship.reactorRel));
        if (ship.layout == null) return Optional.empty();
        return ShipLayout.REGISTRY.get(ship.layout).flatMap(ShipLayout::reactor)
                .map(r -> ShipInteriors.origin(ship.plot).offset(r));
    }

    private static void irradiate(MinecraftServer server, Ship ship) {
        BlockPos core = reactorPos(ship).orElse(null);
        if (core == null) return;
        int level = ship.radiation > 0.66f ? 2 : ship.radiation > 0.33f ? 1 : 0;
        for (ServerPlayer p : ShipService.crew(server, ship)) {
            double d = Math.sqrt(p.blockPosition().distSqr(core));
            if (d > RAD_RANGE + level * 3) continue;
            p.addEffect(new MobEffectInstance(WarpboundEffects.RADIATION, 120, level, false, true, true));
        }
    }

    // ---- действия с пульта

    public static boolean setReactorMode(Ship ship, int mode) {
        if (mode < 0 || mode >= ReactorMode.values().length) return false;
        ship.reactorMode = mode;
        return true;
    }

    public static boolean setGellerPower(Ship ship, float value) {
        ship.gellerPower = Mth.clamp(Math.round(value * 4) / 4f, 0f, 1f);
        return true;
    }

    public static boolean boostField(ServerLevel level, Ship ship) {
        if (ship.boostCooldown > 0 || ReactorMode.of(ship) == ReactorMode.SCRAM) return false;
        ship.field = Math.min(1f, ship.field + BOOST_FIELD);
        ship.heat = Math.min(1f, ship.heat + BOOST_HEAT);
        ship.boostCooldown = BOOST_COOLDOWN;
        reactorPos(ship).ifPresent(p -> level.playSound(null, p, WarpboundSounds.WARP_BURST, SoundSource.BLOCKS, 1f, 1.6f));
        return true;
    }

    public static boolean flushCoolant(ServerLevel level, Ship ship) {
        if (ship.flushCooldown > 0) return false;
        ship.heat = Math.max(0f, ship.heat - FLUSH_HEAT);
        ship.flushCooldown = FLUSH_COOLDOWN;
        reactorPos(ship).ifPresent(p -> level.playSound(null, p, SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 2f, 0.6f));
        return true;
    }
}
