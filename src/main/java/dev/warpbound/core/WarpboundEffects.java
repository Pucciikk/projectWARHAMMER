package dev.warpbound.core;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

/**
 * Эффекты мода. Радиация — от перегретого реактора корабля и от сырого радия в инвентаре:
 * урон раз в две секунды (сильнее с уровнем) и голод. Свинец и респиратор будут защищать (позже).
 */
public final class WarpboundEffects {
    public static final Holder<MobEffect> RADIATION = Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT,
            Warpbound.id("radiation"), new Radiation());

    private WarpboundEffects() {
    }

    public static void register() {
        // сырой радий облучает того, кто его несёт: немного, но постоянно
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (server.getTickCount() % 100 != 0) return;
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                if (p.isCreative() || p.isSpectator()) continue;
                int radium = p.getInventory().countItem(WarpboundBuildingBlocks.RAW_RADIUM)
                        + p.getInventory().countItem(WarpboundBuildingBlocks.RADIUM_ORE.asItem());
                if (radium > 0) p.addEffect(new MobEffectInstance(RADIATION, 140, radium >= 32 ? 1 : 0, false, true, true));
            }
        });
    }

    private static final class Radiation extends MobEffect {
        Radiation() {
            super(MobEffectCategory.HARMFUL, 0x8CFF3A);
        }

        @Override
        public boolean applyEffectTick(LivingEntity entity, int amplifier) {
            entity.hurt(entity.damageSources().magic(), 1f + amplifier);
            if (entity instanceof Player player) player.causeFoodExhaustion(0.6f * (amplifier + 1));
            return true;
        }

        @Override
        public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
            return duration % Math.max(10, 40 - amplifier * 10) == 0;
        }
    }
}
